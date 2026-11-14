// Npp Lite - GPL-3.0-or-later
#pragma once
#include <cstddef>
namespace Lite
{
// Original upstream page indices remain stable for plugin/internal links.
inline constexpr int settingsPageOrder[] = {0, 2, 3, 5, 6, 7, 8, 9, 12, 15, 16, 17, 20, 23};
inline bool isSettingsPageRetained(size_t original)
{
	for (const int page : settingsPageOrder) if (static_cast<size_t>(page) == original) return true;
	return false;
}
inline int settingsPageIndex(size_t original)
{
	for (size_t i = 0; i < sizeof(settingsPageOrder) / sizeof(settingsPageOrder[0]); ++i)
		if (static_cast<size_t>(settingsPageOrder[i]) == original) return static_cast<int>(i);
	return -1;
}
}
