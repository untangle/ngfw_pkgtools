"""Unit tests for RepoAPI factory and base class."""

import unittest
from lib.repo_api import get_api, RepoAPI
from lib.github_api import GitHubAPI
from lib.gerrit_api import GerritAPI


class TestRepoAPIFactory(unittest.TestCase):
    """Test cases for the get_api factory function."""
    
    def test_get_github_api(self):
        """Test that get_api returns GitHubAPI for 'github' type."""
        api = get_api("github")
        self.assertIsInstance(api, GitHubAPI)
        self.assertIsInstance(api, RepoAPI)
    
    def test_get_gerrit_api(self):
        """Test that get_api returns GerritAPI for 'gerrit' type."""
        api = get_api("gerrit")
        self.assertIsInstance(api, GerritAPI)
        self.assertIsInstance(api, RepoAPI)
    
    def test_get_default_api(self):
        """Test that get_api returns GitHubAPI by default."""
        api = get_api()
        self.assertIsInstance(api, GitHubAPI)
    
    def test_get_unknown_api_defaults_to_github(self):
        """Test that unknown repo types default to GitHub."""
        api = get_api("unknown")
        self.assertIsInstance(api, GitHubAPI)


class TestRepoAPIInterface(unittest.TestCase):
    """Test that both implementations conform to the RepoAPI interface."""
    
    def test_github_api_has_all_methods(self):
        """Test that GitHubAPI implements all required methods."""
        api = GitHubAPI()
        
        self.assertTrue(hasattr(api, 'merge_branches'))
        self.assertTrue(callable(api.merge_branches))
        
        self.assertTrue(hasattr(api, 'compare_branches'))
        self.assertTrue(callable(api.compare_branches))
        
        self.assertTrue(hasattr(api, 'create_pr'))
        self.assertTrue(callable(api.create_pr))
        
        self.assertTrue(hasattr(api, 'create_branch'))
        self.assertTrue(callable(api.create_branch))
        
        self.assertTrue(hasattr(api, 'get_branch_revision'))
        self.assertTrue(callable(api.get_branch_revision))
    
    def test_gerrit_api_has_all_methods(self):
        """Test that GerritAPI implements all required methods."""
        api = GerritAPI()
        
        self.assertTrue(hasattr(api, 'merge_branches'))
        self.assertTrue(callable(api.merge_branches))
        
        self.assertTrue(hasattr(api, 'compare_branches'))
        self.assertTrue(callable(api.compare_branches))
        
        self.assertTrue(hasattr(api, 'create_pr'))
        self.assertTrue(callable(api.create_pr))
        
        self.assertTrue(hasattr(api, 'create_branch'))
        self.assertTrue(callable(api.create_branch))
        
        self.assertTrue(hasattr(api, 'get_branch_revision'))
        self.assertTrue(callable(api.get_branch_revision))


if __name__ == '__main__':
    unittest.main()
