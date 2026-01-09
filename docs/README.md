# Documentation Folder

**Status:** Active
**Last Updated:** 2026-01-08

This folder contains all project documentation. AI agents must follow the rules in `/CONTRIBUTING.md`.

## Folder Structure

| Folder | Purpose | File Format |
|--------|---------|-------------|
| `contributing/` | Contributor guides | `lowercase-kebab.md` |
| `examples/` | Runnable example scripts | `lowercase-kebab.py` |
| `reference/internals/` | Reverse engineering notes | `lowercase-kebab.md` |
| `designs/` | Approved design decisions | `lowercase-kebab.md` |
| `scratch/` | Temporary agent work | `YYYY-MM-DD-context.md` |

## Rules for This Folder

1. **Root files are defined** - Only the files listed in "Top-Level Files" belong at `docs/` root. All other docs go in subfolders.

2. **Reference docs are stable** - Only update `reference/` files when fixing errors or adding significant new information.

3. **Designs are living docs** - Files in `designs/` document architectural decisions. Delete when implementation is complete and design is captured elsewhere (code comments, PRs).

4. **Scratch is temporary** - Files in `scratch/` can be deleted after 30 days. Always use date prefix.

## Top-Level Files

- `getting-started.md` - Installation and first workflow
- `cli-reference.md` - Complete CLI command reference
- `python-api.md` - Python API reference with examples
- `configuration.md` - Storage, environment variables, settings
- `troubleshooting.md` - Common errors and known issues
- `releasing.md` - PyPI release checklist and process
