
# search_history.ps1
# PowerShell version of search history tracking

param([string]$Query, [string]$Result)

$HistoryFile = Join-Path "d:\Kimi-k2-Crew\logs" "search_history.json"
if (-not (Test-Path "d:\Kimi-k2-Crew\logs")) { New-Item -ItemType Directory -Path "d:\Kimi-k2-Crew\logs" }

$Entry = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Query = $Query
    Result = $Result
}

$History = if (Test-Path $HistoryFile) { Get-Content $HistoryFile | ConvertFrom-Json } else { @() }
$History += $Entry
$History | ConvertTo-Json | Out-File $HistoryFile -Encoding UTF8
Write-Host "Search history updated." -ForegroundColor Gray
