# Precept one-line installer (Windows PowerShell)
#   irm https://raw.githubusercontent.com/qorstack/precept/main/install.ps1 | iex
#
# Or with workspace + Claude Code:
#   $env:PRECEPT_WORKSPACE = "my-product"; $env:PRECEPT_CLAUDE = "1"
#   irm https://raw.githubusercontent.com/qorstack/precept/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$workspace = $env:PRECEPT_WORKSPACE
$linkClaude = $env:PRECEPT_CLAUDE -eq "1"
$repoPath = if ($env:PRECEPT_REPO) { $env:PRECEPT_REPO } else { (Get-Location).Path }

Write-Host "-> Precept installer" -ForegroundColor Cyan

# 1. Ensure uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "-> Installing uv (https://astral.sh/uv)" -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

# 2. Install precept
Write-Host "-> Installing precept" -ForegroundColor Yellow
uv tool install git+https://github.com/qorstack/precept.git --upgrade

# 3. Smoke test
precept --version

# 4. Optional workspace
if ($workspace) {
    $existing = precept workspace list 2>$null
    if ($existing -notmatch $workspace) {
        Write-Host "-> Creating workspace '$workspace'" -ForegroundColor Yellow
        precept workspace create $workspace
    }
    Write-Host "-> Linking $repoPath to '$workspace'" -ForegroundColor Yellow
    Push-Location $repoPath
    try { precept init --link $workspace } finally { Pop-Location }
}

# 5. Optional Claude Code registration
if ($linkClaude) {
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        Write-Host "-> Registering MCP server with Claude Code" -ForegroundColor Yellow
        Push-Location $repoPath
        try { claude mcp add precept -- uvx precept mcp --repo . } finally { Pop-Location }
    } else {
        Write-Host "! claude CLI not found. Install Claude Code, then run:" -ForegroundColor DarkYellow
        Write-Host "  claude mcp add precept -- uvx precept mcp --repo ."
    }
}

Write-Host ""
Write-Host "Done. Try:" -ForegroundColor Green
Write-Host "  precept scan ."
Write-Host "  precept analyze 'add password reset' --repo ."
