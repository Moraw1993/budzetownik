param([switch]$Fix)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mount = "type=bind,source=$projectRoot,target=/workspace"

function Invoke-QualityCommand {
    param([string[]]$Arguments)
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Kontrola jakości zakończyła się błędem ($LASTEXITCODE)."
    }
}

$node = @('run', '--rm', '--mount', $mount, '--mount', 'type=volume,source=myhomebudget_quality_node_modules,target=/workspace/frontend/node_modules', '-w', '/workspace/frontend', 'node:22-alpine')
$ruff = @('run', '--rm', '--mount', $mount, '-w', '/workspace', 'ghcr.io/astral-sh/ruff:0.16.6')
Invoke-QualityCommand ($node + @('npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'))

if ($Fix) {
    Invoke-QualityCommand ($ruff + @('check', '--fix', 'backend', 'scripts'))
    Invoke-QualityCommand ($ruff + @('format', 'backend', 'scripts'))
    Invoke-QualityCommand ($node + @('npm', 'run', 'lint:css:fix'))
    Invoke-QualityCommand ($node + @('npm', 'run', 'format'))
}

Invoke-QualityCommand ($ruff + @('format', '--check', 'backend', 'scripts'))
Invoke-QualityCommand ($ruff + @('check', 'backend', 'scripts'))
Invoke-QualityCommand ($node + @('npm', 'run', 'format:check'))
Invoke-QualityCommand ($node + @('npm', 'run', 'lint'))
Invoke-QualityCommand ($node + @('npm', 'run', 'lint:css'))
Invoke-QualityCommand ($node + @('npm', 'run', 'typecheck'))
Write-Host 'Formatowanie i kontrola jakości: OK.'
