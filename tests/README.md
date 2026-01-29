# Test Suite for ngfw_pkgtools

This directory contains unit tests for the ngfw_pkgtools repository API libraries.

## Test Coverage

### [`test_github_api.py`](test_github_api.py)
Tests for the GitHub API implementation ([`GitHubAPI`](../lib/github_api.py) class):
- `test_merge_branches_success` - Successful branch merge
- `test_merge_branches_no_need` - Merge when branches are in sync
- `test_merge_branches_conflict` - Merge with conflicts
- `test_merge_branches_not_found` - Merge when branch doesn't exist
- `test_compare_branches_ahead` - Compare when source is ahead
- `test_compare_branches_in_sync` - Compare when branches are in sync
- `test_compare_branches_behind` - Compare when source is behind
- `test_compare_branches_not_found` - Compare when branch doesn't exist
- `test_create_pr_success` - Successful PR creation
- `test_create_branch_success` - Successful branch creation
- `test_get_branch_revision_success` - Get branch revision
- `test_get_branch_revision_not_found` - Get revision when branch doesn't exist

### [`test_gerrit_api.py`](test_gerrit_api.py)
Tests for the Gerrit API implementation ([`GerritAPI`](../lib/gerrit_api.py) class):
- `test_compare_branches_ahead` - Compare when source is ahead
- `test_compare_branches_in_sync` - Compare when branches are in sync
- `test_compare_branches_behind` - Compare when source is behind
- `test_compare_branches_not_found` - Compare when branch doesn't exist
- `test_merge_branches_not_supported` - Verify direct merge is not supported
- `test_create_pr_success` - Successful change creation
- `test_create_pr_failure` - Failed change creation
- `test_create_branch_not_implemented` - Verify branch creation is not implemented
- `test_get_branch_revision_success` - Get branch revision
- `test_get_branch_revision_not_found` - Get revision when branch doesn't exist
- `test_get_branch_revision_no_revision_field` - Handle missing revision field

### [`test_repo_api.py`](test_repo_api.py)
Tests for the abstract base class and factory function:
- `test_get_github_api` - Factory returns GitHubAPI for 'github' type
- `test_get_gerrit_api` - Factory returns GerritAPI for 'gerrit' type
- `test_get_default_api` - Factory returns GitHubAPI by default
- `test_get_unknown_api_defaults_to_github` - Unknown types default to GitHub
- `test_github_api_has_all_methods` - GitHubAPI implements all required methods
- `test_gerrit_api_has_all_methods` - GerritAPI implements all required methods

### [`test_products.py`](test_products.py)
Tests for the Product enum:
- `test_product_values` - All expected products are defined
- `test_product_choices` - choices() returns all product values
- `test_product_str` - Product enum converts to string correctly
- `test_product_is_string_enum` - Product members are string instances
- `test_product_comparison` - Product enum can be compared with strings

## Running Tests

### Run All Tests
```bash
# From the repository root
python3 -m pytest tests/

# Or using the test runner
python3 tests/run_tests.py

# Or from the tests directory
cd tests
python3 run_tests.py
```

### Run Specific Test File
```bash
# Run only GitHub API tests
python3 -m pytest tests/test_github_api.py

# Or using unittest
python3 -m unittest tests.test_github_api
```

### Run Specific Test Case
```bash
# Run a specific test method
python3 -m pytest tests/test_github_api.py::TestGitHubAPI::test_merge_branches_success

# Or using unittest
python3 -m unittest tests.test_github_api.TestGitHubAPI.test_merge_branches_success
```

### Run with Verbose Output
```bash
python3 -m pytest tests/ -v

# Or with unittest
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Test Dependencies

The tests use Python's built-in `unittest` framework and `unittest.mock` for mocking external dependencies. No additional test dependencies are required.

## Writing New Tests

When adding new functionality to the API libraries:

1. Create test methods in the appropriate test file
2. Use `@patch` decorators to mock external API calls
3. Test both success and failure scenarios
4. Ensure edge cases are covered
5. Follow the existing naming convention: `test_<method_name>_<scenario>`

Example:
```python
@patch('lib.github_api.get_json')
def test_new_method_success(self, mock_get_json):
    """Test successful execution of new method."""
    mock_get_json.return_value = (200, {"data": "value"})
    
    result = self.api.new_method("param")
    
    self.assertEqual(result, expected_value)
```

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: python3 tests/run_tests.py
```

## Coverage

To generate test coverage reports (requires `coverage` package):

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m pytest tests/

# Generate report
coverage report

# Generate HTML report
coverage html
```
