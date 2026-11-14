"""Prepare bundled text resources; no network or executable vendoring."""
from pathlib import Path
import copy
import json
import re
import xml.etree.ElementTree as E
root = Path(__file__).resolve().parents[1]
out = root/'PowerEditor/src/Lite/generated'
out.mkdir(parents=True, exist_ok=True)
styles = E.parse(root/'PowerEditor/src/stylers.model.xml')
for style in styles.iter():
    if style.tag in ['WidgetStyle','WordsStyle']:
        style.set('fontName','宋体')
        if style.get('name') == 'Default Style': style.set('fontSize','11')
styles.write(out/'stylers.xml',encoding='utf-8',xml_declaration=True)
lang = E.parse(root/'PowerEditor/installer/nativeLang/chineseSimplified.xml')
native = lang.getroot().find('Native-Langue')
# The curated host menu already has its own stable folder layout. Retain only
# command-ID translations here, never transplant upstream submenu positions.
for tag in ['Entries','SubEntries']:
    element = native.find('Menu/Main/'+tag)
    if element is not None:
        for item in list(element):
            if tag == 'SubEntries' or item.get('menuId') not in ['file','edit','search','view','encoding','language','settings','Plugins','Window']:
                element.remove(item)
lang.write(out/'nativeLang.xml',encoding='utf-8',xml_declaration=True)
udl = E.Element('NotepadPlus')
source = E.parse(root/'deploy/markdown/upstream.udl.xml').getroot().find('UserLang')
for dark in (False,True):
    user = copy.deepcopy(source)
    user.set('name','Markdown（深色）' if dark else 'Markdown')
    user.set('ext','md markdown mdown mkd mdwn')
    if dark: user.set('darkModeTheme','yes')
    paper = '20242B' if dark else 'FFFFFF'
    ink = 'D5DAE2' if dark else '29313D'
    accent = '8CB9EC' if dark else '285D96'
    muted = '9AA9BC' if dark else '68768A'
    code = 'C7D0DD' if dark else '525A68'
    code_paper = '292F38' if dark else 'F2F4F7'
    for style in user.find('Styles'):
        style.set('fontName','宋体')
        style.set('fontSize','11')
        style.set('fgColor',ink)
        style.set('bgColor',paper)
        name = style.get('name')
        if name in ['LINE COMMENTS','KEYWORDS2']:
            style.set('fgColor',accent); style.set('fontStyle','1')
        elif name in ['COMMENTS','OPERATORS']:
            style.set('fgColor',muted); style.set('fontStyle','0')
        elif name in ['KEYWORDS1','DELIMITERS1']:
            style.set('fgColor',accent); style.set('fontStyle','0')
        elif name == 'DELIMITERS2':
            style.set('fgColor',code); style.set('bgColor',code_paper); style.set('fontStyle','0')
        elif name in ['KEYWORDS3','KEYWORDS4','KEYWORDS6','KEYWORDS7','DELIMITERS3','DELIMITERS4','DELIMITERS6','DELIMITERS7']:
            # Avoid slanted Chinese and accidental bold-italic runs. Explicit
            # bold remains distinct while keeping the same glyph size.
            style.set('fontStyle','1')
        elif name in ['KEYWORDS5','DELIMITERS5']:
            style.set('fontStyle','0'); style.set('fgColor',muted)
    udl.append(user)
E.indent(udl,space='    ')
E.ElementTree(udl).write(out/'userDefineLang.xml',encoding='utf-8',xml_declaration=True)
# Only display labels are translated; native XML keys stay untouched.
terms = json.loads((root/'deploy/style-terms.json').read_text(encoding='utf-8'))
style_tree = E.parse(root/'PowerEditor/src/stylers.model.xml')
style_names = sorted({e.get('name','') for e in style_tree.iter() if e.tag in ['WidgetStyle','WordsStyle']})
style_lines = ['// Generated display labels; never use these as XML keys.', '#pragma once', 'namespace Lite {', 'inline const wchar_t* translatedStyleName(std::wstring_view source) {']
for name in style_names:
    label = re.sub(r'[A-Za-z]+(?:-[A-Za-z]+)*', lambda m: terms.get(m[0].upper(),m[0]), name)
    if not re.search(r'[\u4e00-\u9fff]', label):
        label = '语法项（' + label + '）'
    style_lines.append('    if (source == L' + json.dumps(name,ensure_ascii=False) + ') return L' + json.dumps(label,ensure_ascii=False) + ';')
style_lines += ['    return nullptr;', '}', '}']
(out/'StyleLabels.h').write_text('\n'.join(style_lines)+'\n',encoding='utf-8')
# Count only interactive settings, not labels, tooltips or page titles.
retired = {'TOOLBAR','EDITING2','LANGUAGE','HIGHLIGHTING','PRINT','MULTIINSTANCE','DELIMITER','CLOUD_LINK','SEARCHENGINE'}
resource = (root/'PowerEditor/src/WinControls/Preference/preference.rc').read_text(encoding='utf-8-sig')
items = []
for match in re.finditer(r'IDD_PREFERENCE_SUB_(\w+) DIALOGEX.*?\nBEGIN\n(.*?)\nEND',resource,re.S):
    if match[1] not in retired: continue
    for line in match[2].splitlines():
        if re.search(r'^\s*(EDITTEXT|COMBOBOX)\s+',line) or ('CONTROL' in line and ('BS_AUTOCHECKBOX' in line or 'BS_AUTORADIOBUTTON' in line or 'msctls_trackbar32' in line)):
            idmatch = re.search(r'\b(ID[CD]_\w+|IDD_\w+)\b',line)
            if idmatch: items.append({'page':match[1],'control':idmatch[1]})
assert len(items) >= 50
manifest = {'retiredPages':10,'retiredInteractiveControls':len(items),'retiredControls':items,'retainedPages':14,'language':'简体中文','defaultFont':'宋体','markdown':'native UDL, uniform 11pt, no extra line spacing'}
(out/'settings-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Prepared official zh-CN + native Markdown UDL; removed {len(items)} interactive preference controls, 14 pages remain')
