$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$envPath = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $envPath) {
    Write-Host 'Plik .env już istnieje. Zachowano bieżącą konfigurację.'
    exit 0
}
function New-LocalSecret {
    $bytes = [byte[]]::new(48)
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return [Convert]::ToBase64String($bytes)
}
$lines = @(
    'POSTGRES_DB=myhomebudget'
    'POSTGRES_USER=myhomebudget'
    ('POSTGRES_PASSWORD=' + (New-LocalSecret))
    ('DJANGO_SECRET_KEY=' + (New-LocalSecret))
)
$stream = [IO.File]::Open($envPath, [IO.FileMode]::CreateNew)
try {
    $writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($false))
    $writer.Write(($lines -join [Environment]::NewLine) + [Environment]::NewLine)
    $writer.Flush()
} finally {
    if ($writer) { $writer.Dispose() } else { $stream.Dispose() }
}
Write-Host 'Zapisano lokalną konfigurację. Uruchom: docker compose up --build -d'
