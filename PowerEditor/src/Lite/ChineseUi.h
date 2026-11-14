// Npp Lite - GPL-3.0-or-later
#pragma once
#include <windows.h>
#include <string>
#include <string_view>
#include "generated/StyleLabels.h"
namespace Lite
{
struct ChineseLabel { const wchar_t* source; const wchar_t* translated; };
inline constexpr ChineseLabel chineseLabels[] = {
	{L"Disable",L"关闭"},{L"[Default]",L"默认"},{L"Default",L"默认"},{L"Default (stylers.xml)",L"默认主题"},
	{L"Global Styles",L"全局样式"},{L"Default Style",L"默认样式"},{L"Global override",L"全局覆盖"},
	{L"Indent guideline style",L"缩进参考线"},{L"Brace highlight style",L"匹配括号"},{L"Bad brace colour",L"未匹配括号"},
	{L"Current line background colour",L"当前行背景"},{L"Selected text colour",L"选中文本"},{L"Multi-selected text color",L"多选区文本"},
	{L"Caret colour",L"光标"},{L"Multi-edit carets color",L"多重光标"},{L"Edge colour",L"列标记"},
	{L"Line number margin",L"行号边栏"},{L"Bookmark margin",L"书签边栏"},{L"Change History margin",L"修改记录边栏"},
	{L"Change History modified",L"尚未保存的修改"},{L"Change History revert modified",L"撤销后的修改"},{L"Change History revert origin",L"撤销至原文"},{L"Change History saved",L"已保存的修改"},
	{L"Fold",L"折叠标记"},{L"Fold active",L"当前折叠标记"},{L"Fold margin",L"折叠边栏"},{L"White space symbol",L"空白字符"},
	{L"Smart Highlighting",L"智能高亮"},{L"Find Mark Style",L"查找标记"},{L"Find matches highlight all",L"全部查找匹配"},
	{L"Find status: Not found",L"查找状态：未找到"},{L"Find status: Message",L"查找状态：提示"},{L"Find status: Search end reached",L"查找状态：已到末尾"},
	{L"Mark Style 1",L"标记样式一"},{L"Mark Style 2",L"标记样式二"},{L"Mark Style 3",L"标记样式三"},{L"Mark Style 4",L"标记样式四"},{L"Mark Style 5",L"标记样式五"},
	{L"Tags match highlighting",L"配对标签"},{L"Tags attribute",L"标签属性"},{L"Active tab focused indicator",L"当前标签焦点标记"},{L"Active tab unfocused indicator",L"当前标签失焦标记"},
	{L"Active tab text",L"当前标签文字"},{L"Inactive tabs",L"其他标签"},
	{L"Tab color 1",L"标签颜色一"},{L"Tab color 2",L"标签颜色二"},{L"Tab color 3",L"标签颜色三"},{L"Tab color 4",L"标签颜色四"},{L"Tab color 5",L"标签颜色五"},
	{L"Tab color dark mode 1",L"深色标签颜色一"},{L"Tab color dark mode 2",L"深色标签颜色二"},{L"Tab color dark mode 3",L"深色标签颜色三"},{L"Tab color dark mode 4",L"深色标签颜色四"},{L"Tab color dark mode 5",L"深色标签颜色五"},
	{L"URL hovered",L"链接悬停"},{L"Document map",L"文档结构图"},{L"EOL custom color",L"换行符颜色"},{L"Non-printing characters custom color",L"非打印字符颜色"},
	{L"DEFAULT",L"默认"},{L"COMMENT",L"注释"},{L"COMMENTS",L"注释"},{L"COMMENT LINE",L"单行注释"},{L"COMMENT BLOCK",L"块注释"},
	{L"NUMBER",L"数字"},{L"NUMBERS",L"数字"},{L"KEYWORD",L"关键字"},{L"KEYWORDS",L"关键字"},{L"STRING",L"字符串"},{L"CHARACTER",L"字符"},
	{L"OPERATOR",L"运算符"},{L"IDENTIFIER",L"标识符"},{L"PREPROCESSOR",L"预处理指令"},{L"FUNCTION",L"函数"},{L"CLASS NAME",L"类名"},
	{L"Markdown Panel Settings",L"Markdown 面板设置"},{L"Settings",L"设置"},{L"&Settings",L"设置"},
	{L"Save",L"保存"},{L"&Save",L"保存"},{L"Cancel",L"取消"},{L"&Cancel",L"取消"},{L"OK",L"确定"},{L"Reset",L"重置"},
	{L"Choose...",L"选择…"},{L"Browse...",L"浏览…"},{L"Select",L"选择"},
	{L"CSS File:",L"浅色样式文件："},{L"Zoom Level:",L"缩放比例："},
	{L"Automatically Save \r\nHTML from Current \r\nPreview to this File:",L"自动保存当前预览\r\n到此 HTML 文件："},
	{L"Darkmode CSS File:",L"深色样式文件："},{L"Supported File Extensions:",L"支持的文件扩展名："},
	{L"Automatically show panel for supported files",L"打开支持的文件时自动显示预览"},
	{L"HTML Rendering Engine:",L"HTML 渲染引擎："},
	{L"Show Toolbar in Preview Window",L"显示预览工具栏"},
	{L"Show Statusbar in Preview Window (Preview Links)",L"显示预览状态栏（显示链接地址）"},
	{L"Allow all file extensions",L"允许所有扩展名"},
	{L"Enable preview for files without extension",L"允许预览无扩展名文件"},
	{L"Enable three-state toggle (docked → fullscreen → hidden)",L"启用三态切换（停靠 → 全屏 → 隐藏）"},
	{L"File Header",L"文件标题"},{L"Search Header",L"搜索标题"},{L"Hit Word",L"命中词"},{L"Line Number",L"行号"},{L"Name",L"名称"},
	{L"Sequence Identifier",L"转义序列标识"},{L"Sequence Unknown",L"未知转义序列"},{L"Escape Sequence",L"转义序列"},{L"Unknown Escape Sequence",L"未知转义序列"},
	{L"Toggle &Markdown Panel",L"显示或隐藏 Markdown 面板"},{L"Synchronize with &caret position",L"跟随光标位置"},{L"Synchronize with &first visible line in editor",L"跟随编辑区滚动"},
	{L"Show &outline",L"显示大纲"},{L"&Help",L"帮助"},{L"&About",L"关于"},{L"Export to &PDF",L"导出为 PDF"}
};
inline std::wstring chineseLabel(std::wstring_view source)
{
	for (const auto& label : chineseLabels) if (source == label.source) return label.translated;
	if (const auto* label = translatedStyleName(source)) return label;
	return std::wstring(source);
}
inline BOOL CALLBACK translateChild(HWND hwnd, LPARAM)
{
	wchar_t className[128]{};
	GetClassNameW(hwnd,className,128);
	if (wcsstr(className,L"EDIT") || wcsstr(className,L"Edit") || wcsstr(className,L"COMBOBOX") || wcsstr(className,L"ComboBox")) return TRUE;
	wchar_t text[2048]{};
	GetWindowTextW(hwnd,text,2048);
	const auto translated = chineseLabel(text);
	if (translated != text) SetWindowTextW(hwnd,translated.c_str());
	return TRUE;
}
// Only active while a native plugin command runs on this UI thread. On modal
// activation, captions are translated without touching Edit values or combo data.
inline LRESULT CALLBACK chineseDialogHook(int code, WPARAM wParam, LPARAM lParam)
{
	if (code == HCBT_ACTIVATE)
	{
		const auto window = reinterpret_cast<HWND>(wParam);
		translateChild(window,0);
		EnumChildWindows(window,translateChild,0);
	}
	return CallNextHookEx(nullptr,code,wParam,lParam);
}
class ChinesePluginDialogs
{
	HHOOK _hook;
public:
	explicit ChinesePluginDialogs(bool enabled) : _hook(enabled ? SetWindowsHookExW(WH_CBT,chineseDialogHook,nullptr,GetCurrentThreadId()) : nullptr) {}
	~ChinesePluginDialogs() { if (_hook) UnhookWindowsHookEx(_hook); }
};
}
