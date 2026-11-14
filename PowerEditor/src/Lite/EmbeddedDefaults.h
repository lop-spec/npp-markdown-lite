// Npp Lite - GPL-3.0-or-later
#pragma once
#include <windows.h>
#include <string>
namespace Lite
{
inline bool seedDefaults(const std::wstring& directory)
{
	struct DefaultFile { int id; const wchar_t* name; };
	constexpr DefaultFile files[] = { { 9101, L"langs.xml" }, { 9102, L"stylers.xml" }, { 9103, L"config.xml" }, { 9104, L"nativeLang.xml" }, { 9105, L"userDefineLang.xml" } };
	for (const auto& file : files)
	{
		const auto path = directory + L"\\" + file.name;
		const HANDLE output = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
		if (output == INVALID_HANDLE_VALUE)
		{
			if (GetLastError() == ERROR_FILE_EXISTS || GetLastError() == ERROR_ALREADY_EXISTS) continue;
			return false;
		}
		const auto instance = GetModuleHandleW(nullptr);
		const auto resource = FindResourceW(instance, MAKEINTRESOURCEW(file.id), RT_RCDATA);
		const DWORD size = resource ? SizeofResource(instance, resource) : 0;
		const auto memory = resource ? LoadResource(instance, resource) : nullptr;
		const auto data = memory ? LockResource(memory) : nullptr;
		DWORD written = 0;
		const bool ok = data && size && WriteFile(output, data, size, &written, nullptr) && written == size;
		CloseHandle(output);
		if (!ok) { DeleteFileW(path.c_str()); return false; }
	}
	return true;
}
}
