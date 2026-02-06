# Unit Tests for ngfw_pkgtools

This directory contains unit tests for the ngfw_pkgtools project.

## Running Tests

### Using Make (Recommended)

```bash
# Run all tests with coverage
make test

# Format code before testing
make format

# Run linter
make lint
```

### Using Docker Directly

```bash
# Run tests
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest -v

# Run tests with coverage
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest -v --cov=lib --cov-report=term-missing

# Run specific test file
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest tests/test_repoinfo.py -v

# Run specific test
docker-compose -f docker-compose.dev.yml exec ngfw-pkgtools-dev pytest tests/test_repoinfo.py::TestRepositoryInfo::test_repository_info_git_url_construction -v
```

### Running Tests Locally (Without Docker)

```bash
# Install dependencies
pip3 install pytest pytest-cov PyYAML GitPython requests

# Run tests from project root
pytest -v --cov=lib --cov-report=term-missing
```

## Test Structure

### `test_repoinfo.py`

Tests for the `lib.repoinfo` module, which handles repository configuration loading.

**Test Classes:**

1. **TestRepositoryInfo** - Tests the RepositoryInfo dataclass
   - Git URL construction
   - Default values

2. **TestListRepositories** - Tests repository listing with mock data
   - Product-specific git_base_url overrides
   - Default git_base_url fallback
   - Repository-level git_base_url
   - Product-specific attributes (default_branch, etc.)
   - Obsolete repository filtering
   - Product filtering
   - Private attribute handling

3. **TestActualRepositoriesYaml** - Integration tests with actual repositories.yaml
   - Velo repositories use Gerrit (https://code.arista.io/efw)
   - MFW repositories use GitHub
   - EFW repositories use GitHub
   - Git URL validation

## Test Coverage

Current coverage: **87% for lib/repoinfo.py**

The tests cover:
- ✅ Product-specific git URL configuration
- ✅ Multi-level git_base_url resolution (product → repository → default)
- ✅ Repository filtering by product
- ✅ Obsolete repository handling
- ✅ Product-specific attributes
- ✅ Git URL construction

## Adding New Tests

When adding new functionality to the codebase:

1. Create test methods in the appropriate test class
2. Use descriptive test names: `test_<what_is_being_tested>`
3. Add docstrings explaining what the test validates
4. Use fixtures for reusable test data
5. Run tests to ensure they pass: `make test`

### Example Test

```python
def test_new_feature(self, sample_yaml_file):
    """Test that new feature works correctly"""
    # Arrange
    repos = repoinfo.list_repositories('product', yaml_file=sample_yaml_file)
    
    # Act
    result = some_function(repos)
    
    # Assert
    assert result == expected_value
```

## Continuous Integration

These tests should be run:
- Before committing code
- In CI/CD pipelines
- Before merging pull requests

## Troubleshooting

### Tests fail with "FileNotFoundError"
Make sure you're running tests from the project root directory.

### Import errors
Ensure the `conftest.py` file is present and properly configured.

### Docker container not running
Start the container with `make up` before running tests.
