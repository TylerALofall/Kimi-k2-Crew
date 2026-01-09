
# Legal Research Automation - PowerShell Version
# Based on PROMPT.sql logic

$BaseDir = "d:/Kimi-k2-Crew"
$PdfPath = Join-Path $BaseDir "THE_BRIEF_FINAL-12-10-2025.pdf"
$PromptSqlPath = Join-Path $BaseDir "PROMPT.sql"
$ModelName = "qwen3:4b"
$WaitTime = 10

Write-Host "--- Initializing Legal Research Automation (PowerShell) ---" -ForegroundColor Cyan

if (-not (Test-Path $PdfPath)) {
    Write-Error "PDF file not found at $PdfPath"
    exit
}

if (-not (Test-Path $PromptSqlPath)) {
    Write-Error "Prompt file not found at $PromptSqlPath"
    exit
}

# Load PROMPT.sql content
$PromptContent = Get-Content -Path $PromptSqlPath -Raw -Encoding UTF8

# Extract sections exactly as defined in the SQL file
$SystemMsgStartTag = "SYSTEM MESSAGE:"
$PromptStartTag = "PROMPT:"
$PlanStartTag = "*************************"

$SystemMsgStartIndex = $PromptContent.IndexOf($SystemMsgStartTag) + $SystemMsgStartTag.Length
$SystemMsgEndIndex = $PromptContent.IndexOf($PromptStartTag)
$SystemMessage = $PromptContent.Substring($SystemMsgStartIndex, $SystemMsgEndIndex - $SystemMsgStartIndex).Trim("{} `n`r")

$PromptStartIndex = $PromptContent.IndexOf($PromptStartTag) + $PromptStartTag.Length
$PromptEndIndex = $PromptContent.IndexOf($PlanStartTag)
$BasePrompt = $PromptContent.Substring($PromptStartIndex, $PromptEndIndex - $PromptStartIndex).Trim()

# Note: PowerShell doesn't have a built-in PDF text extractor like PyMuPDF.
# For now, we will notify the user that we are using the file path as the reference as in the previous logic.
Write-Host "Targeting PDF evidence: $PdfPath" -ForegroundColor Green

$Stages = @(
    "PASS ONE: Extract proof-needed facts from background and argument sections.",
    "PASS TWO: Validate facts and find additional facts on the record.",
    "PASS THREE: Confirm section matching and citations.",
    "PASS FOUR: Find additional supporting facts from the record."
)

$FullContext = "$BasePrompt`n`nEVIDENCE FILE PATH: $PdfPath"

for ($i = 0; $i -lt $Stages.Count; $i++) {
    $Stage = $Stages[$i]
    Write-Host "`n--- Starting $Stage ---" -ForegroundColor Yellow
    
    # Construct Ollama JSON payload
    $Payload = @{
        model = $ModelName
        messages = @(
            @{ role = "system"; content = $SystemMessage },
            @{ role = "user"; content = $FullContext },
            @{ role = "user"; content = "BEGIN $Stage. Use the [EVIDENCE-FACTS-TEMPLATE] as defined." }
        )
        stream = $false
    } | ConvertTo-Json -Depth 10

    try {
        Write-Host "Calling Ollama ($ModelName)..." -ForegroundColor Gray
        $Response = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post -Body $Payload -ContentType "application/json"
        $Output = $Response.message.content
        
        Write-Host "Response received for Stage $($i + 1)." -ForegroundColor Green
        $OutputFile = Join-Path $BaseDir "research_output_stage_$($i + 1).xml"
        $Output | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-Host "Output saved to $OutputFile" -ForegroundColor Cyan
    }
    catch {
        Write-Error "Error during Stage $($i + 1): $_"
        break
    }

    if ($i -lt ($Stages.Count - 1)) {
        Write-Host "Waiting $WaitTime seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds $WaitTime
    }
}
