// Npp Lite - GPL-3.0-or-later
#define LITE_BUTTON(command, icon, disabled, bitmap) \
    { command, IDI_##icon##_ICON, IDI_##disabled##_ICON, IDI_##icon##_ICON2, IDI_##disabled##_ICON2, IDI_##icon##_ICON_DM, IDI_##disabled##_ICON_DM, IDI_##icon##_ICON_DM2, IDI_##disabled##_ICON_DM2, bitmap }
static constexpr ToolBarButtonUnit toolBarIcons[]{
    LITE_BUTTON(IDM_FILE_NEW, NEW, NEW, IDR_FILENEW),
    LITE_BUTTON(IDM_FILE_OPEN, OPEN, OPEN, IDR_FILEOPEN),
    LITE_BUTTON(IDM_FILE_SAVE, SAVE, SAVE_DISABLE, IDR_FILESAVE),
    { 0, -1, -1, -1, -1, -1, -1, -1, -1, -1 },
    LITE_BUTTON(IDM_EDIT_UNDO, UNDO, UNDO_DISABLE, IDR_UNDO),
    LITE_BUTTON(IDM_EDIT_REDO, REDO, REDO_DISABLE, IDR_REDO),
    { 0, -1, -1, -1, -1, -1, -1, -1, -1, -1 },
    LITE_BUTTON(IDM_SEARCH_FIND, FIND, FIND, IDR_FIND),
    LITE_BUTTON(IDM_SEARCH_REPLACE, REPLACE, REPLACE, IDR_REPLACE),
    LITE_BUTTON(IDM_VIEW_WRAP, VIEW_WRAP, VIEW_WRAP, IDR_WRAP)
};
#undef LITE_BUTTON
