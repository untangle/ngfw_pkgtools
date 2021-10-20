#! /usr/bin/env python3

# FIXME/TODO
# - use static SSH config ?

import argparse
import datetime
import logging
import os
import os.path as osp
import subprocess
import sys
import tarfile

# relative to cwd
from lib import gitutils, repoinfo
from lib import NETBOOT_BASE_DIR, NETBOOT_HOST, NETBOOT_USER


# constants
SUBARCHIVE_TPL = '{}_{}.tar.xz'
REMOTE_ARCHIVE_TPL = "{}_{}_{}.tar.xz"


# functions
def get_remote_archive_name(product, branch):
    ts = datetime.datetime.now().strftime('%Y%m%dT%H%M')
    return REMOTE_ARCHIVE_TPL.format(product.lower(), branch, ts)


def get_remote_archive_directory(product, branch, directory=NETBOOT_BASE_DIR):
    return osp.join(directory, '{}-images-buster'.format(product), branch)


def get_remote_archive_scp_path(archive_name, product, branch, user=NETBOOT_USER, host=NETBOOT_HOST):
    dst_dir = get_remote_archive_directory(product, branch)

    return '{}@{}:{}/{}'.format(user, host, dst_dir, archive_name)


def get_remote_archive_url(archive_name, product, branch, host=NETBOOT_HOST):
    dst_dir = get_remote_archive_directory(product, branch)
    return "http://{}/{}/{}".format(host, dst_dir, archive_name)


def upload(archive, branch, user=NETBOOT_USER, host=NETBOOT_HOST):
    archive_name = get_remote_archive_name(product, branch)
    dst = get_remote_archive_scp_path(archive_name, product, branch)

    logging.info("uploading to {}".format(dst))
    dst_dir = get_remote_archive_directory(product, branch)

    mkdir_cmd = "ssh {}@{} mkdir -p {}".format(user, host, dst_dir)
    scp_cmd = "scp -q {} {}".format(archive, dst)
    try:
        subprocess.run(mkdir_cmd, shell=True, check=True)
        subprocess.run(scp_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error("could not upload: {}".format(e.output))
        sys.exit(1)

    logging.info("available at {}".format(get_remote_archive_url(archive_name, product, branch)))


# CL options
parser = argparse.ArgumentParser(description='Create full source archive for product')

parser.add_argument('--log-level', dest='logLevel',
                    choices=['debug', 'info', 'warning'],
                    default='info',
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
parser.add_argument('--product', dest='product', action='store',
                    choices=('ngfw', 'waf'),
                    required=True,
                    default=None,
                    metavar="PRODUCT",
                    help='product name')
parser.add_argument('--branch', dest='branch',
                    action='store',
                    required=True,
                    default=None,
                    metavar="branch",
                    help='the branch on which to base the archive')


# main
if __name__ == '__main__':
    args = parser.parse_args()

    # logging
    logging.getLogger().setLevel(getattr(logging, args.logLevel.upper()))
    console = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('[%(asctime)s] archive: %(levelname)-7s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # go
    logging.info("started with {}".format(" ".join(sys.argv[1:])))

    # derive remote branch name from branch
    product = args.product
    branch = args.branch

    # open main uncompressed archive
    archive = args.archive
    tar = tarfile.open(archive, 'w')

    subarchives = {}
    # iterate over repositories
    for repo_info in repoinfo.list_repositories(product):
        repo_name = repo_info.name
        repo_url = repo_info.git_url

        repo, origin = gitutils.get_repo(repo_name, repo_url)

        subarchive = SUBARCHIVE_TPL.format(repo_name, branch)
        gitutils.archive_repo_lz(repo, subarchive, osp.join(origin.name, branch))

        logging.info("adding {} to {}".format(subarchive, archive))
        tar.add(subarchive)
        os.unlink(subarchive)

    tar.close()
    logging.info("created {}".format(archive))

    if args.upload:
        upload(archive, branch)

    logging.info("done")
