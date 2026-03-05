# Py Installer for Windows
# This script downloads Python and py without requiring an existing Python installation
#
# Usage:
#  Invoke-WebRequest -Uri https://pyproject.org/install.ps1 -OutFile install.ps1; .\install.ps1
#
# Based on rustup and uv installation patterns

# Configuration
$SRPT_VERSION = "0.2.15"
$PYTHON_VERSION = "3.13.12"
$PYTHON_BUILD_STANDALONE_TAG = "20260211"
$SRPT_BASE_DIR = if ($env:SRPT_BASE_DIR) { $env:SRPT_BASE_DIR } else { "$env:USERPROFILE\.local\share\srpt" }
$SRPT_BIN_DIR = if ($env:SRPT_BIN_DIR) { $env:SRPT_BIN_DIR } else { "$env:USERPROFILE\.local\bin" }

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
    $pythonDir = "$SRPT_BASE_DIR\python\$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG"
    $pythonUrl = "https://github.com/astral-sh/python-build-standalone/releases/download/$PYTHON_BUILD_STANDALONE_TAG/cpython-$PYTHON_VERSION+$PYTHON_BUILD_STANDALONE_TAG-$platform-install_only.tar.gz"
    $downloadFile = "$SRPT_BASE_DIR\downloads\python.tar.gz"
    
    if (Test-Path "$pythonDir\python\python.exe") {
        Write-Host "Python $PYTHON_VERSION already installed at $pythonDir"
        return
    }
    
    Write-Host ""
    Write-Host "Installing Python $PYTHON_VERSION for $platform..."
    
    New-Item -ItemType Directory -Force -Path "$SRPT_BASE_DIR\downloads" | Out-Null
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

# Install srpt
function Install-Srpt {
    $pythonBin = "$SRPT_BASE_DIR\python\$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG\python\python.exe"
    
    Write-Host ""
    Write-Host "Installing srpt $SRPT_VERSION..."
    
    # Create lib directory
    New-Item -ItemType Directory -Force -Path "$SRPT_BASE_DIR\lib" | Out-Null
    
    # Create launcher script
    $launcher = "$SRPT_BIN_DIR\srpt.ps1"
    New-Item -ItemType Directory -Force -Path $SRPT_BIN_DIR | Out-Null
    
    $launcherContent = @'
# srpt launcher script for Windows
$SRPT_BASE_DIR = if ($env:SRPT_BASE_DIR) { $env:SRPT_BASE_DIR } else { "$env:USERPROFILE\.local\share\srpt" }
$PYTHON_VERSION = "3.13.12"
$PYTHON_BUILD_STANDALONE_TAG = "20260211"
$PYTHON_BIN = "$SRPT_BASE_DIR\python\$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG\python\python.exe"
$SRPT_LIB = "$SRPT_BASE_DIR\lib\srpt"

if (-not (Test-Path $PYTHON_BIN)) {
    Write-Error "Error: Managed Python not found at $PYTHON_BIN"
    Write-Host "Please run the installer: https://raw.githubusercontent.com/thie1210/srpt/main/install.ps1"
    exit 1
}

if (-not (Test-Path $SRPT_LIB)) {
    Write-Error "Error: srpt not installed at $SRPT_LIB"
    Write-Host "Please run the installer: https://raw.githubusercontent.com/thie1210/srpt/main/install.ps1"
    exit 1
}

$env:PYTHONPATH = "$SRPT_LIB\src"
& $PYTHON_BIN "$SRPT_LIB\src\srpt\__main__.py" $args
'@
    
    Set-Content -Path $launcher -Value $launcherContent -Encoding UTF8
    
    # Also create a .bat file for cmd.exe compatibility
    $batLauncher = "$SRPT_BIN_DIR\srpt.bat"
    $batContent = "@echo off`npowershell -NoProfile -ExecutionPolicy Bypass -File `"$launcher`" %*"
    Set-Content -Path $batLauncher -Value $batContent -Encoding ASCII
    
    # Copy current srpt source
    $scriptDir = Split-Path -Parent $PSCommandPath
    if (Test-Path "$scriptDir\src\srpt") {
        Write-Host "Installing srpt from $scriptDir..."
        if (Test-Path "$SRPT_BASE_DIR\lib\srpt") {
            Remove-Item -Recurse -Force "$SRPT_BASE_DIR\lib\srpt"
        }
        Copy-Item -Recurse -Path $scriptDir -Destination "$SRPT_BASE_DIR\lib\srpt" -ErrorAction SilentlyContinue
        Write-Host "srpt installed to $SRPT_BASE_DIR\lib\srpt"
    } else {
        Write-Host "Warning: srpt source not found. You'll need to install it manually."
    }
    
    Write-Host ""
    Write-Host "srpt launcher created at $launcher"
}

# Finalize
function Finalize-Install {
    Write-Host ""
    Write-Host "================================"
    Write-Host "Installation complete!"
    Write-Host "================================"
    Write-Host ""
    Write-Host "srpt has been installed to: $SRPT_BIN_DIR"
    Write-Host ""
    
    # Check if srpt is in PATH
    $srptInPath = $env:PATH -split ';' | Where-Object { $_ -eq $SRPT_BIN_DIR }
    if (-not $srptInPath) {
        Write-Host "To get started, add $SRPT_BIN_DIR to your PATH:"
        Write-Host ""
        Write-Host "  `$env:PATH += `";$SRPT_BIN_DIR`""
        Write-Host ""
        Write-Host "Or add to your PowerShell profile:"
        Write-Host "  Add-Content -Path `$PROFILE -Value '`$env:PATH += `";$SRPT_BIN_DIR`"'"
        Write-Host ""
    }
    
    Write-Host "Quick start:"
    Write-Host "  srpt                    # Start Python REPL"
    Write-Host "  srpt my_script.py       # Run a Python script"
    Write-Host "  srpt install requests   # Install a package"
}

# Main
Write-Host "================================"
Write-Host "srpt Installer"
Write-Host "================================"
Write-Host ""

try {
    Install-Python
    Install-Srpt
    Finalize-Install
} catch {
    Write-Error $_
    exit 1
}
