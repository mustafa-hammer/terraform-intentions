#!/bin/bash
# Linting script for hackathon tools
# Runs available linters on Python and Bash scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Hackathon Tools Linting ==="
echo ""

# Track overall status
ERRORS=0

# Python syntax check (always available)
echo "→ Python syntax check..."
if python3 -m py_compile "$PROJECT_ROOT"/scripts/*.py 2>/dev/null; then
    echo "  ✓ Python syntax check passed"
else
    echo "  ✗ Python syntax errors found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Shellcheck (if available)
if command -v shellcheck >/dev/null 2>&1; then
    echo "→ Shellcheck (bash linting)..."
    if shellcheck "$PROJECT_ROOT"/tests/*.sh "$PROJECT_ROOT"/scripts/*.sh 2>/dev/null; then
        echo "  ✓ Shellcheck passed"
    else
        echo "  ✗ Shellcheck found issues"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "→ Shellcheck not available (install with: brew install shellcheck)"
fi
echo ""

# Flake8 (if available)
if command -v flake8 >/dev/null 2>&1 || [ -x "$HOME/.local/bin/flake8" ]; then
    echo "→ Flake8 (Python style)..."
    FLAKE8_CMD=$(command -v flake8 || echo "$HOME/.local/bin/flake8")
    if "$FLAKE8_CMD" "$PROJECT_ROOT"/scripts/*.py --max-line-length=120 --extend-ignore=E203,W503; then
        echo "  ✓ Flake8 passed"
    else
        echo "  ✗ Flake8 found issues"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "→ Flake8 not available (install with: pipx install flake8)"
fi
echo ""

# Pylint (if available)
if command -v pylint >/dev/null 2>&1 || [ -x "$HOME/.local/bin/pylint" ]; then
    echo "→ Pylint (Python linting)..."
    PYLINT_CMD=$(command -v pylint || echo "$HOME/.local/bin/pylint")
    if "$PYLINT_CMD" "$PROJECT_ROOT"/scripts/*.py --max-line-length=120 --disable=C0103,C0114,C0115,C0116,R0912,R0913,R0914,R0915; then
        echo "  ✓ Pylint passed"
    else
        echo "  ✗ Pylint found issues"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "→ Pylint not available (install with: pipx install pylint)"
fi
echo ""

# Ruff (if available)
if command -v ruff >/dev/null 2>&1 || [ -x "$HOME/.local/bin/ruff" ]; then
    echo "→ Ruff (fast Python linter)..."
    RUFF_CMD=$(command -v ruff || echo "$HOME/.local/bin/ruff")
    if "$RUFF_CMD" check "$PROJECT_ROOT"/scripts/*.py; then
        echo "  ✓ Ruff passed"
    else
        echo "  ✗ Ruff found issues"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "→ Ruff not available (install with: pipx install ruff)"
fi
echo ""

# Summary
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "✓ All available linters passed"
    exit 0
else
    echo "✗ $ERRORS linter(s) found issues"
    exit 1
fi

# Made with Bob
