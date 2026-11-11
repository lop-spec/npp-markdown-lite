// Npp Markdown Lite - GPL-3.0-or-later
#pragma once
#include "MarkdownCore.h"
#include <Scintilla.h>
#include <ILexer.h>
#include <Lexilla.h>
#include <SciLexer.h>

namespace MarkdownLite
{
inline constexpr int fenceStyle = 25;
// The upstream Markdown lexer supplies inline markup and front matter. This
// application-side adapter adds block structure without patching either library.
class MarkdownLexer final : public Scintilla::ILexer5
{
	Scintilla::ILexer5* _inner;
	static int stateFor(const Fence& fence, int heading)
	{
		const auto length = (std::min)(fence.length, size_t{65535});
		return static_cast<int>((length << 2) | (fence.marker == '`' ? 1U : fence.marker == '~' ? 2U : 0U)) | (heading << 20);
	}
	static std::string getLine(Scintilla::IDocument* doc, Sci_Position line)
	{
		const auto begin = doc->LineStart(line);
		const auto length = doc->LineEnd(line) - begin;
		if (length <= 0 || length > 1024 * 1024) return {};
		std::string text(static_cast<size_t>(length), '\0');
		doc->GetCharRange(text.data(), begin, length);
		return text;
	}
public:
	explicit MarkdownLexer(Scintilla::ILexer5* inner) : _inner(inner) {}
	~MarkdownLexer() { _inner->Release(); }
	int SCI_METHOD Version() const override { return Scintilla::lvRelease5; }
	void SCI_METHOD Release() override { delete this; }
	const char* SCI_METHOD PropertyNames() override { return _inner->PropertyNames(); }
	int SCI_METHOD PropertyType(const char* name) override { return _inner->PropertyType(name); }
	const char* SCI_METHOD DescribeProperty(const char* name) override { return _inner->DescribeProperty(name); }
	Sci_Position SCI_METHOD PropertySet(const char* key, const char* value) override { return _inner->PropertySet(key, value); }
	const char* SCI_METHOD DescribeWordListSets() override { return _inner->DescribeWordListSets(); }
	Sci_Position SCI_METHOD WordListSet(int n, const char* words) override { return _inner->WordListSet(n, words); }
	void SCI_METHOD Lex(Sci_PositionU start, Sci_Position length, int initialStyle, Scintilla::IDocument* doc) override
	{
		const auto total = doc->Length();
		const auto first = doc->LineFromPosition(static_cast<Sci_Position>(start));
		const auto requestedLast = doc->LineFromPosition((std::min)(total, static_cast<Sci_Position>(start) + length));
		const auto lastDocumentLine = doc->LineFromPosition(total);
		const auto begin = doc->LineStart(first);
		const auto requestedEnd = requestedLast < lastDocumentLine ? doc->LineStart(requestedLast + 1) : total;
		_inner->Lex(static_cast<Sci_PositionU>(begin), requestedEnd - begin, initialStyle == fenceStyle ? 0 : initialStyle, doc);
		const int previous = first > 0 ? doc->GetLineState(first - 1) : 0;
		Fence fence;
		fence.marker = (previous & 3) == 1 ? '`' : (previous & 3) == 2 ? '~' : 0;
		fence.length = static_cast<size_t>((previous >> 2) & 65535);
		int heading = (previous >> 20) & 7;
		struct Block { Sci_Position line; bool code; int heading; bool quote; };
		std::vector<Block> blocks;
		for (auto line = first; line <= lastDocumentLine; ++line)
		{
			const auto text = getLine(doc, line);
			const auto oldState = doc->GetLineState(line);
			const bool frontMatter = doc->StyleAt(doc->LineStart(line)) >= SCE_MARKDOWN_FRONT_MARK && doc->StyleAt(doc->LineStart(line)) <= SCE_MARKDOWN_FRONT_KEY;
			const bool code = !frontMatter && fence.consume(text);
			const int level = code || frontMatter ? 0 : headingLevel(text);
			if (level) heading = level;
			const auto trimmed = trim(text);
			blocks.push_back({line, code, level, !code && !frontMatter && !trimmed.empty() && trimmed.front() == '>'});
			const int state = stateFor(fence, heading);
			doc->SetLineState(line, state);
			if (line >= requestedLast && state == oldState) break;
		}
		if (blocks.empty()) return;
		const auto last = blocks.back().line;
		const auto end = last < lastDocumentLine ? doc->LineStart(last + 1) : total;
		if (end > requestedEnd) _inner->Lex(static_cast<Sci_PositionU>(requestedEnd), end - requestedEnd, doc->StyleAt(requestedEnd > 0 ? requestedEnd - 1 : 0), doc);
		bool previousCode = first > 0 && (previous & 3) != 0;
		for (const auto& block : blocks)
		{
			const auto at = doc->LineStart(block.line);
			const auto next = block.line < lastDocumentLine ? doc->LineStart(block.line + 1) : total;
			// End a native inline-code span at a block boundary as well. A variable
			// length Markdown fence must never turn the following prose into code.
			if (previousCode && !block.code) _inner->Lex(static_cast<Sci_PositionU>(at), end - at, 0, doc);
			if (block.code || block.heading || block.quote)
			{
				const int style = block.code ? fenceStyle : block.heading ? SCE_MARKDOWN_HEADER1 + block.heading - 1 : SCE_MARKDOWN_BLOCKQUOTE;
				doc->StartStyling(at);
				doc->SetStyleFor(next - at, static_cast<char>(style));
			}
			const int currentHeading = (doc->GetLineState(block.line) >> 20) & 7;
			const int fold = (SC_FOLDLEVELBASE + (block.heading ? block.heading - 1 : currentHeading)) | (block.heading ? SC_FOLDLEVELHEADERFLAG : 0);
			doc->SetLevel(block.line, fold);
			previousCode = block.code;
		}
	}
	void SCI_METHOD Fold(Sci_PositionU, Sci_Position, int, Scintilla::IDocument*) override {}
	void* SCI_METHOD PrivateCall(int op, void* p) override { return _inner->PrivateCall(op, p); }
	int SCI_METHOD LineEndTypesSupported() override { return _inner->LineEndTypesSupported(); }
	int SCI_METHOD AllocateSubStyles(int base, int count) override { return _inner->AllocateSubStyles(base, count); }
	int SCI_METHOD SubStylesStart(int base) override { return _inner->SubStylesStart(base); }
	int SCI_METHOD SubStylesLength(int base) override { return _inner->SubStylesLength(base); }
	int SCI_METHOD StyleFromSubStyle(int style) override { return _inner->StyleFromSubStyle(style); }
	int SCI_METHOD PrimaryStyleFromStyle(int style) override { return _inner->PrimaryStyleFromStyle(style); }
	void SCI_METHOD FreeSubStyles() override { _inner->FreeSubStyles(); }
	void SCI_METHOD SetIdentifiers(int style, const char* ids) override { _inner->SetIdentifiers(style, ids); }
	int SCI_METHOD DistanceToSecondaryStyles() override { return _inner->DistanceToSecondaryStyles(); }
	const char* SCI_METHOD GetSubStyleBases() override { return _inner->GetSubStyleBases(); }
	int SCI_METHOD NamedStyles() override { return fenceStyle + 1; }
	const char* SCI_METHOD NameOfStyle(int style) override { return style == fenceStyle ? "MARKDOWN_FENCE" : _inner->NameOfStyle(style); }
	const char* SCI_METHOD TagsOfStyle(int style) override { return style == fenceStyle ? "literal" : _inner->TagsOfStyle(style); }
	const char* SCI_METHOD DescriptionOfStyle(int style) override { return style == fenceStyle ? "Fenced code block" : _inner->DescriptionOfStyle(style); }
	const char* SCI_METHOD GetName() override { return "markdown"; }
	int SCI_METHOD GetIdentifier() override { return SCLEX_MARKDOWN; }
	const char* SCI_METHOD PropertyGet(const char* key) override { return _inner->PropertyGet(key); }
};
inline Scintilla::ILexer5* createLexer()
{
	auto* inner = CreateLexer("markdown");
	return inner ? new MarkdownLexer(inner) : nullptr;
}
}
