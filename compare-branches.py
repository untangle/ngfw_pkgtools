#! /usr/bin/env python3

import argparse
import os
import requests
import sys


# constants
GITHUB_BASE_URL = 'https://api.github.com/repos/untangle/{repository}'
GITHUB_COMPARE_URL = GITHUB_BASE_URL + '/compare/{branchTo}...{branchFrom}'
GITHUB_MERGE_URL = GITHUB_BASE_URL + '/merges'
GITHUB_HEADERS = {'Accept' : 'application/vnd.github.loki-preview+json' }
GITHUB_USER = 'untangle-bot'
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADER1_TPL = "{branchFrom} vs. {branchTo}"
HEADER2_TPL = "    {repository}"
OUTPUT_COMPARE_TPL = "        {ahead:>02} ahead, {behind:>02} behind {extra}"
OUTPUT_MERGE_TPL = "        merge {status}"

NGFW_REPOSITORIES_STEMS = ['src', 'pkgs', 'hades-pkgs', 'imgtools', 'upstream', 'kernels']
NGFW_REPOSITORIES = ['ngfw_' + x for x in NGFW_REPOSITORIES_STEMS] + ['debian-cloud-images']

MFW_REPOSITORIES = ['classd',
                    'mfw_admin',
                    'mfw_build',
                    'mfw_feeds',
                    'nft_dict',
                    'openwrt',
                    'packetd',
                    'sync-settings']

REPOSITORIES = {'mfw': MFW_REPOSITORIES,
                'ngfw': NGFW_REPOSITORIES}


# functions
def getCompareUrl(repository, branchFrom, branchTo):
    return GITHUB_COMPARE_URL.format(repository=repository,
                                     branchFrom=branchFrom,
                                     branchTo=branchTo)


def getJson(url, headers, auth, postData = None):
    if postData:
        r = requests.post(url, headers = headers, auth = auth, json = postData)
    else:
        r = requests.get(url, headers = headers, auth = auth)

    sc = r.status_code
    if sc == 401:
        print("Couldn't authenticate to GitHub, you need to export a valid GITHUB_TOKEN")
        sys.exit(1)
    if sc == 404:
        print("Couldn't find URL '{}'".format(url))
        print("... it means one of repository/branchFrom/branchTo does not exist")
        sys.exit(1)
    elif sc == 204:
        jsonData = None
    else:
        jsonData = r.json()

    return sc, jsonData


def merge(repository, branchFrom, branchTo):
    url = GITHUB_MERGE_URL.format(repository=repository)
    postData = { 'base':branchTo, 'head':branchFrom, 'commit_message':'Merged by Jenkins'}
    sc, jsonData = getJson(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN), postData = postData)

    if sc == 204:
        success = True
        status = 'SKIPPED: no need to merge'
    elif sc == 201:
        success = True
        status = 'DONE: commitId=' + jsonData['sha']
    else:
        success = False
        status = 'FAILED: conflicts'

    return success, status


def compare(repository, branchFrom, branchTo):
    url = getCompareUrl(repository, branchFrom, branchTo)
    sc, jsonData = getJson(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN))
    ahead, behind = [ int(jsonData[x]) for x in ('ahead_by', 'behind_by') ]
    extra = "!!! Need to merge !!!" if ahead > 0 else ""

    return ahead, behind, extra


# main

# CL options
parser = argparse.ArgumentParser(description='''List differences
between two branches across multiple repositories.

It can also optionally try to merge the branches before computing
the differences.''')

parser.add_argument('--merge', dest='merge',
                    action='store_true',
                    default=False,
                    help='try to merge first (default=False)')
parser.add_argument('--branch-from', dest='branchFrom',
                    required=True,
                    metavar="BRANCH_FROM",
                    help='base branch)')
parser.add_argument('--branch-to', dest='branchTo',
                    required=True,
                    metavar="BRANCH_TO",
                    help='target branch)')

target = parser.add_mutually_exclusive_group(required=True)
target.add_argument('--product', type=str, dest='product',
                    metavar='PRODUCT',
                    choices=('mfw', 'ngfw'),
                    help='product to work on (mfw or ngfw)')
target.add_argument('--repositories', type=str, dest='repositories',
                    nargs='*',
                    metavar='REPOSITORIES',
                    help='list of space-separated repositories to target')

args = parser.parse_args()

if args.repositories:
    repositories = args.repositories
else:
    repositories = REPOSITORIES[args.product]

branchFrom, branchTo = args.branchFrom, args.branchTo
rc = 0

print(HEADER1_TPL.format(branchFrom=branchFrom, branchTo=branchTo))

for repository in repositories:
    print()
    print(HEADER2_TPL.format(repository=repository))

    if args.merge:
        success, status = merge(repository, branchFrom, branchTo)
        print(OUTPUT_MERGE_TPL.format(status=status))
        if success:
            continue
        else:
            rc = 1

    ahead, behind, extra = compare(repository, branchFrom, branchTo)
    print(OUTPUT_COMPARE_TPL.format(ahead=ahead,
                                    behind=behind,
                                    extra=extra))

sys.exit(rc)
