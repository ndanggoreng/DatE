# Build DatE + trim + ZIP (target ZIP < 25 MB)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "Building DatE.exe..."
py -m PyInstaller dekstop.spec --noconfirm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Trimming unused Qt files..."
py sys/trim_build.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$version = (Select-String -Path "core/version.py" -Pattern 'APP_VERSION = "(.+)"').Matches.Groups[1].Value
$zipName = "DatE-v$version-windows.zip"
$releaseDir = Join-Path $Root "release"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
$zipPath = Join-Path $releaseDir $zipName

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

$sevenZip = "${env:ProgramFiles}\7-Zip\7z.exe"
if (Test-Path $sevenZip) {
    Write-Host "Creating ZIP (7-Zip max compression)..."
    & $sevenZip a -tzip -mx=9 $zipPath "dist\DatE\*" | Out-Null
} else {
    Write-Host "Creating ZIP (Compress-Archive)..."
    Compress-Archive -Path "dist\DatE" -DestinationPath $zipPath -Force
}

$mb = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Host "Release: $zipPath ($mb MB)"
if ($mb -gt 25) {
    Write-Warning "ZIP masih di atas 25 MB. Pertimbangkan 7-Zip atau kurangi dependensi lebih lanjut."
}
