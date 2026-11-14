param([Parameter(Mandatory)][string]$EditorDirectory, [string]$Archive)
$ErrorActionPreference = 'Stop'
$lock = Get-Content -Raw -Encoding utf8 (Join-Path $PSScriptRoot 'plugin-lock.json') | ConvertFrom-Json
$temporary = $false
if (-not $Archive) {
    $Archive = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString('N') + '.zip')
    $temporary = $true
    & curl.exe -fsSL --connect-timeout 20 --max-time 120 --retry 2 $lock.url -o $Archive
    if ($LASTEXITCODE -ne 0) { throw 'Markdown Panel download failed' }
}
try {
    if ((Get-FileHash -Algorithm SHA256 $Archive).Hash.ToLower() -ne $lock.sha256) { throw 'Markdown Panel official archive hash mismatch' }
    $target = Join-Path $EditorDirectory ('plugins/' + $lock.folder)
    if (Test-Path $target) { throw "Plugin already exists; back it up before replacement: $target" }
    New-Item -ItemType Directory -Force $target | Out-Null
    & (Join-Path $env:SystemRoot 'System32/tar.exe') -xf $Archive -C $target
    if ($LASTEXITCODE -ne 0) { throw 'Markdown Panel extraction failed' }
    foreach ($file in @('NppMarkdownPanel.dll','lib/Markdig.dll','lib/Webview2Viewer.dll','lib/runtimes/win-x64/native/WebView2Loader.dll','style.css','style-dark.css','License.txt')) {
        if (-not (Test-Path (Join-Path $target $file))) { throw "Incomplete official plugin: $file" }
    }
    Get-ChildItem -LiteralPath $target -File -Recurse | Unblock-File
    [pscustomobject]@{plugin='Markdown Panel';version=$lock.version;sha256=$lock.sha256;directory=$target} | ConvertTo-Json
} finally {
    if ($temporary) { Remove-Item -LiteralPath $Archive -ErrorAction SilentlyContinue }
}
