<#
run_demo_wt.ps1

Launch the Flask service, chat server and GUI client each in its own Windows Terminal tab (wt.exe).

Usage:
  .\run_demo_wt.ps1

Notes:
 - Requires Windows Terminal (wt.exe) to be installed and available on PATH.
 - Uses .venv\Scripts\python.exe if present; otherwise falls back to 'python' from PATH.
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = Get-Location }
$scriptDir = (Resolve-Path $scriptDir).ProviderPath

# Python executable in venv if present
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) { $venvPython = 'python' }

# Check for wt.exe
if (-not (Get-Command wt.exe -ErrorAction SilentlyContinue)) {
    Write-Host "Windows Terminal (wt.exe) not found on PATH. Install Windows Terminal or use run_demo.ps1 instead." -ForegroundColor Red
    exit 1
}

# Build tab commands; use single quotes around $scriptDir in the inner PowerShell -Command so paths with spaces are handled
$tab1 = "new-tab PowerShell -NoExit -Command \"Set-Location -LiteralPath '$scriptDir'; & '$venvPython' -m flask --app service_testing.app run\""
$tab2 = "new-tab PowerShell -NoExit -Command \"Set-Location -LiteralPath '$scriptDir'; & '$venvPython' '$scriptDir\\Safe_Chat\\server.py'\""
$tab3 = "new-tab PowerShell -NoExit -Command \"Set-Location -LiteralPath '$scriptDir'; & '$venvPython' '$scriptDir\\Safe_Chat\\client_GUI.py'\""
$tab4 = "new-tab PowerShell -NoExit -Command \"Set-Location -LiteralPath '$scriptDir'; & '$venvPython' '$scriptDir\\Safe_Chat\\client_GUI.py'\""

$args = "$tab1 ; $tab2 ; $tab3 ; $tab4"

Write-Host "Launching Windows Terminal with four tabs (two GUI clients)..." -ForegroundColor Green
Start-Process wt.exe -ArgumentList $args
