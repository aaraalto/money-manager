#!/bin/bash
set -e

# Directory setup
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT_DIR/bin"
STATIC_DIR="$ROOT_DIR/app/static"

mkdir -p "$BIN_DIR"

# Versions
TAILWIND_VERSION="v3.4.1"
ESBUILD_VERSION="0.19.11"
BIOME_VERSION="v1.9.4"

# Detect OS/Arch
OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" = "Darwin" ]; then
    PLATFORM="macos"
    if [ "$ARCH" = "arm64" ]; then
        ARCH="arm64"
    else
        ARCH="x64"
    fi
elif [ "$OS" = "Linux" ]; then
    PLATFORM="linux"
    ARCH="x64" # Assuming x64 for Linux for now
else
    echo "Unsupported OS"
    exit 1
fi

download_tailwind() {
    if [ ! -f "$BIN_DIR/tailwindcss" ]; then
        echo "Downloading Tailwind CSS..."
        curl -k -sL "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-${PLATFORM}-${ARCH}" -o "$BIN_DIR/tailwindcss"
        chmod +x "$BIN_DIR/tailwindcss"
    fi
}

download_esbuild() {
    if [ ! -f "$BIN_DIR/esbuild" ]; then
        echo "Downloading ESBuild..."
        # ESBuild release naming is slightly different
        if [ "$PLATFORM" = "macos" ]; then
            ESBUILD_PLATFORM="darwin"
        else
            ESBUILD_PLATFORM="linux"
        fi
        
        curl -k -sL "https://registry.npmjs.org/@esbuild/${ESBUILD_PLATFORM}-${ARCH}/-/${ESBUILD_PLATFORM}-${ARCH}-${ESBUILD_VERSION}.tgz" | tar -xz -C "$BIN_DIR" --strip-components=2 package/bin/esbuild
    fi
}

download_biome() {
    if [ ! -f "$BIN_DIR/biome" ]; then
        echo "Downloading Biome..."
        # Biome naming convention
        if [ "$PLATFORM" = "macos" ]; then
            BIOME_PLATFORM="darwin"
        else
            BIOME_PLATFORM="linux"
        fi
        
        curl -k -sL "https://github.com/biomejs/biome/releases/download/cli/${BIOME_VERSION}/biome-${BIOME_PLATFORM}-${ARCH}" -o "$BIN_DIR/biome"
        chmod +x "$BIN_DIR/biome"
    fi
}

cmd_install() {
    download_tailwind
    download_esbuild
    download_biome
    echo "Tools installed in $BIN_DIR"
}

cmd_watch() {
    echo "Starting Watch Mode..."
    
    # Tailwind Watch
    "$BIN_DIR/tailwindcss" -i "$STATIC_DIR/css/input.css" -o "$STATIC_DIR/css/output.css" --watch &
    
    # ESBuild Watch
    # Scan all entry points in ts/modules
    # For now, we'll just target the main entry point or specific modules
    # A robust way is to find all files, but let's start with specific mapping for the migration
    # We map ts/modules/api.ts -> js/modules/api.js
    
    "$BIN_DIR/esbuild" "$STATIC_DIR/ts/modules/api.ts" --outfile="$STATIC_DIR/js/modules/api.js" --bundle --format=esm --watch &
    
    wait
}

cmd_build() {
    echo "Building for production..."
    "$BIN_DIR/tailwindcss" -i "$STATIC_DIR/css/input.css" -o "$STATIC_DIR/css/output.css" --minify
    "$BIN_DIR/esbuild" "$STATIC_DIR/ts/modules/api.ts" --outfile="$STATIC_DIR/js/modules/api.js" --bundle --format=esm --minify
}

cmd_lint() {
    echo "Linting..."
    "$BIN_DIR/biome" lint "$STATIC_DIR/ts"
}

cmd_format() {
    echo "Formatting..."
    "$BIN_DIR/biome" format --write "$STATIC_DIR/ts"
}

case "$1" in
    install)
        cmd_install
        ;;
    watch)
        cmd_install
        cmd_watch
        ;;
    build)
        cmd_install
        cmd_build
        ;;
    lint)
        cmd_install
        cmd_lint
        ;;
    format)
        cmd_install
        cmd_format
        ;;
    *)
        echo "Usage: $0 {install|watch|build|lint|format}"
        exit 1
        ;;
esac

