#!/usr/bin/python3

import argparse
import logging
import os.path as osp
import re
import sys

# relative to cwd
from lib import gitutils, simple_version, WORK_DIR, repoinfo


# functions
def set_versioning_value(regex, value, repo, file_name):
    path = osp.join(repo.working_dir, file_name)
    with open(path, 'r') as f:
        lines = f.readlines()

    with open(path, 'w') as f:
        for line in lines:
            line = re.sub(regex, value, line)
            f.write(line)

    msg = "{}: updating to {}".format(file_name, value)
    repo.index.add(file_name)
    repo.index.commit(msg)
    logging.info("on branch {}, {}".format(repo.head.reference, msg))


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
                    choices=('mfw', 'ngfw', 'waf'),
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
    version = args.new_version
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

        for file_name, v in repo_info.versioned_resources_on_release_branch.items():
            set_versioning_value(v['regex'], v['replacement'].format(**locals()), repo, file_name)

        # push
        if not simulate:
            refspec = "{}:{}".format(new_branch, new_branch)
            origin.push(refspec)

        for file_name, v in repo_info.versioned_resources_on_master_branch.items():
            default_branch_name = repo_info.default_branch
            logging.info('checking out branch {}'.format(default_branch_name))
            default_branch = repo.heads[default_branch_name]
            default_branch.checkout()
            set_versioning_value(v['regex'], v['replacement'].format(**locals()), repo, file_name)

            if not simulate:
                refspec = "{}:{}".format(default_branch, default_branch)
                origin.push(refspec)
