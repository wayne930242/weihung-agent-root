#!/usr/bin/env bash
# One-time environment setup for open-gui: Deno (runs the backend directly,
# including the Agent SDK via an npm: specifier — no separate sidecar
# process, design.md D11) and the static frontend build (needs Node.js only
# for its own build tooling). Safe to re-run — every step is
# skip-if-already-done. macOS/Linux only; see init.ps1 for Windows (untested
# — this machine has no Windows environment to verify it against).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== open-gui setup =="

if ! command -v deno >/dev/null 2>&1; then
  echo "Deno not found."
  if command -v brew >/dev/null 2>&1; then
    echo "Installing via Homebrew..."
    brew install deno
  else
    echo "No Homebrew found. Install Deno yourself: https://docs.deno.com/runtime/getting_started/installation/"
    exit 1
  fi
else
  echo "Deno found: $(deno --version | head -1)"
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. The frontend's build tooling (Next.js) needs it."
  echo "Install Node.js yourself (e.g. via nvm): https://nodejs.org/"
  exit 1
else
  echo "Node.js found: $(node --version)"
fi

WEB_DIR="$SCRIPT_DIR/web"
if [ ! -d "$WEB_DIR/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd "$WEB_DIR" && npm install)
else
  echo "Frontend dependencies already installed."
fi

if [ ! -d "$WEB_DIR/out" ]; then
  echo "Building frontend (static export)..."
  (cd "$WEB_DIR" && npm run build)
else
  echo "Frontend already built. Delete $WEB_DIR/out to force a rebuild."
fi

echo "== open-gui setup complete =="
