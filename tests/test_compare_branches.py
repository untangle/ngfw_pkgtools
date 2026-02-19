"""
Unit tests for compare-branches.py adapter classes
"""

import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path to import compare-branches module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module - need to handle the dash in filename
import importlib.util

spec = importlib.util.spec_from_file_location(
    "compare_branches",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compare-branches.py"
    ),
)
compare_branches = importlib.util.module_from_spec(spec)

# Patch the module into sys.modules so patches work correctly
sys.modules["compare_branches"] = compare_branches

# Now execute the module
spec.loader.exec_module(compare_branches)

from lib import repoinfo  # noqa: E402


class TestRepositoryAdapterFactory:
    """Test the factory function that creates appropriate adapters"""

    def test_creates_gerrit_adapter_for_gerrit_repo(self):
        """Test that Gerrit adapter is created for Gerrit repositories"""
        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.git_base_url = "ssh://user@gerrit.corp.arista.io:29418/efw"
        repo_info.name = "test-repo"

        adapter = compare_branches.create_repository_adapter(repo_info)

        assert isinstance(adapter, compare_branches.GerritRepositoryAdapter)
        assert adapter.repo_info == repo_info

    def test_creates_github_adapter_for_github_repo(self):
        """Test that GitHub adapter is created for GitHub repositories"""
        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.git_base_url = "git@github.com:untangle"
        repo_info.name = "test-repo"

        adapter = compare_branches.create_repository_adapter(repo_info)

        assert isinstance(adapter, compare_branches.GitHubRepositoryAdapter)
        assert adapter.repository == "test-repo"


class TestGitHubRepositoryAdapter:
    """Test GitHub repository adapter"""

    def test_initialization(self):
        """Test adapter initialization"""
        adapter = compare_branches.GitHubRepositoryAdapter("test-repo")
        assert adapter.repository == "test-repo"

    @patch("compare_branches.requests.get")
    def test_compare_success(self, mock_get):
        """Test successful branch comparison"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ahead_by": 5, "behind_by": 3}
        mock_get.return_value = mock_response

        adapter = compare_branches.GitHubRepositoryAdapter("test-repo")
        ahead, behind, extra = adapter.compare("feature", "main")

        assert ahead == 5
        assert behind == 3
        assert extra == "!!! Need to merge !!!"

    @patch("compare_branches.requests.get")
    def test_compare_no_changes(self, mock_get):
        """Test comparison when no changes ahead"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ahead_by": 0, "behind_by": 2}
        mock_get.return_value = mock_response

        adapter = compare_branches.GitHubRepositoryAdapter("test-repo")
        ahead, behind, extra = adapter.compare("feature", "main")

        assert ahead == 0
        assert behind == 2
        assert extra == ""

    @patch("compare_branches.requests.post")
    def test_merge_success(self, mock_post):
        """Test successful merge"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"sha": "abc123"}
        mock_post.return_value = mock_response

        adapter = compare_branches.GitHubRepositoryAdapter("test-repo")
        success, status = adapter.merge("feature", "main")

        assert success is True
        assert "DONE" in status
        assert "abc123" in status

    @patch("compare_branches.requests.post")
    def test_merge_no_changes(self, mock_post):
        """Test merge when no changes needed"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        adapter = compare_branches.GitHubRepositoryAdapter("test-repo")
        success, status = adapter.merge("feature", "main")

        assert success is True
        assert "SKIPPED" in status

    @patch("compare_branches.requests.post")
    def test_merge_conflicts(self, mock_post):
        """Test merge with conflicts"""
        mock_response = Mock()
        mock_response.status_code = 409  # Conflict
        mock_post.return_value = mock_response

        adapter = compare_branches.GitHubRepositoryAdapter("test-repo")
        success, status = adapter.merge("feature", "main")

        assert success is False
        assert "FAILED" in status


