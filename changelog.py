#! /usr/bin/env python3

# FIXME/TODO
# - use static SSH config ?

import argparse
import datetime
import git  # FIXME: need >= 2.3, declare in requirements.txt
import logging
import re
import sys

# relative to cwd
from lib import *


# constants
JIRA_FILTER = re.compile(r'{}-\d+'.format(PROJECT))
CHANGELOG_FILTER = re.compile(r'@changelog')
CHANGELOG_EXCLUDE_FILTER = re.compile(r'@exclude')


# functions
def formatCommit(commit, repo, tickets=None):
    s = "{} [{}] {}".format(str(commit)[0:7], repo, commit.summary)
    if not tickets:
        return s
    else:
        return "{} ({})".format(s, ", ".join(tickets))


def get_tag_name(version, tagType):
    ts = datetime.datetime.now().strftime('%Y%m%dT%H%M')
    return "{}-{}-{}".format(version, ts, tagType)


def findMostRecentTag(repo, version, tagType):
    # filter tags by type first
    tags = [t for t in repo.tags if t.name.find(tagType) >= 0]
    # let's see if some of those are about the current version
    versionTags = [t for t in tags if t.name.find(version) >= 0]
    if versionTags:
        tags = versionTags
    tags = sorted(tags, key=lambda x: x.name)
    logging.info("found tags: {}".format(tags))
    if not tags:
        logging.error("no tags found, aborting")
        sys.exit(2)
    old = tags[-1]
    logging.info("most recent tag: {}".format(old.name))
    return old


def filterCommit(commit):
    tickets = JIRA_FILTER.findall(commit.message)
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
X.Y.Z-YYYYmmddTHHMM-(promotion|sync)''')

parser.add_argument('--log-level', dest='logLevel',
                                        choices=['debug', 'info', 'warning'],
                                        default='warning',
                                        help='level at which to log')
parser.add_argument('--create-tags', dest='createTags',
                                        action='store_true',
                                        default=False,
                                        help='create new tags (default=no tag creation)')
parser.add_argument('--version', dest='version',
                                        action='store',
                                        required=True,
                                        default=None,
                                        metavar="VERSION",
                                        type=full_version,
                                        help='the version on which to base the diff. It needs to be of the form x.y.z, that means including the bugfix revision')
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--tag-type', dest='tagType', action='store',
                                    choices=('promotion','sync'),
                                    default=None,
                                    metavar="TAG-TYPE",
                                    help='tag type')
mode.add_argument('--manual-boundaries', dest='manualBoundaries', nargs=2,
                                    default=None,
                                    metavar="TAG_N",
                                    help='specify 2 arbitrary tags to diff between, instead of using <latest-type>..HEAD'
)


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

    if not args.version:
        logging.warning("not a valid full version (x.y.z)")
        sys.exit(0)

    # derive remote branch name from version
    majorMinor = '.'.join(args.version.split(".")[0:2]) # FIXME
    if not args.manualBoundaries:        
        new = BRANCH_TPL.format(majorMinor)
    else:
        old, new = args.manualBoundaries

    # to store final results
    changelogCommits = []
    allCommits = []

    # create tag name and message anyway
    tagName = get_tag_name(args.version, args.tagType)
    tagMsg = "Automated tag creation: version={}, branch={}".format(args.version, new)

    # iterate over repositories
    for name in REPOSITORIES:
        repo, origin = get_repo(name, BASE_DIR)

        if not args.manualBoundaries:
            old = findMostRecentTag(repo, args.version, args.tagType).name
            # origin/release-X.Y may not have been created already (promoting
            # from "current" for instance); in that case, use origin/master
            # instead
            try:
                repo.commit(new)
            except git.exc.BadName:
                new = "origin/master"

        for commit in list_commits_between(repo, old, new):
            allCommits.append((commit, name, None))

            clCommit, tickets = filterCommit(commit)
            if clCommit:
                changelogCommits.append((commit, name, tickets))

        if args.createTags:
            logging.info("about to create tag {}".format(tagName))
            t = repo.create_tag(tagName, ref=new, message=tagMsg)
            origin.push(t)

    allCommits = sortCommitListByDateAuthored(allCommits)
    changelogCommits = sortCommitListByDateAuthored(changelogCommits)

    logging.debug("all commits:\n    {}".format(formatCommitList(allCommits,"\n    ")))
    logging.info("done")

    if changelogCommits:
        print(formatCommitList(changelogCommits))

