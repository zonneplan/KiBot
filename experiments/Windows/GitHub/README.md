This document contains some information about what I learned from experiments using Windows images on GitHub [Test](https://github.com/set-soft/TestWindowsCI/)

# OS

Was Windows Server 2022 identified by GitHub as:

- ImageOS: win22
- ImageVersion: 20220626.1
- 64 bits

# Shell

The default shell is Power Shell. You can choose other shell using `shell: bash` or even `shell: python`.

Power Shell isn't compatible with DOS, i.e the `rename` command is `Rename-Item`!!!

# MingW

Is installed and you can run common UNIX commands, they translate drive letters as this: **C:\** -> **/c/**

Note that moving files across drives fails!!! `sed -i` doesn't work if cwd is in D: and the file is in C:!!!!

# Environment variables

- Listing: `dir env:` is very verbose and explains who defined each variable [See](https://github.com/set-soft/TestWindowsCI/runs/7164910282?check_suite_focus=true)
- Expanding: `${env:VARIABLE}` works inside strings
- Defining: `$env:VARIABLE = VALUE`
- Default PATH: `C:\Program Files\PowerShell\7;C:\Program Files\MongoDB\Server\5.0\bin;C:\aliyun-cli;C:\vcpkg;C:\Program Files (x86)\NSIS\;C:\tools\zstd;C:\Program Files\Mercurial\;C:\hostedtoolcache\windows\stack\2.7.5\x64;C:\cabal\bin;C:\\ghcup\bin;C:\tools\ghc-9.2.3\bin;C:\Program Files\dotnet;C:\mysql\bin;C:\Program Files\R\R-4.2.1\bin\x64;C:\SeleniumWebDrivers\GeckoDriver;C:\Program Files (x86)\sbt\bin;C:\Program Files (x86)\GitHub CLI;C:\Program Files\Git\bin;C:\Program Files (x86)\pipx_bin;C:\npm\prefix;C:\hostedtoolcache\windows\go\1.17.11\x64\bin;C:\hostedtoolcache\windows\Python\3.9.13\x64\Scripts;C:\hostedtoolcache\windows\Python\3.9.13\x64;C:\hostedtoolcache\windows\Ruby\3.0.4\x64\bin;C:\tools\kotlinc\bin;C:\hostedtoolcache\windows\Java_Temurin-Hotspot_jdk\8.0.332-9\x64\bin;C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin;C:\ProgramData\kind;C:\Program Files\Microsoft\jdk-11.0.12.7-hotspot\bin;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\;C:\Windows\System32\OpenSSH\;C:\Program Files\dotnet\;C:\ProgramData\Chocolatey\bin;C:\Program Files\Docker;C:\Program Files\PowerShell\7\;C:\Program Files\Microsoft\Web Platform Installer\;C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\;C:\Program Files\Microsoft SQL Server\150\Tools\Binn\;C:\Program Files\OpenSSL\bin;C:\Strawberry\c\bin;C:\Strawberry\perl\site\bin;C:\Strawberry\perl\bin;C:\ProgramData\chocolatey\lib\pulumi\tools\Pulumi\bin;C:\Program Files\TortoiseSVN\bin;C:\Program Files\CMake\bin;C:\ProgramData\chocolatey\lib\maven\apache-maven-3.8.6\bin;C:\Program Files\Microsoft Service Fabric\bin\Fabric\Fabric.Code;C:\Program Files\Microsoft SDKs\Service Fabric\Tools\ServiceFabricLocalClusterManager;C:\Program Files\nodejs\;C:\Program Files\Git\cmd;C:\Program Files\Git\mingw64\bin;C:\Program Files\Git\usr\bin;C:\Program Files\GitHub CLI\;c:\tools\php;C:\Program Files (x86)\sbt\bin;C:\SeleniumWebDrivers\ChromeDriver\;C:\SeleniumWebDrivers\EdgeDriver\;C:\Program Files\Amazon\AWSCLIV2\;C:\Program Files\Amazon\SessionManagerPlugin\bin\;C:\Program Files\Amazon\AWSSAMCLI\bin\;C:\Program Files\Microsoft SQL Server\130\Tools\Binn\;C:\Program Files\LLVM\bin;C:\Users\runneradmin\.dotnet\tools;C:\Users\runneradmin\.cargo\bin;C:\Users\runneradmin\AppData\Local\Microsoft\WindowsApps`
- Expanding the PATH: `$env:PATH = "C:\Program Files\KiCad\6.0\bin;C:\Program Files\KiCad\6.0\bin\Scripts;${env:PATH}"`

# Default Python

The default installed Python is:

- Version: 3.9.13
- Binary: `/c/hostedtoolcache/windows/Python/3.9.13/x64/python3`
- No `wheel` installed
- Scripts are installed in `/c/hostedtoolcache/windows/Python/3.9.13/x64/Scripts/` (No .exe extension)
- Shebang: `C:\hostedtoolcache\windows\Python\3.9.13\x64\python.exe`

# KiCad

You can install KiCad using Chocolatery: `choco install --no-progress kicad`. The `--no-progress` avoids tons of messages during the 1.06 GB download. It takes about 5 minutes to install.

The default installation is to `C:\Program Files\KiCad\6.0`. The binaries are inside `bin` and the Python tools binaries inside `bin/Scripts`.

After installation the PATH isn't updated after installation (See [Environment variables](#environment-variables)

Included binaries:
- _freeze_importlib.exe
- bitmap2component.exe
- dxf2idf.exe
- eeschema.exe
- gerbview.exe
- idf2vrml.exe
- idfcyl.exe
- idfrect.exe
- kicad-cmd.bat
- kicad.exe
- kicad2step.exe
- pcb_calculator.exe
- pcbnew.exe
- pl_editor.exe
- python.exe
- pythonw.exe
- venvlauncher.exe
- venvwlauncher.exe
- xsltproc.exe

# KiCad Python

Is a mess.

- Interpreter: `python` (`C:\Program Files\KiCad\6.0\bin\python.exe`). NO `python3`available!!!
- Paths: Are reported as Windows native ones
- Modules: Installed at `C:\Program Files\KiCad\6.0\bin\Lib`
- Scripts: Installed at `C:\Program Files\KiCad\6.0\bin\Scripts`
- PIP: pip.exe, pip3.exe, pip3.9.exe and pip3.10.exe (all in Scripts)
- Shebang: `C:\Program Files\KiCad\6.0\bin\python.exe` missing quotes!!!

Problems:

1. Only `python` binary, no `python3`. Even when they include `pip` and `pip3`!
   *Workaround*: Use `python`
2. You can't run pip installed scripts. They have a wrong shebang, useless for bash and Power Shell. You must use `python FULL_PATH`.
   *Workaround*: Use `python SCRIPT` or switch to entry-points.
3. Power Shell silently fails if the shebang is wrong!!!
   *Workaround*: Add more debug to know it even tried to execute it
4. `pip install .` doesn't work.
   *Workaround*: Use `pip install DIR`

# KiCad command shell

This is a batch file to fix various problems, is ment to be run in `cmd`:

```bat
@REM This program source code file is part of KiCad, a free EDA CAD application.
@REM
@REM Copyright (c) 2021 Mark Roszko <mark.roszko@gmail.com>
@REM Copyright (c) 2021 KiCad Developer Team
@REM
@REM This program is free software; you can redistribute it and/or
@REM modify it under the terms of the GNU General Public License
@REM as published by the Free Software Foundation; either version 3
@REM of the License, or (at your option) any later version.
@REM
@REM This program is distributed in the hope that it will be useful, but
@REM WITHOUT ANY WARRANTY; without even the implied warranty of
@REM MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
@REM General Public License for more details.
@REM
@REM You should have received a copy of the GNU General Public License along
@REM with this program.  If not, see <http://www.gnu.org/licenses/>.

@echo off

@REM Get KiCad exe version to reproduce
for /f "USEBACKQ" %%a in (`powershell -NoProfile -Command ^(Get-Item "kicad.exe"^).VersionInfo.ProductVersion`) do set kicadVersion=%%a

@echo ************************************
@echo * KiCad %kicadVersion% Command Prompt
@echo ************************************

@REM We assume this script is located in the bin directory
set _BIN_DIR=%~dp0
set _PYTHON_SCRIPTS_DIR=%_BIN_DIR%Scripts

@REM Now adjust PATH to gurantee our python/pip executables are found first
set PATH=%_BIN_DIR%;%_PYTHON_SCRIPTS_DIR%;%PATH%
set PYTHONHOME=%_BIN_DIR%

@REM We patch python into utf8 mode by default because kicad is utf8 heavy
@REM But let's just add extra insurance
set PYTHONUTF8=1

@echo You may now invoke python or pip targeting kicad's install

cd /d %USERPROFILE%\Documents\KiCad\%kicadVersion%

set _BIN_DIR=
set _PYTHON_SCRIPTS_DIR=

exit /B 0
```

A menu entry is installed with: `%comspec% /k "C:\Program Files\KiCad\6.0\bin\kicad-cmd.bat"`

The /k means continue.

# KiBot install

- You must ensure the python is the one from KiCad
- `pip install --no-compile kibot`
- `pip install lxml` (for 1.2.0)
- Files go to: `C:\Program Files\KiCad\6.0\bin\Lib\site-packages\kibot`
- Run with: `python "C:\Program Files\KiCad\6.0\bin\Scripts\kibot"`
- We should try to add an entry point so we can avoid the shebang problem

# Conclusions

1. The Python included with KiCad is broken, it can't handle *scripts*, just entry points.
