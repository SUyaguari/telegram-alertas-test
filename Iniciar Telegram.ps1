param([switch]$RevisarFormatos)

$ErrorActionPreference = 'Stop'
$stateDir = Join-Path $env:LOCALAPPDATA 'TelegramAlertasN8n'
$venv = Join-Path $stateDir 'venv'
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    py -3.12 -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno de Python.' }
}
& $python -c 'import telethon'
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install 'Telethon==1.45.0'
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar Telethon.' }
}
$secret = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'webhook.dpapi') | ConvertTo-SecureString
$env:N8N_TELEGRAM_BRIDGE_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
try {
    $bridgeArgs = @()
    if ($RevisarFormatos) { $bridgeArgs += '--revisar-formatos' }
    & $python (Join-Path $PSScriptRoot 'escuchar.py') @bridgeArgs
    if ($LASTEXITCODE -ne 0) { throw 'El conector de Telegram se detuvo.' }
} finally {
    Remove-Item Env:N8N_TELEGRAM_BRIDGE_KEY
}
