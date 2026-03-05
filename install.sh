#!/bin/bash
#
# srpt Installer - Bootstrap script for the srpt package manager
# This script downloads Python and srpt without requiring an existing Python installation
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/thie1210/srpt/main/install.sh | sh
#   curl -sSL https://raw.githubusercontent.com/thie1210/srpt/main/install.sh | sh -s -- --help
#
# Based on rustup and uv installation patterns
#

set -euo pipefail

# Configuration
SRPT_VERSION="0.2.10"
PYTHON_VERSION="3.13.12"
PYTHON_BUILD_STANDALONE_TAG="20260211"
SRPT_BASE_DIR="${SRPT_BASE_DIR:-$HOME/.local/share/srpt}"
SRPT_BIN_DIR="${SRPT_BIN_DIR:-$HOME/.local/bin}"

# Platform detection
get_platform() {
    local arch="$(uname -m)"
    local os="$(uname -s)"
    
    case "$os" in
        Darwin)
            case "$arch" in
                arm64|aarch64) echo "aarch64-apple-darwin" ;;
                x86_64) echo "x86_64-apple-darwin" ;;
                *) err "Unsupported architecture: $arch" ;;
            esac
            ;;
        Linux)
            case "$arch" in
                arm64|aarch64) echo "aarch64-unknown-linux-gnu" ;;
                x86_64) echo "x86_64-unknown-linux-gnu" ;;
                *) err "Unsupported architecture: $arch" ;;
            esac
            ;;
        *)
            err "Unsupported OS: $os"
            ;;
    esac
}

# Error handling
err() {
    echo "Error: $1" >&2
    exit 1
}

# Check if command exists
need_cmd() {
    if ! command -v "$1" > /dev/null 2>&1; then
        err "Required command '$1' not found. Please install it first."
    fi
}

# Download file with progress
download() {
    local url="$1"
    local output="$2"
    
    echo "Downloading $url..."
    
    if command -v curl > /dev/null 2>&1; then
        curl --proto '=https' --tlsv1.2 -LfS "$url" -o "$output" || err "Failed to download: $url"
    elif command -v wget > /dev/null 2>&1; then
        wget -q "$url" -O "$output" || err "Failed to download: $url"
    else
        err "Neither curl nor wget is available"
    fi
}

# Main installation
install_python() {
    local platform="$(get_platform)"
    local python_dir="$SRPT_BASE_DIR/python/$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG"
    local python_url="https://github.com/astral-sh/python-build-standalone/releases/download/$PYTHON_BUILD_STANDALONE_TAG/cpython-$PYTHON_VERSION+$PYTHON_BUILD_STANDALONE_TAG-$platform-install_only.tar.gz"
    local download_file="$SRPT_BASE_DIR/downloads/python.tar.gz"
    
    if [ -f "$python_dir/python/bin/python3" ]; then
        echo "  ✓ Python $PYTHON_VERSION already installed"
        return 0
    fi
    
    echo ""
    echo "PYTHON"
    echo "  Installing Python $PYTHON_VERSION for $platform..."
    
    mkdir -p "$SRPT_BASE_DIR/downloads"
    mkdir -p "$python_dir"
    
    if ! download "$python_url" "$download_file"; then
        err "Failed to download Python. The version may not be available for your platform."
    fi
    
    echo "  Extracting..."
    tar -xzf "$download_file" -C "$python_dir" || err "Failed to extract Python"
    rm -f "$download_file"
    
    echo "  ✓ Python installed successfully"
}

