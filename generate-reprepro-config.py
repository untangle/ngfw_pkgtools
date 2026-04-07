#!/usr/bin/env python3
"""
Generate reprepro config files (distributions, updates, pulls) from hiera YAML.

Replaces the Puppet ERB templates that previously generated these configs
on package-server.untangle.int (aws-build-03).

Usage examples:
  # Package-server configs (default):
  python3 generate-reprepro-config.py \\
    --yaml-file /path/to/untangle.int.yaml \\
    --codename bullseye \\
    --output-dir /var/www/public/debian-mirror/bullseye/conf/

  # Updates drive configs (uses copy method instead of http):
  python3 generate-reprepro-config.py \\
    --yaml-file /path/to/untangle.int.yaml \\
    --codename bullseye \\
    --method "copy:/var/www/public/bullseye" \\
    --output-dir /mnt/www/public/bullseye/conf/

  # Dry run — show diff without writing:
  python3 generate-reprepro-config.py \\
    --yaml-file /path/to/untangle.int.yaml \\
    --codename bullseye \\
    --output-dir /var/www/public/debian-mirror/bullseye/conf/ \\
    --dry-run
"""

import argparse
import difflib
import os
import re
import sys

import yaml


def parse_release_version(release):
    """Parse version from a release string like '17.4.1' or 'ngfw-17.4.1'.

    Matches Ruby's String#to_i behavior: returns 0 for non-numeric prefixes.
    """
    parts = release.split(".")
    try:
        major = int(parts[0])
    except ValueError:
        major = 0
    try:
        minor = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        minor = 0
    return major, minor


def parse_branch_version(branch):
    """Parse version from a branch string like 'ngfw-release-17.4' or 'release-16.3'."""
    m = re.search(r"release-(\d+)\.(\d+)", branch)
    if not m:
        raise ValueError(f"Cannot parse version from branch: {branch}")
    return int(m.group(1)), int(m.group(2))


