"""Gerrit API integration module for repository operations."""

import logging
import os
import sys
from typing import Dict, Any, Optional, Tuple

import requests


# Constants
GERRIT_BASE_URL = os.getenv("GERRIT_BASE_URL", "https://gerrit.corp.arista.io")
GERRIT_USER = os.getenv("GERRIT_USER", "")
GERRIT_PASSWORD = os.getenv("GERRIT_PASSWORD", "")


def get_gerrit_auth() -> Tuple[str, str]:
    """Get Gerrit authentication credentials."""
    if not GERRIT_USER or not GERRIT_PASSWORD:
        logging.error("GERRIT_USER and GERRIT_PASSWORD environment variables must be set")
        sys.exit(1)
    return (GERRIT_USER, GERRIT_PASSWORD)


def get_json(
    url: str,
    auth: Tuple[str, str],
    post_data: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """
    Make a GET or POST request to Gerrit API.
    
    Args:
        url: The API endpoint URL
        auth: Tuple of (username, password)
        post_data: Optional data for POST requests
        
    Returns:
        Tuple of (status_code, json_data)
    """
    headers = {"Content-Type": "application/json"}
    
    try:
        if post_data:
            r = requests.post(url, headers=headers, auth=auth, json=post_data)
        else:
            r = requests.get(url, headers=headers, auth=auth)
        
        sc = r.status_code
        
        if sc == 401:
            logging.error("Couldn't authenticate to Gerrit, check GERRIT_USER and GERRIT_PASSWORD")
            sys.exit(1)
        if sc == 404:
            logging.debug(f"Couldn't find URL '{url}'")
            logging.debug("... it means one of repository/branchFrom/branchTo does not exist")
            return None, None
        elif sc == 204:
            json_data = None
        else:
            # Gerrit prepends ")]}'" to JSON responses for security
            text = r.text
            if text.startswith(")]}'"):
                text = text[4:]
            json_data = r.json() if text else None
        
        return sc, json_data
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None, None


def compare_branches(
    repository: str, branch_from: str, branch_to: str
) -> Tuple[Optional[int], Optional[int], Any]:
    """
    Compare two branches in a Gerrit repository.
    
    Args:
        repository: Repository name
        branch_from: Source branch
        branch_to: Target branch
        
    Returns:
        Tuple of (commits_ahead, commits_behind, extra_message)
    """
    # Gerrit uses project names with URL encoding
    project = repository.replace("/", "%2F")
    
    # Get commits in branch_from not in branch_to (ahead)
    url_ahead = f"{GERRIT_BASE_URL}/a/projects/{project}/branches/{branch_from}/commits?n=1000"
    url_to = f"{GERRIT_BASE_URL}/a/projects/{project}/branches/{branch_to}/commits?n=1000"
    
    auth = get_gerrit_auth()
    
    sc_from, commits_from = get_json(url_ahead, auth)
    sc_to, commits_to = get_json(url_to, auth)
    
    if not sc_from or not sc_to or commits_from is None or commits_to is None:
        return None, None, None
    
    # Get commit IDs
    commits_from_ids = {c.get('commit') for c in commits_from}
    commits_to_ids = {c.get('commit') for c in commits_to}
    
    ahead = len(commits_from_ids - commits_to_ids)
    behind = len(commits_to_ids - commits_from_ids)
    
    extra = "!!! Need to merge !!!" if ahead > 0 else ""
    
    return ahead, behind, extra


def merge_branches(
    repository: str, branch_from: str, branch_to: str
) -> Tuple[bool, str]:
    """
    Attempt to merge branch_from into branch_to.
    TODO: implement this
    Note: Gerrit doesn't support direct merges via API like GitHub.
    This would typically require creating a change and submitting it.
    
    Args:
        repository: Repository name
        branch_from: Source branch
        branch_to: Target branch
        
    Returns:
        Tuple of (success, status_message)
    """
    # For Gerrit, merging is more complex and typically involves:
    # 1. Creating a change (similar to a PR)
    # 2. Getting it reviewed
    # 3. Submitting it
    
    # This is a simplified implementation that creates a merge change
    logging.warning("Direct merge not supported in Gerrit - would need to create a change")
    return False, "SKIPPED: Gerrit requires creating a change for review"


def create_change(
    repository: str, branch_to: str, branch_from: str
) -> Tuple[Optional[int], Optional[str]]:
    """
    Create a Gerrit change (similar to GitHub PR).
    
    Args:
        repository: Repository name
        branch_to: Target branch
        branch_from: Source branch
        
    Returns:
        Tuple of (status_code, change_id)
    """
    project = repository.replace("/", "%2F")
    url = f"{GERRIT_BASE_URL}/a/changes/"
    
    auth = get_gerrit_auth()
    
    post_data = {
        "project": repository,
        "subject": f"Merge {branch_from} into {branch_to}",
        "branch": branch_to,
        "status": "NEW",
    }
    
    sc, json_data = get_json(url, auth, post_data=post_data)
    
    if sc and json_data:
        change_id = json_data.get('change_id')
        return sc, change_id
    
    return None, None


def get_branch_revision(repository: str, branch: str) -> Optional[str]:
    """
    Get the current revision (commit SHA) of a branch.
    
    Args:
        repository: Repository name
        branch: Branch name
        
    Returns:
        Commit SHA or None
    """
    project = repository.replace("/", "%2F")
    url = f"{GERRIT_BASE_URL}/a/projects/{project}/branches/{branch}"
    
    auth = get_gerrit_auth()
    sc, json_data = get_json(url, auth)
    
    if sc == 200 and json_data:
        return json_data.get('revision')
    
    return None
