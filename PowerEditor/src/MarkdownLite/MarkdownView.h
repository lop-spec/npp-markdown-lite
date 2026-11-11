// Npp Markdown Lite - GPL-3.0-or-later
#pragma once
#include "MarkdownCore.h"
#include "MenuIds.h"
#include <windows.h>
#include <Scintilla.h>
#include <SciLexer.h>
#include <Lexilla.h>

namespace MarkdownLite
{
template<class View> inline std::string lineText(View& view, intptr_t line)
{
	const auto length = view.execute(SCI_LINELENGTH, line);
	if (length <= 0 || length > 1024 * 1024) return {};
	std::string text(static_cast<size_t>(length) + 1, '\0');
	view.execute(SCI_GETLINE, line, reinterpret_cast<LPARAM>(text.data()));
	text.resize(static_cast<size_t>(length));
	while (!text.empty() && (text.back() == '\r' || text.back() == '\n')) text.pop_back();
	return text;
}
template<class View> inline void replaceRange(View& view, intptr_t first, intptr_t last, const std::string& text)
{
	view.execute(SCI_SETTARGETRANGE, first, last);
	view.execute(SCI_REPLACETARGET, text.size(), reinterpret_cast<LPARAM>(text.c_str()));
}
template<class View> inline const char* eol(View& view)
{
	const auto mode = view.execute(SCI_GETEOLMODE);
	return mode == SC_EOL_CRLF ? "\r\n" : (mode == SC_EOL_CR ? "\r" : "\n");
}
template<class View> inline void applyStyles(View& view, bool dark, bool rich)
{
	view.execute(SCI_SETILEXER, 0, reinterpret_cast<LPARAM>(CreateLexer("markdown")));
	const COLORREF ink = dark ? RGB(214, 218, 225) : RGB(40, 46, 55);
	const COLORREF paper = dark ? RGB(30, 33, 39) : RGB(250, 250, 249);
	const COLORREF accent = dark ? RGB(131, 184, 245) : RGB(37, 88, 154);
	const COLORREF muted = dark ? RGB(158, 170, 185) : RGB(102, 116, 130);
	const COLORREF codePaper = dark ? RGB(40, 45, 53) : RGB(235, 238, 242);
	for (int style = 0; style <= SCE_MARKDOWN_FRONT_KEY; ++style)
	{
		view.execute(SCI_STYLESETFORE, style, ink);
		view.execute(SCI_STYLESETBACK, style, paper);
		view.execute(SCI_STYLESETFONT, style, reinterpret_cast<LPARAM>("Consolas"));
		view.execute(SCI_STYLESETSIZE, style, 12);
		view.execute(SCI_STYLESETBOLD, style, false);
		view.execute(SCI_STYLESETITALIC, style, false);
		view.execute(SCI_STYLESETUNDERLINE, style, false);
		view.execute(SCI_STYLESETEOLFILLED, style, false);
	}
	view.execute(SCI_STYLESETFORE, STYLE_DEFAULT, ink);
	view.execute(SCI_STYLESETBACK, STYLE_DEFAULT, paper);
	view.execute(SCI_SETEXTRAASCENT, rich ? 3 : 0);
	view.execute(SCI_SETEXTRADESCENT, rich ? 3 : 0);
	if (rich)
	{
		constexpr int sizes[] = { 19, 17, 15, 14, 13, 12 };
		for (int i = 0; i < 6; ++i)
		{
			view.execute(SCI_STYLESETFORE, SCE_MARKDOWN_HEADER1 + i, accent);
			view.execute(SCI_STYLESETSIZE, SCE_MARKDOWN_HEADER1 + i, sizes[i]);
			view.execute(SCI_STYLESETBOLD, SCE_MARKDOWN_HEADER1 + i, true);
		}
		for (int style : { SCE_MARKDOWN_STRONG1, SCE_MARKDOWN_STRONG2 }) view.execute(SCI_STYLESETBOLD, style, true);
		for (int style : { SCE_MARKDOWN_EM1, SCE_MARKDOWN_EM2, SCE_MARKDOWN_BLOCKQUOTE }) view.execute(SCI_STYLESETITALIC, style, true);
		for (int style : { SCE_MARKDOWN_CODE, SCE_MARKDOWN_CODE2, SCE_MARKDOWN_CODEBK, SCE_MARKDOWN_FRONT })
		{
			view.execute(SCI_STYLESETBACK, style, codePaper);
			view.execute(SCI_STYLESETSIZE, style, 12);
		}
		view.execute(SCI_STYLESETEOLFILLED, SCE_MARKDOWN_CODEBK, true);
		view.execute(SCI_STYLESETEOLFILLED, SCE_MARKDOWN_FRONT, true);
		for (int style : { SCE_MARKDOWN_PRECHAR, SCE_MARKDOWN_BLOCKQUOTE, SCE_MARKDOWN_HRULE, SCE_MARKDOWN_FRONT_MARK }) view.execute(SCI_STYLESETFORE, style, muted);
		for (int style : { SCE_MARKDOWN_LINK, SCE_MARKDOWN_ULIST_ITEM, SCE_MARKDOWN_OLIST_ITEM, SCE_MARKDOWN_FRONT_KEY }) view.execute(SCI_STYLESETFORE, style, accent);
		view.execute(SCI_STYLESETUNDERLINE, SCE_MARKDOWN_LINK, true);
		view.execute(SCI_STYLESETFORE, SCE_MARKDOWN_STRIKEOUT, muted);
	}
}
template<class View> inline bool inCode(View& view, intptr_t position)
{
	const auto style = view.execute(SCI_GETSTYLEAT, position);
	return style == SCE_MARKDOWN_CODE || style == SCE_MARKDOWN_CODE2 || style == SCE_MARKDOWN_CODEBK || style == SCE_MARKDOWN_FRONT;
}
template<class View> inline bool continueLine(View& view, int ch)
{
	if (view.execute(SCI_GETREADONLY) || view.execute(SCI_GETSELECTIONS) != 1) return false;
	if (ch != '\n' && !(ch == '\r' && view.execute(SCI_GETEOLMODE) == SC_EOL_CR)) return false;
	const auto pos = view.execute(SCI_GETCURRENTPOS);
	const auto line = view.execute(SCI_LINEFROMPOSITION, pos);
	if (line <= 0 || pos != view.execute(SCI_POSITIONFROMLINE, line)) return false;
	const std::string previous = lineText(view, line - 1);
	const auto start = view.execute(SCI_POSITIONFROMLINE, line - 1);
	if (previous.size() > 65536 || inCode(view, start)) return false;
	const auto p = parsePrefix(previous);
	if (!p.list && !p.quote) return false;
	// Splitting a populated line should not turn the remainder into a new list item.
	if (!trim(lineText(view, line)).empty()) return false;
	view.execute(SCI_BEGINUNDOACTION);
	if (trim(std::string_view(previous).substr(p.content)).empty())
	{
		// Empty item: remove its marker and the just-inserted newline. This leaves a
		// genuinely empty line (or exits one quote level), not a phantom list item.
		std::string parent;
		if (p.quote && !p.list)
		{
			parent = p.continuation;
			const auto last = parent.find_last_of('>');
			if (last != parent.npos) parent.erase(last);
		}
		else
		{
			const auto indent = previous.find_first_not_of(" \t");
			parent = previous.substr(0, indent == previous.npos ? previous.size() : indent);
		}
		replaceRange(view, start, pos, parent);
		view.execute(SCI_SETEMPTYSELECTION, start + static_cast<intptr_t>(parent.size()));
	}
	else
	{
		view.execute(SCI_REPLACESEL, 0, reinterpret_cast<LPARAM>(p.continuation.c_str()));
	}
	view.execute(SCI_ENDUNDOACTION);
	return true;
}
template<class View> inline bool wrapSelection(View& view, const std::string& before, const std::string& after)
{
	if (view.execute(SCI_GETREADONLY) || view.execute(SCI_GETSELECTIONS) != 1) return false;
	const auto first = view.execute(SCI_GETSELECTIONSTART);
	const auto last = view.execute(SCI_GETSELECTIONEND);
	if (last - first > 8 * 1024 * 1024) return false;
	std::string selected(static_cast<size_t>(last - first) + 1, '\0');
	view.execute(SCI_GETSELTEXT, 0, reinterpret_cast<LPARAM>(selected.data()));
	selected.resize(static_cast<size_t>(last - first));
	view.execute(SCI_BEGINUNDOACTION);
	replaceRange(view, first, last, before + selected + after);
	view.execute(SCI_SETSEL, first + static_cast<intptr_t>(before.size()), last + static_cast<intptr_t>(before.size()));
	view.execute(SCI_ENDUNDOACTION);
	return true;
}
template<class View> inline void toggleTask(View& view)
{
	if (view.execute(SCI_GETREADONLY)) return;
	auto firstLine = view.execute(SCI_LINEFROMPOSITION, view.execute(SCI_GETSELECTIONSTART));
	auto end = view.execute(SCI_GETSELECTIONEND);
	if (end > view.execute(SCI_GETSELECTIONSTART) && end == view.execute(SCI_POSITIONFROMLINE, view.execute(SCI_LINEFROMPOSITION, end))) --end;
	const auto lastLine = view.execute(SCI_LINEFROMPOSITION, end);
	if (lastLine - firstLine > 10000) return;
	view.execute(SCI_BEGINUNDOACTION);
	for (auto line = lastLine; line >= firstLine; --line)
	{
		const auto start = view.execute(SCI_POSITIONFROMLINE, line);
		if (inCode(view, start)) continue;
		auto text = lineText(view, line);
		const auto p = parsePrefix(text);
		if (p.task != std::string::npos) replaceRange(view, start + static_cast<intptr_t>(p.task), start + static_cast<intptr_t>(p.task + 1), text[p.task] == ' ' ? "x" : " ");
		else if (p.list) replaceRange(view, start + static_cast<intptr_t>(p.content), start + static_cast<intptr_t>(p.content), "[ ] ");
		else
		{
			const auto indent = text.find_first_not_of(" \t");
			const auto at = indent == text.npos ? text.size() : indent;
			replaceRange(view, start + static_cast<intptr_t>(at), start + static_cast<intptr_t>(at), "- [ ] ");
		}
	}
	view.execute(SCI_ENDUNDOACTION);
}
template<class View> inline bool formatTable(View& view)
{
	if (view.execute(SCI_GETREADONLY) || view.execute(SCI_GETCODEPAGE) != SC_CP_UTF8) return false;
	const auto current = view.execute(SCI_LINEFROMPOSITION, view.execute(SCI_GETCURRENTPOS));
	if (inCode(view, view.execute(SCI_POSITIONFROMLINE, current))) return false;
	auto candidate = [&](intptr_t n) { const auto s = lineText(view, n); return !trim(s).empty() && s.find('|') != s.npos && s.size() < 16384; };
	if (!candidate(current)) return false;
	auto first = current;
	auto last = current;
	while (first > 0 && current - first < 1000 && candidate(first - 1)) --first;
	const auto count = view.execute(SCI_GETLINECOUNT);
	while (last + 1 < count && last - first < 1000 && candidate(last + 1)) ++last;
	if (last - first >= 1000) return false;
	std::vector<std::string> lines;
	for (auto n = first; n <= last; ++n) lines.push_back(lineText(view, n));
	const auto formatted = alignTable(lines);
	if (formatted.empty()) return false;
	std::string text;
	for (size_t i = 0; i < formatted.size(); ++i) { if (i) text += eol(view); text += formatted[i]; }
	const auto start = view.execute(SCI_POSITIONFROMLINE, first);
	const auto end = view.execute(SCI_GETLINEENDPOSITION, last);
	view.execute(SCI_BEGINUNDOACTION);
	replaceRange(view, start, end, text);
	view.execute(SCI_SETEMPTYSELECTION, start);
	view.execute(SCI_ENDUNDOACTION);
	return true;
}
template<class View> inline void jumpHeading(View& view, bool forward)
{
	const auto current = view.execute(SCI_LINEFROMPOSITION, view.execute(SCI_GETCURRENTPOS));
	const auto count = view.execute(SCI_GETLINECOUNT);
	Fence fence;
	intptr_t target = -1;
	for (intptr_t n = 0; n < count; ++n)
	{
		const auto text = lineText(view, n);
		if (fence.consume(text) || !headingLevel(text)) continue;
		if (forward && n > current) { target = n; break; }
		if (!forward && n < current) target = n;
	}
	if (target >= 0) { view.execute(SCI_ENSUREVISIBLE, target); view.execute(SCI_GOTOLINE, target); }
}
template<class View> inline bool editCommand(View& view, int id)
{
	if (id < IDM_MD_BOLD || id > IDM_MD_NEXT) return false;
	if (id == IDM_MD_PREV || id == IDM_MD_NEXT) { jumpHeading(view, id == IDM_MD_NEXT); return true; }
	if (view.execute(SCI_GETREADONLY) || view.execute(SCI_GETSELECTIONS) != 1) return true;
	switch (id)
	{
		case IDM_MD_BOLD: wrapSelection(view, "**", "**"); break;
		case IDM_MD_ITALIC: wrapSelection(view, "*", "*"); break;
		case IDM_MD_CODE: wrapSelection(view, "`", "`"); break;
		case IDM_MD_LINK: wrapSelection(view, "[", "](https://)"); break;
		case IDM_MD_FENCE:
		{
			// Four markers safely enclose the common triple-backtick snippets.
			// Grow beyond any run in the selection rather than corrupting pasted code.
			const auto length = view.execute(SCI_GETSELTEXT);
			if (length > 8 * 1024 * 1024) break;
			std::string selected(static_cast<size_t>(length), '\0');
			view.execute(SCI_GETSELTEXT, 0, reinterpret_cast<LPARAM>(selected.data()));
			size_t run = 0, longest = 2;
			for (char c : selected) { run = c == '`' ? run + 1 : 0; longest = (std::max)(longest, run); }
			const std::string fence(longest + 1, '`');
			wrapSelection(view, fence + eol(view), std::string(eol(view)) + fence);
			break;
		}
		case IDM_MD_TASK: toggleTask(view); break;
		case IDM_MD_TABLE:
			if (!formatTable(view)) MessageBeep(MB_ICONINFORMATION);
			break;
	}
	return true;
}
}
