#include "../PowerEditor/src/MarkdownLite/MarkdownCore.h"
#include <cstdlib>
#include <iostream>
using namespace MarkdownLite;
int main()
{
	int checks = 0;
	auto check = [&](bool ok, const char* name) { ++checks; if (!ok) { std::cerr << "FAIL: " << name << '\n'; std::exit(1); } };
	check(isMarkdown(L"readme.MD"), "case insensitive extension");
	check(isMarkdown(L"notes.markdown"), "long extension");
	check(!isMarkdown(L"notes.md.txt"), "not suffix substring");
	check(parsePrefix("- hello").continuation == "- ", "unordered");
	check(parsePrefix("  + hello").continuation == "  + ", "nested unordered");
	check(parsePrefix("9. hello").continuation == "10. ", "ordered carries");
	check(parsePrefix("999999999) hello").continuation == "1000000000) ", "large ordered");
	check(!parsePrefix("1234567890. hello").list, "reject invalid 10 digit marker");
	check(parsePrefix("- [x] done").continuation == "- [ ] ", "reset checked task");
	check(parsePrefix("- [X] done").task == 3, "uppercase task");
	check(parsePrefix("- [ ]").content == 5, "empty task");
	check(parsePrefix("> > quote").continuation == "> > ", "nested quote");
	check(parsePrefix("> 3. hi").continuation == "> 4. ", "ordered in quote");
	check(!parsePrefix("---").list, "horizontal rule not list");
	check(!parsePrefix("*emphasis*").list, "emphasis not list");
	check(headingLevel("  ### Heading") == 3, "heading indent");
	check(!headingLevel("    # Code"), "indented code not heading");
	check(!headingLevel("####### text"), "heading at most six");
	check(!headingLevel("#hashtag"), "hashtag not heading");
	Fence fence;
	check(fence.consume("````md"), "open four fence");
	check(fence.consume("```" ) && fence.marker, "short fence stays open");
	check(fence.consume("~~~~") && fence.marker, "other fence stays open");
	check(fence.consume("```` trailing") && fence.marker, "closing fence no trailing text");
	check(fence.consume("````") && !fence.marker, "close same fence");
	check(!fence.consume("    ```"), "indented fence not opener");
	check(displayWidth("中文abc") == 7, "CJK display columns");
	check(displayWidth("e\xCC\x81") == 1, "combining accent");
	check(tableCells("| a\\|b | `c|d` | e |").size() == 3, "escaped and code pipes");
	check(tableCells("| ``a`|b`` | x |").size() == 2, "code runs");
	const std::vector<std::string> table = { "| 名称 | 值 |", "| :--- | ---: |", "| abc | 中文 |" };
	const auto aligned = alignTable(table);
	check(aligned.size() == table.size(), "format table");
	check(alignTable(aligned) == aligned, "idempotent format");
	check(tableCells(aligned[2])[1] == "中文", "format preserves cell content");
	check(alignTable({"| a | b |", "| x | y |"}).empty(), "reject no separator");
	check(alignTable({"| a | b |", "| --- | --- |", "| x |"}).empty(), "reject ragged table");
	std::cout << "PASS " << checks << " Markdown core checks\n";
}
