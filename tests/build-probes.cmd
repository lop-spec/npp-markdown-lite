@echo off
setlocal
cd /d "%~dp0.."
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSROOT=%%i"
if not defined VSROOT exit /b 2
call "%VSROOT%\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 3
if not exist test-output mkdir test-output
"%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:library /out:tests\native-acceptance.dll tests\native-acceptance.cs
if errorlevel 1 exit /b 4
if not exist PowerEditor\bin64\plugins\LiteProbe mkdir PowerEditor\bin64\plugins\LiteProbe
cl /nologo /LD /MT /EHsc /std:c++20 /utf-8 /Iscintilla\include tests\plugin-probe.cpp /Fo:test-output\plugin-probe.obj /Fe:PowerEditor\bin64\plugins\LiteProbe\LiteProbe.dll /link user32.lib
exit /b %errorlevel%
