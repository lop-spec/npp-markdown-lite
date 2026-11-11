"""Run only on a CI runner or an inherited private/hidden Windows desktop."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib

root = Path(__file__).resolve().parents[1]
exe = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
u = C.WinDLL('user32', use_last_error=True)
k = C.WinDLL('kernel32', use_last_error=True)
g = C.WinDLL('gdi32', use_last_error=True)
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
for name in ['scintilla/include/Scintilla.h', 'PowerEditor/src/menuCmdID.h', 'PowerEditor/src/resource.h', 'PowerEditor/src/MarkdownLite/MenuIds.h']:
    for line in (root / name).read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'\s*#define\s+(\w+)\s+([A-Za-z_0-9 +(),-]+)', line)
        if m:
            expression = m[2].strip()
            for key in re.findall(r'\b[A-Za-z_]\w*\b', expression):
                if key in constants:
                    expression = re.sub(r'\b' + key + r'\b', str(constants[key]), expression)
            if re.fullmatch(r'[0-9 +(),-]+', expression):
                try:
                    value = eval(expression, {'__builtins__': {}})
                    if isinstance(value, int): constants[m[1]] = value
                except Exception: pass

def send(hwnd, message, w=0, l=0):
    if isinstance(message, str): message = constants[message]
    result = C.c_size_t()
    if not u.SendMessageTimeoutW(hwnd, message, w, l, 2, 5000, C.byref(result)):
        raise OSError(C.get_last_error(), 'SendMessageTimeout')
    return C.c_ssize_t(result.value).value

checks = []
def check(ok, label):
    if not ok: raise AssertionError(label)
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
fixture = work / 'sample.md'
sample = '# Markdown 原生编辑\n\n## 标题层级\n\n正文 **粗体** 和 *斜体*，以及 `code()`。\n\n> 引用保留原文\n\n- [ ] 待办事项\n- [x] 已完成\n\n[链接](https://example.com)\n\n```python\nprint("中文内容")\n```\n\n| 名称 | 值 |\n| --- | --- |\n| 中文 | abc |\n'
fixture.write_bytes(sample.encode('utf-8'))
before = hashlib.sha256(fixture.read_bytes()).hexdigest()
process = subprocess.Popen([str(exe), '-multiInst', '-nosession', '-settingsDir=' + str(profile), str(fixture)], creationflags=0x08000000)
handle = None
main = None
try:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None: raise RuntimeError('application exited ' + str(process.returncode))
        candidates = [hwnd for hwnd, name in windows(process.pid) if name == 'NppMarkdownLite']
        if candidates:
            main = candidates[0]
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
        send(sci, 'SCI_COLOURISE', 0, -1)

    def command(name): send(main, 0x111, constants[name])
    check(send(sci, 'SCI_GETLEXER') == 98, 'native Markdown lexer')
    check(send(sci, 'SCI_STYLEGETSIZE', 6) > send(sci, 'SCI_STYLEGETSIZE', 0), 'larger heading font')
    send(sci, 'SCI_COLOURISE', 0, -1)
    check(send(sci, 'SCI_STYLEGETBOLD', 2) == 1, 'bold emphasis style')
    check(send(sci, 'SCI_GETSTYLEAT', 3) == 6, 'heading body receives heading style')
    check(send(sci, 'SCI_GETFOLDLEVEL', 0) & 0x2000, 'headings use original folding margin')
    code_at = sample.encode('utf-8').index(b'print(')
    check(send(sci, 'SCI_GETSTYLEAT', code_at) == 25, 'fenced code has dedicated full-line style')
    check(send(sci, 'SCI_GETWRAPMODE') != 0, 'Markdown soft wrap')
    check(send(sci, 'SCI_GETMODIFY') == 0 and text() == sample, 'opening and styling is byte-preserving')
    check(all((profile / x).exists() for x in ['config.xml', 'langs.xml', 'stylers.xml']), 'single EXE seeds all defaults')
    menu = u.GetMenu(main)
    labels = []
    all_ids = []
    menu_items = []
    def inspect(menu, top=False):
        for i in range(u.GetMenuItemCount(menu)):
            name = C.create_unicode_buffer(512)
            u.GetMenuStringW(menu, i, name, 512, 0x400)
            if top: labels.append(name.value)
            child = u.GetSubMenu(menu, i)
            if child: inspect(child)
            else:
                item_id = u.GetMenuItemID(menu, i)
                all_ids.append(item_id)
                menu_items.append((name.value, item_id))
    inspect(menu, True)
    check(len(labels) == 14, 'compact top menu positions')
    check(all(constants[x] not in all_ids for x in ['IDM_MACRO_STARTRECORDINGMACRO', 'IDM_EXECUTE', 'IDM_TOOL_MD5_GENERATE']), 'retired features absent from menus')
    check(constants['IDM_SETTING_OPENPLUGINSDIR'] in all_ids, 'plugin menu retained')
    toolbar = [hwnd for hwnd, name in windows(process.pid, main) if name == 'ToolbarWindow32']
    check(bool(toolbar) and 12 <= send(toolbar[0], 0x418) <= 16, 'compact native toolbar')
    check(u.GetPropW(main, 'LitePluginReady') == 1, 'real native plugin receives NPPN_READY')

    # The next screenshot is produced before destructive test edits. PrintWindow
    # renders this test window only; it never captures the user's desktop.
    try:
        from screenshot import capture
        u.SetWindowPos(main, None, 0, 0, 2304, 1536, 0x14)
        time.sleep(0.4)
        capture(main, out / 'markdown-light.png')
    except Exception as error:
        (out / 'screenshot-error.txt').write_text(str(error), encoding='utf-8')

    set_text('hello')
    send(sci, 'SCI_SETSEL', 0, 5)
    command('IDM_MD_BOLD')
    check(text() == '**hello**', 'bold wraps exact source selection')
    send(sci, 'SCI_UNDO')
    check(text() == 'hello', 'format command is one undo unit')
    set_text('- [ ] task')
    command('IDM_MD_TASK')
    check(text() == '- [x] task', 'task checkbox toggles source')
    send(sci, 'SCI_SETREADONLY', 1)
    command('IDM_MD_TASK')
    check(text() == '- [x] task', 'readonly source protected')
    set_text('| 名称 | value |\n| --- | --- |\n| 中文 | abc |')
    command('IDM_MD_TABLE')
    aligned = text()
    check('中文' in aligned and '| 名称 |' in aligned, 'Chinese table preserves content')
    command('IDM_MD_TABLE')
    check(text() == aligned, 'table format is idempotent')
    send(sci, 'SCI_UNDO')
    # No auto-save or read-time formatting is allowed.
    check(hashlib.sha256(fixture.read_bytes()).hexdigest() == before, 'original disk file never modified by display or commands')
    for value, suffix in [('- item', '- '), ('9. item', '10. '), ('- [x] done', '- [ ] '), ('> quote', '> ')]:
        set_text(value)
        send(sci, 'SCI_GOTOPOS', len(value))
        send(sci, 'SCI_NEWLINE')
        check(text().endswith('\r\n' + suffix) or text().endswith('\n' + suffix), 'Enter continuation: ' + value)
    set_text('- ')
    send(sci, 'SCI_GOTOPOS', 2)
    send(sci, 'SCI_NEWLINE')
    check(text() == '', 'empty list exits cleanly')
    set_text('```text\n- code')
    send(sci, 'SCI_GOTOPOS', len('```text\n- code'))
    send(sci, 'SCI_NEWLINE')
    check(not text().endswith('- '), 'code fence has no list continuation')
    set_text('````md\n```\n# code heading\n````\n\n# real heading')
    code_at = text().encode('utf-8').index(b'# code')
    real_at = text().encode('utf-8').index(b'# real')
    check(send(sci, 'SCI_GETSTYLEAT', code_at) == 25 and send(sci, 'SCI_GETSTYLEAT', real_at + 3) == 6, 'variable-length fences close correctly without leaking styles')
    set_text('# first\n\n```md\n# not a heading\n```\n\n## second')
    send(sci, 'SCI_GOTOPOS', 0)
    command('IDM_MD_NEXT')
    check(send(sci, 'SCI_LINEFROMPOSITION', send(sci, 'SCI_GETCURRENTPOS')) == 6, 'heading navigation skips fenced code')
    command('IDM_MD_RICH')
    check(send(sci, 'SCI_STYLEGETBOLD', 2) == 0, 'source appearance toggle')
    command('IDM_MD_RICH')
    check(send(sci, 'SCI_STYLEGETBOLD', 2) == 1, 'rich appearance restored')
    set_text('')
    plugin_id = next((item_id for name, item_id in menu_items if name == 'Probe command'), None)
    check(plugin_id is not None, 'plugin command registered')
    send(main, 0x111, plugin_id)
    check(text() == 'plugin-ok', 'plugin command edits original Scintilla')
    if os.environ.get('LITE_OFFICIAL_PLUGIN') == '1':
        encode = next((item_id for name, item_id in menu_items if name.replace('&', '').strip() == 'Base64 Encode'), None)
        decode = next((item_id for name, item_id in menu_items if name.replace('&', '').strip() == 'Base64 Decode'), None)
        check(encode is not None and decode is not None, 'official mimeTools registers native commands')
        set_text('hello')
        send(sci, 'SCI_SELECTALL')
        send(main, 0x111, encode)
        check(text() == 'aGVsbG8=', 'official mimeTools Base64 encode works')
        send(sci, 'SCI_SELECTALL')
        send(main, 0x111, decode)
        check(text() == 'hello', 'official mimeTools Base64 decode works')
    send(sci, 'SCI_SETSAVEPOINT')
    command('IDM_FILE_NEW')
    check(send(sci, 'SCI_GETLEXER') != 98, 'normal document restores native lexer')
    check(send(sci, 'SCI_GETWRAPMODE') == 0 and send(sci, 'SCI_GETEXTRAASCENT') == 0, 'normal document restores wrapping and spacing')
    command('IDM_MD_MODE')
    check(send(sci, 'SCI_GETLEXER') == 98, 'unsaved Markdown mode supported')
    command('IDM_MD_MODE')
    check(send(sci, 'SCI_GETLEXER') != 98, 'Markdown mode can be disabled')
    (out / 'smoke.json').write_text(json.dumps({'checks': checks, 'count': len(checks), 'menus': labels, 'exe_bytes': exe.stat().st_size, 'exe_sha256': hashlib.sha256(exe.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS', len(checks), 'Windows integration checks')
finally:
    if handle: k.CloseHandle(handle)
    if process.poll() is None:
        process.kill()
        process.wait(timeout=10)
    shutil.rmtree(work, ignore_errors=True)
