#include <windows.h>
#include "../PowerEditor/src/MarkdownLite/MarkdownLexer.h"
int main()
{
    auto* lexer = MarkdownLite::createLexer();
    if (lexer) lexer->Release();
}
