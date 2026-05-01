$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeRoot = Join-Path $repoRoot ".runtime\dev"
$dataDir = Join-Path $runtimeRoot "data"
$configDir = Join-Path $runtimeRoot "config"
$logDir = Join-Path $runtimeRoot "log"
$runDir = Join-Path $runtimeRoot "run"

foreach ($dir in @($runtimeRoot, $dataDir, $configDir, $logDir, $runDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

$exampleShopInfo = Join-Path $repoRoot "runtime\examples\shop_info.example.json"
$targetShopInfo = Join-Path $dataDir "shop_info.json"
if ((Test-Path $exampleShopInfo) -and -not (Test-Path $targetShopInfo)) {
    Copy-Item $exampleShopInfo $targetShopInfo
}

$env:PACKAGE_SHOP_DATA_DIR = $dataDir
$env:PACKAGE_SHOP_CONFIG_DIR = $configDir
$env:PACKAGE_SHOP_LOG_DIR = $logDir
$env:PACKAGE_SHOP_RUN_DIR = $runDir

$activateScript = Join-Path $repoRoot "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

Set-Location $repoRoot
python src\api_server.py