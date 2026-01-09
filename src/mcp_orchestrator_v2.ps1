
# mcp_orchestrator_v2.ps1
# PowerShell version of the orchestrator logic

$BaseDir = $PSScriptRoot
if ($BaseDir.EndsWith("scripts") -or $BaseDir.EndsWith("src")) {
    $BaseDir = Split-Path $BaseDir -Parent
}
Import-Module (Join-Path $BaseDir "src" "tools.ps1")

Write-Host "--- Legal Research Orchestrator (PowerShell) ---" -ForegroundColor Cyan

function Run-Stage {
    param($Stage, $Context, $SystemMessage)
    
    $Messages = @(
        @{ role = "system"; content = $SystemMessage },
        @{ role = "user"; content = $Context },
        @{ role = "user"; content = "TASK: $Stage. Follow templates strictly." }
    )
    
    return Invoke-OllamaChat -Model "qwen3:4b" -Messages $Messages
}
