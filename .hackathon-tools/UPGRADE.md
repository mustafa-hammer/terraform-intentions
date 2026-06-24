# Upgrading RTS AI Hackathon Tools

**Audience:** AI agents performing automated upgrades for team projects.

This document provides the canonical upgrade procedure for updating `.hackathon-tools/` in team projects. Follow these steps exactly to ensure a clean, safe upgrade.

---

## Source Repository

The canonical source for hackathon tools is:

**Repository:** `https://github.ibm.com/hashicorp-services/rts-ai-hackathon-tools`

If you don't have a local clone, obtain it first:

```bash
# Clone the repository (if not already available)
git clone https://github.ibm.com/hashicorp-services/rts-ai-hackathon-tools /tmp/rts-ai-hackathon-tools

# Or update existing clone
cd /path/to/rts-ai-hackathon-tools
git pull origin main
```

---

## Pre-Upgrade Checklist

Before starting the upgrade:

1. **Obtain source repository**: Clone or update from `https://github.ibm.com/hashicorp-services/rts-ai-hackathon-tools`
2. **Verify target location**: Confirm the team project has `.hackathon-tools/` directory
3. **Check for uncommitted changes**: Warn the operator if `.hackathon/` has uncommitted changes
4. **Backup recommendation**: Suggest creating a backup (optional but recommended)

---

## Upgrade Procedure

### Step 1: Locate Directories

```bash
# Source: Updated tools repository
# Default location if just cloned:
SOURCE_DIR="/tmp/rts-ai-hackathon-tools"
# Or use existing clone:
# SOURCE_DIR="/path/to/existing/rts-ai-hackathon-tools"

# Target: Team project's tools directory
TARGET_DIR="/path/to/team-project/.hackathon-tools"

# Verify both exist
test -d "$SOURCE_DIR" || { echo "Error: Source not found"; exit 1; }
test -d "$TARGET_DIR" || { echo "Error: Target not found"; exit 1; }
```

### Step 2: Create Backup (Optional)

```bash
# Only if operator confirms
BACKUP_DIR="${TARGET_DIR}.backup.$(date +%Y%m%d-%H%M%S)"
cp -r "$TARGET_DIR" "$BACKUP_DIR"
echo "Backup created at: $BACKUP_DIR"
```

### Step 3: Sync Updated Tools

```bash
# Sync all files from source to target
# Excludes: .git directory to prevent sub-repo issues
rsync -av --delete \
  --exclude='.git' \
  --exclude='.git/' \
  --exclude='**/.git' \
  --exclude='**/.git/' \
  "$SOURCE_DIR/" "$TARGET_DIR/"
```

**Critical:** The `--exclude='.git'` flags prevent copying git metadata, which would create a nested git repository and cause issues when the team pushes their changes.

### Step 4: Remove Any Git Metadata

```bash
# Ensure no git metadata exists in target
# This prevents sub-repository issues
if [ -d "$TARGET_DIR/.git" ]; then
  rm -rf "$TARGET_DIR/.git"
  echo "Removed .git directory from .hackathon-tools/"
fi

# Check for nested .git directories
find "$TARGET_DIR" -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true
echo "Verified no nested .git directories"
```

### Step 5: Set Permissions

```bash
# Make scripts executable
chmod +x "$TARGET_DIR"/scripts/*.sh 2>/dev/null || true
chmod +x "$TARGET_DIR"/scripts/*.py 2>/dev/null || true
chmod +x "$TARGET_DIR"/tests/*.sh 2>/dev/null || true
echo "Set executable permissions on scripts"
```

### Step 6: Verify Update

```bash
# Check that key files exist
test -f "$TARGET_DIR/scripts/generate-repo-summary.py" || echo "Warning: generate-repo-summary.py missing"
test -f "$TARGET_DIR/scripts/validate-review-json.py" || echo "Warning: validate-review-json.py missing"
test -f "$TARGET_DIR/CHANGELOG.md" || echo "Warning: CHANGELOG.md missing"

# Verify no .git directory
if [ -d "$TARGET_DIR/.git" ]; then
  echo "ERROR: .git directory still exists in .hackathon-tools/"
  exit 1
fi

echo "Verification complete"
```

### Step 7: Refresh Bob Integration (If Applicable)

