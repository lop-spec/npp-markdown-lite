param([Parameter(Mandatory)][string]$Exe,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -Path (Join-Path $PSScriptRoot 'native-acceptance.dll')
New-Item -ItemType Directory -Force $OutputDirectory | Out-Null
$temp = Join-Path ([IO.Path]::GetTempPath()) ('npp-lite-portable-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $temp | Out-Null
$fixture = Join-Path $temp 'sample.md'
$text = "# NPP-LITE-PORTABLE-SENTINEL`n`n| Name | Value |`n| --- | --- |`n| Native editor | Official plugin |`n"
[IO.File]::WriteAllText($fixture,$text,(New-Object Text.UTF8Encoding($false)))
$process = $null
try {
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $Exe
    $info.Arguments = '-multiInst -nosession -settingsDir="' + $temp + '" "' + $fixture + '"'
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $process = [Diagnostics.Process]::Start($info)
    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    $main = [IntPtr]::Zero
    $editor = [IntPtr]::Zero
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($process.HasExited) { throw "Npp Lite exited: $($process.ExitCode)" }
        $main = [LiteSmokeNative]::MainWindow($process.Id)
        if ($main -ne [IntPtr]::Zero) {
            $editor = [LiteSmokeNative]::Editor($main)
            if ($editor -ne [IntPtr]::Zero -and [LiteSmokeNative]::Scalar($editor,2183) -eq [Text.Encoding]::UTF8.GetByteCount($text)) { break }
        }
        Start-Sleep -Milliseconds 100
    }
    if ($editor -eq [IntPtr]::Zero) { throw 'Native editor did not start' }
    if ([LiteSmokeNative]::Scalar($editor,4002) -eq 98) { throw 'Unexpected custom Markdown lexer' }
    if ([LiteSmokeNative]::Scalar($editor,2526) -ne 0) { throw 'Unexpected custom extra line spacing' }
    & (Join-Path $PSScriptRoot 'preview-uia.ps1') -Window $main.ToInt64() -Needle 'NPP-LITE-PORTABLE-SENTINEL' -Output (Join-Path $OutputDirectory 'panel.json')
    if ($LASTEXITCODE -ne 0) { throw 'Installed official plugin did not render' }
    [pscustomobject]@{pass=$true;computer=$env:COMPUTERNAME;exe=$Exe;bytes=(Get-Item $Exe).Length;nativeEditor=$true;customMarkdown=$false;officialPanelRendered=$true} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $OutputDirectory 'portable-smoke.json')
    Get-Content -Encoding utf8 (Join-Path $OutputDirectory 'portable-smoke.json')
} finally {
    if ($process -and -not $process.HasExited) {
        $null = $process.CloseMainWindow()
        if (-not $process.WaitForExit(5000)) { $process.Kill(); $process.WaitForExit() }
    }
    Remove-Item -LiteralPath $temp -Force -Recurse -ErrorAction SilentlyContinue
}