# Install py itself
install_srpt() {
    local python_bin="$SRPT_BASE_DIR/python/$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG/python/bin/python3"
    
    echo ""
    echo "SRPT"
    echo "  Installing srpt $SRPT_VERSION..."
    
    mkdir -p "$SRPT_BASE_DIR/lib"
    mkdir -p "$SRPT_BASE_DIR/downloads"
    
    local srpt_url="https://github.com/thie1210/srpt/archive/refs/tags/v$SRPT_VERSION.tar.gz"
    local download_file="$SRPT_BASE_DIR/downloads/srpt.tar.gz"
    
    echo "  Downloading srpt $SRPT_VERSION..."
    if ! download "$srpt_url" "$download_file"; then
        err "Failed to download srpt. Please check your internet connection."
    fi
    
    echo "  Extracting..."
    tar -xzf "$download_file" -C "$SRPT_BASE_DIR/downloads" || err "Failed to extract srpt"
    rm -f "$download_file"
    
    local extracted_dir="$SRPT_BASE_DIR/downloads/srpt-$SRPT_VERSION"
    if [ -d "$extracted_dir" ]; then
        if [ -d "$SRPT_BASE_DIR/lib/srpt" ]; then
            rm -rf "$SRPT_BASE_DIR/lib/srpt"
        fi
        mv "$extracted_dir" "$SRPT_BASE_DIR/lib/srpt"
        echo "  ✓ srpt installed to $SRPT_BASE_DIR/lib/srpt"
    else
        err "Failed to find extracted srpt source"
    fi
    
    # Install dependencies
    echo "  Installing dependencies..."
    "$python_bin" -m pip install --quiet --disable-pip-version-check \
        "httpx[http2]>=0.27.0" \
        "installer>=0.7.0" \
        "packaging>=21.0" \
        "resolvelib>=1.0.0" \
        "rich>=13.0.0" \
        "tomli>=2.0.0" || err "Failed to install dependencies"
    echo "  ✓ Dependencies installed"
    
    # Create launcher script
    local launcher="$SRPT_BIN_DIR/srpt"
    mkdir -p "$SRPT_BIN_DIR"
    
    cat > "$launcher" << 'EOF'
#!/bin/bash
# srpt launcher script
# This script runs srpt using the managed Python installation

set -e

SRPT_BASE_DIR="${SRPT_BASE_DIR:-$HOME/.local/share/srpt}"
PYTHON_VERSION="3.13.12"
PYTHON_BUILD_STANDALONE_TAG="20260211"
PYTHON_BIN="$SRPT_BASE_DIR/python/$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG/python/bin/python3"
SRPT_LIB="$SRPT_BASE_DIR/lib/srpt"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Managed Python not found at $PYTHON_BIN"
    echo "Please run the installer: curl -sSL https://raw.githubusercontent.com/thie1210/srpt/v$SRPT_VERSION/install.sh | sh"
    exit 1
fi

if [ ! -d "$SRPT_LIB" ]; then
    echo "Error: srpt not installed at $SRPT_LIB"
    echo "Please run the installer: curl -sSL https://raw.githubusercontent.com/thie1210/srpt/v$SRPT_VERSION/install.sh | sh"
    exit 1
fi

export PYTHONPATH="$SRPT_LIB/src"
exec "$PYTHON_BIN" "$SRPT_LIB/src/srpt/__main__.py" "$@"
EOF
    
    chmod +x "$launcher"
    echo "  ✓ srpt launcher created at $launcher"
}

# Finalize installation
finalize() {
    echo ""
    echo "INSTALLATION"
    echo "  ✓ srpt installed to $SRPT_BIN_DIR/srpt"
    echo ""
    
    # Check if srpt is in PATH
    if ! command -v srpt > /dev/null 2>&1; then
        echo "PATH"
        echo "  ⚠ srpt not in PATH"
        echo "  → Add to PATH: export PATH=\"$SRPT_BIN_DIR:\$PATH\""
        echo "  → Add to shell profile (~/.bashrc, ~/.zshrc) for permanence"
        echo ""
    else
        srpt --version
        echo ""
    fi
    
    echo "QUICK START"
    echo "  srpt                    # Start Python REPL"
    echo "  srpt script.py          # Run a Python script"
    echo "  srpt install requests   # Install a package"
    echo "  srpt status             # Show project status"
    echo ""
}

# Main
main() {
    echo "SRPT INSTALLER"
    echo ""
    
    need_cmd curl
    need_cmd tar
    
    install_python
    install_srpt
    finalize
}

# Run
main "$@"
