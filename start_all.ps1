#requires -Version 5.1
<#
.SYNOPSIS
  一键启动答于言文档解析引擎的全部 4 个本地服务。

.DESCRIPTION
  按顺序启动:
    1. Qwen2.5-VL-3B NPU 推理服务  (端口 8910)
    2. 场景分析后端 scene_runtime  (端口 8766)
    3. 前端静态服务 serve_snapextract (端口 8000)
    4. 多模态代理 proxy.py          (端口 8765)
  最后验证 4 个端口都在 LISTENING，并打开浏览器。

.NOTES
  脚本用 $PSScriptRoot 自定位，无论解压到哪里都能直接双击运行。
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'

function Write-Step($n, $msg) {
    Write-Host ""
    Write-Host "[$n/5] $msg" -ForegroundColor Cyan
}

function Test-Port($port) {
    try {
        $conn = New-Object System.Net.Sockets.TcpClient
        $conn.Connect('127.0.0.1', $port)
        $conn.Close()
        return $true
    } catch {
        return $false
    }
}

Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "  答于言 · 文档解析引擎 · 一键启动" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "  根目录: $root"

# Step 1: Qwen NPU
Write-Step 1 "Qwen2.5-VL-3B NPU 推理服务 (8910)"
& (Join-Path $backend 'start_qwen25vl3b.cmd') | ForEach-Object { "  $_" }

# Step 2: Scene runtime
Write-Step 2 "场景分析后端 scene_runtime (8766)"
& (Join-Path $backend 'start_scene_runtime.cmd') | ForEach-Object { "  $_" }

# Step 3: Frontend static
Write-Step 3 "前端静态服务 serve_snapextract (8000)"
& (Join-Path $backend 'start_frontend.cmd') | ForEach-Object { "  $_" }

# Step 4: Multimodal proxy
Write-Step 4 "多模态代理 proxy.py (8765)"
$proxyScript = Join-Path $frontend 'proxy.py'
if (-not (Test-Path -LiteralPath $proxyScript)) {
    throw "proxy.py not found: $proxyScript"
}

# Skip if already running on 8765
if (Test-Port 8765) {
    Write-Host "  proxy.py 已在 8765 端口运行，跳过" -ForegroundColor DarkGray
} else {
    $python = (Get-Command python -ErrorAction Stop).Source
    $proc = Start-Process -FilePath $python `
        -ArgumentList @($proxyScript) `
        -WorkingDirectory $frontend `
        -WindowStyle Hidden `
        -PassThru
    Start-Sleep -Seconds 3
    if (Test-Port 8765) {
        Write-Host "  Started proxy.py (PID: $($proc.Id))"
    } else {
        Write-Host "  proxy.py 启动失败，检查 frontend\proxy.py" -ForegroundColor Red
    }
}

# Step 5: Verify
Write-Step 5 "验证 4 个端口"
$ports = @{
    8910 = 'Qwen NPU'
    8766 = 'Scene runtime'
    8000 = 'Frontend static'
    8765 = 'Multimodal proxy'
}
$allUp = $true
foreach ($p in $ports.Keys | Sort-Object) {
    if (Test-Port $p) {
        Write-Host "  ✔ $p  $($ports[$p])" -ForegroundColor Green
    } else {
        Write-Host "  ✘ $p  $($ports[$p])" -ForegroundColor Red
        $allUp = $false
    }
}

Write-Host ""
if ($allUp) {
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "  全部 4 个服务在线，3 秒后自动打开浏览器" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Start-Sleep -Seconds 3
    Start-Process 'http://localhost:8000/snapextract_v3.html'
} else {
    Write-Host "==================================================" -ForegroundColor Red
    Write-Host "  部分服务未启动成功，请检查上方红色行" -ForegroundColor Red
    Write-Host "==================================================" -ForegroundColor Red
    Read-Host "按回车键退出"
}
