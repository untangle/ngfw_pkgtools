# GitHub to Gerrit Migration Guide

## Overview

This document describes the migration of the codebase from GitHub to Gerrit, including updates to support both repository types during the transition period.

## Changes Made

### 1. Repository Configuration (`repositories.yaml`)

Added support for specifying repository type:

- **`default_repo_type`**: Set to `github` (default for all repositories)
- **`repo_type`**: Per-repository field to override the default

Currently migrated repositories:
- `discoverd` - set to `gerrit`
- `bctid` - set to `gerrit`

All other repositories remain on GitHub until migrated.

**Example:**
```yaml
default_repo_type: github

repositories:
  discoverd:
    repo_type: gerrit
    private: true
    products:
      mfw:
      efw:
```

### 2. Repository Info Library (`lib/repoinfo.py`)

Updated the [`RepositoryInfo`](lib/repoinfo.py:11) dataclass to include:
- New field: `repo_type` (default: `'github'`)
- Automatically populated from `repositories.yaml` configuration

### 3. Gerrit API Integration (`lib/gerrit_api.py`)

Created a new module with Gerrit-specific API functions:

**Key Functions:**
- [`compare_branches()`](lib/gerrit_api.py:73) - Compare two branches in Gerrit
- [`merge_branches()`](lib/gerrit_api.py:113) - Attempt to merge branches (creates change for review)
- [`create_change()`](lib/gerrit_api.py:135) - Create a Gerrit change (equivalent to GitHub PR)
- [`get_branch_revision()`](lib/gerrit_api.py:165) - Get current commit SHA of a branch

**Required Environment Variables:**
- `GERRIT_BASE_URL` - Base URL of your Gerrit instance (default: `https://gerrit.corp.arista.io`)
- `GERRIT_USER` - Gerrit username for authentication
- `GERRIT_PASSWORD` - Gerrit password or HTTP password

### 4. Compare Branches Script (`compare-branches.py`)

Updated to support both GitHub and Gerrit repositories:

**Changes:**
- Renamed original functions with `github_` prefix (e.g., [`github_merge()`](compare-branches.py:94), [`github_compare()`](compare-branches.py:120))
- Created unified interface functions that route to GitHub or Gerrit based on `repo_type`:
  - [`merge()`](compare-branches.py:186) - Routes merge operations
  - [`compare()`](compare-branches.py:194) - Routes comparison operations
  - [`createPR()`](compare-branches.py:202) - Routes PR/Change creation
  - [`createBranch()`](compare-branches.py:211) - Routes branch creation
  - [`getHeadSha()`](compare-branches.py:221) - Routes SHA retrieval

**Output Changes:**
- Now displays repository type in output: `type: github` or `type: gerrit`

## Usage

### Setting Up Environment Variables

For GitHub (existing):
```bash
export GITHUB_TOKEN="your_github_token"
```

For Gerrit (new):
```bash
export GERRIT_BASE_URL="https://gerrit.corp.arista.io"  # Optional, this is the default
export GERRIT_USER="your_username"
export GERRIT_PASSWORD="your_http_password"
```

### Running compare-branches.py

The script usage remains the same:

```bash
# Compare branches for a product
./compare-branches.py --product mfw --branch-from master --branch-to release-1.0

# Compare specific repositories
./compare-branches.py --repositories discoverd bctid --branch-from master --branch-to release-1.0

# With merge attempt
./compare-branches.py --product mfw --branch-from master --branch-to release-1.0 --merge

# With PR/Change creation on conflicts
./compare-branches.py --product mfw --branch-from master --branch-to release-1.0 --merge --pull-request
```

The script will automatically use the appropriate API (GitHub or Gerrit) based on each repository's `repo_type` configuration.

## Migration Process

To migrate a repository from GitHub to Gerrit:

1. **Update `repositories.yaml`:**
   ```yaml
   repository_name:
     repo_type: gerrit
     # ... other configuration
   ```

2. **Ensure Gerrit environment variables are set** (see above)

3. **Test the repository** with compare-branches.py:
   ```bash
   ./compare-branches.py --repositories repository_name --branch-from master --branch-to develop
   ```

4. **Verify output** shows `type: gerrit`

## Important Notes

### Gerrit vs GitHub Differences

1. **Merging:**
   - GitHub: Direct merge via API
   - Gerrit: Creates a change that requires review and submission

2. **Pull Requests vs Changes:**
   - GitHub: Creates a PR with a temporary branch
   - Gerrit: Creates a change directly (no temporary branch needed)

3. **Authentication:**
   - GitHub: Uses personal access token
   - Gerrit: Uses HTTP password (generated in Gerrit settings)

### Limitations

- Gerrit's [`merge_branches()`](lib/gerrit_api.py:113) currently returns a skip status as direct merges require the change workflow
- Branch creation for Gerrit repositories is not implemented (not needed for Gerrit workflow)
- The [`compare_branches()`](lib/gerrit_api.py:73) function fetches up to 1000 commits for comparison

## Testing

To test the migration:

1. **Test GitHub repositories** (should work as before):
   ```bash
   ./compare-branches.py --repositories ngfw_pkgs --branch-from master --branch-to develop
   ```

2. **Test Gerrit repositories** (discoverd, bctid):
   ```bash
   ./compare-branches.py --repositories discoverd bctid --branch-from master --branch-to develop
   ```

3. **Test mixed product** (contains both types):
   ```bash
   ./compare-branches.py --product mfw --branch-from master --branch-to develop
   ```

## Troubleshooting

### Authentication Errors

**GitHub:**
- Ensure `GITHUB_TOKEN` is set and valid
- Token needs appropriate repository permissions

**Gerrit:**
- Ensure `GERRIT_BASE_URL`, `GERRIT_USER`, and `GERRIT_PASSWORD` are set
- Password should be HTTP password from Gerrit settings, not your login password
- Check Gerrit user has appropriate project access

### API Errors

- Check logs with `--log-level debug` for detailed error messages
- Verify repository names match exactly in Gerrit/GitHub
- Ensure branches exist in the repository

## Future Work

- Implement full Gerrit merge workflow with change submission
- Add support for Gerrit-specific features (reviewers, labels, etc.)
- Migrate additional scripts (create-branch.py, etc.)
- Add automated tests for both GitHub and Gerrit code paths
