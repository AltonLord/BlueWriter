# BlueWriter Installer for Windows
# 
# This script installs BlueWriter and all its dependencies.
# Run with: Right-click -> Run with PowerShell
#           Or: powershell -ExecutionPolicy Bypass -File install-windows.ps1

param(
    [switch]$Silent,
    [switch]$NoShortcuts,
    [string]$InstallDir = "$env:LOCALAPPDATA\BlueWriter"
)

$ErrorActionPreference = "Stop"

# Configuration
$AppName = "BlueWriter"
$MinPythonVersion = [version]"3.10"
$PythonInstallerUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Split-Path -Parent $ScriptDir

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

function Write-Header {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Blue
    Write-Host "  BlueWriter Installer" -ForegroundColor Green
    Write-Host "  AI-Powered Fiction Writing" -ForegroundColor White
    Write-Host "================================================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    $time = Get-Date -Format "HH:mm:ss"
    Write-Host "[$time] > " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    $time = Get-Date -Format "HH:mm:ss"
    Write-Host "[$time] + " -ForegroundColor Green -NoNewline
    Write-Host $Message -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    $time = Get-Date -Format "HH:mm:ss"
    Write-Host "[$time] ! " -ForegroundColor Yellow -NoNewline
    Write-Host $Message -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    $time = Get-Date -Format "HH:mm:ss"
    Write-Host "[$time] X " -ForegroundColor Red -NoNewline
    Write-Host $Message -ForegroundColor Red
}

# -----------------------------------------------------------------------------
# Python Detection and Installation
# -----------------------------------------------------------------------------

function Find-Python {
    Write-Step "Checking Python installation..."
    
    # Try different Python locations
    $pythonPaths = @(
        "python",
        "py -3",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe"
    )
    
    foreach ($pythonPath in $pythonPaths) {
        try {
            $versionOutput = & cmd /c "$pythonPath --version 2>&1"
            if ($versionOutput -match "Python (\d+\.\d+)") {
                $version = [version]$matches[1]
                if ($version -ge $MinPythonVersion) {
                    Write-Success "Found Python $version at: $pythonPath"
                    return $pythonPath
                }
            }
        } catch {
            continue
        }
    }
    
    return $null
}

function Install-Python {
    Write-Step "Python $MinPythonVersion+ not found. Installing Python 3.11..."
    
    # Try winget first (Windows 10/11)
    try {
        $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetCheck) {
            Write-Step "Using Windows Package Manager (winget)..."
            winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements
            
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            
            $python = Find-Python
            if ($python) {
                return $python
            }
        }
    } catch {
        Write-Warning "winget installation failed, trying direct download..."
    }
    
    # Download and install directly
    Write-Step "Downloading Python installer..."
    $installerPath = "$env:TEMP\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $PythonInstallerUrl -OutFile $installerPath -UseBasicParsing
    } catch {
        Write-ErrorMsg "Failed to download Python installer"
        throw
    }
    
    Write-Step "Running Python installer..."
    $installArgs = "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1"
    Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait
    
    # Cleanup
    Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Find Python again
    $python = Find-Python
    if (-not $python) {
        Write-ErrorMsg "Python installation failed. Please install Python 3.10+ manually from python.org"
        throw "Python installation failed"
    }
    
    return $python
}

# -----------------------------------------------------------------------------
# Installation Steps
# -----------------------------------------------------------------------------

function New-InstallDirectories {
    Write-Step "Creating installation directories..."
    
    if (Test-Path $InstallDir) {
        if (Test-Path "$InstallDir\data") {
            Write-Step "Backing up existing data..."
            $backupDir = "$env:TEMP\bluewriter_backup_" + (Get-Date -Format "yyyyMMddHHmmss")
            Copy-Item -Path "$InstallDir\data" -Destination $backupDir -Recurse
        }
    }
    
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    New-Item -ItemType Directory -Force -Path "$InstallDir\data" | Out-Null
    
    Write-Success "Directories created"
}

