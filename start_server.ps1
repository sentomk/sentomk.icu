param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 --version *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = "py -3"
    }
}

if (-not $pythonCmd -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $pythonCmd = "python"
} elseif (-not $pythonCmd -and (Get-Command python3 -ErrorAction SilentlyContinue)) {
    $pythonCmd = "python3"
}

if (-not $pythonCmd) {
    Write-Host "Python not found in PATH. Install Python first." -ForegroundColor Red
    exit 1
}

Write-Host "Starting static server at http://localhost:$Port" -ForegroundColor Green
Invoke-Expression "$pythonCmd -m http.server $Port"