def generate_distributions(dist):
    """Generate the distributions config file content."""
    codename = dist["codename"]
    version = dist["version"]
    gpg_key = dist["gpg_key"]
    architectures = dist["architectures"]
    components = dist["components"]
    ngfw_releases = dist.get("ngfw_releases", [])
    ngfw_branches = dist.get("ngfw_branches", [])
    waf_releases = dist.get("waf_releases", [])
    waf_branches = dist.get("waf_branches", [])
    stable_distribution = dist.get("stable_distribution")
    hostname = dist["_hostname"]

    archs_without_i386 = [a for a in architectures if a != "i386"]

    lines = []

    # --- Static Debian distributions ---
    lines.append("########################################################################")
    lines.append("# local Debian distributions")
    lines.append("")

    # main packages
    lines.append("# main packages")
    lines.append("Origin: Debian")
    lines.append("Label: Debian")
    lines.append(f"Version: {version}")
    lines.append(f"Codename: {codename}-official")
    lines.append(f"SignWith: {gpg_key}")
    lines.append(f"Architectures: {' '.join(architectures)} source")
    lines.append(f"Update: debian-official debian-official-udeb")
    lines.append("Components: main contrib non-free")
    lines.append("UDebComponents: main")
    lines.append("Description: Debian")
    lines.append("Log: debian.log")
    lines.append("")

    # backports
    lines.append("# backports")
    lines.append("Origin: Debian")
    lines.append("Label: Debian")
    lines.append(f"Version: {version}")
    lines.append(f"Codename: {codename}-backports")
    lines.append(f"SignWith: {gpg_key}")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("Update: debian-backports debian-backports-armhf")
    lines.append("Components: main contrib non-free")
    lines.append("UDebComponents: main")
    lines.append("Description: Debian")
    lines.append("Log: debian-backports.log")
    lines.append("")

    # security
    lines.append("# security")
    lines.append("Origin: Debian")
    lines.append("Label: Debian")
    lines.append(f"Version: {version}")
    lines.append(f"Codename: {codename}-security")
    lines.append(f"SignWith: {gpg_key}")
    lines.append(f"Architectures: {' '.join(architectures)} source")
    lines.append("Update: debian-security debian-security-udeb")
    lines.append("Components: main")
    lines.append("UDebComponents: main")
    lines.append("Description: Debian")
    lines.append("Log: debian-security.log")
    lines.append("")

    # manual
    lines.append("# manual")
    lines.append("Origin: Debian")
    lines.append("Label: Debian")
    lines.append(f"Version: {version}")
    lines.append(f"Codename: {codename}-manual")
    lines.append(f"SignWith: {gpg_key}")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("Components: main contrib non-free")
    lines.append("UDebComponents: main")
    lines.append("Description: Debian")
    lines.append("Log: debian-manual.log")
    lines.append("")

    # --- influxdb ---
    lines.append("########################################################################")
    lines.append("# local influxdb distributions")
    lines.append("")
    lines.append("Origin: influxdb")
    lines.append("Label: influxdb")
    lines.append("Codename: influxdb-stable")
    lines.append(f"SignWith: {gpg_key}")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("Update: influxdb-stable")
    lines.append("Components: stable")
    lines.append("Description: influxdb")
    lines.append("Log: influxdb.log")
    lines.append("")

    # --- commented-out empty distributions block ---
    lines.append("# ########################################################################")
    lines.append("# # Empty distributions, to accomodate building d-i & ISO images")
    lines.append("# # main packages")
    lines.append("# Origin: Untangle")
    lines.append(f"# SignWith: {gpg_key}")
    lines.append("# Label: Untangle")
    lines.append(f"# Version: {version}")
    lines.append(f"# Codename: {codename}")
    lines.append(f"# Architectures: {' '.join(architectures)}")
    lines.append("# Components: main contrib non-free")
    lines.append("# Description: Debian")
    lines.append(f"# Log: {codename}.log")
    lines.append("")

    # --- NGFW distributions ---
    lines.append("########################################################################")
    lines.append("# Untangle NGFW distributions")
    lines.append("")

    for release in ngfw_releases:
        if release == "current":
            continue
        major, minor = parse_release_version(release)
        greater_than_16_1 = (major >= 16 and minor >= 1) or major > 16
        archs = archs_without_i386 if greater_than_16_1 else architectures

        lines.append("Origin: Untangle")
        lines.append(f"SignWith: {gpg_key}")
        lines.append("Label: Untangle")
        lines.append(f"Codename: {release}")
        lines.append(f"Suite: {release}")
        lines.append(f"Version: {release}")
        lines.append(f"Update: {release}-normal {release}-binary")
        lines.append(f"Architectures: {' '.join(archs)} source")
        lines.append(f"Components: {' '.join(components)}")
        lines.append("#Contents: .gz .bz2")
        lines.append("UDebComponents: main")
        lines.append("Description: Untangle")
        lines.append(f"Log: {release}.log")
        lines.append("")

    for branch in ngfw_branches:
        major, minor = parse_branch_version(branch)
        greater_than_16_2 = (major >= 16 and minor >= 2) or major > 16
        greater_than_16_4 = (major >= 16 and minor >= 4) or major > 16
        archs = archs_without_i386 if greater_than_16_2 else architectures
        branch_codename = branch if greater_than_16_4 else f"current-release{major}{minor}"
        branch_version = branch_codename if greater_than_16_4 else f"release{major}{minor}"

        lines.append("Origin: Untangle")
        lines.append(f"SignWith: {gpg_key}")
        lines.append("Label: Untangle")
        lines.append(f"Codename: {branch_codename}")
        if branch_codename == stable_distribution:
            lines.append("Suite: stable")
        lines.append(f"Version: {branch_version}")
        update_line = (
            f"Update: update-debian-{codename} update-debian-{codename}-backports "
            f"update-debian-{codename}-security update-debian-{codename}-manual"
        )
        lines.append(update_line)
        lines.append(f"Architectures: {' '.join(archs)} source")
        lines.append(f"Components: {' '.join(components)}")
        lines.append("#Contents: .gz .bz2")
        lines.append("UDebComponents: main")
        lines.append("Description: Untangle")
        lines.append(f"Log: {branch_codename}.log")
        lines.append("")

    # current distribution
    if hostname == "aws-build-03":
        current_update = (
            f"update-debian-{codename} update-debian-{codename}-backports "
            f"update-debian-{codename}-security update-debian-{codename}-manual"
        )
    else:
        current_update = "current-normal current-binary"

    current_archs = archs_without_i386 if codename == "buster" else architectures

    lines.append("Origin: Untangle")
    lines.append(f"SignWith: {gpg_key}")
    lines.append("Label: Untangle")
    lines.append("Codename: current")
    lines.append("Suite: testing")
    lines.append("Version: current")
    lines.append(f"Update: {current_update}")
    lines.append(f"Architectures: {' '.join(current_archs)} source")
    lines.append(f"Components: {' '.join(components)}")
    lines.append("#Contents: .gz .bz2")
    lines.append("UDebComponents: main")
    lines.append("Description: Untangle")
    lines.append("Log: current.log")
    lines.append("")

    # --- WAF distributions ---
    lines.append("########################################################################")
    lines.append("# Untangle WAF distributions")
    lines.append("")

    for waf_release in waf_releases:
        if waf_release == "waf-current":
            continue
        lines.append("Origin: Untangle")
        lines.append(f"SignWith: {gpg_key}")
        lines.append("Label: Untangle")
        lines.append(f"Codename: {waf_release}")
        lines.append(f"Suite: {waf_release}")
        lines.append(f"Version: {waf_release}")
        lines.append(f"Update: {waf_release}-normal {waf_release}-binary")
        lines.append(f"Architectures: {' '.join(archs_without_i386)} source")
        lines.append(f"Components: {' '.join(components)}")
        lines.append("#Contents: .gz .bz2")
        lines.append("UDebComponents: main")
        lines.append("Description: Untangle")
        lines.append(f"Log: {waf_release}.log")
        lines.append("")

    for branch in waf_branches:
        major, minor = parse_branch_version(branch)
        branch_codename = branch

        lines.append("Origin: Untangle")
        lines.append(f"SignWith: {gpg_key}")
        lines.append("Label: Untangle")
        lines.append(f"Codename: {branch_codename}")
        lines.append(f"Version: {branch_codename}")
        update_line = (
            f"Update: update-debian-{codename} update-debian-{codename}-backports "
            f"update-debian-{codename}-security update-debian-{codename}-manual"
        )
        lines.append(update_line)
        lines.append(f"Architectures: {' '.join(archs_without_i386)} source")
        lines.append(f"Components: {' '.join(components)}")
        lines.append("#Contents: .gz .bz2")
        lines.append("UDebComponents: main")
        lines.append("Description: Untangle")
        lines.append(f"Log: {branch_codename}.log")
        lines.append("")

    # waf-current distribution
    if hostname == "build-03":
        waf_current_update = (
            f"update-debian-{codename} update-debian-{codename}-backports "
            f"update-debian-{codename}-security update-debian-{codename}-manual "
            f"update-influxdb-{codename}"
        )
    else:
        waf_current_update = "waf-current-normal waf-current-binary"

    lines.append("Origin: Untangle")
    lines.append(f"SignWith: {gpg_key}")
    lines.append("Label: Untangle")
    lines.append("Codename: waf-current")
    lines.append("Suite: waf-current")
    lines.append("Version: waf-current")
    lines.append(f"Update: {waf_current_update}")
    lines.append("Pull: from-ngfw-current")
    lines.append(f"Architectures: {' '.join(archs_without_i386)} source")
    lines.append(f"Components: {' '.join(components)}")
    lines.append("#Contents: .gz .bz2")
    lines.append("UDebComponents: main")
    lines.append("Description: Untangle")
    lines.append("Log: waf-current.log")

    return "\n".join(lines) + "\n"


