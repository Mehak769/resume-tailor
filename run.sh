#!/usr/bin/env bash
# resume-tailor quick-start launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure environment is synced
if [ ! -d ".venv" ]; then
    echo "⚡ Setting up virtual environment..."
    uv sync --all-extras
fi

# Run resume-tailor forwarding all arguments or launching interactive mode
uv run resume-tailor "$@"
