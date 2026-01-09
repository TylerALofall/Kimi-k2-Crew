
# learning.ps1
# PowerShell version of learning.py

Write-Host "--- Initializing Legal Learning Module ---" -ForegroundColor Cyan

function Update-KnowledgeBase {
    param([string]$FactId, [string]$Findings)
$BaseDir = $PSScriptRoot
if ($BaseDir.EndsWith("scripts") -or $BaseDir.EndsWith("src")) {
    $BaseDir = Split-Path $BaseDir -Parent
}
$KnowledgeFile = Join-Path $BaseDir "logs" "knowledge_base.json"
if (-not (Test-Path (Join-Path $BaseDir "logs"))) { New-Item -ItemType Directory -Path (Join-Path $BaseDir "logs") }
    
    $Knowledge = if (Test-Path $KnowledgeFile) { Get-Content $KnowledgeFile | ConvertFrom-Json } else { @{} }
    $Knowledge[$FactId] = $Findings
    $Knowledge | ConvertTo-Json | Out-File $KnowledgeFile -Encoding UTF8
    Write-Host "Knowledge base updated for $FactId." -ForegroundColor Gray
}
