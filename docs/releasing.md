# Releasing to PyPI

This document describes how to release a new version of `notebooklm-py` to PyPI.

## Pre-release Checklist

- [ ] All tests pass: `pytest`
- [ ] E2E readonly tests pass: `pytest tests/e2e -m readonly`
- [ ] No uncommitted changes: `git status`
- [ ] On `main` branch with latest changes

## Release Steps

### 1. Update Version

Edit `pyproject.toml` and update the version number:

```toml
[project]
name = "notebooklm-py"
version = "X.Y.Z"  # Update this
```

Follow [semantic versioning](https://semver.org/):
- **MAJOR** (X): Breaking API changes
- **MINOR** (Y): New features, backward compatible
- **PATCH** (Z): Bug fixes, backward compatible

### 2. Commit Version Bump

```bash
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git push
```

### 3. Test on TestPyPI

Build and upload to TestPyPI first:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

Test the installation (uses TestPyPI for the package, PyPI for dependencies):

```bash
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple notebooklm-py
```

Or with pip:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple notebooklm-py
```

Verify it works:

```bash
notebooklm --version
notebooklm --help
```

### 4. Create Release Tag

Once TestPyPI verification passes:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

This triggers the GitHub Actions workflow (`.github/workflows/publish.yml`) which automatically publishes to PyPI using trusted publishing.

### 5. Verify PyPI Release

After the workflow completes:

```bash
# Install from PyPI
pip install --upgrade notebooklm-py

# Verify
notebooklm --version
```

## Troubleshooting

### TestPyPI upload fails

Ensure you have a TestPyPI account and API token:
1. Create account at https://test.pypi.org/account/register/
2. Create API token at https://test.pypi.org/manage/account/token/
3. Configure in `~/.pypirc` or use `twine upload --username __token__ --password <token>`

### GitHub Actions publish fails

Ensure trusted publishing is configured on PyPI:
1. Go to https://pypi.org/manage/project/notebooklm-py/settings/publishing/
2. Add publisher with:
   - Owner: `teng-lin`
   - Repository: `notebooklm-py`
   - Workflow: `publish.yml`

### Version already exists

PyPI versions are immutable. If you need to fix something:
1. Yank the bad version (optional): `twine yank notebooklm-py X.Y.Z`
2. Bump to next patch version and release again

## Quick Reference

```bash
# Full release flow
pytest                                    # Run tests
vim pyproject.toml                        # Bump version
git add pyproject.toml && git commit -m "chore: bump version to X.Y.Z"
git push
python -m build                           # Build
twine upload --repository testpypi dist/* # Upload to TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple notebooklm-py  # Test
git tag vX.Y.Z && git push origin vX.Y.Z  # Release to PyPI
```
