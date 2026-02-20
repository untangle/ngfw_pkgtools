#! /usr/bin/env python3

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import git
import requests

# relative to cwd
from lib import gitutils, repoinfo

# constants
GITHUB_BASE_URL = "https://api.github.com/repos/untangle/{repository}"
GITHUB_COMPARE_URL = GITHUB_BASE_URL + "/compare/{branchTo}...{branchFrom}"
GITHUB_MERGE_URL = GITHUB_BASE_URL + "/merges"
GITHUB_PR_URL = GITHUB_BASE_URL + "/pulls"
GITHUB_CREATE_BRANCH_URL = GITHUB_BASE_URL + "/git/refs"
GITHUB_GET_BRANCH_URL = GITHUB_BASE_URL + "/branches/{branch}"
GITHUB_HEADERS = {"Accept": "application/vnd.github.loki-preview+json"}
GITHUB_USER = "untangle-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Gerrit constants
GERRIT_USER = os.getenv("GERRIT_USER", os.getenv("USER", "buildbot"))

# Output templates
HEADER1_TPL = "{branchFrom} vs. {branchTo}"
HEADER2_TPL = "    {repository}"
OUTPUT_COMPARE_TPL = "        {ahead:>02} ahead, {behind:>02} behind {extra}"
OUTPUT_MERGE_TPL = "        merge {status}"


# Repository Adapter Classes
class RepositoryAdapter:
    """Base class for repository operations"""

    def compare(self, branchFrom: str, branchTo: str) -> Tuple[Optional[int], Optional[int], Any]:
        """Compare two branches and return (ahead, behind, extra_message)"""
        raise NotImplementedError

    def merge(self, branchFrom: str, branchTo: str) -> Tuple[bool, str]:
        """Merge branches and return (success, status_message)"""
        raise NotImplementedError

    def create_branch(self, branchFrom: str, branchTo: str) -> Tuple[int, str]:
        """Create a new branch and return (status_code, branch_name)"""
        raise NotImplementedError

    def create_pull_request(
        self, branchTo: str, newBranch: str, branchFrom: str
    ) -> Tuple[int, str]:
        """Create a pull request/change and return (status_code, branch_name)"""
        raise NotImplementedError


