#!/bin/bash
# Test script to verify the changed-files.txt fix

set -e

# Get the project root directory (parent of tests/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Testing generate-repo-summary.py changed-files.txt generation..."
echo ""

# Create a temporary test directory
TEST_DIR=$(mktemp -d)

# Ensure cleanup on exit (success or failure)
trap 'cd "$PROJECT_ROOT" && rm -rf "$TEST_DIR"' EXIT

cd "$TEST_DIR"

# Initialize a git repo
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

# Create some files
echo "# Test Project" > README.md
echo "print('hello')" > main.py
git add .
git commit -q -m "Initial commit"

# Create test output directory
mkdir -p .hackathon

echo "Test 1: Running WITHOUT --base-ref (should list all files)"
python3 "$PROJECT_ROOT/scripts/generate-repo-summary.py" \
  --repo . \
  --out .hackathon/repo-summary.json \
  --changed-files-out .hackathon/changed-files.txt

if [ -s .hackathon/changed-files.txt ]; then
  echo "✓ PASS: changed-files.txt is not empty"
  echo "  Contents:"
  cat .hackathon/changed-files.txt | sed 's/^/    /'
else
  echo "✗ FAIL: changed-files.txt is empty"
  exit 1
fi

echo ""
echo "Test 2: Running WITH --base-ref but no changes (should fall back to all files)"
python3 "$PROJECT_ROOT/scripts/generate-repo-summary.py" \
  --repo . \
  --out .hackathon/repo-summary.json \
  --changed-files-out .hackathon/changed-files.txt \
  --base-ref HEAD \
  --head-ref HEAD

if [ -s .hackathon/changed-files.txt ]; then
  echo "✓ PASS: changed-files.txt is not empty (fallback worked)"
  echo "  Contents:"
  cat .hackathon/changed-files.txt | sed 's/^/    /'
else
  echo "✗ FAIL: changed-files.txt is empty"
  exit 1
fi

echo ""
echo "Test 3: Running WITH --base-ref and actual changes"
echo "# Updated" >> README.md
git add README.md
git commit -q -m "Update README"

python3 "$PROJECT_ROOT/scripts/generate-repo-summary.py" \
  --repo . \
  --out .hackathon/repo-summary.json \
  --changed-files-out .hackathon/changed-files.txt \
  --base-ref HEAD~1 \
  --head-ref HEAD

if [ -s .hackathon/changed-files.txt ]; then
  echo "✓ PASS: changed-files.txt is not empty"
  echo "  Contents:"
  cat .hackathon/changed-files.txt | sed 's/^/    /'
else
  echo "✗ FAIL: changed-files.txt is empty"
  exit 1
fi

echo ""
echo "All tests passed! ✓"

# Cleanup happens automatically via trap

# Made with Bob
