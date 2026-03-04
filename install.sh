#!/bin/bash
#
# Py Installer - Bootstrap script for the py package manager
# This script downloads Python and py without requiring an existing Python installation
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/thie1210/py/main/install.sh | sh
#   curl -sSL https://raw.githubusercontent.com/thie1210/py/main/install.sh | sh -s -- --help
#
# Based on rustup and uv installation patterns
#

set -euo pipefail

# Configuration
PY_VERSION="0.1.1"
PYTHON_VERSION="3.13.12"
PYTHON_BUILD_STANDALONE_TAG="20260211"
PY_BASE_DIR="${PY_BASE_DIR:-$HOME/.local/share/py}"
PY_BIN_DIR="${PY_BIN_DIR:-$HOME/.local/bin}"

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
    local python_dir="$PY_BASE_DIR/python/$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG"
    local python_url="https://github.com/astral-sh/python-build-standalone/releases/download/$PYTHON_BUILD_STANDALONE_TAG/cpython-$PYTHON_VERSION+$PYTHON_BUILD_STANDALONE_TAG-$platform-install_only.tar.gz"
    local download_file="$PY_BASE_DIR/downloads/python.tar.gz"
    
    if [ -f "$python_dir/python/bin/python3" ]; then
        echo "  ✓ Python $PYTHON_VERSION already installed"
        return 0
    fi
    
    echo ""
    echo "PYTHON"
    echo "  Installing Python $PYTHON_VERSION for $platform..."
    
    mkdir -p "$PY_BASE_DIR/downloads"
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
install_py() {
    local python_bin="$PY_BASE_DIR/python/$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG/python/bin/python3"
    
    echo ""
    echo "PY"
    echo "  Installing py $PY_VERSION..."
    
    # Create lib directory for py installation
    mkdir -p "$PY_BASE_DIR/lib"
    mkdir -p "$PY_BASE_DIR/downloads"
    
    # Download py source from GitHub
    local py_url="https://github.com/thie1210/py/archive/refs/tags/v$PY_VERSION.tar.gz"
    local download_file="$PY_BASE_DIR/downloads/py.tar.gz"
    
    echo "  Downloading py $PY_VERSION..."
    if ! download "$py_url" "$download_file"; then
        err "Failed to download py. Please check your internet connection."
    fi
    
    echo "  Extracting..."
    tar -xzf "$download_file" -C "$PY_BASE_DIR/downloads" || err "Failed to extract py"
    rm -f "$download_file"
    
    # Move to final location
    local extracted_dir="$PY_BASE_DIR/downloads/py-$PY_VERSION"
    if [ -d "$extracted_dir" ]; then
        mv "$extracted_dir" "$PY_BASE_DIR/lib/py"
        echo "  ✓ py installed to $PY_BASE_DIR/lib/py"
    else
        err "Failed to find extracted py source"
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
    local launcher="$PY_BIN_DIR/py"
    mkdir -p "$PY_BIN_DIR"
    
    cat > "$launcher" << 'EOF'
#!/bin/bash
# Py launcher script
# This script runs py using the managed Python installation

set -e

PY_BASE_DIR="${PY_BASE_DIR:-$HOME/.local/share/py}"
PYTHON_VERSION="3.13.12"
PYTHON_BUILD_STANDALONE_TAG="20260211"
PYTHON_BIN="$PY_BASE_DIR/python/$PYTHON_VERSION-$PYTHON_BUILD_STANDALONE_TAG/python/bin/python3"
PY_LIB="$PY_BASE_DIR/lib/py"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Managed Python not found at $PYTHON_BIN"
    echo "Please run the installer: curl -sSL https://raw.githubusercontent.com/thie1210/py/v$PY_VERSION/install.sh | sh"
    exit 1
fi

if [ ! -d "$PY_LIB" ]; then
    echo "Error: py not installed at $PY_LIB"
    echo "Please run the installer: curl -sSL https://raw.githubusercontent.com/thie1210/py/v$PY_VERSION/install.sh | sh"
    exit 1
fi

export PYTHONPATH="$PY_LIB/src"
exec "$PYTHON_BIN" "$PY_LIB/src/py/__main__.py" "$@"
EOF
    
    chmod +x "$launcher"
    echo "  ✓ py launcher created at $launcher"
}

# Finalize installation
finalize() {
    echo ""
    echo "INSTALLATION"
    echo "  ✓ py installed to $PY_BIN_DIR/py"
    echo ""
    
    # Check if py is in PATH
    if ! command -v py > /dev/null 2>&1; then
        echo "PATH"
        echo "  ⚠ py not in PATH"
        echo "  → Add to PATH: export PATH=\"$PY_BIN_DIR:\$PATH\""
        echo "  → Add to shell profile (~/.bashrc, ~/.zshrc) for permanence"
        echo ""
    else
        py --version
        echo ""
    fi
    
    echo "QUICK START"
    echo "  py                    # Start Python REPL"
    echo "  py script.py          # Run a Python script"
    echo "  py install requests   # Install a package"
    echo "  py status             # Show project status"
    echo ""
}

# Main
main() {
    echo "PY INSTALLER"
    echo ""
    
    need_cmd curl
    need_cmd tar
    
    install_python
    install_py
    finalize
}

# Run
main "$@"
