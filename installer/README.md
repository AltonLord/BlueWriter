# BlueWriter Installers

This directory contains installers for different platforms.

## Quick Install

### Linux (Ubuntu, Debian, Fedora, Arch)

```bash
# From the BlueWriter directory:
./installer/install-linux.sh

# Or from anywhere:
/path/to/BlueWriter/installer/install-linux.sh
```

### Windows

1. Right-click `install-windows.ps1`
2. Select "Run with PowerShell"

Or from PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File installer\install-windows.ps1
```

### macOS

```bash
./installer/install-macos.sh
```
*(Coming soon)*

## What the Installers Do

1. **Check Python** - Verifies Python 3.10+ is installed
2. **Install Python** - If needed, installs Python automatically
3. **Install Qt Dependencies** - System libraries for the GUI
4. **Create Virtual Environment** - Isolated Python environment
5. **Install Packages** - All Python dependencies from requirements.txt
6. **Create Launcher** - Desktop shortcut/menu entry
7. **Create Uninstaller** - Easy removal script

## Installation Locations

| Platform | Application | Data |
|----------|-------------|------|
| Linux | `~/.local/share/bluewriter/` | `~/.local/share/bluewriter/data/` |
| Windows | `%LOCALAPPDATA%\BlueWriter\` | `%LOCALAPPDATA%\BlueWriter\data\` |
| macOS | `~/Applications/BlueWriter/` | `~/Library/Application Support/BlueWriter/` |

## Uninstalling

### Linux
```bash
~/.local/share/bluewriter/uninstall.sh
```

### Windows
Run `uninstall.ps1` from the installation directory, or:
```powershell
& "$env:LOCALAPPDATA\BlueWriter\uninstall.ps1"
```

## Troubleshooting

### "Python not found" after installation

**Linux:** Log out and back in, or run:
```bash
source ~/.profile
```

**Windows:** Restart your terminal, or refresh PATH:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### Qt/GUI errors on Linux

Install Qt dependencies manually:
```bash
# Ubuntu/Debian
sudo apt install libxcb-cursor0 libxkbcommon0 libegl1

# Fedora
sudo dnf install xcb-util-cursor libxkbcommon mesa-libEGL
```

### "Execution Policy" error on Windows

Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Application won't start

1. Check the terminal/console for error messages
2. Try running from command line:
   - Linux: `~/.local/bin/bluewriter`
   - Windows: `%LOCALAPPDATA%\BlueWriter\BlueWriter.bat`

## Building Installers

### Creating a Release Package

```bash
# Create a distributable zip
cd /path/to/BlueWriter
zip -r BlueWriter-v1.0.0.zip . -x "*.git*" -x "*venv*" -x "*.pyc" -x "*__pycache__*" -x "data/*.db*"
```

### Windows Executable (Optional)

For a single-file Windows executable, you can use PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name BlueWriter main.py
```
Note: This creates a large file (~100MB) but requires no Python installation.
