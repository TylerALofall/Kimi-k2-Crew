
# tools.ps1
# PowerShell version of core legal research tools

function Get-LegalContext {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        # Fallback text extraction for PDF in pure PowerShell
        $bytes = [System.IO.File]::ReadAllBytes($FilePath)
        $text = [System.Text.Encoding]::ASCII.GetString($bytes) -replace '[^ -~]', ''
        return $text.Substring(0, [Math]::Min($text.Length, 10000))
    }
    return ""
}

function Invoke-OllamaChat {
    param(
        [string]$Model,
        [array]$Messages
    )
    $Payload = @{
        model = $Model
        messages = $Messages
        stream = $false
    } | ConvertTo-Json -Depth 10

    $Response = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post -Body $Payload -ContentType "application/json"
    return $Response.message.content
}

Export-ModuleMember -Function Get-LegalContext, Invoke-OllamaChat
