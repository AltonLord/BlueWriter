#!/bin/bash
#
# BlueWriter Installer for Linux (Ubuntu/Debian)
# 
# This script installs BlueWriter and all its dependencies.
# Run with: ./install-linux.sh
#
# What it does:
# 1. Checks for Python 3.10+ (installs if needed)
# 2. Ensures python3-venv is installed
# 3. Creates a virtual environment
# 4. Installs all Python dependencies
# 5. Creates a desktop launcher
# 6. Sets up the application for easy launching
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="BlueWriter"
APP_ID="com.bluewriter.app"
MIN_PYTHON_VERSION="3.10"
INSTALL_DIR="$HOME/.local/share/bluewriter"
DESKTOP_DIR="$HOME/.local/share/applications"
BIN_DIR="$HOME/.local/bin"

# Get the directory where the source code is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}║${NC}              ${GREEN}BlueWriter Installer${NC}                         ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}              AI-Powered Fiction Writing                    ${BLUE}║${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}►${NC} $1"
}

print_warning() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${RED}✗${NC} $1"
}

print_success() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}✓${NC} $1"
}

# Compare version numbers
version_gte() {
    # Returns 0 (true) if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# -----------------------------------------------------------------------------
# Dependency Checks
# -----------------------------------------------------------------------------

check_python() {
    print_step "Checking Python installation..."
    
    # Try different Python commands (including newer versions)
    for cmd in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$cmd" &> /dev/null; then
            local version=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            if version_gte "$version" "$MIN_PYTHON_VERSION"; then
                PYTHON_CMD="$cmd"
                PYTHON_VERSION="$version"
                print_success "Found $cmd (version $version)"
                return 0
            fi
        fi
    done
    
    return 1
}

ensure_venv_package() {
    print_step "Checking Python venv support..."
    
    # Test if venv works
    local test_dir=$(mktemp -d)
    if $PYTHON_CMD -m venv "$test_dir/test_venv" 2>/dev/null; then
        rm -rf "$test_dir"
        print_success "Python venv is available"
        return 0
    fi
    rm -rf "$test_dir"
    
    print_warning "Python venv not available, installing..."
    
    # Detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        DISTRO="unknown"
    fi
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            if [ "$EUID" -ne 0 ]; then
                SUDO="sudo"
                print_warning "Root privileges required to install python3-venv."
            else
                SUDO=""
            fi
            
            # Install venv for the specific Python version
            local venv_package="python${PYTHON_VERSION}-venv"
            print_step "Installing $venv_package..."
            $SUDO apt-get update -qq
            $SUDO apt-get install -y "$venv_package" || {
                # Fallback to generic python3-venv
                print_warning "Specific venv package not found, trying python3-venv..."
                $SUDO apt-get install -y python3-venv
            }
            ;;
            
        fedora|rhel|centos|rocky|alma)
            if [ "$EUID" -ne 0 ]; then
                SUDO="sudo"
            else
                SUDO=""
            fi
            # On Fedora/RHEL, venv is usually included, but ensure pip is there
            $SUDO dnf install -y python3-pip
            ;;
            
        arch|manjaro)
            # Arch includes venv by default with python
            print_warning "venv should be included with Python on Arch"
            ;;
            
        *)
            print_error "Cannot auto-install python3-venv for $DISTRO"
            print_error "Please install it manually: sudo apt install python${PYTHON_VERSION}-venv"
            exit 1
            ;;
    esac
    
    # Verify it works now
    local test_dir=$(mktemp -d)
    if $PYTHON_CMD -m venv "$test_dir/test_venv" 2>/dev/null; then
        rm -rf "$test_dir"
        print_success "Python venv is now available"
        return 0
    fi
    rm -rf "$test_dir"
    
    print_error "Failed to set up Python venv"
    exit 1
}