class TestGerritRepositoryAdapter:
    """Test Gerrit repository adapter"""

    def test_initialization(self):
        """Test adapter initialization"""
        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.name = "test-repo"
        repo_info.git_url = "ssh://user@gerrit.corp.arista.io:29418/efw/test-repo"

        adapter = compare_branches.GerritRepositoryAdapter(repo_info)
        assert adapter.repo_info == repo_info

    @patch("compare_branches.gitutils.get_repo")
    def test_compare_success(self, mock_get_repo):
        """Test successful branch comparison using git commands"""
        # Mock repository
        mock_repo = Mock()
        mock_origin = Mock()
        mock_get_repo.return_value = (mock_repo, mock_origin)

        # Mock git rev-parse to indicate branches exist
        mock_repo.git.rev_parse.return_value = "abc123"

        # Mock iter_commits - 5 ahead, 3 behind
        mock_repo.iter_commits.side_effect = [
            [Mock() for _ in range(5)],  # ahead
            [Mock() for _ in range(3)],  # behind
        ]

        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.name = "test-repo"
        repo_info.git_url = "ssh://user@gerrit.corp.arista.io:29418/efw/test-repo"
        repo_info.default_branch = "master"

        adapter = compare_branches.GerritRepositoryAdapter(repo_info)
        ahead, behind, extra = adapter.compare("feature", "main")

        assert ahead == 5
        assert behind == 3
        assert extra == "!!! Need to merge !!!"
        mock_origin.fetch.assert_called_once()

    @patch("compare_branches.gitutils.get_repo")
    def test_compare_no_changes(self, mock_get_repo):
        """Test comparison when no changes ahead"""
        mock_repo = Mock()
        mock_origin = Mock()
        mock_get_repo.return_value = (mock_repo, mock_origin)

        # Mock git rev-parse to indicate branches exist
        mock_repo.git.rev_parse.return_value = "abc123"

        # No commits ahead, 2 behind
        mock_repo.iter_commits.side_effect = [
            [],  # ahead
            [Mock(), Mock()],  # behind
        ]

        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.name = "test-repo"
        repo_info.git_url = "ssh://user@gerrit.corp.arista.io:29418/efw/test-repo"
        repo_info.default_branch = "master"

        adapter = compare_branches.GerritRepositoryAdapter(repo_info)
        ahead, behind, extra = adapter.compare("feature", "main")

        assert ahead == 0
        assert behind == 2
        assert extra == ""

    @patch("compare_branches.gitutils.get_repo")
    def test_merge_success(self, mock_get_repo):
        """Test successful merge creating WIP change"""
        mock_repo = Mock()
        mock_origin = Mock()
        mock_branch = Mock()
        # Mock both branches in heads dict (now we checkout branchTo, not branchFrom)
        mock_repo.heads = {"main": mock_branch, "feature": mock_branch}
        mock_repo.working_dir = "/tmp/test-repo"
        mock_repo.git.rev_parse.return_value = ".git"
        
        # Mock push_info to be iterable
        mock_push_info = Mock()
        mock_push_info.summary = "[new reference]"
        mock_origin.push.return_value = [mock_push_info]
        
        mock_get_repo.return_value = (mock_repo, mock_origin)

        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.name = "test-repo"
        repo_info.git_url = "ssh://user@gerrit.corp.arista.io:29418/efw/test-repo"

        adapter = compare_branches.GerritRepositoryAdapter(repo_info)
        success, status = adapter.merge("feature", "main")

        assert success is True
        assert "WIP change created" in status
        # Verify WIP refspec was used
        mock_origin.push.assert_called_once_with("HEAD:refs/for/main%wip")

    @patch("compare_branches.gitutils.get_repo")
    def test_merge_conflicts(self, mock_get_repo):
        """Test merge with conflicts"""
        mock_repo = Mock()
        mock_origin = Mock()
        mock_branch = Mock()
        # Mock both branches in heads dict
        mock_repo.heads = {"main": mock_branch, "feature": mock_branch}
        mock_repo.working_dir = "/tmp/test-repo"
        mock_repo.git.rev_parse.return_value = ".git"
        mock_get_repo.return_value = (mock_repo, mock_origin)

        # Simulate merge conflict
        import git

        mock_repo.git.merge.side_effect = git.exc.GitCommandError(
            "merge", "CONFLICT (content): Merge conflict"
        )

        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.name = "test-repo"
        repo_info.git_url = "ssh://user@gerrit.corp.arista.io:29418/efw/test-repo"

        adapter = compare_branches.GerritRepositoryAdapter(repo_info)
        success, status = adapter.merge("feature", "main")

        assert success is False
        assert "conflicts" in status

    @patch("compare_branches.gitutils.get_repo")
    def test_create_branch(self, mock_get_repo):
        """Test branch creation"""
        mock_repo = Mock()
        mock_origin = Mock()
        mock_new_branch = Mock()
        mock_repo.create_head.return_value = mock_new_branch
        mock_get_repo.return_value = (mock_repo, mock_origin)

        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.name = "test-repo"
        repo_info.git_url = "ssh://user@gerrit.corp.arista.io:29418/efw/test-repo"

        adapter = compare_branches.GerritRepositoryAdapter(repo_info)
        status_code, branch_name = adapter.create_branch("feature", "main")

        assert status_code == 200
        assert "automerge-from-feature-to-main" in branch_name
        assert mock_repo.create_head.called
        assert mock_origin.push.called

    @patch("compare_branches.gitutils.get_repo")
    def test_create_pull_request(self, mock_get_repo):
        """Test creating Gerrit WIP change (equivalent to PR)"""
        mock_repo = Mock()
        mock_origin = Mock()
        mock_repo.working_dir = "/tmp/test-repo"
        mock_repo.git.rev_parse.return_value = ".git"
        mock_get_repo.return_value = (mock_repo, mock_origin)

        repo_info = Mock(spec=repoinfo.RepositoryInfo)
        repo_info.name = "test-repo"
        repo_info.git_url = "ssh://user@gerrit.corp.arista.io:29418/efw/test-repo"

        adapter = compare_branches.GerritRepositoryAdapter(repo_info)
        status_code, branch_name = adapter.create_pull_request("main", "new-branch", "feature")

        assert status_code == 200
        assert branch_name == "new-branch"
        # Verify WIP refspec was used
        mock_origin.push.assert_called_once_with("new-branch:refs/for/main%wip")


class TestAdapterPolymorphism:
    """Test that both adapters implement the same interface"""

    def test_both_adapters_have_same_methods(self):
        """Verify both adapters implement all required methods"""
        required_methods = ["compare", "merge", "create_branch", "create_pull_request"]

        github_adapter = compare_branches.GitHubRepositoryAdapter("test")
        gerrit_repo_info = Mock(spec=repoinfo.RepositoryInfo)
        gerrit_adapter = compare_branches.GerritRepositoryAdapter(gerrit_repo_info)

        for method in required_methods:
            assert hasattr(github_adapter, method)
            assert callable(getattr(github_adapter, method))
            assert hasattr(gerrit_adapter, method)
            assert callable(getattr(gerrit_adapter, method))
