param(
    [int]$Port = 8766
)

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$script = Join-Path $root "scene_runtime\app.py"

# Prefer a local .conda-ocr if it exists alongside this script; otherwise
# fall back to the historic env path used during development.
$pythonCandidates = @(
    (Join-Path $root ".conda-ocr\python.exe"),
    "C:\Users\1\Documents\Codex\2026-05-13\ocr-qwen-ai\.conda-ocr\python.exe"
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not (Test-Path -LiteralPath $script)) {
    throw "Scene runtime script not found: $script"
}

if (-not $python) {
    throw "Scene runtime python not found. Tried: $($pythonCandidates -join '; ')"
}

$existing = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match '^python(?:\.exe)?$' -and
        $_.CommandLine -like "*scene_runtime\\app.py*"
    }

if ($existing) {
    Write-Output "Scene runtime is already running."
    Write-Output "URL: http://127.0.0.1:$Port/api/scene-analysis/run"
    exit 0
}

$proc = Start-Process -FilePath $python `
    -ArgumentList @($script) `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 2

try {
    Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/scene-analysis/run" -Method OPTIONS -UseBasicParsing -TimeoutSec 10 | Out-Null
}
catch {
    if (!$proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }
    throw
}

Write-Output "Started scene runtime."
Write-Output "PID: $($proc.Id)"
Write-Output "URL: http://127.0.0.1:$Port/api/scene-analysis/run"
