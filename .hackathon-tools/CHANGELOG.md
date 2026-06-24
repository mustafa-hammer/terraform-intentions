# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed blank `changed-files.txt` generation in `scripts/generate-repo-summary.py`. The script now falls back to listing all tracked files when `--base-ref` is provided but git diff returns no changes, preventing empty output files.
- Fixed shellcheck SC2064 warning in `tests/test-changed-files-fix.sh` by correcting trap variable quoting.
- Fixed 7 flake8 style issues (line length, whitespace, unused import) in Python scripts.
- Fixed 2 pylint issues (unused argument, import location) achieving perfect 10/10 score.

### Security
- Added git ref validation in `scripts/generate-repo-summary.py` to prevent potential injection attacks via `--base-ref` and `--head-ref` parameters.
- Added security warning to `--verification-command` help text about shell command execution.
- Added security documentation in `run_verification()` function.
- Improved test script cleanup with trap to ensure temporary directories are removed even on failure.

### Changed
- Added guidance in `review-commands/prepare-hackathon-submission.md` for determining appropriate base ref when generating repo summaries. Includes examples for both with and without base ref scenarios.

### Added
- Created `tests/` directory with `test-changed-files-fix.sh` to verify the changed-files.txt fix works correctly.
- Added `scripts/lint.sh` automated linting script that runs all available linters (shellcheck, flake8, pylint, ruff).

## [1.0.0] - 2026-06-22

### Added
- Initial release of RTS AI Hackathon Tools with participant workflows, harness adapters, epic templates, review agents, schemas, and documentation.

[Unreleased]: https://github.com/hashicorp/rts-ai-hackathon-tools/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/hashicorp/rts-ai-hackathon-tools/releases/tag/v1.0.0