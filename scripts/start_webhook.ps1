<#
.SYNOPSIS
  Starts the ngrok tunnel for the TruthLens Twilio webhook and wires the
  current public URL into .env (TWILIO_WEBHOOK_PUBLIC_URL), then recreates
  the backend container so the new URL takes effect.

.DESCRIPTION
  Free ngrok assigns a new random URL on every run. Run this script after
  every reboot / tunnel restart, then re-point the Twilio console webhook
  to the URL it prints (one URL change in Twilio Console -> Messaging ->
  Try it out -> WhatsApp sandbox settings -> WHEN A MESSAGE COMES IN).

.USAGE
  powershell -ExecutionPolicy Bypass -File scripts\start_webhook.ps1
#>

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile  = Join-Path $repoRoot ".env"

# Locate ngrok (winget both installs a shim and a package binary)
$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
$ngPath = $null
if ($ngrok) { $ngPath = $ngrok.Source }
if (-not $ngPath -or -not (Test-Path $ngPath)) {
    $ngPath = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
}
if (-not (Test-Path $ngPath)) {
    Write-Error "ngrok.exe not found. Install with: winget install -e Ngrok.Ngrok"
}

# Stop any previous tunnel
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Start the new tunnel against the backend's published port
$log = "$env:TEMP\opencode\ngrok.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Start-Process -FilePath $ngPath -ArgumentList 'http', '8000', "--log=$log", '--log-format=term' -WindowStyle Hidden
Start-Sleep -Seconds 10

# Read the assigned public URL from the local ngrok API
try {
    $api = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 20
    $url = ($api.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1).public_url
} catch {
    Write-Error "Could not reach the local ngrok daemon on 127.0.0.1:4040. Tunnel likely failed to start; check $log"
}

if (-not $url) { Write-Error "ngrok reported no https tunnel. Check $log" }

# Patch .env (replace existing TWILIO_WEBHOOK_PUBLIC_URL line, append if absent)
$lines = Get-Content $envFile | Where-Object { $_ -notmatch '^\s*TWILIO_WEBHOOK_PUBLIC_URL\s*=' }
$lines += "TWILIO_WEBHOOK_PUBLIC_URL=$url/api/v1/whatsapp"
Set-Content -Path $envFile -Value $lines -Encoding UTF8

# Recreate the backend so the setting is read (restart is not enough)
Push-Location $repoRoot
docker compose up -d backend | Out-Null
Pop-Location

Write-Output ""
Write-Output "Tunnel live: $url"
Write-Output "Webhook URL to paste into the Twilio console sandbox settings:"
Write-Output "  $url/api/v1/whatsapp"
Write-Output "Backend recreated and reading the new URL."
