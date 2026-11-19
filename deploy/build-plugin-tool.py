"""Build the portable, plugin-only WinGUp from pinned upstream sources in Windows CI."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

root = Path(__file__).resolve().parents[1]
bin64 = root / 'PowerEditor/bin64'
generated = root / 'PowerEditor/src/Lite/generated'

def download(url, digest, path):
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f'SHA256 mismatch: {url}')
    path.write_bytes(data)

def once(code, old, new):
    if code.count(old) != 1:
        raise ValueError(f'WinGUp source anchor changed: {old!r}')
    return code.replace(old, new)

with tempfile.TemporaryDirectory(prefix='npp-lite-wingup-') as scratch:
    tmp = Path(scratch)
    archive = tmp / 'wingup.zip'
    download('https://codeload.github.com/notepad-plus-plus/wingup/zip/refs/tags/v5.4.3',
             '5f74b4b912b71a18660430d1a1baf045f0e5b3edad287eac182f1f026c2bc940', archive)
    with zipfile.ZipFile(archive) as z:
        z.extractall(tmp)
    src = tmp / 'wingup-5.4.3'
    main = src / 'src/winmain.cpp'
    code = main.read_text(encoding='utf-8-sig')
    code = once(code, '#define APP_MUTEX L"nppInstance"', '#define APP_MUTEX L"nppLiteInstance"\n#include "LitePluginScope.h"')
    shutil.copy2(root / 'deploy/lite-plugin-scope.h', src / 'src/LitePluginScope.h')
    code = once(code, '\tbool isMoveFolder = isInList(FLAG_MOVEFOLDER, params);', '''\tbool isMoveFolder = isInList(FLAG_MOVEFOLDER, params);
	if (!litePluginScope(params, isUnzip, isCleanUp, isMoveFolder))
		return -1;''')
    code = once(code, 'L"The maintained app seems to be still running but GUP will try to proceed anyway...");', 'L"Npp Lite is still running; refusing plugin filesystem changes.");\n\t\t\treturn -1;')
    # The official GUP requires a Notepad++-signed host (incl. for folder moves).
    # Replace that identity decision only in plugin mode with LitePluginScope's
    # no-elevation, fixed-layout and argument checks; keep package digest checks.
    import re
    code, count = re.subn(r'#ifdef _DEBUG\n\t\t// Don\x27t check any thing in debug mode\n#else\n\t\t// Check signature of the launched program, with the same certif as gup.exe\n.*?\n#endif', '', code, flags=re.S)
    if count != 3:
        raise ValueError(f'Expected exactly 3 plugin identity checks, got {count}')
    main.write_text(code, encoding='utf-8-sig')
    subprocess.run(['cmake', '-S', 'curl', '-B', 'curl/build/x64', '-A', 'x64',
                    '-DBUILD_SHARED_LIBS=OFF', '-DCURL_STATIC_CRT=ON', '-DBUILD_CURL_EXE=OFF',
                    '-DCURL_USE_SCHANNEL=ON', '-DCURL_USE_OPENSSL=OFF', '-DBUILD_TESTING=OFF',
                    '-DUSE_LIBPSL=OFF', '-DCURL_USE_LIBPSL=OFF', '-DUSE_NGHTTP2=OFF', '-DUSE_LIBIDN2=OFF'], cwd=src, check=True)
    subprocess.run(['cmake', '--build', 'curl/build/x64', '--config', 'Release', '--parallel', '2'], cwd=src, check=True)
    subprocess.run(['msbuild', 'GUP.sln', '/m', '/p:configuration=Release', '/p:platform=x64', '/v:minimal'], cwd=src/'vcproj', check=True)
    tools = bin64 / 'updater'
    tools.mkdir(parents=True, exist_ok=True)
    helper = tools / 'plugin-tool.exe'
    shutil.copy2(src / 'bin64/GUP.exe', helper)
    shutil.copy2(src / 'LICENSE', tools / 'LICENSE.txt')
    (tools / 'gup.xml').write_text('<?xml version="1.0"?><GUPInput><SoftwareName>Npp Lite</SoftwareName><ClassName2Close>NppLite</ClassName2Close><MessageBoxTitle>Npp Lite</MessageBoxTitle></GUPInput>', encoding='utf-8')
    shutil.copy2(root / 'deploy/plugin-tool-source.txt', tools / 'SOURCE.txt')
    npp = tmp / 'npp.zip'
    download('https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.9.9.1/npp.8.9.9.1.portable.x64.zip',
             'cbcefa34677e10fe6dd19802f7d6b3b9860cd6de62afeaae7680e09c51b47779', npp)
    catalog = bin64 / 'plugins/Config/nppPluginList.dll'
    catalog.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(npp) as z:
        catalog.write_bytes(z.read('plugins/Config/nppPluginList.dll'))
    generated.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(helper.read_bytes()).hexdigest()
    (generated / 'PluginToolHash.h').write_text(f'#pragma once\n#define LITE_PLUGIN_TOOL_SHA256 L"{digest}"\n', encoding='ascii')
