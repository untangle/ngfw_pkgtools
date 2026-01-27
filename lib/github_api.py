"""GitHub API integration module for repository operations."""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import requests


# Constants
GITHUB_BASE_URL = "https://api.github.com/repos/untangle/{repository}"
GITHUB_COMPARE_URL = GITHUB_BASE_URL + "/compare/{branchTo}...{branchFrom}"
GITHUB_MERGE_URL = GITHUB_BASE_URL + "/merges"
GITHUB_PR_URL = GITHUB_BASE_URL + "/pulls"
GITHUB_CREATE_BRANCH_URL = GITHUB_BASE_URL + "/git/refs"
GITHUB_GET_BRANCH_URL = GITHUB_BASE_URL + "/branches/{branch}"
GITHUB_HEADERS = {"Accept": "application/vnd.github.loki-preview+json"}
GITHUB_USER = "untangle-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def get_compare_url(repository: str, branch_from: str, branch_to: str) -> str:
    """Generate GitHub compare URL."""
    return GITHUB_COMPARE_URL.format(
        repository=repository, branchFrom=branch_from, branchTo=branch_to
    )


def get_pr_url(repository: str) -> str:
    """Generate GitHub PR URL."""
    return GITHUB_PR_URL.format(repository=repository)


def get_pr_body(date: str, new_branch: str, branch_to: str, branch_from: str) -> Dict[str, str]:
    """Generate PR body for GitHub."""
    return {
        "title": "Merge PR from {branchFrom} into {branchTo} on {date} ".format(
            branchFrom=branch_from, branchTo=branch_to, date=date
        ),
        "body": "PR opened by jenkins",
        "head": new_branch,
        "base": branch_to,
    }


def get_branch_url(repository: str) -> str:
    """Generate GitHub branch creation URL."""
    return GITHUB_CREATE_BRANCH_URL.format(repository=repository)


def get_branch_body(new_branch: str, commit_sha: str) -> Dict[str, str]:
    """Generate branch creation body for GitHub."""
    return {"ref": "refs/heads/" + new_branch, "sha": commit_sha}


def get_head_sha_url(repository: str, branch: str) -> str:
    """Generate GitHub branch info URL."""
    return GITHUB_GET_BRANCH_URL.format(repository=repository, branch=branch)


def get_json(
    url: str,
    headers: Dict[str, str],
    auth: Tuple[str, str],
    post_data: Optional[Dict[str, str]] = None,
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """
    Make a GET or POST request to GitHub API.
    
    Args:
        url: The API endpoint URL
        headers: Request headers
        auth: Tuple of (username, token)
        post_data: Optional data for POST requests
        
    Returns:
        Tuple of (status_code, json_data)
    """
    if post_data:
        r = requests.post(url, headers=headers, auth=auth, json=post_data)
    else:
        r = requests.get(url, headers=headers, auth=auth)

    sc = r.status_code
    if sc == 401:
        logging.error("Couldn't authenticate to GitHub, you need to export a valid GITHUB_TOKEN")
        sys.exit(1)
    if sc == 404:
        logging.debug("Couldn't find URL '{}'".format(url))
        logging.debug("... it means one of repository/branchFrom/branchTo does not exist")
        return None, None
    elif sc == 204:
        json_data = None
    else:
        json_data = r.json()

    return sc, json_data


def merge_branches(repository: str, branch_from: str, branch_to: str) -> Tuple[bool, str]:
    """
    Merge branch_from into branch_to on GitHub.
    
    Args:
        repository: Repository name
        branch_from: Source branch
        branch_to: Target branch
        
    Returns:
        Tuple of (success, status_message)
    """
    url = GITHUB_MERGE_URL.format(repository=repository)
    post_data = {
        "base": branch_to,
        "head": branch_from,
        "commit_message": "Merged by Jenkins",
    }
    sc, json_data = get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN), post_data=post_data)

    if not sc:
        success = True
        status = "SKIPPED: no comparison could be made"
    elif sc == 204:
        success = True
        status = "SKIPPED: no need to merge"
    elif sc == 201:
        success = True
        if not json_data:
            raise RuntimeError("merge_branches(...), sc is 201, but json_data is None")
        status = "DONE: commitId=" + json_data["sha"]
    else:
        success = False
        status = "FAILED: conflicts"

    return success, status


def compare_branches(
    repository: str, branch_from: str, branch_to: str
) -> Tuple[Optional[int], Optional[int], Any]:
    """
    Compare two branches on GitHub.
    
    Args:
        repository: Repository name
        branch_from: Source branch
        branch_to: Target branch
        
    Returns:
        Tuple of (commits_ahead, commits_behind, extra_message)
    """
    url = get_compare_url(repository, branch_from, branch_to)
    sc, json_data = get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN))
    if not sc or not json_data:
        return None, None, None

    ahead, behind = [int(json_data[x]) for x in ("ahead_by", "behind_by")]
    extra = "!!! Need to merge !!!" if ahead > 0 else ""

    return ahead, behind, extra


def create_pr(repository: str, branch_to: str, new_branch: str, branch_from: str) -> Tuple[int, str]:
    """
    Create a pull request on GitHub.
    
    Args:
        repository: Repository name
        branch_to: Target branch
        new_branch: Source branch for the PR
        branch_from: Original branch name (for PR title)
        
    Returns:
        Tuple of (status_code, branch_name)
    """
    url = get_pr_url(repository)
    body = get_pr_body(
        datetime.today().strftime("%Y-%m-%d_%H-%M-%S"), new_branch, branch_to, branch_from
    )
    sc, _ = get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN), post_data=body)
    if not sc:
        raise RuntimeError("create_pr(...) returned status code is None")
    return sc, new_branch


def create_branch(repository: str, branch_from: str, branch_to: str):
    """
    Create a new branch on GitHub.
    
    Args:
        repository: Repository name
        branch_from: Source branch to base the new branch on
        branch_to: Target branch (used in naming)
        
    Returns:
        Tuple of (status_code, new_branch_name)
    """
    url = get_branch_url(repository)
    new_branch = "automerge-from-{branchFrom}-to-{branchTo}-{date}-{time}".format(
        branchFrom=branch_from,
        branchTo=branch_to,
        date=datetime.today().strftime("%Y-%m-%d"),
        time=time.time_ns(),
    )

    sha = get_branch_revision(repository, branch_from)
    logging.debug("got sha: {sha}; creating workspace branch with this...".format(sha=sha))
    post_data = get_branch_body(new_branch, sha)
    sc, _ = get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN), post_data=post_data)

    logging.debug("new branch is: {newBranch}".format(newBranch=new_branch))
    return sc, new_branch


def get_branch_revision(repository: str, branch: str) -> str:
    """
    Get the current revision (commit SHA) of a branch on GitHub.
    
    Args:
        repository: Repository name
        branch: Branch name
        
    Returns:
        Commit SHA
    """
    url = get_head_sha_url(repository, branch)
    sc, json_data = get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN))

    if not sc:
        logging.debug("idk what this means?")
        return ""
    elif sc == 200:
        if not json_data:
            raise RuntimeError("get_branch_revision(...), status code is 200, but json_data is None")
        return json_data["commit"].get("sha")
    else:
        logging.debug("unable to get branch sha; exit")
        exit(1)
