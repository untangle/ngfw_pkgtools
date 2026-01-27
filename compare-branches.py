#! /usr/bin/env python3

import argparse
import logging
import sys
from typing import Optional, Tuple, Any

# relative to cwd
from lib import repoinfo
from lib import gerrit_api
from lib import github_api

# constants
HEADER1_TPL = "{branchFrom} vs. {branchTo}"
HEADER2_TPL = "    {repository}"
OUTPUT_COMPARE_TPL = "        {ahead:>02} ahead, {behind:>02} behind {extra}"
OUTPUT_MERGE_TPL = "        merge {status}"


# Unified interface functions that route to GitHub or Gerrit
def merge(repository: str, branch_from: str, branch_to: str, repo_type: str = "github") -> Tuple[bool, str]:
    """Merge branches - routes to GitHub or Gerrit based on repo_type."""
    if repo_type == "gerrit":
        return gerrit_api.merge_branches(repository, branch_from, branch_to)
    else:
        return github_api.merge_branches(repository, branch_from, branch_to)


def compare(
    repository: str, branch_from: str, branch_to: str, repo_type: str = "github"
) -> Tuple[Optional[int], Optional[int], Any]:
    """Compare branches - routes to GitHub or Gerrit based on repo_type."""
    if repo_type == "gerrit":
        return gerrit_api.compare_branches(repository, branch_from, branch_to)
    else:
        return github_api.compare_branches(repository, branch_from, branch_to)


def create_pr(repository: str, branch_to: str, new_branch: str, branch_from: str, repo_type: str = "github") -> Tuple[int, str]:
    """Create PR/Change - routes to GitHub or Gerrit based on repo_type."""
    if repo_type == "gerrit":
        sc, change_id = gerrit_api.create_change(repository, branch_to, branch_from)
        return sc, change_id if change_id else ""
    else:
        return github_api.create_pr(repository, branch_to, new_branch, branch_from)


def create_branch(repository: str, branch_from: str, branch_to: str, repo_type: str = "github"):
    """Create branch - routes to GitHub or Gerrit based on repo_type."""
    if repo_type == "gerrit":
        # For Gerrit, we don't create temporary branches the same way
        # Return a placeholder
        logging.warning("Branch creation for Gerrit not implemented - using change workflow")
        return None, None
    else:
        return github_api.create_branch(repository, branch_from, branch_to)


def get_head_sha(repository: str, branch: str, repo_type: str = "github") -> str:
    """Get HEAD SHA - routes to GitHub or Gerrit based on repo_type."""
    if repo_type == "gerrit":
        sha = gerrit_api.get_branch_revision(repository, branch)
        return sha if sha else ""
    else:
        return github_api.get_branch_revision(repository, branch)


# CL options
parser = argparse.ArgumentParser(
    description="""List differences
between two branches across multiple repositories.

It can also optionally try to merge the branches before computing
the differences."""
)

parser.add_argument(
    "--log-level",
    dest="logLevel",
    choices=["debug", "info", "warning"],
    default="warning",
    help="level at which to log",
)
parser.add_argument(
    "--merge",
    dest="merge",
    action="store_true",
    default=False,
    help="try to merge first (default=False)",
)
parser.add_argument(
    "--pull-request",
    dest="openpr",
    action="store_true",
    default=False,
    help="open PR on failed merges (default=False)",
)
parser.add_argument(
    "--branch-from",
    dest="branchFrom",
    required=True,
    metavar="BRANCH_FROM",
    help="base branch)",
)
parser.add_argument(
    "--branch-to",
    dest="branchTo",
    required=True,
    metavar="BRANCH_TO",
    help="target branch)",
)

target = parser.add_mutually_exclusive_group(required=True)
target.add_argument(
    "--product",
    type=str,
    dest="product",
    metavar="PRODUCT",
    choices=("mfw", "ngfw", "waf", "efw", "velo"),
    help="product to work on",
)
target.add_argument(
    "--repositories",
    type=str,
    dest="repositories",
    nargs="*",
    metavar="REPOSITORIES",
    help="list of space-separated repositories to target",
)

if __name__ == "__main__":
    args = parser.parse_args()

    # logging
    logging.getLogger().setLevel(getattr(logging, args.logLevel.upper()))
    console = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("[%(asctime)s] changelog: %(levelname)-7s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

    product = args.product

    if args.repositories:
        # When repositories are specified directly, we need to get their info
        # For now, assume they're all GitHub unless we can look them up
        repo_objects = []
        for repo_name in args.repositories:
            # Try to find the repo in the product's repo list
            found = False
            if product:
                all_repos = repoinfo.list_repositories(product)
                for r in all_repos:
                    if r.name == repo_name:
                        repo_objects.append(r)
                        found = True
                        break
            if not found:
                # Create a minimal repo object with default values
                logging.warning(f"Repository {repo_name} not found in product config, assuming GitHub")
                from dataclasses import dataclass
                @dataclass
                class MinimalRepo:
                    name: str
                    repo_type: str = "github"
                    disable_forward_merge: bool = False
                repo_objects.append(MinimalRepo(name=repo_name))
    else:
        repo_objects = [
            r for r in repoinfo.list_repositories(product) if not r.disable_forward_merge
        ]

    branch_from, branch_to = args.branchFrom, args.branchTo
    rc = 0

    print(HEADER1_TPL.format(branchFrom=branch_from, branchTo=branch_to))

    for repo in repo_objects:
        repository = repo.name
        repo_type = getattr(repo, 'repo_type', 'github')
        
        s = [""]
        s.append(HEADER2_TPL.format(repository=repository))
        s.append(f"        type: {repo_type}")

        if args.merge:
            success, status = merge(repository, branch_from, branch_to, repo_type)
            logging.debug("For {}: success={}, status={}".format(repository, success, status))
            s.append(OUTPUT_MERGE_TPL.format(status=status))
            if success:
                print("\n".join(s))
                continue
            else:
                rc = 1

        ahead, behind, extra = compare(repository, branch_from, branch_to, repo_type)
        if ahead is None:
            continue

        s.append(OUTPUT_COMPARE_TPL.format(ahead=ahead, behind=behind, extra=extra))
        print("\n".join(s))

        if args.openpr:
            if repo_type == "gerrit":
                # For Gerrit, create a change directly
                success, change_id = create_pr(repository, branch_to, "", branch_from, repo_type)
                if not success:
                    print("Unable to create Gerrit change - merge manually pls")
                    exit(1)
                else:
                    print(f"Created Gerrit change: {change_id}")
            else:
                # For GitHub, create branch then PR
                success, new_branch = create_branch(repository, branch_from, branch_to, repo_type)
                if success is False:
                    print("Unable to create new branch - merge manually pls")
                    exit(1)
                # Last, open a PR against the branch_to
                success = create_pr(repository, branch_to, new_branch, branch_from, repo_type)
                if success is False:
                    print("Unable to create PR - merge manually pls")
                    exit(1)

    sys.exit(rc)
