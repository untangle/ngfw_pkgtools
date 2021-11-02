#!/usr/bin/python3

import argparse
import logging
import sys

# relative to cwd
from lib import gitutils, simple_version, WORK_DIR, repoinfo


# functions


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
        logging.debug(repo_info)
        if repo_info.skip_versioning_entirely:
            continue

        repo_name = repo_info.name
        repo_url = repo_info.git_url
        repo_default_branch = repo_info.default_branch

        repo, origin = gitutils.get_repo(repo_name, repo_url, branch=repo_default_branch)

        if not repo_info.disable_branch_creation:
            # checkout new branch
            logging.info('creating branch {}'.format(branch))
            new_branch = repo.create_head(branch)
            new_branch.checkout()

            for vr in repo_info.versioned_resources:
                if vr.change_on_release_branch:
                    vr.set_versioning_value(repo, locals())

            # push
            refspec = "{}:{}".format(new_branch, new_branch)
            if not simulate:
                logging.info("pushing refspecs {}".format(refspec))
                origin.push(refspec)
            else:
                logging.info("would push refspecs {}".format(refspec))
                        
        for vr in repo_info.versioned_resources:
            if vr.change_on_release_branch:
                continue
            logging.info('checking out branch {}'.format(repo_default_branch))
            default_branch = repo.heads[repo_default_branch]
            default_branch.checkout()
            vr.set_versioning_value(repo, locals())

            refspec = "{}:{}".format(default_branch, default_branch)
            if not simulate:
                logging.info("pushing refspecs {}".format(refspec))
                origin.push(refspec)
            else:
                logging.info("would push refspecs {}".format(refspec))
