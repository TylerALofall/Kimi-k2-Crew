# ollama_fact_game.ps1
# Multi-model, multi-pass fact finding workflow for the PROMPT.sql template.

[CmdletBinding()]
param(
    [string]$OpeningBriefPath,
    [string]$PromptSqlPath,
    [string[]]$Models = @("qwen3:4b"),
    [string]$OutputDir,
    [switch]$LoadSession
)

$Script:BaseDir = Split-Path $PSScriptRoot -Parent
if (-not $OpeningBriefPath) {
    $OpeningBriefPath = Join-Path $Script:BaseDir "THE_BRIEF_FINAL-12-10-2025.pdf"
}
if (-not $PromptSqlPath) {
    $PromptSqlPath = Join-Path $Script:BaseDir "PROMPT.sql"
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $Script:BaseDir "outputs"
}

$Script:SessionPath = Join-Path $OutputDir "ollama_fact_game_session.clixml"

function Get-PromptSections {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "PROMPT.sql not found at $Path"
    }

    $content = Get-Content -Path $Path -Raw -Encoding UTF8
    $systemTag = "SYSTEM MESSAGE:"
    $promptTag = "PROMPT:"
    $planTag = "*************************"

    $systemStart = $content.IndexOf($systemTag)
    $promptStart = $content.IndexOf($promptTag)
    $planStart = $content.IndexOf($planTag)

    if ($systemStart -lt 0 -or $promptStart -lt 0 -or $planStart -lt 0) {
        throw "Unable to parse PROMPT.sql sections. Ensure SYSTEM MESSAGE:, PROMPT:, and plan separators exist."
    }

    $systemMessage = $content.Substring($systemStart + $systemTag.Length, $promptStart - ($systemStart + $systemTag.Length)).Trim()
    $basePrompt = $content.Substring($promptStart + $promptTag.Length, $planStart - ($promptStart + $promptTag.Length)).Trim()

    return [ordered]@{
        SystemMessage = $systemMessage
        BasePrompt = $basePrompt
    }
}

function Get-DocumentPreview {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Opening brief not found at $Path"
    }

    $extension = [IO.Path]::GetExtension($Path).ToLowerInvariant()
    if ($extension -eq ".txt" -or $extension -eq ".md") {
        return (Get-Content -Path $Path -Raw -Encoding UTF8)
    }

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $text = [System.Text.Encoding]::ASCII.GetString($bytes) -replace "[^ -~]", ""
    if ($text.Length -gt 12000) {
        return $text.Substring(0, 12000)
    }
    return $text
}

function Invoke-OllamaChat {
    param(
        [string]$Model,
        [array]$Messages
    )

    $payload = @{
        model = $Model
        messages = $Messages
        stream = $false
    } | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post -Body $payload -ContentType "application/json"
    return $response.message.content
}

function Initialize-OllamaFactGameSession {
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
    }

    if (Test-Path $Script:SessionPath) {
        $loaded = Import-Clixml -Path $Script:SessionPath
        $global:OllamaFactGameSession = $loaded
    }

    if (-not $global:OllamaFactGameSession) {
        $global:OllamaFactGameSession = [ordered]@{
            CreatedAt = (Get-Date)
            OpeningBriefPath = $OpeningBriefPath
            PromptSqlPath = $PromptSqlPath
            OutputDir = $OutputDir
            Stages = @{}
        }
    }
}

function Save-OllamaFactGameSession {
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
    }
    $global:OllamaFactGameSession | Export-Clixml -Path $Script:SessionPath
}

function Add-StageOutput {
    param(
        [string]$Stage,
        [string]$Model,
        [string]$Content
    )

    if (-not $global:OllamaFactGameSession.Stages.ContainsKey($Stage)) {
        $global:OllamaFactGameSession.Stages[$Stage] = @()
    }

    $entry = [ordered]@{
        Model = $Model
        Content = $Content
        Timestamp = (Get-Date)
    }
    $global:OllamaFactGameSession.Stages[$Stage] += $entry
}

function Write-StageOutputsToDisk {
    param([string]$Stage)
    if (-not $global:OllamaFactGameSession.Stages.ContainsKey($Stage)) {
        return
    }

    $entries = $global:OllamaFactGameSession.Stages[$Stage]
    $index = 1
    foreach ($entry in $entries) {
        $fileName = "{0}_{1}_{2}.xml" -f $Stage.Replace(" ", "_"), $entry.Model.Replace(":", "_"), $index
        $filePath = Join-Path $OutputDir $fileName
        $entry.Content | Out-File -FilePath $filePath -Encoding UTF8
        $index++
    }
}

