#! /usr/bin/env python3

# FIXME/TODO
# - use static SSH config ?

import argparse
import datetime
import logging
import os
import subprocess
import sys
import tarfile

# relative to cwd
from lib import *


# constants
SUBARCHIVE_TPL = '{}-{}.tar.xz'
REMOTE_ARCHIVE_TPL = "{}_full_source-{}-{}.tar.xz"


# functions
def fullVersion(o):
    if len(o.split('.')) != 3:
        raise argparse.ArgumentTypeError("Not a valid full version (x.y.z)")
    else:
        return o


# CL options
parser = argparse.ArgumentParser(description='Create archive for {}'.format(PROJECT))

parser.add_argument('--log-level', dest='logLevel',
                    choices=['debug', 'info', 'warning'],
                    default='warning',
                    help='level at which to log')
parser.add_argument('--archive', dest='archive',
                    action='store',
                    required=True,
                    default=None,
                    metavar="ARCHIVE",
                    help='the destination file')
parser.add_argument('--upload', dest='upload',
                    action='store_true',
                    default=False,
                    help='upload to package-server (default=no)')
parser.add_argument('--version', dest='version',
                    action='store',
                    required=True,
                    default=None,
                    metavar="VERSION",
                    type=full_version,
                    help='the version on which to base the archive. It needs to be of the form x.y.z, that means including the bugfix revision')


def fullVersion(o):
    if len(o.split('.')) != 3:
        raise argparse.ArgumentTypeError("Not a valid full version (x.y.z)")
    else:
        return o


def get_remote_archive_name(version):
    ts = datetime.datetime.now().strftime('%Y%m%dT%H%M')
    return REMOTE_ARCHIVE_TPL.format(PROJECT.lower(), version, ts)


def get_remote_archive_scp_path(version, user=NETBOOT_USER, host=NETBOOT_HOST, directory=NETBOOT_DIR):
    dst_name = get_remote_archive_name(version)
    dst_path = osp.join(directory, version, dst_name)
    return '{}@{}:{}'.format(user, host, dst_path)


def get_remote_archive_url(version, host=NETBOOT_HOST, directory=NETBOOT_HTTP_DIR):
    dst_name = get_remote_archive_name(version)
    return "http://{}/{}/{}/{}".format(host, directory, version, dst_name)


def upload(archive, version, user=NETBOOT_USER, host=NETBOOT_HOST, directory=NETBOOT_DIR):
    dst = get_remote_archive_scp_path(version)

    logging.info("uploading to {}".format(dst))
    cmd = "scp -q {} {}".format(archive, dst)
    # rc = subprocess.run(cmd, shell=True)
    # if rc != 0:
    #     logging.error("could not upload")
    #     sys.exit(rc)

    logging.info("available at {}".format(get_remote_archive_url(version)))


# main
if __name__ == '__main__':
    args = parser.parse_args()

    # logging
    logging.getLogger().setLevel(getattr(logging, args.logLevel.upper()))
    console = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('[%(asctime)s] changelog: %(levelname)-7s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # go
    logging.info("started with {}".format(" ".join(sys.argv[1:])))

    # derive remote branch name from version
    version = args.version
    majorMinor = '.'.join(version.split(".")[0:2])  # FIXME
    branch = BRANCH_TPL.format(majorMinor)

    # open main uncompressed archive
    archive = args.archive
    tar = tarfile.open(archive, 'w')

    subarchives = {}
    # iterate over repositories
    for name in ('ngfw_src', 'ngfw_pkgs', 'ngfw_kernels'):
        repo, origin = get_repo(name)

        subarchive = SUBARCHIVE_TPL.format(name, version)
        archive_repo_lz(repo, subarchive, branch)

        logging.info("adding {} to {}".format(subarchive, archive))
        tar.add(subarchive)
        os.unlink(subarchive)

    tar.close()
    logging.info("created {}".format(archive))

    if args.upload:
        upload(archive, version)

    logging.info("done")