install_python() {
    print_step "Python $MIN_PYTHON_VERSION+ not found. Installing..."
    
    # Detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        print_error "Cannot detect Linux distribution"
        exit 1
    fi
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            print_step "Detected $DISTRO - using apt..."
            
            # Check if we need sudo
            if [ "$EUID" -ne 0 ]; then
                SUDO="sudo"
                print_warning "Root privileges required. You may be prompted for your password."
            else
                SUDO=""
            fi
            
            # Add deadsnakes PPA for newer Python (Ubuntu)
            if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "pop" ] || [ "$DISTRO" = "linuxmint" ]; then
                print_step "Adding deadsnakes PPA for Python 3.11..."
                $SUDO apt-get update -qq
                $SUDO apt-get install -y software-properties-common
                $SUDO add-apt-repository -y ppa:deadsnakes/ppa
                $SUDO apt-get update -qq
            fi
            
            # Install Python 3.11 (well-supported, stable)
            print_step "Installing Python 3.11..."
            $SUDO apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
            
            PYTHON_CMD="python3.11"
            PYTHON_VERSION="3.11"
            ;;
            
        fedora|rhel|centos|rocky|alma)
            print_step "Detected $DISTRO - using dnf..."
            
            if [ "$EUID" -ne 0 ]; then
                SUDO="sudo"
            else
                SUDO=""
            fi
            
            $SUDO dnf install -y python3.11 python3.11-devel python3-pip
            PYTHON_CMD="python3.11"
            PYTHON_VERSION="3.11"
            ;;
            
        arch|manjaro)
            print_step "Detected $DISTRO - using pacman..."
            
            if [ "$EUID" -ne 0 ]; then
                SUDO="sudo"
            else
                SUDO=""
            fi
            
            $SUDO pacman -Sy --noconfirm python python-pip
            PYTHON_CMD="python3"
            PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            ;;
            
        *)
            print_error "Unsupported distribution: $DISTRO"
            print_error "Please install Python $MIN_PYTHON_VERSION+ manually and run this script again."
            exit 1
            ;;
    esac
    
    # Verify installation
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python installation failed"
        exit 1
    fi
    
    print_success "Python installed successfully"
}

install_system_dependencies() {
    print_step "Checking system dependencies for Qt..."
    
    # Detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        DISTRO="unknown"
    fi
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            if [ "$EUID" -ne 0 ]; then
                SUDO="sudo"
            else
                SUDO=""
            fi
            
            # Install Qt dependencies
            print_step "Installing Qt system dependencies..."
            $SUDO apt-get install -y \
                libxkbcommon0 \
                libxcb-cursor0 \
                libxcb-icccm4 \
                libxcb-image0 \
                libxcb-keysyms1 \
                libxcb-randr0 \
                libxcb-render-util0 \
                libxcb-shape0 \
                libxcb-xfixes0 \
                libxcb-xinerama0 \
                libegl1 \
                libgl1 \
                libdbus-1-3 \
                2>/dev/null || true
            ;;
        *)
            print_warning "Cannot auto-install Qt dependencies for $DISTRO"
            print_warning "If BlueWriter fails to start, install Qt6/xcb libraries manually"
            ;;
    esac
}

# -----------------------------------------------------------------------------
# Installation
# -----------------------------------------------------------------------------

create_directories() {
    print_step "Creating installation directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$INSTALL_DIR/data"
    
    print_success "Directories created"
}

copy_source_files() {
    print_step "Copying application files..."
    
    # Copy all source files except venv and data
    rsync -a --exclude='venv' \
             --exclude='data/*.db' \
             --exclude='data/*.db-*' \
             --exclude='__pycache__' \
             --exclude='.git' \
             --exclude='.pytest_cache' \
             --exclude='*.pyc' \
             --exclude='installer' \
             "$SOURCE_DIR/" "$INSTALL_DIR/"
    
    print_success "Application files copied"
}

create_virtual_environment() {
    print_step "Creating Python virtual environment..."
    
    # Remove old venv if exists
    if [ -d "$INSTALL_DIR/venv" ]; then
        rm -rf "$INSTALL_DIR/venv"
    fi
    
    # Create new venv
    $PYTHON_CMD -m venv "$INSTALL_DIR/venv"
    
    if [ ! -f "$INSTALL_DIR/venv/bin/python" ]; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    
    print_success "Virtual environment created"
}

install_python_packages() {
    print_step "Installing Python packages (this may take a few minutes)..."
    
    # Activate venv and install
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip first
    pip install --upgrade pip --quiet
    
    # Install requirements
    pip install -r "$INSTALL_DIR/requirements.txt" --quiet
    
    deactivate
    
    print_success "Python packages installed"
}

create_launcher_script() {
    print_step "Creating launcher script..."
    
    cat > "$INSTALL_DIR/bluewriter.sh" << 'LAUNCHER'
#!/bin/bash
#
# BlueWriter Launcher
# This script activates the virtual environment and runs BlueWriter
#

INSTALL_DIR="$HOME/.local/share/bluewriter"

# Change to install directory
cd "$INSTALL_DIR"

# Activate virtual environment
source "$INSTALL_DIR/venv/bin/activate"

# Run BlueWriter
python main.py "$@"

# Deactivate on exit
deactivate
LAUNCHER

    chmod +x "$INSTALL_DIR/bluewriter.sh"
    
    # Create symlink in bin directory
    ln -sf "$INSTALL_DIR/bluewriter.sh" "$BIN_DIR/bluewriter"
    
    print_success "Launcher script created"
}

