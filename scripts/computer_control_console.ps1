# computer_control_console.ps1
# PowerShell-only console helpers for screen capture, cursor state, and button mapping.

Set-StrictMode -Version Latest

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class MouseInput {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);
    public const int MOUSEEVENTF_LEFTDOWN = 0x02;
    public const int MOUSEEVENTF_LEFTUP = 0x04;
}
"@

function Get-CursorPosition {
    $position = [System.Windows.Forms.Cursor]::Position
    [ordered]@{
        X = $position.X
        Y = $position.Y
    }
}

function Get-DesktopSnapshot {
    param(
        [string]$OutputPath,
        [int]$GridSize = 80,
        [string]$OverlayText
    )

    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

    $gridPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(140, 255, 0, 0)), 1
    for ($x = 0; $x -lt $bounds.Width; $x += $GridSize) {
        $graphics.DrawLine($gridPen, $x, 0, $x, $bounds.Height)
    }
    for ($y = 0; $y -lt $bounds.Height; $y += $GridSize) {
        $graphics.DrawLine($gridPen, 0, $y, $bounds.Width, $y)
    }

    if ($OverlayText) {
        $font = New-Object System.Drawing.Font "Segoe UI", 16, [System.Drawing.FontStyle]::Bold
        $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(200, 0, 0, 0))
        $textBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 255, 255))
        $layoutRect = New-Object System.Drawing.RectangleF 12, 12, ($bounds.Width - 24), 48
        $graphics.FillRectangle($brush, $layoutRect)
        $graphics.DrawString($OverlayText, $font, $textBrush, $layoutRect)
        $font.Dispose()
        $brush.Dispose()
        $textBrush.Dispose()
    }

    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()

    return $OutputPath
}

function Get-UiButtons {
    param(
        [int]$MaxResults = 200
    )

    $desktop = [System.Windows.Automation.AutomationElement]::RootElement
    $condition = New-Object System.Windows.Automation.PropertyCondition `
        ([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)

    $buttons = $desktop.FindAll([System.Windows.Automation.TreeScope]::Subtree, $condition)
    $results = @()
    $count = [Math]::Min($buttons.Count, $MaxResults)
    for ($i = 0; $i -lt $count; $i++) {
        $button = $buttons.Item($i)
        $bounds = $button.Current.BoundingRectangle
        $name = $button.Current.Name
        $results += [ordered]@{
            Name = if ($name) { $name } else { "(Unnamed)" }
            X = [int]$bounds.X
            Y = [int]$bounds.Y
            Width = [int]$bounds.Width
            Height = [int]$bounds.Height
        }
    }

    return $results
}

function Convert-ButtonsToPlaceholders {
    param(
        [array]$Buttons
    )

    $output = @()
    $index = 1
    foreach ($button in $Buttons) {
        $output += [ordered]@{
            Placeholder = "BUTTON_$index"
            Name = $button.Name
            X = $button.X
            Y = $button.Y
            Width = $button.Width
            Height = $button.Height
        }
        $index++
    }
    return $output
}

function Invoke-MouseClick {
    param(
        [int]$X,
        [int]$Y
    )

    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($X, $Y)
    Start-Sleep -Milliseconds 80
    [MouseInput]::mouse_event([MouseInput]::MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    Start-Sleep -Milliseconds 50
    [MouseInput]::mouse_event([MouseInput]::MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
}

function Send-KeyboardInput {
    param(
        [string]$Keys
    )

    [System.Windows.Forms.SendKeys]::SendWait($Keys)
}

function Get-ConsoleTick {
    param(
        [string]$OutputDir = (Join-Path $PSScriptRoot "..\\outputs\\console"),
        [int]$GridSize = 80,
        [string]$OverlayText
    )

    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $screenshotPath = Join-Path $OutputDir "console_$timestamp.png"
    $cursor = Get-CursorPosition
    $buttons = Get-UiButtons
    $placeholders = Convert-ButtonsToPlaceholders -Buttons $buttons

    Get-DesktopSnapshot -OutputPath $screenshotPath -GridSize $GridSize -OverlayText $OverlayText | Out-Null

    [ordered]@{
        ScreenshotPath = $screenshotPath
        Cursor = $cursor
        Buttons = $placeholders
        TakenAt = (Get-Date)
    }
}

function Start-ConsoleStream {
    param(
        [int]$IntervalSeconds = 1,
        [string]$OutputDir = (Join-Path $PSScriptRoot "..\\outputs\\console"),
        [int]$GridSize = 80,
        [string]$OverlayText
    )

    Write-Host "Starting console stream. Press Ctrl+C to stop." -ForegroundColor Cyan
    while ($true) {
        $tick = Get-ConsoleTick -OutputDir $OutputDir -GridSize $GridSize -OverlayText $OverlayText
        $tick | ConvertTo-Json -Depth 5
        Start-Sleep -Seconds $IntervalSeconds
    }
}

Export-ModuleMember -Function Get-CursorPosition, Get-DesktopSnapshot, Get-UiButtons, Convert-ButtonsToPlaceholders, Invoke-MouseClick, Send-KeyboardInput, Get-ConsoleTick, Start-ConsoleStream
