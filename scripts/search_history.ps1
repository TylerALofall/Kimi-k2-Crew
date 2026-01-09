
# search_history.ps1
# PowerShell version of search history tracking

param([string]$Query, [string]$Result)

$BaseDir = $PSScriptRoot
if ($BaseDir.EndsWith("scripts") -or $BaseDir.EndsWith("src")) {
    $BaseDir = Split-Path $BaseDir -Parent
}
$HistoryFile = Join-Path $BaseDir "logs" "search_history.json"
if (-not (Test-Path (Join-Path $BaseDir "logs"))) { New-Item -ItemType Directory -Path (Join-Path $BaseDir "logs") }

$Entry = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Query = $Query
    Result = $Result
}

$History = if (Test-Path $HistoryFile) { Get-Content $HistoryFile | ConvertFrom-Json } else { @() }
$History += $Entry
$History | ConvertTo-Json | Out-File $HistoryFile -Encoding UTF8
Write-Host "Search history updated." -ForegroundColor Gray