create_desktop_entry() {
    print_step "Creating desktop launcher..."
    
    # Create icon directory if needed
    mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
    
    # Check if we have an icon, if not create a simple one
    if [ -f "$INSTALL_DIR/resources/icon.png" ]; then
        cp "$INSTALL_DIR/resources/icon.png" "$HOME/.local/share/icons/hicolor/256x256/apps/bluewriter.png"
    else
        # Create a simple placeholder icon using Python
        "$INSTALL_DIR/venv/bin/python" << 'ICONSCRIPT'
import os
try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a 256x256 image
    img = Image.new('RGB', (256, 256), color='#2563eb')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "BW" text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    draw.text((60, 80), "BW", fill='white', font=font)
    
    icon_path = os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps/bluewriter.png")
    img.save(icon_path)
except ImportError:
    # PIL not available, skip icon creation
    pass
ICONSCRIPT
    fi
    
    # Create desktop entry
    cat > "$DESKTOP_DIR/bluewriter.desktop" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=BlueWriter
Comment=AI-Powered Fiction Writing Application
Exec=$HOME/.local/bin/bluewriter
Icon=bluewriter
Terminal=false
Categories=Office;WordProcessor;Literature;
Keywords=writing;fiction;novel;story;ai;
StartupNotify=true
StartupWMClass=BlueWriter
DESKTOP

    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi
    
    # Update icon cache
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi
    
    print_success "Desktop launcher created"
}

create_uninstaller() {
    print_step "Creating uninstaller..."
    
    cat > "$INSTALL_DIR/uninstall.sh" << 'UNINSTALL'
#!/bin/bash
#
# BlueWriter Uninstaller
#

echo "Uninstalling BlueWriter..."

INSTALL_DIR="$HOME/.local/share/bluewriter"
DESKTOP_DIR="$HOME/.local/share/applications"
BIN_DIR="$HOME/.local/bin"

# Remove desktop entry
rm -f "$DESKTOP_DIR/bluewriter.desktop"

# Remove launcher symlink
rm -f "$BIN_DIR/bluewriter"

# Remove icon
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/bluewriter.png"

# Ask about data
read -p "Remove user data (projects, stories)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$INSTALL_DIR"
    echo "BlueWriter completely removed."
else
    # Remove everything except data
    find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 ! -name 'data' -exec rm -rf {} +
    echo "BlueWriter removed. Your data is preserved in $INSTALL_DIR/data"
fi

# Update desktop database
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "Uninstallation complete."
UNINSTALL

    chmod +x "$INSTALL_DIR/uninstall.sh"
    
    print_success "Uninstaller created"
}

# -----------------------------------------------------------------------------
# Main Installation Flow
# -----------------------------------------------------------------------------

main() {
    print_header
    
    echo "This installer will set up BlueWriter on your system."
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo "Source directory: $SOURCE_DIR"
    echo ""
    
    read -p "Continue with installation? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo ""
    echo -e "${BLUE}Starting installation...${NC}"
    echo ""
    
    # Step 1: Check/Install Python
    if ! check_python; then
        install_python
    fi
    
    # Step 2: Ensure venv package is installed
    ensure_venv_package
    
    # Step 3: Install system dependencies
    install_system_dependencies
    
    # Step 4: Create directories
    create_directories
    
    # Step 5: Copy source files
    copy_source_files
    
    # Step 6: Create virtual environment
    create_virtual_environment
    
    # Step 7: Install Python packages
    install_python_packages
    
    # Step 8: Create launcher
    create_launcher_script
    
    # Step 9: Create desktop entry
    create_desktop_entry
    
    # Step 10: Create uninstaller
    create_uninstaller
    
    # Done!
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║              Installation Complete! 🎉                     ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "You can now launch BlueWriter by:"
    echo ""
    echo "  1. Clicking the 'BlueWriter' icon in your applications menu"
    echo "  2. Running 'bluewriter' from the terminal"
    echo ""
    echo "To uninstall, run: $INSTALL_DIR/uninstall.sh"
    echo ""
    
    # Offer to launch now
    read -p "Launch BlueWriter now? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        "$BIN_DIR/bluewriter" &
    fi
}

# Run main function
main "$@"
