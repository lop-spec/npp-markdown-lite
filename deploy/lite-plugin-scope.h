// Npp Lite's portable plugin-only policy for WinGUp (LGPL-3.0-or-later).
// The helper cannot update the editor or accept elevated execution. It operates
// only on the adjacent npp-lite.exe and the adjacent plugins tree.
static bool litePluginScope(const ParamVector& args, bool unzip, bool clean, bool move)
{
	if ((!unzip && !clean && !move) || (move && (unzip || clean)) || args.size() < (move ? 4u : 3u))
		return false;
	HANDLE token = nullptr;
	TOKEN_ELEVATION elevation{};
	DWORD bytes = 0;
	if (!::OpenProcessToken(::GetCurrentProcess(), TOKEN_QUERY, &token))
		return false;
	const bool standardUser = ::GetTokenInformation(token, TokenElevation, &elevation, sizeof(elevation), &bytes) && !elevation.TokenIsElevated;
	::CloseHandle(token);
	if (!standardUser)
		return false;

	wchar_t exe[MAX_PATH]{};
	const DWORD length = ::GetModuleFileNameW(nullptr, exe, MAX_PATH);
	if (!length || length >= MAX_PATH || !::PathRemoveFileSpecW(exe) || !::PathRemoveFileSpecW(exe))
		return false;
	const wstring base(exe);
	const wstring host = base + L"\\npp-lite.exe";
	const wstring active = base + L"\\plugins";
	const wstring disabled = active + L"\\disabled";
	const auto equalPath = [](const wstring& a, const wstring& b) { return _wcsicmp(a.c_str(), b.c_str()) == 0; };
	const auto ordinary = [](const wstring& path, bool allowMissing) {
		const DWORD attr = ::GetFileAttributesW(path.c_str());
		return attr == INVALID_FILE_ATTRIBUTES ? allowMissing && ::GetLastError() == ERROR_FILE_NOT_FOUND : !(attr & FILE_ATTRIBUTE_REPARSE_POINT);
	};
	if (!equalPath(args[0], host) || !ordinary(host, false) || !ordinary(active, false))
		return false;
	if (move)
	{
		if (!ordinary(disabled, false) || !((equalPath(args[1], active) && equalPath(args[2], disabled)) || (equalPath(args[1], disabled) && equalPath(args[2], active))))
			return false;
	}
	else if (!equalPath(args[1], active) && (unzip || !equalPath(args[1], disabled) || !ordinary(disabled, false)))
		return false;
	for (size_t i = move ? 3 : 2; i < args.size(); ++i)
	{
		wstring name = args[i];
		if (unzip)
		{
			const auto hash = name.rfind(L' ');
			if (hash == wstring::npos || name.size() - hash != 65 || name.find_first_not_of(L"0123456789abcdefABCDEF", hash + 1) != wstring::npos)
				return false;
			const auto url = hash ? name.rfind(L' ', hash - 1) : wstring::npos;
			if (url == wstring::npos || name.compare(url + 1, 8, L"https://") != 0)
				return false;
			name.resize(url);
		}
		if (name.empty() || name.front() == L'.' || name.back() == L'.' || name.back() == L' ' ||
			name.find_first_of(L"\\/:*?\"<>|\r\n\t") != wstring::npos || equalPath(name, L"config") || equalPath(name, L"disabled") ||
			!ordinary(args[1] + L"\\" + name, true) || (move && !ordinary(args[2] + L"\\" + name, true)))
			return false;
	}
	return true;
}
