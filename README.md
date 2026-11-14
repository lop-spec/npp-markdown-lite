# Npp Lite

Notepad++ 原生精简二开。保持原生编辑框、标签栏、查找替换、正则、列选择、多选区、分屏与 x64 插件接口，Markdown 展示只使用官方 **Markdown Panel 0.9.3** 插件。

[下载便携包（已装插件）](https://github.com/lop-spec/npp-markdown-lite/releases/latest) · [裁剪清单](docs/removed-commands.md) · [构建验证](https://github.com/lop-spec/npp-markdown-lite/actions)

## 1.1.0

- 删除上一版全部自写 Markdown 文件、命令、词法器、标题字号、额外行距、表格对齐、智能列表、任务操作与配套测试。编辑区回到官方原生紧凑显示。
- 相对 1.0.0 **新增裁剪80个原生命令**：相关主命令处理代码编译排除，默认快捷键不再注册；即使发送旧命令ID也不能触发。按命令计数，包含同一功能的不同模式，不宣称80种独立能力。详见清单。
- 主工具栏从12键减到8键：新建、打开、保存、撤销、重做、查找、替换、换行。剪切、复制、粘贴、全部保存仍可用菜单和快捷键操作。
- 保留原生 .NET 插件加载和停靠接口。Markdown Panel 为独立官方 DLL，不把插件实现复制进编辑器。

## 使用

解压便携包，双击 `npp-lite.exe`。里面已安装完整的 `plugins/NppMarkdownPanel`。打开 `.md` 后插件自动显示渲染面板；也可在「插件 → MarkdownPanel → Toggle Markdown Panel」开关。源码始终在原生编辑区可编辑，右侧是插件渲染，不是所见即所得直编。

必须连同 `plugins` 目录一起传输；只复制主 EXE 不会携带插件。主 EXE 静态 CRT、未压壳，小于10,000,000字节；插件及系统运行时不计入主 EXE 大小。

插件使用 **.NET Framework 4.7.2+** 和 **WebView2 Runtime**，它们是系统依赖，不伪装成无运行时。普通 Markdown、表格与本地样式可离线显示；远程图片和插件默认的 Mermaid CDN 仍需要网络。插件支持点击复选框回写源码，因此不要把预览面板称为绝不修改文档。

没有添加图片粘贴、自写富文本、自动上传、预处理器或后处理器。保留插件原样，下载来源、版本和SHA256固定在 `deploy/plugin-lock.json`。

## 设置隔离

便携包含 `doLocalConf.xml`，设置保存在当前解压目录；不含该标记的裸 EXE 使用 `%APPDATA%/NppLite`。首次启动从EXE内嵌资源写入缺失的默认XML，不覆盖已有设置。不覆盖官方 Notepad++ 或旧 NppMarkdownLite 的配置。独立窗口类 `NppLite`，可并行运行。

## 构建与验证

基于官方 Notepad++ 8.9.9 开发树 `67eca422e60a169801a9aaeb19e285b7f27cfd13`，保留完整源码快照和上游版权。

发行文件由 GitHub Actions 的 MSVC Release x64 构建；原生测试覆盖基础编辑、矩形选择、80项退役命令、插件ABI，以及官方 Markdown Panel 的真实 WebView2 渲染和编辑后更新。超出10MB或验证失败不发版。测试探针DLL不随便携包分发。

```bat
msbuild PowerEditor\visual.net\notepadPlus.sln /m /p:Configuration=Release /p:Platform=x64
tests\build-probes.cmd
powershell -File deploy\install-panel.ps1 -EditorDirectory PowerEditor\bin64
python tests\windows-smoke.py PowerEditor\bin64\npp-lite.exe test-output
```

真实GUI测试只在CI或私有隐藏桌面运行，避免干扰日常窗口。发行附构建提交、体积、SHA256、裁剪清单和测试证据。

## 许可证

编辑器 GPL-3.0-or-later，保留 Don Ho 与上游贡献者版权及各组件许可证；非官方发行，不代表 Notepad++ 官方。Markdown Panel 为 Mohzy83 的 MIT 项目，便携包内保留完整官方许可证及依赖。新增修改由OpenAI GPT通过Pi辅助完成。
