"""Abstract base class for repository API implementations."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any


class RepoAPI(ABC):
    """Abstract base class for repository API operations."""
    
    @abstractmethod
    def merge_branches(self, repository: str, branch_from: str, branch_to: str) -> Tuple[bool, str]:
        """
        Merge branch_from into branch_to.
        
        Args:
            repository: Repository name
            branch_from: Source branch
            branch_to: Target branch
            
        Returns:
            Tuple of (success, status_message)
        """
        pass
    
    @abstractmethod
    def compare_branches(
        self, repository: str, branch_from: str, branch_to: str
    ) -> Tuple[Optional[int], Optional[int], Any]:
        """
        Compare two branches.
        
        Args:
            repository: Repository name
            branch_from: Source branch
            branch_to: Target branch
            
        Returns:
            Tuple of (commits_ahead, commits_behind, extra_message)
        """
        pass
    
    @abstractmethod
    def create_pr(
        self, repository: str, branch_to: str, new_branch: str, branch_from: str
    ) -> Tuple[Optional[int], str]:
        """
        Create a pull request or change.
        
        Args:
            repository: Repository name
            branch_to: Target branch
            new_branch: Source branch for the PR
            branch_from: Original branch name (for PR title)
            
        Returns:
            Tuple of (status_code, identifier)
        """
        pass
    
    @abstractmethod
    def create_branch(
        self, repository: str, branch_from: str, branch_to: str
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Create a new branch.
        
        Args:
            repository: Repository name
            branch_from: Source branch to base the new branch on
            branch_to: Target branch (used in naming)
            
        Returns:
            Tuple of (status_code, new_branch_name)
        """
        pass
    
    @abstractmethod
    def get_branch_revision(self, repository: str, branch: str) -> str:
        """
        Get the current revision (commit SHA) of a branch.
        
        Args:
            repository: Repository name
            branch: Branch name
            
        Returns:
            Commit SHA
        """
        pass


def get_api(repo_type: str = "github") -> RepoAPI:
    """
    Factory function to get the appropriate API implementation.
    
    Args:
        repo_type: Type of repository ("github" or "gerrit")
        
    Returns:
        RepoAPI implementation instance
    """
    if repo_type == "gerrit":
        from lib.gerrit_api import GerritAPI
        return GerritAPI()
    else:
        from lib.github_api import GitHubAPI
        return GitHubAPI()
