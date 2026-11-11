#include <windows.h>
#include <Scintilla.h>
#include "../PowerEditor/src/MISC/PluginsManager/PluginInterface.h"
#include "../PowerEditor/src/MISC/PluginsManager/Notepad_plus_msgs.h"
static NppData app{};
static FuncItem commands[1]{};
static void probeCommand()
{
	const char text[] = "plugin-ok";
	SendMessageW(app._scintillaMainHandle, SCI_ADDTEXT, sizeof(text) - 1, reinterpret_cast<LPARAM>(text));
}
extern "C" __declspec(dllexport) void setInfo(NppData data) { app = data; }
extern "C" __declspec(dllexport) const wchar_t* getName() { return L"Lite ABI Probe"; }
extern "C" __declspec(dllexport) FuncItem* getFuncsArray(int* count)
{
	*count = 1;
	lstrcpyW(commands[0]._itemName, L"Probe command");
	commands[0]._pFunc = probeCommand;
	return commands;
}
extern "C" __declspec(dllexport) void beNotified(SCNotification* notification)
{
	if (notification->nmhdr.code == NPPN_READY) SetPropW(app._nppHandle, L"LitePluginReady", reinterpret_cast<HANDLE>(1));
}
extern "C" __declspec(dllexport) LRESULT messageProc(UINT, WPARAM, LPARAM) { return TRUE; }
extern "C" __declspec(dllexport) BOOL isUnicode() { return TRUE; }
BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID) { return TRUE; }
