@echo off
setlocal
cd /d "%~dp0.."
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSROOT=%%i"
if not defined VSROOT exit /b 2
call "%VSROOT%\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 3
if not exist test-output mkdir test-output
cl /nologo /Zs /EHsc /std:c++20 /utf-8 /W4 /WX /Iscintilla\include /Ilexilla\include tests\lexer-compile-test.cpp
if errorlevel 1 exit /b 6
cl /nologo /EHsc /std:c++20 /utf-8 /W4 /WX tests\markdown-core-test.cpp /Fe:test-output\markdown-core-test.exe /Fo:test-output\markdown-core-test.obj
if errorlevel 1 exit /b 4
test-output\markdown-core-test.exe
if errorlevel 1 exit /b 5
if not exist PowerEditor\bin64\plugins\LiteProbe mkdir PowerEditor\bin64\plugins\LiteProbe
cl /nologo /LD /MT /EHsc /std:c++20 /utf-8 /Iscintilla\include tests\plugin-probe.cpp /Fo:test-output\plugin-probe.obj /Fe:PowerEditor\bin64\plugins\LiteProbe\LiteProbe.dll /link user32.lib
exit /b %errorlevel%
