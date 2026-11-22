$ErrorActionPreference = 'Stop'
$secretPath = Join-Path $PSScriptRoot 'webhook.dpapi'
if (Test-Path -LiteralPath $secretPath) {
    throw 'El conector ya tiene un secreto local en webhook.dpapi.'
}

$apiKeyInput = Read-Host 'API key de n8n' -AsSecureString
$apiKey = [System.Net.NetworkCredential]::new('', $apiKeyInput).Password
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
$secret = [Convert]::ToBase64String($bytes)
$encrypted = ConvertTo-SecureString -String $secret -AsPlainText -Force | ConvertFrom-SecureString

$body = @{
    name = 'Telegram personal - acceso local'
    type = 'httpHeaderAuth'
    data = @{ name = 'X-Telegram-Bridge-Key'; value = $secret }
} | ConvertTo-Json -Depth 4 -Compress

$headers = @{ 'X-N8N-API-KEY' = $apiKey }
$uri = 'http://localhost:5678/api/v1/credentials'
$credential = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 20
$encrypted | Set-Content -LiteralPath $secretPath -Encoding Ascii
Write-Host ('Credencial creada: ' + $credential.name)
