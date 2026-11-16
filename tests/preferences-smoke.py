"""Focused Win32 preference acceptance on the inherited CI/private desktop."""
import ctypes as C
from ctypes import wintypes as W
import json
import re
import time

def verify(context):
    u, send, pointer, windows, check, main, pid, out, root = context
    u.GetDlgItem.argtypes = [W.HWND,C.c_int]
    u.GetDlgItem.restype = W.HWND
    u.GetDlgCtrlID.argtypes = [W.HWND]
    u.GetWindowTextW.argtypes = [W.HWND,W.LPWSTR,C.c_int]
    u.PostMessageW.argtypes = [W.HWND,W.UINT,C.c_size_t,C.c_ssize_t]
    def caption(hwnd):
        text=C.create_unicode_buffer(4096)
        u.GetWindowTextW(hwnd,text,len(text))
        return text.value
    def listed(hwnd,index,combo=False):
        text=C.create_unicode_buffer(4096)
        send(hwnd,0x148 if combo else 0x189,index,C.addressof(text))
        return text.value
    send(main,0x111,48011)
    deadline=time.monotonic()+10
    preferences=None
    while time.monotonic()<deadline:
        preferences=next((h for h,n in windows(pid) if u.GetDlgItem(h,6002)),None)
        if preferences: break
        time.sleep(.1)
    check(bool(preferences),'native preferences dialog opens')
    listing=u.GetDlgItem(preferences,6002)
    count=send(listing,0x18B)
    check(count==14,'exactly 14 retained preference pages')
    page_names=[listed(listing,i) for i in range(count)]
    (out/'preference-titles.json').write_text(json.dumps(page_names,ensure_ascii=False,indent=2),encoding='utf-8')
    check(all(re.search('[\u4e00-\u9fff]',name) for name in page_names),'all preference page titles Chinese')
    manifest=json.loads((root/'PowerEditor/src/Lite/generated/settings-manifest.json').read_text(encoding='utf-8'))
    check(manifest['retiredInteractiveControls']>=50,'at least 50 interactive settings removed, labels excluded')
    # Technical identifiers, keyboard keys, units and encoding standards retain
    # their universal spellings, as do user file paths and input values.
    technical=re.compile(r'^(?:[\d\s%.,:;()\[\]{}<>_+\-/*\\=&|#@!?\"\']+|[A-Z0-9]+(?:[-_ /().][A-Z0-9]+)*|Fluent UI.*|UTF.*|Windows.*|Unix.*|Macintosh.*|DirectWrite.*|GDI.*|Notepad\+\+.*|Npp Lite.*)$')
    pages=[]; untranslated=[]; live_ids=set()
    for index,name in enumerate(page_names):
        send(listing,0x186,index)
        send(preferences,0x111,(1<<16)|6002,listing)
        controls=[]
        for hwnd,kind in windows(pid,preferences):
            live_ids.add(u.GetDlgCtrlID(hwnd))
            if not u.IsWindowVisible(hwnd): continue
            text=caption(hwnd).strip()
            if kind in ['Static','Button'] and text:
                controls.append({'id':u.GetDlgCtrlID(hwnd),'text':text})
                cleaned=text.replace('&','').strip()
                if re.search('[A-Za-z]',cleaned) and not re.search('[\u4e00-\u9fff]',cleaned) and not technical.fullmatch(cleaned) and not re.fullmatch(r'MB\s*\([0-9 -]+\)',cleaned):
                    untranslated.append({'page':name,'id':u.GetDlgCtrlID(hwnd),'text':text})
        pages.append({'name':name,'controls':controls})
    constants={}
    header=(root/'PowerEditor/src/WinControls/Preference/preference_rc.h').read_text(encoding='utf-8-sig')
    for key,value in re.findall(r'#define\s+(\w+)\s+(\d+)',header): constants[key]=int(value)
    removed=[item for item in manifest['retiredControls'] if constants.get(item['control']) in live_ids]
    (out/'preferences.json').write_text(json.dumps({'pages':pages,'manifest':manifest,'unexpectedControls':removed,'untranslated':untranslated},ensure_ascii=False,indent=2),encoding='utf-8')
    check(not removed,'retired interactive controls do not exist in live preferences')
    check(not untranslated,'no untranslated prose in retained preference controls')
    send(preferences,0x111,6001)
    return page_names

def verify_styles(context,profile):
    import xml.etree.ElementTree as E
    u, send, pointer, windows, check, main, pid, out, root = context
    u.PostMessageW(main,0x111,46001,0)
    deadline=time.monotonic()+10
    dialog=None
    while time.monotonic()<deadline:
        dialog=next((h for h,n in windows(pid) if u.GetDlgItem(h,2305)),None)
        if dialog: break
        time.sleep(.1)
    check(bool(dialog),'native style settings opens')
    listing=u.GetDlgItem(dialog,2305)
    labels=[]
    for i in range(send(listing,0x18B)):
        text=C.create_unicode_buffer(4096); send(listing,0x189,i,C.addressof(text)); labels.append(text.value)
    check(labels and all(re.search('[\u4e00-\u9fff]',name) for name in labels),'all global style labels Chinese')
    font=C.create_unicode_buffer(256)
    send(u.GetDlgItem(dialog,2202),0xD,len(font),C.addressof(font))
    check(font.value in ['SimSun','宋体'],'style font selector correctly shows SimSun alias')
    # Exercise the native edit/save path, restoring the user's temporary value.
    send(u.GetDlgItem(dialog,2204),0xF5)
    send(u.GetDlgItem(dialog,2204),0xF5)
    send(dialog,0x111,2301)
    tree=E.parse(profile/'stylers.xml')
    names=[e.get('name') for e in tree.iter('WidgetStyle')]
    check('Default Style' in names and '默认样式' not in names,'Chinese style editing preserves canonical XML keys')
    (out/'style-settings.json').write_text(json.dumps({'labels':labels,'font':font.value,'canonicalKeys':True},ensure_ascii=False,indent=2),encoding='utf-8')

def verify_plugin(context,command_id):
    u, send, pointer, windows, check, main, pid, out, root = context
    u.PostMessageW.argtypes=[W.HWND,W.UINT,C.c_size_t,C.c_ssize_t]
    u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
    def caption(hwnd):
        text=C.create_unicode_buffer(4096); u.GetWindowTextW(hwnd,text,len(text)); return text.value
    u.PostMessageW(main,0x111,command_id,0)
    deadline=time.monotonic()+12
    dialog=None
    while time.monotonic()<deadline:
        dialog=next((h for h,n in windows(pid) if n.startswith('WindowsForms') and caption(h)=='设置'),None)
        if dialog: break
        time.sleep(.1)
    check(bool(dialog),'official plugin settings dialog is Chinese')
    labels=[caption(h) for h,n in windows(pid,dialog) if 'STATIC' in n.upper() or 'BUTTON' in n.upper()]
    (out/'plugin-settings.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2),encoding='utf-8')
    check('浅色样式文件：' in labels and '缩放比例：' in labels and '保存' in labels and '取消' in labels,'official plugin settings labels translated without replacing DLL')
    u.PostMessageW(dialog,0x10,0,0)
    time.sleep(.2)
