# Keep this file ASCII only: Windows PowerShell 5.1 reads BOM-less scripts in the ANSI code page.
param(
    [string]$ApplioZip,
    [switch]$NoModel
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$Root = $PSScriptRoot
$Applio = Join-Path $Root 'Applio'
$Python = Join-Path $Applio 'env\python.exe'
$ApplioUrl = 'https://huggingface.co/IAHispano/Applio/resolve/main/Compiled/Windows/ApplioV3.6.5.zip'
$ApplioSha256 = '0d6d777a2668a6b16e83d7648f227961088a54cfcb93025f63099cd1088e1ff2'
$ModelUrl = 'https://github.com/Friskes/voice-changer/releases/download/v1.0.0/ru-masha-200.zip'
$ModelSha256 = 'fbb2182d0ddd078ec960edf346d6d88b5be10b7d7d5f8603cbb38d16f250181a'
$ModelDir = Join-Path $Applio 'logs\ru-masha-200'

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-Verified($Url, $Path, $Sha256, $Title) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force (Split-Path $Path) | Out-Null
        Write-Host "Downloading $Title..."
        & curl.exe -L --fail --retry 3 -C - -o "$Path.part" $Url
        if ($LASTEXITCODE) { throw "Download of $Title failed (curl exit code $LASTEXITCODE)." }
        Move-Item "$Path.part" $Path
    }
    Write-Host "Verifying SHA256 of $(Split-Path $Path -Leaf)..."
    $actual = (Get-FileHash -Algorithm SHA256 $Path).Hash.ToLower()
    if ($actual -ne $Sha256) {
        throw "SHA256 mismatch for $Path`n  expected $Sha256`n  actual   $actual`nDelete the file and run install again."
    }
}

if (Test-Path $Python) {
    Write-Host "Applio found in $Applio, skipping download."
} else {
    if (Test-Path $Applio) {
        throw "$Applio exists but has no env\python.exe. Remove the folder and run install again."
    }
    if (-not $ApplioZip) { $ApplioZip = Join-Path $Root 'downloads\ApplioV3.6.5.zip' }
    Get-Verified $ApplioUrl $ApplioZip $ApplioSha256 'Applio 3.6.5 (4.6 GB)'
    Write-Host "Extracting to $Applio (several minutes)..."
    [IO.Compression.ZipFile]::ExtractToDirectory($ApplioZip, $Applio)
}

$env:PYTHONIOENCODING = 'utf-8'
& $Python (Join-Path $Root 'tools\apply_patches.py')
if ($LASTEXITCODE) { throw 'Patching failed, see the message above.' }

if ($NoModel) {
    Write-Host 'Voice model skipped (-NoModel).'
} elseif (Test-Path (Join-Path $ModelDir 'ru-masha_200e_30600s.pth')) {
    Write-Host 'Voice model ru-masha-200 is already in place.'
} else {
    try {
        $modelZip = Join-Path $Root 'downloads\ru-masha-200.zip'
        Get-Verified $ModelUrl $modelZip $ModelSha256 'voice model ru-masha-200 (440 MB)'
        New-Item -ItemType Directory -Force $ModelDir | Out-Null
        $zip = [IO.Compression.ZipFile]::OpenRead($modelZip)
        try {
            foreach ($entry in $zip.Entries) {
                if ($entry.Name) {
                    [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, (Join-Path $ModelDir $entry.Name), $true)
                }
            }
        } finally {
            $zip.Dispose()
        }
        Write-Host "Voice model unpacked to $ModelDir. Its license: $ModelDir\LICENSE-Dialogs-OpenRAIL.md"
    } catch {
        Write-Warning "Voice model was not installed: $($_.Exception.Message)"
        Write-Warning "Get ru-masha-200.zip from https://github.com/Friskes/voice-changer/releases and unpack it into $ModelDir, or use your own model."
    }
}

Write-Host ''
Write-Host 'Done. Start run.bat and pick the model on the Realtime tab.'