def generate_updates(dist):
    """Generate the updates config file content."""
    codename = dist["codename"]
    version = dist["version"]
    architectures = dist["architectures"]
    ngfw_releases = dist.get("ngfw_releases", [])
    waf_releases = dist.get("waf_releases", [])
    method = dist["_method"]

    lines = []

    # --- NGFW release sync entries ---
    lines.append("########################################################################")
    lines.append("# Those are used for sync'ing NGFW releases from package-server.u.i to")
    lines.append("# updates.u.c")

    for release in ngfw_releases:
        major, minor = parse_release_version(release)
        greater_than_16_1 = (major >= 16 and minor >= 1) or major > 16
        archs = [a for a in architectures if not (greater_than_16_1 and a == "i386")]

        lines.append(f"Name: {release}-normal")
        lines.append(f"Method: {method}")
        lines.append(f"Suite: {release}")
        lines.append("Components: main")
        lines.append("VerifyRelease: blindtrust")
        lines.append("")
        lines.append(f"Name: {release}-binary")
        lines.append(f"Method: {method}")
        lines.append(f"Suite: {release}")
        lines.append("Components: non-free")
        lines.append(f"Architectures: {' '.join(archs)}")
        lines.append("VerifyRelease: blindtrust")
        lines.append("")

    lines.append("")

    # --- WAF release sync entries ---
    lines.append("########################################################################")
    lines.append("# Those are used for sync'ing WAF releases from package-server.u.i to")
    lines.append("# updates.u.c")

    for release in waf_releases:
        lines.append(f"Name: {release}-normal")
        lines.append(f"Method: {method}")
        lines.append(f"Suite: {release}")
        lines.append("Components: main")
        lines.append("VerifyRelease: blindtrust")
        lines.append("")
        lines.append(f"Name: {release}-binary")
        lines.append(f"Method: {method}")
        lines.append(f"Suite: {release}")
        lines.append("Components: non-free")
        lines.append(f"Architectures: {' '.join(architectures)}")
        lines.append("VerifyRelease: blindtrust")
        lines.append("")

    lines.append("")

    # --- Debian update sources ---
    lines.append("########################################################################")
    lines.append("# the debian-* update modules are used to dump packages from remote")
    lines.append("# official Debian mirrors into our local mirrors")
    lines.append("")

    # main packages
    lines.append("# main packages")
    lines.append("Name: debian-official")
    lines.append("Method: http://ftp.us.debian.org/debian")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}")
    lines.append("Components: main contrib non-free")
    lines.append(f"Architectures: {' '.join(architectures)} source")
    lines.append("FilterList: purge packages/debian.txt")
    lines.append("")

    # main packages (udeb)
    lines.append("# main packages (udeb)")
    lines.append("Name: debian-official-udeb")
    lines.append("Method: http://ftp.us.debian.org/debian")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}")
    lines.append("Components:")
    lines.append("UDebComponents: main")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("FilterList: purge packages/debian-udeb.txt")
    lines.append("")

    # backports
    lines.append("# backports")
    lines.append("Name: debian-backports")
    lines.append("Method: http://ftp.us.debian.org/debian")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}-backports")
    lines.append("Components: main contrib non-free")
    lines.append("UDebComponents: main")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("FilterList: purge packages/debian-backports.txt")
    lines.append("")

    # backports-armhf
    lines.append("# backports-armhf")
    lines.append("Name: debian-backports-armhf")
    lines.append("Method: http://ftp.us.debian.org/debian")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}-backports")
    lines.append("Components: main contrib non-free")
    lines.append("UDebComponents: main")
    lines.append("Architectures: armhf")
    lines.append("FilterList: purge packages/debian-backports-armhf.txt")
    lines.append("")

    # security
    lines.append("# security")
    lines.append("Name: debian-security")
    if version >= 11:
        lines.append("Method: http://security.debian.org/debian-security")
        lines.append(f"Suite: {codename}-security")
    else:
        lines.append("Method: http://security.debian.org")
        lines.append(f"Suite: {codename}/updates")
    lines.append("VerifyRelease: blindtrust")
    lines.append("Components: main contrib non-free")
    lines.append(f"Architectures: {' '.join(architectures)} source")
    lines.append("FilterList: purge packages/debian.txt")
    lines.append("")

    # security (udeb)
    lines.append("# security (udeb)")
    lines.append("Name: debian-security-udeb")
    if version >= 11:
        lines.append("Method: http://security.debian.org/debian-security")
        lines.append(f"Suite: {codename}-security")
    else:
        lines.append("Method: http://security.debian.org")
        lines.append(f"Suite: {codename}/updates")
    lines.append("VerifyRelease: blindtrust")
    lines.append("Components:")
    lines.append("UDebComponents: main")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("FilterList: purge packages/debian-udeb.txt")
    lines.append("")

    # --- influxdb ---
    lines.append("########################################################################")
    lines.append("# the influxdb-* update modules are used to dump packages from remote")
    lines.append("# official influxdb mirrors into our local mirrors")
    lines.append("")
    lines.append("Name: influxdb-stable")
    lines.append("Method: https://repos.influxdata.com/debian")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}")
    lines.append("Components: stable")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("FilterList: purge packages/influxdb.txt")
    lines.append("")

    # --- Local update modules ---
    lines.append("########################################################################")
    lines.append("# the update-debian-* update modules are used to dump packages from our")
    lines.append("# local official Debian mirrors into our distributions (nightly, chaos,")
    lines.append("# etc)")
    lines.append("")

    # main packages
    lines.append("# main packages")
    lines.append(f"Name: update-debian-{codename}")
    lines.append(f"Method: http://package-server/public/{codename}")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}-official")
    lines.append("Components: main>main contrib>main non-free>main")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("")

    # backports
    lines.append("# backports")
    lines.append(f"Name: update-debian-{codename}-backports")
    lines.append(f"Method: http://package-server/public/{codename}")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}-backports")
    lines.append("Components: main>main contrib>main non-free>main")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("")

    # security
    lines.append("# security")
    lines.append(f"Name: update-debian-{codename}-security")
    lines.append(f"Method: http://package-server/public/{codename}")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}-security")
    lines.append("Components: main>main # updates/main>main")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("")

    # manual
    lines.append("# manual")
    lines.append(f"Name: update-debian-{codename}-manual")
    lines.append(f"Method: http://package-server/public/{codename}")
    lines.append("VerifyRelease: blindtrust")
    lines.append(f"Suite: {codename}-manual")
    lines.append("Components: main>main contrib>main non-free>main # updates/main>main")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("")

    # --- influxdb local update ---
    lines.append("########################################################################")
    lines.append("# the update-influxdb-* update modules are used to dump packages from our")
    lines.append("# local official influxdb mirrors into our distributions (nightly, chaos,")
    lines.append("# etc)")
    lines.append("")
    lines.append(f"Name: update-influxdb-{codename}")
    lines.append(f"Method: http://package-server/public/{codename}")
    lines.append("VerifyRelease: blindtrust")
    lines.append("Suite: influxdb-stable")
    lines.append("Components: stable>main")
    lines.append("UDebComponents:")
    lines.append(f"Architectures: {' '.join(architectures)}")
    lines.append("")

    # old
    lines.append("# old")
    lines.append("Name: localreadd")
    lines.append("Suite: *")
    lines.append(f"Method: copy:/disks/volume1/packages/{codename}-old")

    return "\n".join(lines) + "\n"


