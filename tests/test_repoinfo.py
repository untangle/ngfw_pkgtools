"""
Unit tests for lib.repoinfo module

Tests repository configuration loading and product-specific git URL handling.
"""

import os
import tempfile
import pytest
import yaml
from lib import repoinfo


class TestRepositoryInfo:
    """Test RepositoryInfo dataclass"""

    def test_repository_info_git_url_construction(self):
        """Test that git_url is properly constructed from git_base_url and name"""
        repo = repoinfo.RepositoryInfo(
            name="test-repo",
            git_base_url="git@github.com:untangle",
            versioned_resources=[]
        )
        assert repo.git_url == "git@github.com:untangle/test-repo"

    def test_repository_info_defaults(self):
        """Test default values for RepositoryInfo"""
        repo = repoinfo.RepositoryInfo(
            name="test-repo",
            git_base_url="git@github.com:untangle",
            versioned_resources=[]
        )
        assert repo.default_branch == "master"
        assert repo.obsolete is False
        assert repo.disable_branch_creation is False
        assert repo.disable_forward_merge is False
        assert repo.skip_versioning_entirely is False
        assert repo.private is False


class TestListRepositories:
    """Test list_repositories function"""

    @pytest.fixture
    def sample_yaml_file(self):
        """Create a temporary YAML file for testing"""
        yaml_content = {
            'default_git_base_url': 'git@github.com:untangle',
            'git_sources': {
                'github': 'git@github.com:untangle',
                'gerrit': 'ssh://{username}@gerrit.corp.arista.io:29418/efw'
            },
            'repositories': {
                'test-repo-1': {
                    'git_source': 'gerrit',
                    'products': {
                        'mfw': None,
                        'velo': None
                    }
                },
                'test-repo-2': {
                    'private': True,
                    'products': {
                        'ngfw': {
                            'default_branch': 'main'
                        }
                    }
                },
                'test-repo-3': {
                    'git_base_url': 'git@github.com:custom',
                    'products': {
                        'mfw': None
                    }
                },
                'obsolete-repo': {
                    'obsolete': True,
                    'products': {
                        'mfw': None
                    }
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            temp_file = f.name

        yield temp_file

        # Cleanup
        os.unlink(temp_file)

    def test_repository_git_source(self, sample_yaml_file):
        """Test that repository-level git_source resolves to correct git_base_url"""
        repos = repoinfo.list_repositories('velo', yaml_file=sample_yaml_file)

        # Find test-repo-1
        repo = next((r for r in repos if r.name == 'test-repo-1'), None)
        assert repo is not None
        # Should have username substituted
        assert repo.git_base_url.startswith('ssh://')
        assert '@gerrit.corp.arista.io:29418/efw' in repo.git_base_url
        assert repo.git_url.endswith('/test-repo-1')

    def test_default_git_base_url(self, sample_yaml_file):
        """Test that default git_base_url is used when no git_source is specified"""
        repos = repoinfo.list_repositories('ngfw', yaml_file=sample_yaml_file)

        # Find test-repo-2 (has no git_source or git_base_url, should use default)
        repo = next((r for r in repos if r.name == 'test-repo-2'), None)
        assert repo is not None
        assert repo.git_base_url == 'git@github.com:untangle'
        assert repo.git_url == 'git@github.com:untangle/test-repo-2'

    def test_repository_level_git_base_url(self, sample_yaml_file):
        """Test that repository-level git_base_url overrides default"""
        repos = repoinfo.list_repositories('mfw', yaml_file=sample_yaml_file)

        # Find test-repo-3
        repo = next((r for r in repos if r.name == 'test-repo-3'), None)
        assert repo is not None
        assert repo.git_base_url == 'git@github.com:custom'
        assert repo.git_url == 'git@github.com:custom/test-repo-3'

    def test_product_specific_default_branch(self, sample_yaml_file):
        """Test that product-specific default_branch is applied"""
        repos = repoinfo.list_repositories('ngfw', yaml_file=sample_yaml_file)

        # Find test-repo-2
        repo = next((r for r in repos if r.name == 'test-repo-2'), None)
        assert repo is not None
        assert repo.default_branch == 'main'

    def test_obsolete_repositories_excluded(self, sample_yaml_file):
        """Test that obsolete repositories are excluded by default"""
        repos = repoinfo.list_repositories('mfw', yaml_file=sample_yaml_file)

        # obsolete-repo should not be in the list
        repo_names = [r.name for r in repos]
        assert 'obsolete-repo' not in repo_names

    def test_obsolete_repositories_included_when_requested(self, sample_yaml_file):
        """Test that obsolete repositories are included when requested"""
        repos = repoinfo.list_repositories('mfw', yaml_file=sample_yaml_file, include_obsolete=True)

        # obsolete-repo should be in the list
        repo_names = [r.name for r in repos]
        assert 'obsolete-repo' in repo_names

    def test_product_filtering(self, sample_yaml_file):
        """Test that only repositories for the specified product are returned"""
        mfw_repos = repoinfo.list_repositories('mfw', yaml_file=sample_yaml_file)
        ngfw_repos = repoinfo.list_repositories('ngfw', yaml_file=sample_yaml_file)

        mfw_names = [r.name for r in mfw_repos]
        ngfw_names = [r.name for r in ngfw_repos]

        # test-repo-1 and test-repo-3 are only in mfw
        assert 'test-repo-1' in mfw_names
        assert 'test-repo-3' in mfw_names
        assert 'test-repo-1' not in ngfw_names
        assert 'test-repo-3' not in ngfw_names

        # test-repo-2 is only in ngfw
        assert 'test-repo-2' in ngfw_names
        assert 'test-repo-2' not in mfw_names

    def test_private_attribute(self, sample_yaml_file):
        """Test that private attribute is correctly set"""
        mfw_repos = repoinfo.list_repositories('mfw', yaml_file=sample_yaml_file)
        ngfw_repos = repoinfo.list_repositories('ngfw', yaml_file=sample_yaml_file)

        repo1 = next((r for r in mfw_repos if r.name == 'test-repo-1'), None)
        repo2 = next((r for r in ngfw_repos if r.name == 'test-repo-2'), None)

        assert repo1 is not None
        assert repo2 is not None
        assert repo1.private is False
        assert repo2.private is True


class TestActualRepositoriesYaml:
    """Test against the actual repositories.yaml file"""

    @pytest.fixture
    def actual_yaml_file(self):
        """Get the path to the actual repositories.yaml file"""
        import os.path as osp
        # Get the path relative to the test file
        test_dir = osp.dirname(__file__)
        yaml_path = osp.join(test_dir, '..', 'repositories.yaml')
        return osp.abspath(yaml_path)

    def test_velo_repositories_use_gerrit(self, actual_yaml_file):
        """Test that velo repositories use Gerrit URLs"""
        repos = repoinfo.list_repositories('velo', yaml_file=actual_yaml_file)

        velo_repo_names = [
            'golang-shared', 'mfw_feeds', 'mfw_schema',
            'packetd', 'restd', 'secret-manager', 'sync-settings'
        ]

        for repo_name in velo_repo_names:
            repo = next((r for r in repos if r.name == repo_name), None)
            assert repo is not None, f"Repository {repo_name} not found for velo"
            assert repo.git_base_url.startswith('ssh://'), \
                f"Repository {repo_name} should use Gerrit SSH URL for velo"
            assert '@gerrit.corp.arista.io:29418/efw' in repo.git_base_url, \
                f"Repository {repo_name} should use Gerrit URL for velo"

    def test_gerrit_repositories_consistent_across_products(self, actual_yaml_file):
        """Test that repositories with git_source=gerrit use Gerrit for ALL products"""
        # These repos have git_source: gerrit, so they use Gerrit for all products
        gerrit_repo_names = ['golang-shared', 'mfw_feeds', 'packetd']

        for product in ['mfw', 'efw', 'velo']:
            repos = repoinfo.list_repositories(product, yaml_file=actual_yaml_file)
            for repo_name in gerrit_repo_names:
                repo = next((r for r in repos if r.name == repo_name), None)
                if repo:  # Repository might not be in all products
                    assert repo.git_base_url.startswith('ssh://'), \
                        f"Repository {repo_name} should use Gerrit SSH URL for {product}"
                    assert '@gerrit.corp.arista.io:29418/efw' in repo.git_base_url, \
                        f"Repository {repo_name} should use Gerrit URL for {product}"

    def test_github_repositories_use_default(self, actual_yaml_file):
        """Test that repositories without git_source use default GitHub URL"""
        # These repos don't have git_source, so they use the default (GitHub)
        github_repo_names = ['ngfw_pkgtools', 'runtests']

        for product in ['mfw', 'ngfw']:
            repos = repoinfo.list_repositories(product, yaml_file=actual_yaml_file)
            for repo_name in github_repo_names:
                repo = next((r for r in repos if r.name == repo_name), None)
                if repo:  # Repository might not be in all products
                    assert repo.git_base_url == 'git@github.com:untangle', \
                        f"Repository {repo_name} should use default GitHub URL for {product}"

    def test_all_velo_repos_have_valid_git_urls(self, actual_yaml_file):
        """Test that all velo repositories have properly constructed git URLs"""
        repos = repoinfo.list_repositories('velo', yaml_file=actual_yaml_file)

        for repo in repos:
            assert repo.git_url, f"Repository {repo.name} has empty git_url"
            assert repo.git_url.startswith(repo.git_base_url), \
                f"Repository {repo.name} git_url doesn't start with git_base_url"
            # Check that git_url ends with either repo name or gerrit_name (if specified)
            expected_name = repo.gerrit_name if repo.gerrit_name else repo.name
            assert repo.git_url.endswith(expected_name), \
                f"Repository {repo.name} git_url doesn't end with expected name {expected_name}"


class TestRemoteRepositoryExistence:
    """Test that remote repositories actually exist (requires network access)
    
    Run these tests with: pytest -v -m remote
    Skip these tests with: pytest -v -m "not remote" (default)
    """

    @pytest.fixture
    def actual_yaml_file(self):
        """Get the path to the actual repositories.yaml file"""
        import os.path as osp
        # Get the path relative to the test file
        test_dir = osp.dirname(__file__)
        yaml_path = osp.join(test_dir, '..', 'repositories.yaml')
        return osp.abspath(yaml_path)

    @pytest.mark.remote
    def test_velo_gerrit_repositories_exist(self, actual_yaml_file):
        """Test that velo Gerrit repositories can be accessed"""
        import subprocess
        
        repos = repoinfo.list_repositories('velo', yaml_file=actual_yaml_file)
        gerrit_repos = [r for r in repos if 'gerrit' in r.git_base_url]
        
        failures = []
        for repo in gerrit_repos:
            # Use git ls-remote to check if repository exists without cloning
            result = subprocess.run(
                ['git', 'ls-remote', '--heads', repo.git_url],
                capture_output=True,
                timeout=10,
                text=True
            )
            if result.returncode != 0:
                failures.append(f"{repo.name} ({repo.git_url}): {result.stderr}")
        
        assert not failures, f"Failed to access repositories:\n" + "\n".join(failures)

    @pytest.mark.remote
    def test_github_repositories_exist(self, actual_yaml_file):
        """Test that GitHub repositories can be accessed"""
        import subprocess
        
        repos = repoinfo.list_repositories('ngfw', yaml_file=actual_yaml_file)
        github_repos = [r for r in repos if 'github' in r.git_base_url][:5]  # Test first 5
        
        failures = []
        for repo in github_repos:
            # Use git ls-remote to check if repository exists without cloning
            result = subprocess.run(
                ['git', 'ls-remote', '--heads', repo.git_url],
                capture_output=True,
                timeout=10,
                text=True
            )
            if result.returncode != 0:
                failures.append(f"{repo.name} ({repo.git_url}): {result.stderr}")
        
        assert not failures, f"Failed to access repositories:\n" + "\n".join(failures)
