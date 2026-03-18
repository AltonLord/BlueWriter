#!/bin/bash
#
# Build BlueWriter release packages
#
# This script creates distributable installer packages:
# - Linux: Self-extracting .run file
# - Windows: Self-extracting .exe (via 7z SFX) or zip with launcher
#
# Usage: ./build-packages.sh [version]
# Example: ./build-packages.sh 1.0.0-beta
#

set -e

# Configuration
VERSION="${1:-1.0.0-beta}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SOURCE_DIR/dist"
MAKESELF="/tmp/makeself/makeself.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Building BlueWriter v${VERSION} packages...${NC}"
echo ""

# Create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$BUILD_DIR/staging"

# -----------------------------------------------------------------------------
# Prepare source files (common for all platforms)
# -----------------------------------------------------------------------------

echo -e "${GREEN}►${NC} Preparing source files..."

# Create staging directory with clean source
STAGING="$BUILD_DIR/staging/BlueWriter"
mkdir -p "$STAGING"

# Copy source files, excluding dev/build artifacts
rsync -a \
    --exclude='venv' \
    --exclude='dist' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='data/*.db' \
    --exclude='data/*.db-wal' \
    --exclude='data/*.db-shm' \
    --exclude='.coverage' \
    --exclude='htmlcov' \
    --exclude='*.egg-info' \
    "$SOURCE_DIR/" "$STAGING/"

# Remove any cached bytecode
find "$STAGING" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$STAGING" -type f -name "*.pyc" -delete 2>/dev/null || true

echo -e "${GREEN}✓${NC} Source files prepared"

# -----------------------------------------------------------------------------
# Build Linux self-extracting installer
# -----------------------------------------------------------------------------

echo -e "${GREEN}►${NC} Building Linux package..."

# Check for makeself
if [ ! -f "$MAKESELF" ]; then
    echo "Downloading makeself..."
    cd /tmp
    curl -sL https://github.com/megastep/makeself/releases/download/release-2.5.0/makeself-2.5.0.run -o makeself.run
    chmod +x makeself.run
    ./makeself.run --target /tmp/makeself --quiet
    cd "$SCRIPT_DIR"
fi

# Create the self-extracting archive
LINUX_PACKAGE="$BUILD_DIR/BlueWriter-${VERSION}-linux-x64.run"

"$MAKESELF" --gzip --current \
    "$STAGING" \
    "$LINUX_PACKAGE" \
    "BlueWriter v${VERSION} Installer" \
    ./installer/install-linux.sh

chmod +x "$LINUX_PACKAGE"

echo -e "${GREEN}✓${NC} Linux package: $(basename "$LINUX_PACKAGE")"

# -----------------------------------------------------------------------------
# Build Windows package (zip with auto-extract launcher)
# -----------------------------------------------------------------------------

echo -e "${GREEN}►${NC} Building Windows package..."

# Create Windows-specific staging
WIN_STAGING="$BUILD_DIR/staging-win/BlueWriter"
mkdir -p "$WIN_STAGING"
cp -r "$STAGING"/* "$WIN_STAGING/"

# Create a simple batch launcher that extracts and runs the installer
cat > "$BUILD_DIR/staging-win/Install-BlueWriter.bat" << 'BATCH'
@echo off
title BlueWriter Installer
echo.
echo  ============================================
echo   BlueWriter Installer
echo   AI-Powered Fiction Writing
echo  ============================================
echo.
echo  This will install BlueWriter on your system.
echo.
pause

cd /d "%~dp0"
cd BlueWriter
powershell -ExecutionPolicy Bypass -File installer\install-windows.ps1

pause
BATCH

# Create zip for Windows
WINDOWS_ZIP="$BUILD_DIR/BlueWriter-${VERSION}-windows-x64.zip"
cd "$BUILD_DIR/staging-win"
zip -rq "$WINDOWS_ZIP" .
cd "$SCRIPT_DIR"

echo -e "${GREEN}✓${NC} Windows package: $(basename "$WINDOWS_ZIP")"

# -----------------------------------------------------------------------------
# Also create a simple portable zip (no installer, for advanced users)
# -----------------------------------------------------------------------------

echo -e "${GREEN}►${NC} Building portable package..."

PORTABLE_ZIP="$BUILD_DIR/BlueWriter-${VERSION}-portable.zip"
cd "$BUILD_DIR/staging"
zip -rq "$PORTABLE_ZIP" BlueWriter
cd "$SCRIPT_DIR"

echo -e "${GREEN}✓${NC} Portable package: $(basename "$PORTABLE_ZIP")"

# -----------------------------------------------------------------------------
# Create checksums
# -----------------------------------------------------------------------------

echo -e "${GREEN}►${NC} Generating checksums..."

cd "$BUILD_DIR"
sha256sum *.run *.zip > SHA256SUMS.txt 2>/dev/null || true

echo -e "${GREEN}✓${NC} Checksums generated"

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------

rm -rf "$BUILD_DIR/staging"
rm -rf "$BUILD_DIR/staging-win"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Packages created in: $BUILD_DIR"
echo ""
ls -lh "$BUILD_DIR"/*.run "$BUILD_DIR"/*.zip 2>/dev/null
echo ""
echo "SHA256 Checksums:"
cat "$BUILD_DIR/SHA256SUMS.txt"
echo ""
echo -e "${BLUE}Distribution Instructions:${NC}"
echo ""
echo "Linux users:"
echo "  1. Download BlueWriter-${VERSION}-linux-x64.run"
echo "  2. chmod +x BlueWriter-*.run"
echo "  3. ./BlueWriter-${VERSION}-linux-x64.run"
echo ""
echo "Windows users:"
echo "  1. Download BlueWriter-${VERSION}-windows-x64.zip"
echo "  2. Extract the zip"
echo "  3. Double-click Install-BlueWriter.bat"
echo ""
