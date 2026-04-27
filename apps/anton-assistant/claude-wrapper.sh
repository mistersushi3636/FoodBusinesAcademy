#!/bin/bash
# Auto-find latest Claude Code CLI regardless of extension version.
# Use this as CLAUDE_CLI_PATH instead of hardcoded version path.

CLAUDE=$(find /Users/anton/.vscode/extensions \
  -name "claude" \
  -path "*/native-binary/claude" \
  -type f 2>/dev/null \
  | sort -V | tail -1)

# Fallback: system PATH
if [ -z "$CLAUDE" ]; then
  CLAUDE=$(command -v claude 2>/dev/null)
fi

if [ -z "$CLAUDE" ]; then
  echo "ERROR: claude CLI not found. Install Claude Code VSCode extension." >&2
  exit 1
fi

exec "$CLAUDE" "$@"