function Copy-SourceFiles {
    Write-Step "Copying application files..."
    
    $excludes = @("venv", ".git", ".pytest_cache", "__pycache__", "*.pyc", "installer", "*.db", "*.db-wal", "*.db-shm")
    
    Get-ChildItem -Path $SourceDir -Exclude $excludes | ForEach-Object {
        if ($_.Name -ne "data") {
            Copy-Item -Path $_.FullName -Destination $InstallDir -Recurse -Force
        }
    }
    
    if (-not (Test-Path "$InstallDir\data\bluewriter.db")) {
        if (Test-Path "$SourceDir\data") {
            Copy-Item -Path "$SourceDir\data\*" -Destination "$InstallDir\data" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Success "Application files copied"
}

function New-VirtualEnvironment {
    param([string]$PythonPath)
    
    Write-Step "Creating Python virtual environment..."
    
    if (Test-Path "$InstallDir\venv") {
        Remove-Item -Path "$InstallDir\venv" -Recurse -Force
    }
    
    & cmd /c "$PythonPath -m venv `"$InstallDir\venv`""
    
    if (-not (Test-Path "$InstallDir\venv\Scripts\python.exe")) {
        throw "Failed to create virtual environment"
    }
    
    Write-Success "Virtual environment created"
}

function Install-PythonPackages {
    Write-Step "Installing Python packages (this may take a few minutes)..."
    
    $venvPython = "$InstallDir\venv\Scripts\python.exe"
    $venvPip = "$InstallDir\venv\Scripts\pip.exe"
    
    & $venvPython -m pip install --upgrade pip --quiet 2>$null
    & $venvPip install -r "$InstallDir\requirements.txt" --quiet 2>$null
    
    Write-Success "Python packages installed"
}

function New-LauncherScript {
    Write-Step "Creating launcher script..."
    
    $launcherLines = @(
        "@echo off",
        "cd /d `"%LOCALAPPDATA%\BlueWriter`"",
        "call venv\Scripts\activate.bat",
        "python main.py %*"
    )
    
    $launcherLines | Out-File -FilePath "$InstallDir\BlueWriter.bat" -Encoding ASCII
    
    Write-Success "Launcher script created"
}

function New-Shortcuts {
    Write-Step "Creating shortcuts..."
    
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Start Menu shortcut
    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    $shortcut = $WshShell.CreateShortcut("$startMenuPath\BlueWriter.lnk")
    $shortcut.TargetPath = "$InstallDir\BlueWriter.bat"
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.Description = "AI-Powered Fiction Writing Application"
    $shortcut.WindowStyle = 7
    
    if (Test-Path "$InstallDir\resources\icon.ico") {
        $shortcut.IconLocation = "$InstallDir\resources\icon.ico"
    }
    
    $shortcut.Save()
    Write-Success "Start Menu shortcut created"
    
    # Desktop shortcut
    if (-not $NoShortcuts) {
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcut = $WshShell.CreateShortcut("$desktopPath\BlueWriter.lnk")
        $shortcut.TargetPath = "$InstallDir\BlueWriter.bat"
        $shortcut.WorkingDirectory = $InstallDir
        $shortcut.Description = "AI-Powered Fiction Writing Application"
        $shortcut.WindowStyle = 7
        
        if (Test-Path "$InstallDir\resources\icon.ico") {
            $shortcut.IconLocation = "$InstallDir\resources\icon.ico"
        }
        
        $shortcut.Save()
        Write-Success "Desktop shortcut created"
    }
}

function New-Uninstaller {
    Write-Step "Creating uninstaller..."
    
    $uninstallLines = @(
        "# BlueWriter Uninstaller",
        "`$InstallDir = `"`$env:LOCALAPPDATA\BlueWriter`"",
        "",
        "Write-Host `"Uninstalling BlueWriter...`" -ForegroundColor Yellow",
        "",
        "# Remove shortcuts",
        "`$startMenuPath = `"`$env:APPDATA\Microsoft\Windows\Start Menu\Programs`"",
        "Remove-Item `"`$startMenuPath\BlueWriter.lnk`" -Force -ErrorAction SilentlyContinue",
        "",
        "`$desktopPath = [Environment]::GetFolderPath(`"Desktop`")",
        "Remove-Item `"`$desktopPath\BlueWriter.lnk`" -Force -ErrorAction SilentlyContinue",
        "",
        "# Ask about data",
        "`$response = Read-Host `"Remove user data (projects, stories)? [y/N]`"",
        "if (`$response -eq 'y' -or `$response -eq 'Y') {",
        "    Remove-Item `$InstallDir -Recurse -Force",
        "    Write-Host `"BlueWriter completely removed.`" -ForegroundColor Green",
        "} else {",
        "    Get-ChildItem `$InstallDir -Exclude `"data`" | Remove-Item -Recurse -Force",
        "    Write-Host `"BlueWriter removed. Your data is preserved in `$InstallDir\data`" -ForegroundColor Green",
        "}",
        "",
        "Write-Host `"Uninstallation complete.`" -ForegroundColor Green",
        "Read-Host `"Press Enter to exit`""
    )
    
    $uninstallLines | Out-File -FilePath "$InstallDir\uninstall.ps1" -Encoding UTF8
    
    Write-Success "Uninstaller created"
}

# -----------------------------------------------------------------------------
# Main Installation Flow
# -----------------------------------------------------------------------------

function Main {
    Write-Header
    
    Write-Host "This will install BlueWriter on your system."
    Write-Host ""
    Write-Host "Installation directory: $InstallDir"
    Write-Host "Source directory: $SourceDir"
    Write-Host ""
    
    if (-not $Silent) {
        $response = Read-Host "Continue with installation? [Y/n]"
        if ($response -eq 'n' -or $response -eq 'N') {
            Write-Host "Installation cancelled."
            exit 0
        }
    }
    
    Write-Host ""
    Write-Host "Starting installation..." -ForegroundColor Blue
    Write-Host ""
    
    try {
        $pythonPath = Find-Python
        if (-not $pythonPath) {
            $pythonPath = Install-Python
        }
        
        New-InstallDirectories
        Copy-SourceFiles
        New-VirtualEnvironment -PythonPath $pythonPath
        Install-PythonPackages
        New-LauncherScript
        New-Shortcuts
        New-Uninstaller
        
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host "  Installation Complete!" -ForegroundColor Green
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now launch BlueWriter by:"
        Write-Host ""
        Write-Host "  1. Clicking the 'BlueWriter' icon on your Desktop"
        Write-Host "  2. Finding 'BlueWriter' in your Start Menu"
        Write-Host ""
        Write-Host "To uninstall, run: $InstallDir\uninstall.ps1"
        Write-Host ""
        
        if (-not $Silent) {
            $response = Read-Host "Launch BlueWriter now? [Y/n]"
            if ($response -ne 'n' -and $response -ne 'N') {
                Start-Process "$InstallDir\BlueWriter.bat"
            }
        }
        
    } catch {
        Write-ErrorMsg "Installation failed: $_"
        Write-Host ""
        Write-Host "Please check the error above and try again."
        Write-Host "If the problem persists, please report it at:"
        Write-Host "https://github.com/AltonLord/BlueWriter/issues"
        exit 1
    }
}

# Run main function
Main
