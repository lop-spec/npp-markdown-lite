# Npp Markdown Lite

**Notepad++ 的非官方精简二开：原生编辑、少按钮、面向 Markdown 的源码排版。**

[下载 Windows x64 单 EXE](https://github.com/lop-spec/npp-markdown-lite/releases/latest) · [构建与测试](https://github.com/lop-spec/npp-markdown-lite/actions) · [设计边界](docs/design.md)

基于官方 [Notepad++ master 67eca42](https://github.com/notepad-plus-plus/notepad-plus-plus/commit/67eca422e60a169801a9aaeb19e285b7f27cfd13)（8.9.9 开发树，2026-11-10）。保留上游 Win32、Scintilla、Lexilla、Boost.Regex 与原生插件架构，不是 Electron、WebView 或从零仿写。仓库导入完整源代码快照，之后的修改可直接对照首个源码提交。

## 保留什么

- 原生编辑框、标签栏、原生查找替换与正则、列编辑、多选区、撤销重做、分屏、编码和换行格式。
- 常用语言高亮、首选项、样式和快捷键设置。
- x64 Notepad++ 原生插件加载、插件菜单、插件按钮、通知与 Scintilla 消息接口。

主工具栏缩为 **12 个按钮**，菜单按文件、编辑、搜索、视图、编码、常用语言、设置、Markdown、插件、窗口、帮助组织。宏录制/播放、外部运行和哈希工具的主命令代码不参与编译；不携带更新器、预装插件、补全数据库或语言包。为保留原生编辑与插件接口，共用底层设施仍沿用上游，并非把整个编辑器改成只有记事本功能。

## Markdown 怎么用

打开 `.md`、`.markdown`、`.mdown`、`.mkd`、`.mdwn` 即启用；未保存文档可用「文件 → 新建 Markdown」或「语言 → Markdown 模式」。

- 完整标题正文的层级字号、原生标题折叠、粗体、斜体、链接、整行引用、行内代码和围栏代码块背景；适配浅色与深色模式。
- 使用原生等宽字体和 DirectWrite 支持的编辑器绘制路径；自动软换行、增加行距。切到其他文件恢复原来的换行和行距。
- Enter 续写列表、编号、任务和引用，空项目退出；围栏代码中不自动补列表。
- 「Markdown」菜单提供粗体、斜体、代码、链接、围栏、任务切换、表格对齐、前后标题跳转。可在原生快捷键设置中自行绑定，不覆盖已有编辑快捷键。
- 「增强排版」可以切回统一字号；源文始终可见，不把光标前后的字符偷偷隐藏。

**显示本身不改文件，也不改剪贴板。** 只有明确执行编辑命令才修改源码，支持撤销。表格对齐仅对当前标准管道表格执行，保留转义管道与行内代码；中文按常见等宽列宽估算。不是 HTML 渲染器：不加载图片，不执行 HTML/脚本，不支持完整 CommonMark/GFM 排版；代码块保留原文，不做嵌套语言解析，复杂 emoji 的显示宽度取决于系统字体。

## 单 EXE 与插件

下载 `npp-markdown-lite.exe` 后直接运行，无安装器、无自解压壳、无第三方运行时。首次运行会将内嵌的默认 XML 写入独立的 `%APPDATA%\NppMarkdownLite`，以后只创建缺失文件，不覆盖自定义设置。窗口类与实例锁独立，不接管官方 Notepad++ 进程或配置。支持上游 `-settingsDir=` 与便携设置机制。

第三方 **x64** 插件可以通过「设置 → 导入插件」导入，或放在 EXE 同目录 `plugins\插件名\插件名.dll`，重启后加载。仅加载自己信任的 DLL；插件是在本机执行的原生程序。没有捆绑在线插件商店或下载更新器。测试探针覆盖初始化、启动通知、菜单注册和原生编辑控件调用；另外使用官方 8.9.9 的 mimeTools 验证实际 Base64 编解码。不承诺所有第三方插件均兼容；硬编码官方窗口类名或完整菜单位置的插件需要适配。

## 构建与验证

GitHub Actions 使用 MSVC Release x64 和静态 CRT 构建发行物。**未压壳 EXE 必须小于 10,000,000 字节**，超过即失败，不以压缩包体积冒充。

开发构建沿用上游 `BUILD.md`。测试入口：

```bat
msbuild PowerEditor\visual.net\notepadPlus.sln /m /p:Configuration=Release /p:Platform=x64
tests\build-probes.cmd
python tests\windows-smoke.py PowerEditor\bin64\notepad++.exe test-output
```

集成测试会启动真实 GUI；在个人工作电脑上应运行于私有隐藏桌面。测试探针 DLL **不随发行物分发**。发行附带源码提交、体积、SHA256、构建链接与测试结果。

## 许可证与归属

GPL-3.0-or-later，见 [LICENSE](LICENSE)。Notepad++ 原作者 Don Ho 及各上游贡献者的版权和许可证保持不变。Scintilla、Lexilla、Boost 等组件沿用各自许可证。项目为独立、非官方发行，不代表或冒充 Notepad++ 官方。

新增代码与集成由 AI 编码助手（OpenAI GPT，通过 Pi）辅助完成，源码和测试均公开。
