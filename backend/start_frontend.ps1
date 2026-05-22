param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$script = Join-Path $root "serve_snapextract.py"

# Static files live one level up in ../frontend/
$frontendDir = (Resolve-Path (Join-Path $root "..\frontend")).Path

if (-not (Test-Path -LiteralPath $script)) {
    throw "Frontend server script not found: $script"
}

if (-not (Test-Path -LiteralPath $frontendDir)) {
    throw "Frontend directory not found: $frontendDir"
}

$existing = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match '^python(?:\.exe)?$' -and
        $_.CommandLine -like "*serve_snapextract.py*" -and
        $_.CommandLine -like "*--port $Port*"
    }

if ($existing) {
    Write-Output "Frontend proxy is already running."
    Write-Output "URL: http://127.0.0.1:$Port/snapextract_v3.html"
    exit 0
}

$python = (Get-Command python -ErrorAction Stop).Source
$proc = Start-Process -FilePath $python `
    -ArgumentList @($script, "--port", $Port.ToString(), "--frontend-dir", $frontendDir) `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 2

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/snapextract_v3.html" -UseBasicParsing -TimeoutSec 10
    if ($resp.StatusCode -ne 200) {
        throw "Unexpected HTTP status: $($resp.StatusCode)"
    }
}
catch {
    if (!$proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }
    throw
}

Write-Output "Started frontend proxy."
Write-Output "PID: $($proc.Id)"
Write-Output "URL: http://127.0.0.1:$Port/snapextract_v3.html"
