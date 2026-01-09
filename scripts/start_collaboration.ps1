
# start_collaboration.ps1
# PowerShell version of start_collaboration.py

$BaseDir = $PSScriptRoot
if ($BaseDir.EndsWith("scripts") -or $BaseDir.EndsWith("src")) {
    $BaseDir = Split-Path $BaseDir -Parent
}
Write-Host "--- Starting Collaborative Legal Research ---" -ForegroundColor Cyan
powershell -File (Join-Path $BaseDir "run_ollama_research.ps1")
