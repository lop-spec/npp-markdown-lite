param([Parameter(Mandatory)][long]$Window,[Parameter(Mandatory)][string]$Needle,[Parameter(Mandatory)][string]$Output)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -Path (Join-Path $PSScriptRoot 'native-acceptance.dll')
$deadline = [DateTime]::UtcNow.AddSeconds(35)
$records = @()
$found = $false
while ([DateTime]::UtcNow -lt $deadline -and -not $found) {
    $records = @()
    # A docked WinForms provider can be disconnected from the main Win32 UIA
    # tree. Enter through the real Chrome child HWND, never through Scintilla.
    foreach ($handle in [LiteSmokeNative]::Renderers([IntPtr]$Window)) {
        $renderer = [Windows.Automation.AutomationElement]::FromHandle($handle)
        $nodes = @($renderer) + @($renderer.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition))
        foreach ($node in $nodes) {
            try {
                $current = $node.Current
                $text = $current.Name
                $pattern = $null
                if ($node.TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$pattern)) {
                    $text += ' ' + $pattern.DocumentRange.GetText(20000)
                }
                $records += [pscustomobject]@{renderer=$handle.ToInt64();type=$current.ControlType.ProgrammaticName;framework=$current.FrameworkId;class=$current.ClassName;name=$current.Name;text=$text}
                if ($text.Contains($Needle)) { $found = $true }
            } catch { }
        }
    }
    if (-not $found) { Start-Sleep -Milliseconds 500 }
}
[pscustomobject]@{rendered=$found;needle=$Needle;webviewElements=$records} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $Output
if (-not $found) { Write-Output "WebView2 document did not expose expected text: $Needle"; exit 1 }
Write-Output "PASS WebView2 rendered text: $Needle"
exit 0
