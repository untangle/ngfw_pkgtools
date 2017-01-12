import json, os, requests, subprocess, sys

# constants
GITHUB_BASE_URL = 'https://api.github.com/repos/untangle/{repository}/compare/{branchRef}...{branch}'
GITHUB_HEADERS = {'Accept' : 'application/vnd.github.loki-preview+json' } 
GITHUB_USER = 'untangle-bot'
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OUTPUT_TPL = "{branch} vs. {branchRef} | {repository:<20}: {ahead:>02} ahead, {behind:>02} behind {extra}"
REPOSITORIES_STEMS = ('src', 'pkgs', 'hades-src', 'hades-pkgs', 'pkgtools', 'isotools-jessie', 'upstream')
REPOSITORIES = ('ngfw_' + x for x in REPOSITORIES_STEMS)

# functions
def getUrl(repository, branchRef, branch):
  return GITHUB_BASE_URL.format(repository=repository,
                                branchRef=branchRef,
                                branch=branch)

def getJson(url, headers, auth):
  r = requests.get(url, headers = headers, auth = auth)
  return r.json()

def printResult(repository, branchRef, branch):
  url = getUrl(repository, branchRef, branch)
  jsonData = getJson(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN))

  ahead, behind = [ int(jsonData[x]) for x in ('ahead_by', 'behind_by') ]
  extra = "!!! Need to merge !!!" if ahead > 0 else ""

  print OUTPUT_TPL.format(branch=branch, branchRef=branchRef,
                          repository=repository, ahead=ahead,
                          behind=behind, extra=extra)

# main
branch, branchRef = sys.argv[1:3]

for repository in REPOSITORIES:
  printResult(repository, branchRef, branch)
