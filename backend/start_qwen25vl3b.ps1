param(
    [int]$Port = 8910
)

$ErrorActionPreference = "Stop"

$root = "C:\Users\1\Desktop\snapdragon\ai-engine-direct-helper-main\samples"
$config = "genie\python\models\qwen2.5vl3b\config.json"
$serviceExe = Join-Path $root "GenieAPIService.exe"
$logFile = Join-Path $root "qwen25vl3b-service.log"

if (-not (Test-Path -LiteralPath $serviceExe)) {
    throw "GenieAPIService.exe not found: $serviceExe"
}

if (-not (Test-Path -LiteralPath (Join-Path $root $config))) {
    throw "Model config not found: $(Join-Path $root $config)"
}

$existing = Get-Process GenieAPIService -ErrorAction SilentlyContinue
if ($existing) {
    Write-Output "GenieAPIService is already running."
    Write-Output "URL: http://127.0.0.1:$Port"
    exit 0
}

if (Test-Path -LiteralPath $logFile) {
    Remove-Item -LiteralPath $logFile -Force
}

$proc = Start-Process -FilePath $serviceExe `
    -ArgumentList @("-c", $config, "-l", "-d", "3", "-f", $logFile, "-p", $Port) `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -PassThru

$started = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2

    if ($proc.HasExited) {
        break
    }

    if (Test-Path -LiteralPath $logFile) {
        $tail = Get-Content -LiteralPath $logFile -Tail 50 -ErrorAction SilentlyContinue
        if ($tail -match "Genie API Service IS Running" -or $tail -match "Model load successfully") {
            $started = $true
            break
        }
    }
}

if (-not $started) {
    if (Test-Path -LiteralPath $logFile) {
        Get-Content -LiteralPath $logFile -Tail 100
    }
    throw "Failed to start qwen2.5vl3b service."
}

Write-Output "Started qwen2.5vl3b service."
Write-Output "PID: $($proc.Id)"
Write-Output "URL: http://127.0.0.1:$Port"
Write-Output "Log: $logFile"
