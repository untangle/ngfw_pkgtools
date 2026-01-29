"""Unit tests for GitHub API implementation."""

import unittest
from unittest.mock import patch, MagicMock
from lib.github_api import GitHubAPI


class TestGitHubAPI(unittest.TestCase):
    """Test cases for GitHubAPI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api = GitHubAPI()
        self.test_repo = "test-repo"
        self.test_branch_from = "feature-branch"
        self.test_branch_to = "main"
    
    @patch('lib.github_api.get_json')
    def test_merge_branches_success(self, mock_get_json):
        """Test successful branch merge."""
        mock_get_json.return_value = (201, {"sha": "abc123"})
        
        success, status = self.api.merge_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertTrue(success)
        self.assertIn("DONE", status)
        self.assertIn("abc123", status)
    
    @patch('lib.github_api.get_json')
    def test_merge_branches_no_need(self, mock_get_json):
        """Test merge when branches are already in sync."""
        mock_get_json.return_value = (204, None)
        
        success, status = self.api.merge_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertTrue(success)
        self.assertIn("SKIPPED: no need to merge", status)
    
    @patch('lib.github_api.get_json')
    def test_merge_branches_conflict(self, mock_get_json):
        """Test merge with conflicts."""
        mock_get_json.return_value = (409, {"message": "Merge conflict"})
        
        success, status = self.api.merge_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertFalse(success)
        self.assertIn("FAILED: conflicts", status)
    
    @patch('lib.github_api.get_json')
    def test_merge_branches_not_found(self, mock_get_json):
        """Test merge when branch not found."""
        mock_get_json.return_value = (None, None)
        
        success, status = self.api.merge_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertTrue(success)
        self.assertIn("SKIPPED: no comparison could be made", status)
    
    @patch('lib.github_api.get_json')
    def test_compare_branches_ahead(self, mock_get_json):
        """Test comparing branches when source is ahead."""
        mock_get_json.return_value = (200, {
            "ahead_by": 5,
            "behind_by": 0
        })
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertEqual(ahead, 5)
        self.assertEqual(behind, 0)
        self.assertIn("Need to merge", extra)
    
    @patch('lib.github_api.get_json')
    def test_compare_branches_in_sync(self, mock_get_json):
        """Test comparing branches when they are in sync."""
        mock_get_json.return_value = (200, {
            "ahead_by": 0,
            "behind_by": 0
        })
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertEqual(ahead, 0)
        self.assertEqual(behind, 0)
        self.assertEqual(extra, "")
    
    @patch('lib.github_api.get_json')
    def test_compare_branches_behind(self, mock_get_json):
        """Test comparing branches when source is behind."""
        mock_get_json.return_value = (200, {
            "ahead_by": 0,
            "behind_by": 3
        })
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertEqual(ahead, 0)
        self.assertEqual(behind, 3)
        self.assertEqual(extra, "")
    
    @patch('lib.github_api.get_json')
    def test_compare_branches_not_found(self, mock_get_json):
        """Test comparing branches when one doesn't exist."""
        mock_get_json.return_value = (None, None)
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertIsNone(ahead)
        self.assertIsNone(behind)
        self.assertIsNone(extra)
    
    @patch('lib.github_api.get_json')
    def test_create_pr_success(self, mock_get_json):
        """Test successful PR creation."""
        mock_get_json.return_value = (201, {"number": 42})
        new_branch = "automerge-test"
        
        sc, branch = self.api.create_pr(
            self.test_repo, self.test_branch_to, new_branch, self.test_branch_from
        )
        
        self.assertEqual(sc, 201)
        self.assertEqual(branch, new_branch)
    
    @patch('lib.github_api.get_json')
    def test_create_branch_success(self, mock_get_json):
        """Test successful branch creation."""
        # Mock get_branch_revision call
        mock_get_json.side_effect = [
            (200, {"commit": {"sha": "def456"}}),  # get_branch_revision
            (201, {"ref": "refs/heads/new-branch"})  # create_branch
        ]
        
        sc, new_branch = self.api.create_branch(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertEqual(sc, 201)
        self.assertIsNotNone(new_branch)
        self.assertIn("automerge", new_branch)
    
    @patch('lib.github_api.get_json')
    def test_get_branch_revision_success(self, mock_get_json):
        """Test getting branch revision."""
        test_sha = "abc123def456"
        mock_get_json.return_value = (200, {
            "commit": {"sha": test_sha}
        })
        
        sha = self.api.get_branch_revision(self.test_repo, self.test_branch_from)
        
        self.assertEqual(sha, test_sha)
    
    @patch('lib.github_api.get_json')
    def test_get_branch_revision_not_found(self, mock_get_json):
        """Test getting branch revision when branch doesn't exist."""
        mock_get_json.return_value = (None, None)
        
        sha = self.api.get_branch_revision(self.test_repo, self.test_branch_from)
        
        self.assertEqual(sha, "")


if __name__ == '__main__':
    unittest.main()