function Get-StageOutput {
    param(
        [string]$Stage,
        [string]$Model
    )

    if (-not $global:OllamaFactGameSession.Stages.ContainsKey($Stage)) {
        return $null
    }

    $entries = $global:OllamaFactGameSession.Stages[$Stage]
    if ($Model) {
        return $entries | Where-Object { $_.Model -eq $Model }
    }
    return $entries
}

function Get-CombinedOutput {
    param([string]$Stage)
    $entries = Get-StageOutput -Stage $Stage
    if (-not $entries) {
        return ""
    }
    return ($entries | ForEach-Object { $_.Content }) -join "`n`n"
}

function Find-ResearchFactId {
    param(
        [string]$Id
    )

    if (-not $Id) {
        throw "Provide a UID or Temp_Fact_ID to search for."
    }

    $results = @()
    foreach ($stage in $global:OllamaFactGameSession.Stages.Keys) {
        foreach ($entry in $global:OllamaFactGameSession.Stages[$stage]) {
            if ($entry.Content -match [regex]::Escape($Id)) {
                $results += [ordered]@{
                    Stage = $stage
                    Model = $entry.Model
                    Timestamp = $entry.Timestamp
                    Preview = ($entry.Content -split "`n" | Select-Object -First 8) -join "`n"
                }
            }
        }
    }

    return $results
}

function Start-OllamaFactGame {
    Initialize-OllamaFactGameSession

    $promptSections = Get-PromptSections -Path $PromptSqlPath
    $documentPreview = Get-DocumentPreview -Path $OpeningBriefPath

    $baseContext = @(
        @{ role = "system"; content = $promptSections.SystemMessage },
        @{ role = "user"; content = $promptSections.BasePrompt },
        @{ role = "user"; content = "OPENING BRIEF PREVIEW (TRUNCATED):`n$documentPreview" }
    )

    $seedStage = "seed_list_pass"
    $previousOutput = ""
    foreach ($model in $Models) {
        Write-Host "Generating seed list with $model..." -ForegroundColor Cyan
        $messages = $baseContext + @(
            @{ role = "user"; content = "TASK: Produce a detailed seed list of facts from the opening brief. Use exact language when possible. Do NOT invent facts. Output as bullet list with Temp_Fact_ID placeholders only." }
        )
        if ($previousOutput) {
            $messages += @{ role = "user"; content = "PRIOR MODEL SEED LIST (challenge and extend, no duplicates):`n$previousOutput" }
        }

        $output = Invoke-OllamaChat -Model $model -Messages $messages
        Add-StageOutput -Stage $seedStage -Model $model -Content $output
        $previousOutput = $output
    }

    $seedCombined = Get-CombinedOutput -Stage $seedStage

    $xmlStage = "pass_one_xml"
    $previousXml = ""
    foreach ($model in $Models) {
        Write-Host "Generating pass-one XML with $model..." -ForegroundColor Cyan
        $messages = $baseContext + @(
            @{ role = "user"; content = "TASK: Using the seed list below, create PASS ONE XML using the [EVIDENCE-FACTS-TEMPLATE] and SCREENSHOTS_COLLECTION_TEMPLATE from PROMPT.sql. Keep Temp_Fact_ID as placeholders. Do NOT invent facts or UIDs." },
            @{ role = "user"; content = "SEED LIST:`n$seedCombined" }
        )
        if ($previousXml) {
            $messages += @{ role = "user"; content = "PRIOR MODEL XML (challenge and improve, no UID changes):`n$previousXml" }
        }

        $output = Invoke-OllamaChat -Model $model -Messages $messages
        Add-StageOutput -Stage $xmlStage -Model $model -Content $output
        $previousXml = $output
    }

    Write-StageOutputsToDisk -Stage $seedStage
    Write-StageOutputsToDisk -Stage $xmlStage
    Save-OllamaFactGameSession

    Write-Host "Pass one complete. Use Get-StageOutput or Find-ResearchFactId to print results." -ForegroundColor Green
}

function Show-OllamaFactGameSession {
    if (-not $global:OllamaFactGameSession) {
        Write-Host "No session loaded." -ForegroundColor Yellow
        return
    }
    Write-Host "Session created: $($global:OllamaFactGameSession.CreatedAt)" -ForegroundColor Green
    foreach ($stage in $global:OllamaFactGameSession.Stages.Keys) {
        $count = $global:OllamaFactGameSession.Stages[$stage].Count
        Write-Host "- $stage ($count outputs)" -ForegroundColor Cyan
    }
}

function Load-OllamaFactGameSession {
    Initialize-OllamaFactGameSession
    Show-OllamaFactGameSession
}

if ($LoadSession) {
    Load-OllamaFactGameSession
}

if ($MyInvocation.InvocationName -ne ".") {
    Start-OllamaFactGame
}
