# run_demo.ps1
# Launches Flask service, chat server (with ngrok), and 2 GUI clients.
# Usage: Right-click -> Run with PowerShell, or: .\run_demo.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $scriptDir

# Find python
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
    $venvPython = "python"
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   ChatShield - Starting all services..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Flask prediction service
Write-Host "[1/3] Starting Flask prediction service..." -ForegroundColor Yellow
Start-Process -FilePath powershell.exe -ArgumentList @(
    '-NoExit',
    '-Command',
    "Set-Location -LiteralPath '$scriptDir'; `$env:FLASK_APP='service_testing.app'; & '$venvPython' -m flask --app service_testing.app run; Read-Host 'Press Enter to close'"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# 2. Start Chat Server (ngrok tunnel starts here, HOST:PORT printed in this window)
Write-Host "[2/3] Starting Chat Server + ngrok tunnel..." -ForegroundColor Yellow
Write-Host ""
Write-Host ">>> CHECK THE SERVER WINDOW for your shareable HOST and PORT <<<" -ForegroundColor Green
Write-Host ""
Start-Process -FilePath powershell.exe -ArgumentList @(
    '-NoExit',
    '-Command',
    "Set-Location -LiteralPath '$scriptDir'; & '$venvPython' '$scriptDir\Safe_Chat\server.py'; Read-Host 'Press Enter to close'"
) -WindowStyle Normal

# Wait for server + ngrok to be ready
Write-Host "Waiting for server to start (5 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 3. Launch 2 GUI clients
Write-Host "[3/3] Launching 2 chat client windows..." -ForegroundColor Yellow
for ($i = 1; $i -le 2; $i++) {
    Start-Process -FilePath powershell.exe -ArgumentList @(
        '-NoExit',
        '-Command',
        "Set-Location -LiteralPath '$scriptDir'; & '$venvPython' '$scriptDir\Safe_Chat\client_GUI.py'; Read-Host 'Press Enter to close'"
    ) -WindowStyle Normal
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  All windows launched!" -ForegroundColor Green
Write-Host ""
Write-Host "  HOW TO CONNECT:" -ForegroundColor White
Write-Host "  1. Look at the SERVER window for HOST and PORT" -ForegroundColor White
Write-Host "  2. Paste them into each client's Connect screen" -ForegroundColor White
Write-Host "  3. Use the same Room ID on both clients to chat" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close this launcher"