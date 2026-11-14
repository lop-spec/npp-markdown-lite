param([Parameter(Mandatory)][long]$Window,[Parameter(Mandatory)][string]$Needle,[Parameter(Mandatory)][string]$Output)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = [Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Window)
$deadline = [DateTime]::UtcNow.AddSeconds(35)
$records = @()
$found = $false
while ([DateTime]::UtcNow -lt $deadline -and -not $found) {
    $nodes = $root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
    $records = @()
    foreach ($node in $nodes) {
        try {
            $current = $node.Current
            if ($current.FrameworkId -ne 'Chrome' -and $current.ClassName -notlike '*Chrome*') { continue }
            $text = $current.Name
            $pattern = $null
            if ($node.TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$pattern)) {
                $text += ' ' + $pattern.DocumentRange.GetText(20000)
            }
            $records += [pscustomobject]@{type=$current.ControlType.ProgrammaticName;framework=$current.FrameworkId;class=$current.ClassName;name=$current.Name;text=$text}
            if ($text.Contains($Needle)) { $found = $true }
        } catch { }
    }
    if (-not $found) { Start-Sleep -Milliseconds 500 }
}
[pscustomobject]@{rendered=$found;needle=$Needle;webviewElements=$records} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $Output
if (-not $found) { Write-Output "WebView2 document did not expose expected text: $Needle"; exit 1 }
Write-Output "PASS WebView2 rendered text: $Needle"
