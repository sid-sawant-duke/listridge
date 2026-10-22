#!/usr/bin/env bash
# Listridge installer. Safe to run more than once.
set -euo pipefail

cd "$(dirname "$0")"

say()  { printf '%s\n' "$1"; }
fail() { printf '\n❌ %s\n   Next step: %s\n' "$1" "$2"; exit 1; }

say "Setting up Listridge..."

# 1. macOS only for now
if [[ "$(uname)" != "Darwin" ]]; then
  fail "This tool only runs on a Mac for now." "Run it on a Mac. Windows support is coming later."
fi

# 2. Python 3.9+
if ! command -v python3 >/dev/null 2>&1; then
  fail "Python 3 isn't installed." "Install it from https://www.python.org/downloads/ then run ./install.sh again."
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  fail "Your Python is too old (need 3.9 or newer)." "Install a newer Python from https://www.python.org/downloads/ then run ./install.sh again."
fi
say "✓ Python $(python3 -c 'import platform; print(platform.python_version())')"

# 3. Local virtual environment with the one dependency (Excel support)
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv || fail "Couldn't create the Python environment." "Run ./install.sh again. If it keeps failing, reinstall Python."
fi
.venv/bin/python -m pip install --quiet --upgrade pip >/dev/null
.venv/bin/python -m pip install --quiet openpyxl \
  || fail "Couldn't install Excel support (openpyxl)." "Check your internet connection and run ./install.sh again."
say "✓ Excel support installed"

# 4. Data folders (gitignored, stay on this Mac)
mkdir -p data/raw data/work data/campaigns config
if [[ ! -f data/suppression.csv ]]; then
  printf 'linkedin_url,full_name,company,reason\n' > data/suppression.csv
fi
say "✓ Data folders ready"

# 5. Browser mode (optional): ./install.sh --browser
if [[ "${1:-}" == "--browser" ]]; then
  if ! command -v npx >/dev/null 2>&1; then
    fail "Browser mode needs Node.js, which isn't installed." "Install it from https://nodejs.org (LTS), then run ./install.sh --browser again."
  fi
  if [[ ! -d "/Applications/Google Chrome.app" && ! -d "$HOME/Applications/Google Chrome.app" ]]; then
    fail "Browser mode needs Google Chrome." "Install it from https://www.google.com/chrome, then run ./install.sh --browser again."
  fi
  mkdir -p .browser-session/profile .browser-session/output
  say "Downloading the browser tool (one time)..."
  npx --yes @playwright/mcp@0.0.83 --help >/dev/null 2>&1 \
    || fail "Couldn't download the browser tool." "Check your internet connection and run ./install.sh --browser again."
  say "✓ Browser mode ready. It uses its own Chrome profile in .browser-session/, separate from your normal Chrome."
  say "  When Claude Code asks whether to use the 'playwright' server from .mcp.json, choose yes."
  say "  Then run /login-linkedin once."
else
  say "• Browser mode is off. Uploading a file works without it. To turn it on: ./install.sh --browser"
fi

say ""
say "All set. Open Claude Code in this folder and run, in order:"
say "  /configure-icp   → define a good lead"
say "  /setup-sequence  → set your email style"
say "  /ingest-rank     → load and score your leads"
say "  /enrich          → (optional) add emails and phones"
say "  /draft-sequence  → write emails and export the CSV"
