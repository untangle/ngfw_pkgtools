#!/usr/bin/python3

import argparse
import logging
import sys

# relative to cwd
from lib import gitutils, simple_version, repoinfo


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
                    required=False,
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
                    choices=('mfw', 'ngfw', 'waf', 'efw'),
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
    logging.info("started with %s", " ".join(sys.argv[1:]))

    product = args.product
    branch = args.branch
    version = args.new_version
    simulate = args.simulate

    if version and not branch.startswith("{}-".format(product)):
        logging.error("branch name must start with product name when new version is given")
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
            logging.info('creating branch %s', branch)
            new_branch = repo.create_head(branch)
            new_branch.checkout()

            # version resources on new branch
            for vr in repo_info.versioned_resources:
                if vr.change_on_release_branch:
                    vr.set_versioning_value(repo, locals())

            # push new branch
            refspecs = ['{branch}:{branch}'.format(branch=new_branch),]
            gitutils.push(origin, refspecs, simulate)

        # version resources on master branch
        refspecs = set()
        if version:
            for vr in repo_info.versioned_resources:
                if vr.change_on_release_branch:
                    continue

                if repo.head.reference.name != repo_default_branch:
                    logging.info('on branch %s', repo.head.reference)
                    logging.info('checking out branch %s', repo_default_branch)
                    default_branch = repo.heads[repo_default_branch]
                    default_branch.checkout()

                rs = vr.set_versioning_value(repo, locals())
                refspecs.update(rs)

        if refspecs:  # push
            gitutils.push(origin, refspecs, simulate)