def generate_pulls():
    """Generate the pulls config file content."""
    lines = [
        "Name: from-ngfw-current",
        "From: current",
        "FilterList: purge packages/ngfw-to-waf.txt",
    ]
    return "\n".join(lines) + "\n"


def load_yaml(yaml_file):
    with open(yaml_file) as f:
        return yaml.safe_load(f)


def show_diff(filename, old_content, new_content):
    """Show a unified diff between old and new content."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}")
    diff_text = "".join(diff)
    if diff_text:
        return diff_text
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate reprepro config files from hiera YAML data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--yaml-file",
        required=True,
        help="Path to the hiera YAML file (e.g., untangle.int.yaml)",
    )
    parser.add_argument(
        "--codename",
        required=True,
        help="Distribution codename to generate configs for (e.g., bullseye)",
    )
    parser.add_argument(
        "--public-ip",
        default="localhost",
        help="Public IP for update method URLs (default: localhost)",
    )
    parser.add_argument(
        "--method",
        default=None,
        help=(
            "Override the sync method URL entirely "
            "(e.g., 'copy:/var/www/public/bullseye' for updates drive). "
            "If not specified, uses 'http://<public-ip>/public/<codename>'"
        ),
    )
    parser.add_argument(
        "--hostname",
        default="aws-build-03",
        help="Hostname of the target server (default: aws-build-03). "
        "Controls 'current' distribution update behavior.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write the generated config files to",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated/changed without writing files",
    )

    args = parser.parse_args()

    # Load YAML
    data = load_yaml(args.yaml_file)
    distributions = data.get("ut_package_server::distributions", {})

    if args.codename not in distributions:
        print(f"Error: codename '{args.codename}' not found in YAML.", file=sys.stderr)
        print(f"Available codenames: {', '.join(distributions.keys())}", file=sys.stderr)
        sys.exit(1)

    dist = distributions[args.codename]

    # Ensure version is numeric for comparisons
    version = dist.get("version", 0)
    if isinstance(version, str):
        try:
            version = float(version)
        except ValueError:
            version = 0
    dist["version"] = version

    # Compute the method URL for sync entries
    if args.method:
        method = args.method
    else:
        method = f"http://{args.public_ip}/public/{args.codename}"
    dist["_method"] = method
    dist["_hostname"] = args.hostname

    # Generate all three config files
    configs = {
        "distributions": generate_distributions(dist),
        "updates": generate_updates(dist),
        "pulls": generate_pulls(),
    }

    if args.dry_run:
        print("=== DRY RUN — no files will be written ===\n")
        has_changes = False

        for filename, content in configs.items():
            filepath = os.path.join(args.output_dir, filename)
            if os.path.exists(filepath):
                with open(filepath) as f:
                    existing = f.read()
                diff = show_diff(filename, existing, content)
                if diff:
                    has_changes = True
                    print(f"--- {filename}: CHANGES DETECTED ---")
                    print(diff)
                else:
                    print(f"--- {filename}: no changes ---")
            else:
                has_changes = True
                print(f"--- {filename}: NEW FILE (does not exist yet) ---")
                print(content)
            print()

        if not has_changes:
            print("All config files are already up to date.")
        return

    # Write files
    os.makedirs(args.output_dir, exist_ok=True)
    for filename, content in configs.items():
        filepath = os.path.join(args.output_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Wrote {filepath}")

    print("\nDone. Config files generated successfully.")


if __name__ == "__main__":
    main()
