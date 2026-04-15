<#
create_shortcut.ps1

Creates a desktop shortcut named "Run CyberBullying Chat.lnk" that launches
the project's `run_demo.ps1` via PowerShell. Run this script once to place the
shortcut on the current user's desktop.

Usage:
  Right-click -> Run with PowerShell
  OR from PowerShell (repo root):
    .\create_shortcut.ps1
#>

# Ensure path resolution is correct
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = Get-Location }
$scriptDir = (Resolve-Path $scriptDir).ProviderPath

# Paths
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutName = 'Run CyberBullying Chat.lnk'
$shortcutPath = Join-Path $desktop $shortcutName

# Use Windows PowerShell path; the shortcut will call PowerShell to run run_demo.ps1
$pwshPath = Join-Path $env:SystemRoot 'system32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path $pwshPath)) { $pwshPath = 'powershell.exe' }

# Arguments: change to script directory and run the run_demo.ps1 script
$runDemoScript = Join-Path $scriptDir 'run_demo.ps1'
# Escape single quotes in the path for safe inclusion inside a quoted -Command string
$escapedScriptDir = $scriptDir -replace "'", "''"
# Build the arguments string safely by concatenation so quoting is correct when the shortcut runs
$arguments = '-NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath ''' + $escapedScriptDir + '''; .\run_demo.ps1"'

# Create shortcut via WScript.Shell COM object
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pwshPath
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $scriptDir
$shortcut.IconLocation = "$pwshPath,0"
$shortcut.Save()

Write-Host "Created shortcut:`n  $shortcutPath" -ForegroundColor Green
