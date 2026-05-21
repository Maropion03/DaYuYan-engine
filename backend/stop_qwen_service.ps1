$ErrorActionPreference = "Stop"

$procs = Get-Process GenieAPIService -ErrorAction SilentlyContinue
if (-not $procs) {
    Write-Output "GenieAPIService is not running."
    exit 0
}

$procs | Stop-Process -Force
Write-Output "Stopped GenieAPIService."
