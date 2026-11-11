// Npp Markdown Lite - GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cctype>
#include <cwctype>
#include <string>
#include <string_view>
#include <vector>

namespace MarkdownLite
{
inline bool isMarkdown(std::wstring_view name)
{
	const auto dot = name.find_last_of(L'.');
	if (dot == name.npos) return false;
	std::wstring ext(name.substr(dot));
	for (auto& c : ext) c = static_cast<wchar_t>(std::towlower(c));
	return ext == L".md" || ext == L".markdown" || ext == L".mdown" || ext == L".mkd" || ext == L".mdwn";
}
inline std::string_view trim(std::string_view s)
{
	const auto first = s.find_first_not_of(" \t\r\n");
	if (first == s.npos) return {};
	return s.substr(first, s.find_last_not_of(" \t\r\n") - first + 1);
}
struct Prefix
{
	std::string continuation;
	size_t content = 0;
	size_t task = std::string::npos;
	bool list = false;
	bool quote = false;
};
inline Prefix parsePrefix(std::string_view line)
{
	Prefix p;
	size_t i = 0;
	while (i < line.size() && (line[i] == ' ' || line[i] == '\t')) ++i;
	while (i < line.size() && line[i] == '>')
	{
		p.quote = true;
		++i;
		if (i < line.size() && line[i] == ' ') ++i;
	}
	const size_t marker = i;
	std::string next;
	if (i + 1 < line.size() && (line[i] == '-' || line[i] == '+' || line[i] == '*') && (line[i + 1] == ' ' || line[i + 1] == '\t'))
	{
		next = std::string(line.substr(0, i + 2));
		i += 2;
		p.list = true;
	}
	else
	{
		size_t end = i;
		while (end < line.size() && line[end] >= '0' && line[end] <= '9' && end - i < 9) ++end;
		if (end > i && end + 1 < line.size() && (line[end] == '.' || line[end] == ')') && (line[end + 1] == ' ' || line[end + 1] == '\t'))
		{
			unsigned long n = 0;
			for (size_t j = i; j < end; ++j) n = n * 10 + static_cast<unsigned long>(line[j] - '0');
			next = std::string(line.substr(0, i)) + std::to_string(n + 1) + line[end] + line[end + 1];
			i = end + 2;
			p.list = true;
		}
	}
	if (p.list)
	{
		while (i < line.size() && (line[i] == ' ' || line[i] == '\t')) { next += line[i]; ++i; }
		if (i + 3 <= line.size() && line[i] == '[' && (line[i + 1] == ' ' || line[i + 1] == 'x' || line[i + 1] == 'X') && line[i + 2] == ']' && (i + 3 == line.size() || line[i + 3] == ' ' || line[i + 3] == '\t'))
		{
			p.task = i + 1;
			next += "[ ] ";
			i += 3;
			while (i < line.size() && (line[i] == ' ' || line[i] == '\t')) ++i;
		}
		p.content = i;
		p.continuation = next;
	}
	else if (p.quote)
	{
		p.content = marker;
		p.continuation = std::string(line.substr(0, marker));
	}
	return p;
}
inline int headingLevel(std::string_view line)
{
	size_t i = 0;
	while (i < line.size() && line[i] == ' ' && i < 4) ++i;
	if (i > 3) return 0;
	const auto start = i;
	while (i < line.size() && line[i] == '#') ++i;
	const auto n = i - start;
	return n > 0 && n <= 6 && (i == line.size() || line[i] == ' ' || line[i] == '\t') ? static_cast<int>(n) : 0;
}
// A fence closes only with the same character, enough markers, and no trailing text.
struct Fence
{
	char marker = 0;
	size_t length = 0;
	bool consume(std::string_view line)
	{
		size_t indent = 0;
		while (indent < line.size() && line[indent] == ' ') ++indent;
		if (indent > 3 || indent == line.size()) return marker != 0;
		line.remove_prefix(indent);
		const char ch = line[0];
		size_t n = 0;
		while (n < line.size() && line[n] == ch) ++n;
		if ((ch == '`' || ch == '~') && n >= 3)
		{
			if (!marker && (ch != '`' || line.substr(n).find('`') == line.npos)) { marker = ch; length = n; return true; }
			if (marker == ch && n >= length && trim(line.substr(n)).empty()) { marker = 0; length = 0; return true; }
		}
		return marker != 0;
	}
};
inline std::vector<std::string> tableCells(std::string_view line)
{
	line = trim(line);
	if (line.empty()) return {};
	if (line.front() == '|') line.remove_prefix(1);
	std::vector<std::string> cells;
	size_t start = 0;
	size_t codeRun = 0;
	for (size_t i = 0; i < line.size(); ++i)
	{
		if (line[i] == '\\' && i + 1 < line.size()) { ++i; continue; }
		if (line[i] == '`')
		{
			size_t n = 1;
			while (i + n < line.size() && line[i + n] == '`') ++n;
			if (!codeRun) codeRun = n;
			else if (codeRun == n) codeRun = 0;
			i += n - 1;
			continue;
		}
		if (line[i] == '|' && !codeRun)
		{
			cells.emplace_back(trim(line.substr(start, i - start)));
			start = i + 1;
		}
	}
	if (start < line.size()) cells.emplace_back(trim(line.substr(start)));
	else if (line.back() != '|') cells.emplace_back();
	return cells;
}
// Display columns for monospace tables: common CJK/fullwidth/emoji are two cells.
inline size_t displayWidth(std::string_view s)
{
	size_t width = 0;
	for (size_t i = 0; i < s.size();)
	{
		const auto c = static_cast<unsigned char>(s[i++]);
		unsigned int cp = c;
		int extra = 0;
		if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; extra = 1; }
		else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; extra = 2; }
		else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; extra = 3; }
		for (int j = 0; j < extra && i < s.size(); ++j) cp = (cp << 6) | (static_cast<unsigned char>(s[i++]) & 0x3F);
		if ((cp >= 0x300 && cp <= 0x36F) || cp == 0x200D || (cp >= 0xFE00 && cp <= 0xFE0F)) continue;
		width += ((cp >= 0x1100 && cp <= 0x115F) || (cp >= 0x2E80 && cp <= 0xA4CF) || (cp >= 0xAC00 && cp <= 0xD7A3) || (cp >= 0xF900 && cp <= 0xFAFF) || (cp >= 0xFE10 && cp <= 0xFE6F) || (cp >= 0xFF01 && cp <= 0xFF60) || (cp >= 0x1F300 && cp <= 0x1FAFF) || (cp >= 0x20000 && cp <= 0x3FFFD)) ? 2U : 1U;
	}
	return width;
}
inline bool separatorCell(std::string_view cell)
{
	if (!cell.empty() && cell.front() == ':') cell.remove_prefix(1);
	if (!cell.empty() && cell.back() == ':') cell.remove_suffix(1);
	return cell.size() >= 3 && cell.find_first_not_of('-') == cell.npos;
}
inline std::vector<std::string> alignTable(const std::vector<std::string>& lines)
{
	if (lines.size() < 2) return {};
	std::vector<std::vector<std::string>> rows;
	for (const auto& line : lines) rows.push_back(tableCells(line));
	const auto cols = rows.front().size();
	if (cols == 0 || cols > 64 || rows[1].size() != cols) return {};
	for (const auto& cell : rows[1]) if (!separatorCell(cell)) return {};
	std::vector<size_t> widths(cols, 3);
	for (const auto& row : rows)
	{
		if (row.size() != cols) return {};
		for (size_t c = 0; c < cols; ++c) widths[c] = (std::max)(widths[c], displayWidth(row[c]));
	}
	std::vector<std::string> result;
	for (size_t r = 0; r < rows.size(); ++r)
	{
		std::string out = "|";
		for (size_t c = 0; c < cols; ++c)
		{
			std::string cell = rows[r][c];
			if (r == 1)
			{
				const bool left = cell.front() == ':';
				const bool right = cell.back() == ':';
				cell = (left ? ":" : "") + std::string(widths[c] - static_cast<size_t>(left) - static_cast<size_t>(right), '-') + (right ? ":" : "");
			}
			out += " " + cell + std::string(widths[c] - displayWidth(cell), ' ') + " |";
		}
		result.push_back(out);
	}
	return result;
}
}
