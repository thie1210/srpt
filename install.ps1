# Py Installer for Windows
# This script downloads Python and py without requiring an existing Python installation
#
# Usage:
#  Invoke-WebRequest -Uri https://pyproject.org/install.ps1 -OutFile install.ps1; .\install.ps1
#
# Based on rustup and uv installation patterns

# Configuration
$PY_VERSION = "0.1.0"
$PYTHON_VERSION = "3.13.12"
$PYTHON_BUILD_STANDALONE_TAG = "20260211"
$PY_BASE_DIR = if ($env:PY_BASE_DIR) { $env:PY_BASE_DIR } else { "$env:USERPROFILE\.local\share\py" }
$PY_BIN_DIR = if ($env:PY_BIN_DIR) { $env:PY_BIN_DIR } else { "$env:USERPROFILE\.local\bin" }

# Platform detection
function Get-Platform {
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
    $os = [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
    
    if ($os -match "Windows") {
        switch ($arch) {
            "X64" { return "x86_64-pc-windows-msvc" }
            "Arm64" { return "aarch64-pc-windows-msvc" }
            default { throw "Unsupported architecture: $arch" }
        }
    }
    
    throw "Unsupported OS: $os"
}

# Download file with progress
function Download-File {
    param($Url, $Output)
    
    Write-Host "Downloading $Url..."
    
    try {
        # Use .NET WebClient for better compatibility
        $client = New-Object System.Net.WebClient
        $client.DownloadFile($Url, $Output)
    } catch {
        throw "Failed to download: $Url"
    }
}

# Install Python
function Install-Python {
    $platform = Get-Platform
    $pythonDir = "$PY_BASE_DIR\python\$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG"
    $pythonUrl = "https://github.com/astral-sh/python-build-standalone/releases/download/$PYTHON_BUILD_STANDALONE_TAG/cpython-$PYTHON_VERSION+$PYTHON_BUILD_STANDALONE_TAG-$platform-install_only.tar.gz"
    $downloadFile = "$PY_BASE_DIR\downloads\python.tar.gz"
    
    if (Test-Path "$pythonDir\python\python.exe") {
        Write-Host "Python $PYTHON_VERSION already installed at $pythonDir"
        return
    }
    
    Write-Host ""
    Write-Host "Installing Python $PYTHON_VERSION for $platform..."
    
    New-Item -ItemType Directory -Force -Path "$PY_BASE_DIR\downloads" | Out-Null
    New-Item -ItemType Directory -Force -Path $pythonDir | Out-Null
    
    Download-File -Url $pythonUrl -Output $downloadFile
    
    Write-Host "Extracting Python..."
    
    # Use 7zip or built-in tar (Windows 10+)
    if (Get-Command tar -ErrorAction SilentlyContinue) {
        tar -xzf $downloadFile -C $pythonDir
    } else {
        # Fallback: Use .NET to extract
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($downloadFile, $pythonDir)
    }
    
    Remove-Item $downloadFile -ErrorAction SilentlyContinue
    
    Write-Host "Python installed successfully!"
}

# Install py
function Install-PyTool {
    $pythonBin = "$PY_BASE_DIR\python\$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG\python\python.exe"
    
    Write-Host ""
    Write-Host "Installing py $PY_VERSION..."
    
    # Create lib directory
    New-Item -ItemType Directory -Force -Path "$PY_BASE_DIR\lib" | Out-Null
    
    # Create launcher script
    $launcher = "$PY_BIN_DIR\py.ps1"
    New-Item -ItemType Directory -Force -Path $PY_BIN_DIR | Out-Null
    
    $launcherContent = @'
# Py launcher script for Windows
$PY_BASE_DIR = if ($env:PY_BASE_DIR) { $env:PY_BASE_DIR } else { "$env:USERPROFILE\.local\share\py" }
$PYTHON_VERSION = "3.13.12"
$PYTHON_BUILD_STANDALONE_TAG = "20260211"
$PYTHON_BIN = "$PY_BASE_DIR\python\$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG\python\python.exe"
$PY_LIB = "$PY_BASE_DIR\lib\py"

if (-not (Test-Path $PYTHON_BIN)) {
    Write-Error "Error: Managed Python not found at $PYTHON_BIN"
    Write-Host "Please run the installer: https://pyproject.org/install.ps1"
    exit 1
}

if (-not (Test-Path $PY_LIB)) {
    Write-Error "Error: py not installed at $PY_LIB"
    Write-Host "Please run the installer: https://pyproject.org/install.ps1"
    exit 1
}

$env:PYTHONPATH = "$PY_LIB\src"
& $PYTHON_BIN "$PY_LIB\src\py\__main__.py" $args
'@
    
    Set-Content -Path $launcher -Value $launcherContent -Encoding UTF8
    
    # Also create a .bat file for cmd.exe compatibility
    $batLauncher = "$PY_BIN_DIR\py.bat"
    $batContent = "@echo off`npowershell -NoProfile -ExecutionPolicy Bypass -File `"$launcher`" %*"
    Set-Content -Path $batLauncher -Value $batContent -Encoding ASCII
    
    # Copy current py source
    $scriptDir = Split-Path -Parent $PSCommandPath
    if (Test-Path "$scriptDir\src\py") {
        Write-Host "Installing py from $scriptDir..."
        if (Test-Path "$PY_BASE_DIR\lib\py") {
            Remove-Item -Recurse -Force "$PY_BASE_DIR\lib\py"
        }
        Copy-Item -Recurse -Path $scriptDir -Destination "$PY_BASE_DIR\lib\py" -ErrorAction SilentlyContinue
        Write-Host "py installed to $PY_BASE_DIR\lib\py"
    } else {
        Write-Host "Warning: py source not found. You'll need to install it manually."
    }
    
    Write-Host ""
    Write-Host "py launcher created at $launcher"
}

# Finalize
function Finalize-Install {
    Write-Host ""
    Write-Host "================================"
    Write-Host "Installation complete!"
    Write-Host "================================"
    Write-Host ""
    Write-Host "py has been installed to: $PY_BIN_DIR"
    Write-Host ""
    
    # Check if py is in PATH
    $pyInPath = $env:PATH -split ';' | Where-Object { $_ -eq $PY_BIN_DIR }
    if (-not $pyInPath) {
        Write-Host "To get started, add $PY_BIN_DIR to your PATH:"
        Write-Host ""
        Write-Host "  `$env:PATH += `";$PY_BIN_DIR`""
        Write-Host ""
        Write-Host "Or add to your PowerShell profile:"
        Write-Host "  Add-Content -Path `$PROFILE -Value '`$env:PATH += `";$PY_BIN_DIR`"'"
        Write-Host ""
    }
    
    Write-Host "Quick start:"
    Write-Host "  py                    # Start Python REPL"
    Write-Host "  py my_script.py       # Run a Python script"
    Write-Host "  py install requests   # Install a package"
}

# Main
Write-Host "================================"
Write-Host "Py Installer"
Write-Host "================================"
Write-Host ""

try {
    Install-Python
    Install-PyTool
    Finalize-Install
} catch {
    Write-Error $_
    exit 1
}
