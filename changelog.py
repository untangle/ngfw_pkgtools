#! /usr/bin/env python3

# FIXME/TODO
# - use static SSH config ?

import argparse
import datetime
import git  # FIXME: need >= 2.3, declare in requirements.txt
import logging
import os.path as osp
import re
import sys

# relative to cwd
from lib import full_version, gitutils, repoinfo


# constants
CHANGELOG_FILTER = re.compile(r'@changelog')
CHANGELOG_EXCLUDE_FILTER = re.compile(r'@exclude')


# functions
def formatCommit(commit, repo, tickets=None):
    s = "{} [{}] {}".format(str(commit)[0:7], repo, commit.summary)
    if not tickets:
        return s
    else:
        return "{} ({})".format(s, ", ".join(tickets))


def get_tag_name(product, version, tagType):
    ts = datetime.datetime.now().strftime('%Y%m%dT%H%M')
    return "{}-{}-{}-{}".format(product, version, ts, tagType)


def findMostRecentTag(product, repo, version, tagType):
    tags = repo.tags

    if product == 'ngfw':
        # older ngfw tags didn't have the product prefix
        tags = [t for t in tags if re.match(r'(^\d|ngfw-)', t.name)]
    else:
        tags = [t for t in tags if t.name.startswith(product)]

    # then filter by type
    tags = [t for t in tags if t.name.find(tagType) >= 0]

    # let's see if some of those are about the current version
    versionTags = [t for t in tags if t.name.find(version) >= 0]
    if versionTags:
        tags = versionTags
    tags = sorted(tags, key=lambda x: x.name)
    logging.info("found tags: {}".format([t.name for t in tags]))
    if not tags:
        logging.warning("no tags found")
        return None
    old = tags[-1]
    logging.info("most recent tag: {}".format(old.name))
    return old


def filterCommit(commit, jira_filter):
    tickets = jira_filter.findall(commit.message)
    cl = CHANGELOG_FILTER.search(commit.message)
    exclude = CHANGELOG_EXCLUDE_FILTER.search(commit.message)
    if (tickets or cl) and not exclude:
        # only attach those tickets that are not directly mentioned in
        # the subject
        tickets = [ t for t in tickets if commit.summary.find(t) < 0 ]
        return commit, tickets
    else:
        return None, None


def sortCommitListByDateAuthored(l):
    return sorted(l, key = lambda x: x[0].authored_date)


def formatCommitList(l, sep = '\n'):
    return sep.join([formatCommit(*x) for x in l])


# CL options
parser = argparse.ArgumentParser(description='''List changelog entries
between tags across multiple repositories.

It can also optionally create and push additional tags, of the form
product-X.Y.Z-YYYYmmddTHHMM-(promotion|sync)''')

parser.add_argument('--log-level', dest='logLevel',
                                        choices=['debug', 'info', 'warning'],
                                        default='warning',
                                        help='level at which to log')
parser.add_argument('--create-tags', dest='createTags',
                                        action='store_true',
                                        default=False,
                                        help='create new tags (default=no tag creation)')
parser.add_argument('--product', dest='product', action='store',
                                    choices=('ngfw', 'waf'),
                                    required=True,
                                    default=None,
                                    metavar="PRODUCT",
                                    help='product name')
parser.add_argument('--simulate',
                    dest='simulate',
                    action='store_true',
                    default=False,
                    help='do not push anything (default=push)')
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--tag-type', dest='tagType', action='store',
                                    choices=('promotion','sync'),
                                    default=None,
                                    metavar="TAG-TYPE",
                                    help='tag type')
mode.add_argument('--manual-boundaries', dest='manualBoundaries', nargs=2,
                                    default=None,
                                    metavar="TAG_N",
                                    help='specify 2 arbitrary tags to diff between, instead of using <latest-type>..HEAD')
target = parser.add_mutually_exclusive_group(required=True)
target.add_argument('--version',
                    dest='version',
                    action='store',
                    default=None,
                    metavar="VERSION",
                    type=full_version,
                    help='the version on which to base the diff. It needs to be of the form x.y.z, that means including the bugfix revision')
target.add_argument('--distribution',
                    dest='distribution',
                    action='store',
                    default=None,
                    metavar="DISTRIBUTION",
                    help='the distribution on which to base the diff.')


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

    if args.distribution:
        version = re.match(r'^.*(\d+\.\d+.\d+)', args.distribution).groups()[0]
    else:
        version = args.version

    product = args.product

    jira_filter = re.compile(r'{}-\d+'.format(args.product.upper()))

    # derive remote branch name from version
    major, minor = [int(i) for i in version.split(".")[0:2]]
    if not args.manualBoundaries:
        if product == 'ngfw' and (major < 16 or (major == 16 and minor < 4)):
            new = 'release-{}.{}'.format(major, minor)
        else:
            new = '{}-release-{}.{}'.format(product, major, minor)
        new = osp.join('origin', new)

    else:
        old, new = args.manualBoundaries

    # to store final results
    changelogCommits = []
    allCommits = []

    # create tag name and message anyway
    tagName = get_tag_name(product, version, args.tagType)
    tagMsg = "Automated tag creation: product={}, version={}, branch={}".format(product, version, new)

    # iterate over repositories
    for repo_info in repoinfo.list_repositories(product):
        if repo_info.disable_forward_merge:
            continue

        repo_name = repo_info.name
        repo_url = repo_info.git_url

        repo, origin = gitutils.get_repo(repo_name, repo_url)

        if not args.manualBoundaries:
            old = findMostRecentTag(product, repo, version, args.tagType)
            if old:
                old = old.name

                # origin/release-X.Y may not have been created already (promoting
                # from "current" for instance); in that case, use origin/master
                # instead
                try:
                    repo.commit(new)
                except git.exc.BadName:
                    new = osp.join(origin.name, 'master')

        if old:
            for commit in gitutils.list_commits_between(repo, old, new):
                allCommits.append((commit, repo_name, None))

                clCommit, tickets = filterCommit(commit, jira_filter)
                if clCommit:
                    changelogCommits.append((commit, repo_name, tickets))

        if args.createTags:
            logging.info("about to create tag {} on branch {}".format(tagName, new))
            t = repo.create_tag(tagName, ref=new, message=tagMsg)
            if not args.simulate:
                origin.push(t)

    allCommits = sortCommitListByDateAuthored(allCommits)
    changelogCommits = sortCommitListByDateAuthored(changelogCommits)

    logging.debug("all commits:\n    {}".format(formatCommitList(allCommits,"\n    ")))
    logging.info("done")

    if changelogCommits:
        print(formatCommitList(changelogCommits))

