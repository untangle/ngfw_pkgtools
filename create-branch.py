#!/usr/bin/python3

import argparse
import logging
import os.path as osp
import sys

# relative to cwd
from lib import gitutils, simple_version, WORK_DIR, repoinfo


# constants
DISTRIBUTION_FILE = 'resources/DISTRIBUTION'
VERSION_FILE = 'resources/VERSION'
PUBLIC_VERSION_FILE = 'resources/PUBVERSION'


# functions
def set_resources_distribution(distribution, repo):
    path = osp.join(WORK_DIR, 'ngfw_pkgtools', DISTRIBUTION_FILE)
    with open(path, 'w') as f:
        f.write(distribution + '\n')

    msg = "Updating resources: distribution={}".format(distribution)
    repo.index.add(DISTRIBUTION_FILE)
    repo.index.commit(msg)
    logging.info("on branch {}, {}".format(repo.head.reference, msg.lower()))


def set_resources_version(version, repo):
    path = osp.join(WORK_DIR, 'ngfw_pkgtools', PUBLIC_VERSION_FILE)
    with open(path, 'w') as f:
        f.write(version + '\n')

    path = osp.join(WORK_DIR, 'ngfw_pkgtools', VERSION_FILE)
    with open(path, 'w') as f:
        f.write(version + '.0' + '\n')

    msg = "Updating resources: version={}".format(version)
    repo.index.add(PUBLIC_VERSION_FILE)
    repo.index.add(VERSION_FILE)
    repo.index.commit(msg)
    logging.info("on branch {}, {}".format(repo.head.reference, msg.lower()))


# CL options
parser = argparse.ArgumentParser(description='''Create release branches''')
parser.add_argument('--log-level',
                    dest='logLevel',
                    choices=['debug', 'info', 'warning'],
                    default='warning',
                    help='level at which to log')
parser.add_argument('--simulate',
                    dest='simulate',
                    action='store_true',
                    default=False,
                    help='do not push anything (default=push)')
parser.add_argument('--new-version',
                    dest='new_version',
                    action='store',
                    required=True,
                    default=None,
                    metavar="NEW_VERSION",
                    type=simple_version,
                    help='the new public version for the master branch (x.y)')
parser.add_argument('--branch',
                    dest='branch',
                    action='store',
                    required=True,
                    default=None,
                    metavar="BRANCH",
                    help='the new branch name (needs to start with the product name')
parser.add_argument('--product',
                    dest='product',
                    action='store',
                    choices=('ngfw', 'waf'),
                    required=True,
                    default=None,
                    metavar="PRODUCT",
                    help='product name')

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

    product = args.product
    branch = args.branch
    new_version = args.new_version
    simulate = args.simulate

    if not args.new_version:
        logging.error("not a valid simple version (x.y)")
        sys.exit(1)

    if not args.branch.startswith("{}-".format(product)):
        logging.error("branch name must start with product name")
        sys.exit(1)

    # iterate over repositories
    for repo_info in repoinfo.list_repositories(product):
        if repo_info.disable_branch_creation:
            continue

        repo_name = repo_info.name
        repo_url = repo_info.git_url

        repo, origin = gitutils.get_repo(repo_name, repo_url)

        # checkout new branch
        logging.info('creating branch {}'.format(branch))
        new_branch = repo.create_head(branch)
        new_branch.checkout()

        if repo_name == 'ngfw_pkgtools':
            set_resources_distribution(new_branch.name, repo)

        # push
        if not simulate:
            refspec = "{}:{}".format(new_branch, new_branch)
            origin.push(refspec)

        if repo_name == 'ngfw_pkgtools':
            default_branch_name = repo_info.default_branch
            logging.info('checking out branch {}'.format(default_branch_name))
            default_branch = repo.heads[default_branch_name]
            default_branch.checkout()
            set_resources_version(new_version, repo)
            if not simulate:
                refspec = "{}:{}".format(default_branch, default_branch)
                origin.push(refspec)