```bash
# If the project uses Bob and has .bob/ directory
if [ -d "/path/to/team-project/.bob" ]; then
  echo "Bob integration detected"
  echo "Bob will automatically load updated tools from .hackathon-tools/.bob/"
  echo "Recommend: Restart IDE or reload Bob extension"
fi
```

---

## Post-Upgrade Actions

### Inform the Operator

Provide this summary to the operator:

```
✓ Upgrade complete

Updated: .hackathon-tools/
Source: [path to source]
Backup: [path to backup, if created]

What was updated:
- All scripts in scripts/
- All documentation in review-commands/
- All templates and schemas
- Bob integration files (if present)

What was NOT updated (preserved):
- .hackathon/epic.md (your team's epic)
- .hackathon/team-profile.md (your team's profile)
- .hackathon/learning-notes.md (your team's notes)
- .hackathon/private/* (your team's private files)
- Any custom modifications outside .hackathon-tools/

Next steps:
1. Review CHANGELOG.md in .hackathon-tools/ for changes
2. If using Bob, restart your IDE or reload the extension
3. Test the tools: run .hackathon-tools/scripts/lint.sh
4. Continue your hackathon work!

To rollback (if needed):
  mv [backup path] .hackathon-tools
```

### Verification Test (Optional)

```bash
# Suggest running the test suite if it exists
if [ -f "$TARGET_DIR/tests/test-changed-files-fix.sh" ]; then
  echo "Run test suite to verify: $TARGET_DIR/tests/test-changed-files-fix.sh"
fi

# Suggest running linting
if [ -f "$TARGET_DIR/scripts/lint.sh" ]; then
  echo "Run linting to verify: $TARGET_DIR/scripts/lint.sh"
fi
```

---

## Troubleshooting

### Issue: "Permission denied" errors

```bash
chmod +x "$TARGET_DIR"/scripts/*.sh
chmod +x "$TARGET_DIR"/scripts/*.py
```

### Issue: Git complains about nested repository

```bash
# This should not happen if you followed Step 4
# But if it does:
rm -rf "$TARGET_DIR/.git"
find "$TARGET_DIR" -type d -name ".git" -exec rm -rf {} +
```

### Issue: Bob doesn't see updated commands

1. Verify `.hackathon-tools/.bob/` exists and has content
2. Restart the IDE/editor
3. Reload the Bob extension if available

### Issue: Scripts not executable

```bash
find "$TARGET_DIR" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} \;
```

---

## Rollback Procedure

If the upgrade causes issues:

```bash
# If backup exists
BACKUP_DIR="[path from Step 2]"
if [ -d "$BACKUP_DIR" ]; then
  rm -rf "$TARGET_DIR"
  mv "$BACKUP_DIR" "$TARGET_DIR"
  echo "Rollback complete"
else
  echo "No backup found - manual recovery needed"
fi
```

---

## Important Notes

### What This Upgrade Does NOT Touch

- `.hackathon/` directory (team's working files)
- `.hackathon/private/` (team's private notes)
- Project source code
- Project configuration files
- Git history or branches

### Git Repository Safety

The upgrade procedure explicitly:
- Excludes `.git` directories during rsync
- Removes any `.git` metadata after sync
- Verifies no nested repositories exist

This prevents "submodule" or "nested repository" issues when teams commit and push their work.

### Idempotency

This upgrade procedure is idempotent - it can be run multiple times safely. Each run will:
- Sync the latest tools
- Remove git metadata
- Set correct permissions
- Preserve team data

---

## Agent Implementation Notes

When implementing this upgrade in an AI agent:

1. **Always confirm with operator** before starting
2. **Show the backup path** if created
3. **Verify no .git directories** after sync
4. **Provide clear success/failure messages**
5. **Offer rollback** if issues occur
6. **Check CHANGELOG.md** and summarize changes for operator
7. **Test basic functionality** if possible (run lint.sh)

### Example Agent Workflow

```
1. Agent: "I can upgrade your .hackathon-tools/ to the latest version. This will update scripts and documentation while preserving your team's work. Create backup first? [yes/no]"
2. Operator: "yes"
3. Agent: [Creates backup, performs upgrade]
4. Agent: "✓ Upgrade complete. Backup at: .hackathon-tools.backup.20260624-120000. No git metadata in tools directory. Ready to continue."