"""Unit tests for Gerrit API implementation."""

import unittest
from unittest.mock import patch, MagicMock
from lib.gerrit_api import GerritAPI


class TestGerritAPI(unittest.TestCase):
    """Test cases for GerritAPI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api = GerritAPI()
        self.test_repo = "test-project"
        self.test_branch_from = "feature-branch"
        self.test_branch_to = "main"
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_compare_branches_ahead(self, mock_auth, mock_get_json):
        """Test comparing branches when source is ahead."""
        mock_auth.return_value = ("user", "pass")
        
        # Mock responses for both branch commit queries
        commits_from = [
            {"commit": "abc123"},
            {"commit": "def456"},
            {"commit": "ghi789"}
        ]
        commits_to = [
            {"commit": "ghi789"}
        ]
        
        mock_get_json.side_effect = [
            (200, commits_from),  # branch_from commits
            (200, commits_to)     # branch_to commits
        ]
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertEqual(ahead, 2)  # abc123 and def456 are ahead
        self.assertEqual(behind, 0)
        self.assertIn("Need to merge", extra)
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_compare_branches_in_sync(self, mock_auth, mock_get_json):
        """Test comparing branches when they are in sync."""
        mock_auth.return_value = ("user", "pass")
        
        commits = [
            {"commit": "abc123"},
            {"commit": "def456"}
        ]
        
        mock_get_json.side_effect = [
            (200, commits),  # branch_from commits
            (200, commits)   # branch_to commits (same)
        ]
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertEqual(ahead, 0)
        self.assertEqual(behind, 0)
        self.assertEqual(extra, "")
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_compare_branches_behind(self, mock_auth, mock_get_json):
        """Test comparing branches when source is behind."""
        mock_auth.return_value = ("user", "pass")
        
        commits_from = [
            {"commit": "abc123"}
        ]
        commits_to = [
            {"commit": "abc123"},
            {"commit": "def456"},
            {"commit": "ghi789"}
        ]
        
        mock_get_json.side_effect = [
            (200, commits_from),  # branch_from commits
            (200, commits_to)     # branch_to commits
        ]
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertEqual(ahead, 0)
        self.assertEqual(behind, 2)  # def456 and ghi789 are behind
        self.assertEqual(extra, "")
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_compare_branches_not_found(self, mock_auth, mock_get_json):
        """Test comparing branches when one doesn't exist."""
        mock_auth.return_value = ("user", "pass")
        mock_get_json.side_effect = [
            (None, None),  # branch_from not found
            (200, [])      # branch_to
        ]
        
        ahead, behind, extra = self.api.compare_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertIsNone(ahead)
        self.assertIsNone(behind)
        self.assertIsNone(extra)
    
    def test_merge_branches_not_supported(self):
        """Test that direct merge is not supported in Gerrit."""
        success, status = self.api.merge_branches(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertFalse(success)
        self.assertIn("SKIPPED", status)
        self.assertIn("Gerrit", status)
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_create_pr_success(self, mock_auth, mock_get_json):
        """Test successful change creation."""
        mock_auth.return_value = ("user", "pass")
        test_change_id = "I1234567890abcdef"
        
        mock_get_json.return_value = (201, {
            "change_id": test_change_id,
            "id": "project~branch~I1234567890abcdef"
        })
        
        sc, change_id = self.api.create_pr(
            self.test_repo, self.test_branch_to, "", self.test_branch_from
        )
        
        self.assertEqual(sc, 201)
        self.assertEqual(change_id, test_change_id)
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_create_pr_failure(self, mock_auth, mock_get_json):
        """Test failed change creation."""
        mock_auth.return_value = ("user", "pass")
        mock_get_json.return_value = (None, None)
        
        sc, change_id = self.api.create_pr(
            self.test_repo, self.test_branch_to, "", self.test_branch_from
        )
        
        self.assertIsNone(sc)
        self.assertEqual(change_id, '')
    
    def test_create_branch_not_implemented(self):
        """Test that branch creation is not implemented for Gerrit."""
        sc, branch = self.api.create_branch(
            self.test_repo, self.test_branch_from, self.test_branch_to
        )
        
        self.assertIsNone(sc)
        self.assertIsNone(branch)
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_get_branch_revision_success(self, mock_auth, mock_get_json):
        """Test getting branch revision."""
        mock_auth.return_value = ("user", "pass")
        test_sha = "abc123def456"
        
        mock_get_json.return_value = (200, {
            "revision": test_sha
        })
        
        sha = self.api.get_branch_revision(self.test_repo, self.test_branch_from)
        
        self.assertEqual(sha, test_sha)
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_get_branch_revision_not_found(self, mock_auth, mock_get_json):
        """Test getting branch revision when branch doesn't exist."""
        mock_auth.return_value = ("user", "pass")
        mock_get_json.return_value = (404, None)
        
        sha = self.api.get_branch_revision(self.test_repo, self.test_branch_from)
        
        self.assertEqual(sha, '')
    
    @patch('lib.gerrit_api.get_json')
    @patch('lib.gerrit_api.get_gerrit_auth')
    def test_get_branch_revision_no_revision_field(self, mock_auth, mock_get_json):
        """Test getting branch revision when response has no revision field."""
        mock_auth.return_value = ("user", "pass")
        mock_get_json.return_value = (200, {})
        
        sha = self.api.get_branch_revision(self.test_repo, self.test_branch_from)
        
        self.assertEqual(sha, '')


if __name__ == '__main__':
    unittest.main()