class GitHubRepositoryAdapter(RepositoryAdapter):
    """Adapter for GitHub repository operations"""

    def __init__(self, repository_name: str):
        """
        Initialize GitHub adapter.

        Args:
            repository_name: Name of the repository
        """
        self.repository = repository_name

    @staticmethod
    def _get_json(
        url: str,
        headers: Dict[str, str],
        auth: Tuple[str, str],
        postData: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """Make GitHub API request and return status code and JSON data"""
        if postData:
            r = requests.post(url, headers=headers, auth=auth, json=postData)
        else:
            r = requests.get(url, headers=headers, auth=auth)

        sc = r.status_code
        if sc == 401:
            logging.error(
                "Couldn't authenticate to GitHub, you need to export a valid GITHUB_TOKEN"
            )
            sys.exit(1)
        if sc == 404:
            logging.debug("Couldn't find URL '{}'".format(url))
            logging.debug("... it means one of repository/branchFrom/branchTo does not exist")
            return None, None
        elif sc == 204:
            jsonData = None
        else:
            jsonData = r.json()

        return sc, jsonData

    def _get_head_sha(self, branch: str) -> str:
        """Get the SHA of the head commit for a branch"""
        url = GITHUB_GET_BRANCH_URL.format(repository=self.repository, branch=branch)
        sc, jsonData = self._get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN))

        if not sc:
            logging.debug("idk what this means?")
            return ""
        elif sc == 200:
            if not jsonData:
                raise RuntimeError("_get_head_sha(...), status code is 200, but jsonData is None")
            return jsonData["commit"].get("sha")
        else:
            logging.debug("unable to get branch sha; exit")
            exit(1)

    def compare(self, branchFrom: str, branchTo: str) -> Tuple[Optional[int], Optional[int], Any]:
        """
        Compare two branches using GitHub API.

        Args:
            branchFrom: Source branch name
            branchTo: Target branch name

        Returns:
            Tuple of (ahead_count, behind_count, extra_message)
        """
        url = GITHUB_COMPARE_URL.format(
            repository=self.repository, branchFrom=branchFrom, branchTo=branchTo
        )
        sc, jsonData = self._get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN))
        if not sc or not jsonData:
            return None, None, None

        ahead, behind = [int(jsonData[x]) for x in ("ahead_by", "behind_by")]
        extra = "!!! Need to merge !!!" if ahead > 0 else ""

        return ahead, behind, extra

    def merge(self, branchFrom: str, branchTo: str) -> Tuple[bool, str]:
        """
        Merge branches using GitHub API.

        Args:
            branchFrom: Source branch to merge from
            branchTo: Target branch to merge into

        Returns:
            Tuple of (success, status_message)
        """
        url = GITHUB_MERGE_URL.format(repository=self.repository)
        postData = {
            "base": branchTo,
            "head": branchFrom,
            "commit_message": "Merged by Jenkins",
        }
        sc, jsonData = self._get_json(
            url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN), postData=postData
        )

        if not sc:
            success = True
            status = "SKIPPED: no comparison could be made"
        elif sc == 204:
            success = True
            status = "SKIPPED: no need to merge"
        elif sc == 201:
            success = True
            if not jsonData:
                raise RuntimeError("merge(...), sc is 201, but success is None")
            status = "DONE: commitId=" + jsonData["sha"]
        else:
            success = False
            status = "FAILED: conflicts"

        return success, status

    def create_branch(self, branchFrom: str, branchTo: str) -> Tuple[int, str]:
        """
        Create a new branch using GitHub API.

        Args:
            branchFrom: Source branch to branch from
            branchTo: Target branch (used in naming)

        Returns:
            Tuple of (status_code, new_branch_name)
        """
        url = GITHUB_CREATE_BRANCH_URL.format(repository=self.repository)
        newBranch = "automerge-from-{branchFrom}-to-{branchTo}-{date}-{time}".format(
            branchFrom=branchFrom,
            branchTo=branchTo,
            date=datetime.today().strftime("%Y-%m-%d"),
            time=time.time_ns(),
        )

        sha = self._get_head_sha(branchFrom)
        logging.debug("got sha: {sha}; creating workspace branch with this...".format(sha=sha))
        postData = {"ref": "refs/heads/" + newBranch, "sha": sha}
        sc, _ = self._get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN), postData=postData)

        logging.debug("new branch is: {newBranch}".format(newBranch=newBranch))
        return sc, newBranch

    def create_pull_request(
        self, branchTo: str, newBranch: str, branchFrom: str
    ) -> Tuple[int, str]:
        """
        Create a pull request using GitHub API.

        Args:
            branchTo: Target branch for the PR
            newBranch: New branch name
            branchFrom: Source branch

        Returns:
            Tuple of (status_code, branch_name)
        """
        url = GITHUB_PR_URL.format(repository=self.repository)
        body = {
            "title": "Merge PR from {branchFrom} into {branchTo} on {date} ".format(
                branchFrom=branchFrom,
                branchTo=branchTo,
                date=datetime.today().strftime("%Y-%m-%d_%H-%M-%S"),
            ),
            "body": "PR opened by jenkins",
            "head": newBranch,
            "base": branchTo,
        }
        sc, _ = self._get_json(url, GITHUB_HEADERS, (GITHUB_USER, GITHUB_TOKEN), postData=body)
        if not sc:
            raise RuntimeError("create_pull_request(...) returned status code is None")
        return sc, newBranch


