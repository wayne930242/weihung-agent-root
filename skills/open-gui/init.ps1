# One-time environment setup for open-gui on Windows.
# Mirrors init.sh. UNTESTED — written from documented tool behavior, not
# verified against a real Windows machine (none available in this session).
# Report issues; this is best-effort cross-platform support.
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== open-gui setup =="

if (-not (Get-Command deno -ErrorAction SilentlyContinue)) {
    Write-Host "Deno not found."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installing via winget..."
        winget install --id=DenoLand.Deno
    } elseif (Get-Command scoop -ErrorAction SilentlyContinue) {
        Write-Host "Installing via scoop..."
        scoop install deno
    } else {
        Write-Host "No winget or scoop found. Install Deno yourself: https://docs.deno.com/runtime/getting_started/installation/"
        exit 1
    }
} else {
    Write-Host "Deno found: $(deno --version | Select-Object -First 1)"
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js not found. The frontend's build tooling (Next.js) needs it."
    Write-Host "Install Node.js yourself: https://nodejs.org/"
    exit 1
} else {
    Write-Host "Node.js found: $(node --version)"
}

$WebDir = Join-Path $ScriptDir "web"
if (-not (Test-Path (Join-Path $WebDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $WebDir
    npm install
    Pop-Location
} else {
    Write-Host "Frontend dependencies already installed."
}

if (-not (Test-Path (Join-Path $WebDir "out"))) {
    Write-Host "Building frontend (static export)..."
    Push-Location $WebDir
    npm run build
    Pop-Location
} else {
    Write-Host "Frontend already built. Delete $WebDir\out to force a rebuild."
}

Write-Host "== open-gui setup complete =="
