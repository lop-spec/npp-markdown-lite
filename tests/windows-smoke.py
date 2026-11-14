"""Run on CI or an inherited private desktop; never activates the user's desktop."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
root = Path(__file__).resolve().parents[1]
exe = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
u = C.WinDLL('user32', use_last_error=True)
k = C.WinDLL('kernel32', use_last_error=True)
u.SendMessageTimeoutW.argtypes = [W.HWND, W.UINT, C.c_size_t, C.c_ssize_t, W.UINT, W.UINT, C.POINTER(C.c_size_t)]
u.SendMessageTimeoutW.restype = C.c_ssize_t
u.GetMenu.argtypes = [W.HWND]
u.GetMenu.restype = W.HMENU
u.GetSubMenu.argtypes = [W.HMENU, C.c_int]
u.GetSubMenu.restype = W.HMENU
u.GetMenuItemCount.argtypes = [W.HMENU]
u.GetMenuItemID.argtypes = [W.HMENU, C.c_int]
u.GetMenuItemID.restype = W.UINT
u.GetMenuStringW.argtypes = [W.HMENU, W.UINT, W.LPWSTR, C.c_int, W.UINT]
u.GetPropW.argtypes = [W.HWND, W.LPCWSTR]
u.GetPropW.restype = W.HANDLE
u.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, C.c_int]
u.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
u.IsWindowVisible.argtypes = [W.HWND]
u.SetWindowPos.argtypes = [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT]
k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
k.OpenProcess.restype = W.HANDLE
k.VirtualAllocEx.argtypes = [W.HANDLE, W.LPVOID, C.c_size_t, W.DWORD, W.DWORD]
k.VirtualAllocEx.restype = W.LPVOID
k.VirtualFreeEx.argtypes = [W.HANDLE, W.LPVOID, C.c_size_t, W.DWORD]
k.WriteProcessMemory.argtypes = [W.HANDLE, W.LPVOID, W.LPCVOID, C.c_size_t, C.POINTER(C.c_size_t)]
k.ReadProcessMemory.argtypes = [W.HANDLE, W.LPCVOID, W.LPVOID, C.c_size_t, C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes = [W.HANDLE]
CALLBACK = C.WINFUNCTYPE(W.BOOL, W.HWND, C.c_ssize_t)
u.EnumWindows.argtypes = [CALLBACK, C.c_ssize_t]
u.EnumChildWindows.argtypes = [W.HWND, CALLBACK, C.c_ssize_t]
constants = {}
for name in ['scintilla/include/Scintilla.h', 'PowerEditor/src/menuCmdID.h', 'PowerEditor/src/resource.h']:
    for line in (root / name).read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'\s*#define\s+(\w+)\s+([A-Za-z_0-9 +(),-]+)', line)
        if not m: continue
        expression = m[2].strip()
        for key in re.findall(r'\b[A-Za-z_]\w*\b', expression):
            if key in constants: expression = re.sub(r'\b' + key + r'\b', str(constants[key]), expression)
        if re.fullmatch(r'[0-9 +(),-]+', expression):
            try:
                value = eval(expression, {'__builtins__': {}})
                if isinstance(value, int): constants[m[1]] = value
            except Exception: pass

def send(hwnd, message, w=0, l=0):
    if isinstance(message, str): message = constants[message]
    result = C.c_size_t()
    if not u.SendMessageTimeoutW(hwnd, message, w, l, 2, 5000, C.byref(result)): raise OSError(C.get_last_error(), 'SendMessageTimeout')
    return C.c_ssize_t(result.value).value
checks = []
def check(ok, label):
    if not ok:
        (out / 'failure.json').write_text(json.dumps({'failure': label, 'passed': checks}, ensure_ascii=False, indent=2), encoding='utf-8')
        raise AssertionError(label)
    checks.append(label)
def windows(pid, parent=None):
    found = []
    @CALLBACK
    def visit(hwnd, _):
        p = W.DWORD()
        u.GetWindowThreadProcessId(hwnd, C.byref(p))
        if p.value == pid:
            name = C.create_unicode_buffer(128)
            u.GetClassNameW(hwnd, name, len(name))
            found.append((hwnd, name.value))
        return True
    if parent: u.EnumChildWindows(parent, visit, 0)
    else: u.EnumWindows(visit, 0)
    return found
work = Path(tempfile.mkdtemp(prefix='npp-lite-smoke-'))
profile = work / 'settings'
profile.mkdir()
if os.environ.get('LITE_DARK') == '1':
    config=(root/'PowerEditor/src/Lite/config.xml').read_text(encoding='utf-8')
    config=config.replace('<GUIConfigs>','<GUIConfigs><GUIConfig name="DarkMode" enable="yes" tone="0" />')
    (profile/'config.xml').write_text(config,encoding='utf-8')
fixture = work / 'sample.md'
sample = '# NPP-LITE-PREVIEW-SENTINEL\n\nOriginal Markdown source.\n\n| Name | Value |\n| --- | --- |\n| hello | world |\n'
fixture.write_bytes(sample.encode('utf-8'))
before = hashlib.sha256(fixture.read_bytes()).hexdigest()
process = subprocess.Popen([str(exe), '-multiInst', '-nosession', '-settingsDir=' + str(profile), str(fixture)], creationflags=0x08000000)
handle = None
try:
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        if process.poll() is not None: raise RuntimeError('application exited ' + str(process.returncode))
        main = next((hwnd for hwnd, name in windows(process.pid) if name == 'NppLite'), None)
        if main:
            edits = [hwnd for hwnd, name in windows(process.pid, main) if name == 'Scintilla' and u.IsWindowVisible(hwnd)]
            if edits and send(edits[0], 'SCI_GETTEXTLENGTH') == len(sample.encode('utf-8')): break
        time.sleep(0.1)
    else: raise TimeoutError('main editor not ready: ' + str(windows(process.pid)))
    sci = edits[0]
    handle = k.OpenProcess(0x438, False, process.pid)
    if not handle: raise OSError(C.get_last_error(), 'OpenProcess')
    def pointer_message(hwnd, message, data=None, capacity=None, w=0):
        size = capacity if capacity else len(data)
        memory = k.VirtualAllocEx(handle, None, size, 0x3000, 4)
        if not memory: raise OSError(C.get_last_error(), 'VirtualAllocEx')
        try:
            if data is not None:
                local = C.create_string_buffer(data)
                if not k.WriteProcessMemory(handle, memory, local, len(data), None): raise OSError('write memory')
            result = send(hwnd, message, w, memory)
            if capacity:
                local = C.create_string_buffer(capacity)
                if not k.ReadProcessMemory(handle, memory, local, capacity, None): raise OSError('read memory')
                return local.raw
            return result
        finally: k.VirtualFreeEx(handle, memory, 0, 0x8000)
    def text():
        length = send(sci, 'SCI_GETTEXTLENGTH') + 1
        return pointer_message(sci, 'SCI_GETTEXT', capacity=length, w=length)[:-1].decode('utf-8')
    def set_text(value):
        send(sci, 'SCI_SETREADONLY', 0)
        pointer_message(sci, 'SCI_SETTEXT', value.encode('utf-8') + b'\0')
        send(sci, 'SCI_EMPTYUNDOBUFFER')
    def command(name): send(main, 0x111, constants[name])
    check(text() == sample and send(sci, 'SCI_GETMODIFY') == 0, 'opening MD preserves native editable source')
    check(send(sci, 'SCI_GETLEXER') == 152 and send(sci, 'SCI_GETEXTRAASCENT') == 0 and send(sci, 'SCI_GETEXTRADESCENT') == 0, 'native Markdown UDL with no extra line spacing')
    send(sci,'SCI_COLOURISE',0,-1)
    used_styles={send(sci,'SCI_GETSTYLEAT',i) for i in range(len(sample.encode('utf-8')))}
    check(len(used_styles)>=3,'Markdown headings, body and punctuation receive native highlighting')
    check(all(send(sci,'SCI_STYLEGETSIZE',style)==11 for style in used_styles),'all Markdown styles use equal 11pt size')
    check(all(pointer_message(sci,'SCI_STYLEGETFONT',capacity=128,w=style).split(b'\0')[0].decode('utf-8')=='宋体' for style in used_styles),'all Markdown styles actually use requested SimSun font')
    check(send(sci,'SCI_TEXTHEIGHT',0)==send(sci,'SCI_TEXTHEIGHT',2),'heading and body retain equal native line height')
    command('IDM_FILE_NEW')
    check(send(sci,'SCI_GETLEXER')==152 and send(sci,'SCI_GETTEXTLENGTH')==0,'new documents default to native Markdown')
    command('IDM_FILE_CLOSE')
    preference_tests=runpy.run_path(str(root/'tests/preferences-smoke.py'))
    context=(u,send,pointer_message,windows,check,main,process.pid,out,root)
    if os.environ.get('LITE_DARK')!='1': preference_tests['verify'](context)
    check(not (root / 'PowerEditor/src/MarkdownLite').exists(), 'custom Markdown source directory deleted')
    labels, items = [], []
    def inspect(menu, top=False):
        for i in range(u.GetMenuItemCount(menu)):
            name = C.create_unicode_buffer(512)
            u.GetMenuStringW(menu, i, name, 512, 0x400)
            if top: labels.append(name.value)
            child = u.GetSubMenu(menu, i)
            if child: inspect(child)
            else: items.append((name.value, u.GetMenuItemID(menu, i)))
    inspect(u.GetMenu(main), True)
    check(len(labels) == 13 and not any('Markdown' in label for label in labels), 'no built-in Markdown top menu')
    ids = {item_id for _, item_id in items}
    retired = re.findall(r'^\s*(IDM_\w+)', (root / 'PowerEditor/src/Lite/RetiredCommands.h').read_text(encoding='utf-8'), re.M)
    check(len(retired) == 80 and len(set(retired)) == 80, '80 additional native commands uniquely enumerated')
    set_text('zeta\nAlpha\n42\n- [ ] task')
    send(sci, 'SCI_SETSEL', 0, 4)
    snapshot = text()
    for name in retired:
        check(constants[name] not in ids, 'absent menu: ' + name)
        send(main, 0x111, constants[name])
        check(text() == snapshot and send(sci, 'SCI_GETSELECTIONSTART') == 0 and send(sci, 'SCI_GETSELECTIONEND') == 4, 'retired dispatch inert: ' + name)
    for old_md in range(49800, 49812): send(main, 0x111, old_md)
    check(text() == snapshot, 'all 12 removed Markdown command IDs remain inert')
    toolbar = [hwnd for hwnd, name in windows(process.pid, main) if name == 'ToolbarWindow32']
    check(bool(toolbar), 'native toolbar retained')
    toolbar_ids = []
    for index in range(send(toolbar[0], 0x418)):
        data = pointer_message(toolbar[0], 0x417, capacity=32, w=index)
        toolbar_ids.append(int.from_bytes(data[4:8], 'little', signed=True))
    host_toolbar = [i for i in toolbar_ids if 40000 <= i < 50000]
    expected_toolbar = [constants[name] for name in ['IDM_FILE_NEW','IDM_FILE_OPEN','IDM_FILE_SAVE','IDM_EDIT_UNDO','IDM_EDIT_REDO','IDM_SEARCH_FIND','IDM_SEARCH_REPLACE','IDM_VIEW_WRAP']]
    check(host_toolbar == expected_toolbar, 'exactly 8 host toolbar buttons; plugin additions allowed')
    check(all(constants[name] not in toolbar_ids for name in ['IDM_FILE_SAVEALL','IDM_EDIT_CUT','IDM_EDIT_COPY','IDM_EDIT_PASTE']), '4 redundant toolbar buttons removed, commands retained')
    send(sci, 'SCI_SETSEL', 0, 4)
    pointer_message(sci, 'SCI_REPLACESEL', b'test\0')
    check(text().startswith('test'), 'native selection replacement')
    send(sci, 'SCI_UNDO')
    check(text() == snapshot, 'native undo retained')
    send(sci, 'SCI_SETSELECTIONMODE', 1)
    check(send(sci, 'SCI_GETSELECTIONMODE') == 1, 'native rectangular selection retained')
    send(sci, 'SCI_SETSELECTIONMODE', 0)
    check(u.GetPropW(main, 'LitePluginReady') == 1, 'native plugin ABI startup notification')
    probe = next((i for name, i in items if name == 'Probe command'), None)
    check(probe is not None, 'native plugin menu registration')
    set_text('')
    send(main, 0x111, probe)
    check(text() == 'plugin-ok', 'native plugin edits original Scintilla')
    panel = next((i for name, i in items if '显示或隐藏 Markdown 面板' in name), None)
    check(panel is not None, 'official Markdown Panel menu registered')
    set_text(sample)
    send(main, 0x111, panel)
    time.sleep(3)
    check(any('WindowsForms' in name for _, name in windows(process.pid, main)), 'official Markdown Panel creates native docked form')
    u.SetWindowPos(main, None, 0, 0, 1536, 1024, 0x414)
    def verify_preview(needle, filename):
        result = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'tests/preview-uia.ps1'),'-Window',str(main),'-Needle',needle,'-Output',str(out/filename)], capture_output=True, timeout=60, creationflags=0x08000000)
        if result.returncode: print(result.stdout.decode('utf-8',errors='replace'), result.stderr.decode('utf-8',errors='replace'))
        check(result.returncode == 0, 'WebView2 rendered document: ' + needle)
    verify_preview('NPP-LITE-PREVIEW-SENTINEL', 'panel-initial.json')
    check(text() == sample, 'panel preview does not rewrite Markdown source')
    set_text(sample.replace('PREVIEW-SENTINEL', 'EDIT-UPDATED'))
    verify_preview('NPP-LITE-EDIT-UPDATED', 'panel-updated.json')
    check(hashlib.sha256(fixture.read_bytes()).hexdigest() == before, 'preview and editing leave disk untouched until save')
    if os.environ.get('LITE_DARK')!='1':
        settings=next((i for name,i in items if name=='设置' and i>=22000 and i<40000),None)
        check(settings is not None,'official plugin settings command translated')
        preference_tests['verify_plugin'](context,settings)
    from screenshot import capture
    u.SetWindowPos(main, None, 0, 0, 2304, 1536, 0x414)
    time.sleep(1)
    capture(main, out / 'native-editor-panel.png')
    (out/'smoke.json').write_text(json.dumps({'checks':checks,'count':len(checks),'retired_commands':retired,'menus':labels,'exe_bytes':exe.stat().st_size,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2),encoding='utf-8')
    print('PASS',len(checks),'native editor / 80-command / real Markdown Panel checks')
except Exception:
    if process.poll() is None:
        (out/'native-windows.json').write_text(json.dumps(windows(process.pid, main) if main else windows(process.pid), ensure_ascii=False, indent=2),encoding='utf-8')
        if main:
            try:
                from screenshot import capture
                capture(main,out/'failed-preview.png')
            except Exception: pass
    raise
finally:
    if handle: k.CloseHandle(handle)
    if process.poll() is None:
        process.kill()
        process.wait(timeout=10)
    shutil.rmtree(work,ignore_errors=True)