class GerritRepositoryAdapter(RepositoryAdapter):
    """Adapter for Gerrit repository operations"""

    def __init__(self, repo_info: repoinfo.RepositoryInfo):
        """
        Initialize Gerrit adapter.

        Args:
            repo_info: RepositoryInfo object containing repository metadata
        """
        self.repo_info = repo_info

    def _install_commit_msg_hook(self, repo: git.Repo, origin: git.Remote):
        """
        Install Gerrit commit-msg hook if not already present.

        Args:
            repo: GitPython Repo object
            origin: GitPython Remote object
        """
        import subprocess
        import os

        try:
            # Get git directory using git rev-parse
            git_dir = repo.git.rev_parse("--git-dir")
            hooks_dir = os.path.join(repo.working_dir, git_dir, "hooks")
            commit_msg_hook = os.path.join(hooks_dir, "commit-msg")

            if not os.path.exists(commit_msg_hook):
                logging.info("Installing Gerrit commit-msg hook")
                os.makedirs(hooks_dir, exist_ok=True)

                # Extract Gerrit host from URL (e.g., ssh://user@gerrit.corp.arista.io:29418/repo)
                gerrit_host = (
                    origin.url.split("@")[1].split(":")[0]
                    if "@" in origin.url
                    else origin.url.split("//")[1].split(":")[0]
                )
                hook_url = f"https://{gerrit_host}/tools/hooks/commit-msg"

                # Download and install the hook
                subprocess.run(
                    ["curl", "-Lo", commit_msg_hook, hook_url],
                    cwd=repo.working_dir,
                    check=True,
                    capture_output=True,
                )
                os.chmod(commit_msg_hook, 0o755)
                logging.info(f"Gerrit commit-msg hook installed successfully from {hook_url}")
        except Exception as e:
            logging.warning(f"Failed to install commit-msg hook: {e}")

    def compare(self, branchFrom: str, branchTo: str) -> Tuple[Optional[int], Optional[int], Any]:
        """
        Compare two branches using git commands.

        Args:
            branchFrom: Source branch name
            branchTo: Target branch name

        Returns:
            Tuple of (ahead_count, behind_count, extra_message)
        """
        try:
            repo, origin = gitutils.get_repo(
                self.repo_info.name, self.repo_info.git_url, branch=self.repo_info.default_branch
            )

            # Fetch latest changes
            origin.fetch()

            # Check if both branches exist in the repository
            try:
                # Try to get the branches - this will fail if they don't exist
                repo.git.rev_parse(f"origin/{branchFrom}")
                repo.git.rev_parse(f"origin/{branchTo}")
            except git.exc.GitCommandError:
                # One or both branches don't exist
                logging.debug(
                    f"Branch {branchFrom} or {branchTo} doesn't exist in {self.repo_info.name}"
                )
                return None, None, None

            # Get ahead count: commits in branchFrom not in branchTo
            # Use two-dot syntax (..) for proper comparison
            try:
                ahead_commits = list(repo.iter_commits(f"origin/{branchTo}..origin/{branchFrom}"))
                ahead = len(ahead_commits)
            except git.exc.GitCommandError:
                ahead = 0

            # Get behind count: commits in branchTo not in branchFrom
            try:
                behind_commits = list(repo.iter_commits(f"origin/{branchFrom}..origin/{branchTo}"))
                behind = len(behind_commits)
            except git.exc.GitCommandError:
                behind = 0

            extra = "!!! Need to merge !!!" if ahead > 0 else ""

            return ahead, behind, extra
        except Exception as e:
            logging.error(f"Error comparing Gerrit branches for {self.repo_info.name}: {e}")
            return None, None, None

    def merge(self, branchFrom: str, branchTo: str, push_conflicts: bool = False) -> Tuple[bool, str]:
        """
        Create a Gerrit WIP change to merge branchFrom into branchTo.

        Args:
            branchFrom: Source branch to merge from
            branchTo: Target branch to merge into
            push_conflicts: If True, push WIP changes even with conflict markers (default: False)

        Returns:
            Tuple of (success, status_message)
        """
        try:
            logging.info(
                f"Gerrit merge: {self.repo_info.name} - merging {branchFrom} into {branchTo}"
            )
            repo, origin = gitutils.get_repo(
                self.repo_info.name, self.repo_info.git_url, branch=branchTo
            )

            # Install Gerrit commit-msg hook
            self._install_commit_msg_hook(repo, origin)

            # Ensure we're on branchTo (target branch)
            logging.info(f"Checking out branch: {branchTo}")
            repo.heads[branchTo].checkout()
            origin.fetch()

            # Try to merge branchFrom into branchTo
            logging.info(f"Attempting to merge origin/{branchFrom} into {branchTo}")
            has_conflicts = False
            conflicted_files = []
            
            try:
                repo.git.merge(
                    f"origin/{branchFrom}", "--no-ff", "-m", f"Merge {branchFrom} into {branchTo}"
                )
                logging.info("Merge successful")
            except git.exc.GitCommandError as e:
                if "conflict" in str(e).lower():
                    has_conflicts = True
                    # Get list of conflicted files
                    try:
                        conflicted_files = repo.git.diff("--name-only", "--diff-filter=U").split("\n")
                        conflicted_files = [f for f in conflicted_files if f]  # Remove empty strings
                        conflict_list = ", ".join(conflicted_files) if conflicted_files else "unknown files"
                        
                        logging.warning(f"Merge conflicts detected in: {conflict_list}")
                        
                        if push_conflicts:
                            # Add all files (including conflicted ones with markers)
                            logging.info("Adding conflicted files with conflict markers for WIP review")
                            repo.git.add("-A")
                            
                            # Commit with conflict markers
                            commit_msg = f"WIP: Merge {branchFrom} into {branchTo} (HAS CONFLICTS)\n\nConflicted files:\n"
                            for cf in conflicted_files:
                                commit_msg += f"  - {cf}\n"
                            
                            repo.git.commit("-m", commit_msg)
                            logging.info("Committed merge with conflict markers")
                        else:
                            # Provide manual resolution instructions
                            logging.error(f"Repository path: {repo.working_dir}")
                            logging.error("To resolve manually:")
                            logging.error(f"  cd {repo.working_dir}")
                            logging.error(f"  # Fix conflicts in: {conflict_list}")
                            logging.error("  git add <resolved-files>")
                            logging.error("  git commit")
                            logging.error(f"  git push origin HEAD:refs/for/{branchTo}%wip")
                            
                            # Abort the merge to clean up
                            try:
                                repo.git.merge("--abort")
                                logging.info("Merge aborted, repository cleaned up")
                            except Exception:
                                pass
                            
                            return False, f"FAILED: conflicts in {conflict_list}"
                    except Exception as conflict_err:
                        logging.error(f"Error handling conflicts: {conflict_err}")
                        return False, "FAILED: conflicts (unable to process)"
                elif "Already up to date" in str(e) or "Already up-to-date" in str(e):
                    logging.info("Branches already up to date")
                    return True, "SKIPPED: no need to merge"
                else:
                    logging.error(f"Unexpected merge error: {e}")
                    raise

            # Push to Gerrit as WIP change for review
            refspec = f"HEAD:refs/for/{branchTo}%wip"
            logging.info(f"Pushing to Gerrit with refspec: {refspec}")
            logging.info(f"Remote URL: {origin.url}")
            try:
                push_info = origin.push(refspec)
                logging.info(f"Push result: {push_info}")
                for info in push_info:
                    logging.info(f"  - {info.summary}")
                
                if has_conflicts:
                    conflict_list = ", ".join(conflicted_files)
                    return True, f"DONE: WIP change created WITH CONFLICTS in {conflict_list}"
                else:
                    return True, "DONE: WIP change created for review"
            except git.exc.GitCommandError as e:
                logging.error(f"Failed to push Gerrit change: {e}")
                logging.error(f"  stderr: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
                logging.error(f"  stdout: {e.stdout if hasattr(e, 'stdout') else 'N/A'}")
                return False, f"FAILED: could not push change - {e}"

        except Exception as e:
            logging.error(f"Error merging Gerrit branches for {self.repo_info.name}: {e}")
            import traceback

            logging.error(traceback.format_exc())
            return False, f"FAILED: {e}"

    def create_branch(self, branchFrom: str, branchTo: str) -> Tuple[int, str]:
        """
        Create a new branch in a Gerrit repository.

        Args:
            branchFrom: Source branch to branch from
            branchTo: Target branch (used in naming)

        Returns:
            Tuple of (status_code, new_branch_name)
        """
        try:
            repo, origin = gitutils.get_repo(
                self.repo_info.name, self.repo_info.git_url, branch=branchFrom
            )

            # Create new branch name with timestamp
            newBranch = "automerge-from-{branchFrom}-to-{branchTo}-{date}-{time}".format(
                branchFrom=branchFrom,
                branchTo=branchTo,
                date=datetime.today().strftime("%Y-%m-%d"),
                time=time.time_ns(),
            )

            # Create and push branch
            repo.create_head(newBranch)
            origin.push(f"{newBranch}:{newBranch}")

            logging.debug(f"Created Gerrit branch: {newBranch}")
            return 200, newBranch
        except Exception as e:
            logging.error(f"Failed to create Gerrit branch: {e}")
            return 500, ""

    def create_pull_request(
        self, branchTo: str, newBranch: str, branchFrom: str
    ) -> Tuple[int, str]:
        """
        Create a Gerrit WIP change (equivalent to GitHub PR).

        Args:
            branchTo: Target branch for the change
            newBranch: New branch name to create change from
            branchFrom: Source branch

        Returns:
            Tuple of (status_code, branch_name)
        """
        try:
            repo, origin = gitutils.get_repo(
                self.repo_info.name, self.repo_info.git_url, branch=newBranch
            )

            # Install Gerrit commit-msg hook
            self._install_commit_msg_hook(repo, origin)

            # Push newBranch to Gerrit as WIP change targeting branchTo
            refspec = f"{newBranch}:refs/for/{branchTo}%wip"
            origin.push(refspec)

            return 200, newBranch
        except git.exc.GitCommandError as e:
            logging.error(f"Failed to create Gerrit change: {e}")
            return 500, newBranch


def create_repository_adapter(repo_info: repoinfo.RepositoryInfo) -> RepositoryAdapter:
    """
    Factory function to create appropriate repository adapter.

    Args:
        repo_info: RepositoryInfo object containing repository metadata

    Returns:
        GitHubRepositoryAdapter or GerritRepositoryAdapter based on git_base_url
    """
    if "gerrit" in repo_info.git_base_url:
        return GerritRepositoryAdapter(repo_info)
    else:
        return GitHubRepositoryAdapter(repo_info.name)


# CL options
parser = argparse.ArgumentParser(
    description="""List differences
between two branches across multiple repositories.

It can also optionally try to merge the branches before computing
the differences."""
)

parser.add_argument(
    "--log-level",
    dest="logLevel",
    choices=["debug", "info", "warning"],
    default="warning",
    help="level at which to log",
)
parser.add_argument(
    "--merge",
    dest="merge",
    action="store_true",
    default=False,
    help="try to merge first (default=False)",
)
parser.add_argument(
    "--push-conflicts",
    dest="pushConflicts",
    action="store_true",
    default=False,
    help="push WIP changes with conflict markers to Gerrit for review (default=False)",
)
parser.add_argument(
    "--pull-request",
    dest="openpr",
    action="store_true",
    default=False,
    help="open PR on failed merges (default=False)",
)
parser.add_argument(
    "--branch-from",
    dest="branchFrom",
    required=True,
    metavar="BRANCH_FROM",
    help="base branch)",
)
parser.add_argument(
    "--branch-to",
    dest="branchTo",
    required=True,
    metavar="BRANCH_TO",
    help="target branch)",
)

target = parser.add_mutually_exclusive_group(required=True)
target.add_argument(
    "--product",
    type=str,
    dest="product",
    metavar="PRODUCT",
    choices=("mfw", "ngfw", "waf", "efw", "velo"),
    help="product to work on",
)
target.add_argument(
    "--repositories",
    type=str,
    dest="repositories",
    nargs="*",
    metavar="REPOSITORIES",
    help="list of space-separated repositories to target",
)

if __name__ == "__main__":
    args = parser.parse_args()

    # logging
    logging.getLogger().setLevel(getattr(logging, args.logLevel.upper()))
    console = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("[%(asctime)s] changelog: %(levelname)-7s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

    product = args.product

    # Get repository info objects instead of just names
    if args.repositories:
        # When specific repositories are provided, get their info objects
        all_repo_infos = repoinfo.list_repositories(product)
        repository_infos = [r for r in all_repo_infos if r.name in args.repositories]
    else:
        # Get all repositories for the product that don't disable forward merge
        repository_infos = [
            r for r in repoinfo.list_repositories(product) if not r.disable_forward_merge
        ]

    branchFrom, branchTo = args.branchFrom, args.branchTo
    rc = 0

    print(HEADER1_TPL.format(branchFrom=branchFrom, branchTo=branchTo))

    for repo_info in repository_infos:
        repository = repo_info.name

        # Create appropriate adapter for this repository
        adapter = create_repository_adapter(repo_info)

        s = [""]
        s.append(HEADER2_TPL.format(repository=repository))

        if args.merge:
            # Use adapter pattern - pass push_conflicts for Gerrit repos
            if isinstance(adapter, GerritRepositoryAdapter):
                success, status = adapter.merge(branchFrom, branchTo, push_conflicts=args.pushConflicts)
            else:
                success, status = adapter.merge(branchFrom, branchTo)
            logging.debug("For {}: success={}, status={}".format(repository, success, status))
            s.append(OUTPUT_MERGE_TPL.format(status=status))
            if success:
                print("\n".join(s))
                continue
            else:
                rc = 1

        # Use adapter pattern
        ahead, behind, extra = adapter.compare(branchFrom, branchTo)
        if ahead is None:
            continue

        s.append(OUTPUT_COMPARE_TPL.format(ahead=ahead, behind=behind, extra=extra))
        print("\n".join(s))

        if args.openpr:
            # Use adapter pattern
            sc, newBranch = adapter.create_branch(branchFrom, branchTo)
            if sc != 200:
                print("Unable to create new branch - merge manually pls")
                exit(1)

            sc, _ = adapter.create_pull_request(branchTo, newBranch, branchFrom)
            if sc != 200:
                print("Unable to create PR/change - merge manually pls")
                exit(1)

    sys.exit(rc)
