#!/usr/bin/env python3
"""
Generate BlueWriter application icons in various formats.

Run this script to create icon files:
    python generate_icons.py

Requires: Pillow (pip install Pillow)
Optional: cairosvg for SVG conversion (pip install cairosvg)
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    exit(1)

# Icon configuration
ICON_SIZES = [16, 32, 48, 64, 128, 256, 512]
OUTPUT_DIR = Path(__file__).parent

# Colors
BACKGROUND_COLOR = "#2563eb"  # Blue
TEXT_COLOR = "#ffffff"  # White
ACCENT_COLOR = "#60a5fa"  # Light blue


def create_icon(size: int) -> Image.Image:
    """Create a BlueWriter icon at the specified size."""
    
    # Create image with background
    img = Image.new('RGBA', (size, size), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Calculate proportions
    padding = size // 8
    
    # Draw a stylized book/page shape
    page_left = padding
    page_top = padding
    page_right = size - padding
    page_bottom = size - padding
    
    # Draw page background (slightly lighter)
    corner_radius = size // 10
    draw.rounded_rectangle(
        [page_left, page_top, page_right, page_bottom],
        radius=corner_radius,
        fill="#1e40af"  # Darker blue
    )
    
    # Draw inner page (lighter)
    inner_padding = size // 6
    draw.rounded_rectangle(
        [page_left + inner_padding // 2, page_top + inner_padding // 2,
         page_right - inner_padding // 2, page_bottom - inner_padding // 2],
        radius=corner_radius // 2,
        fill="#3b82f6"
    )
    
    # Draw "BW" text
    try:
        # Try to find a nice font
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        
        font = None
        font_size = size // 3
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
        
        if font is None:
            font = ImageFont.load_default()
            font_size = size // 4
            
    except Exception:
        font = ImageFont.load_default()
        font_size = size // 4
    
    # Draw text centered
    text = "BW"
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - bbox[1]  # Adjust for baseline
    
    # Draw text with slight shadow
    shadow_offset = max(1, size // 64)
    draw.text((text_x + shadow_offset, text_y + shadow_offset), text, 
              font=font, fill="#1e3a8a")  # Shadow
    draw.text((text_x, text_y), text, font=font, fill=TEXT_COLOR)
    
    # Draw a small quill/pen accent
    pen_size = size // 8
    pen_x = size - padding - pen_size
    pen_y = size - padding - pen_size
    
    # Simple diagonal line representing a pen
    draw.line(
        [(pen_x, pen_y + pen_size), (pen_x + pen_size, pen_y)],
        fill=ACCENT_COLOR,
        width=max(1, size // 32)
    )
    
    return img


def create_ico(output_path: Path, sizes: list = None):
    """Create a Windows .ico file with multiple sizes."""
    if sizes is None:
        sizes = [16, 32, 48, 256]
    
    images = [create_icon(size) for size in sizes]
    
    # Save as ICO
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )
    print(f"Created: {output_path}")


def create_png(output_path: Path, size: int):
    """Create a PNG icon at specified size."""
    img = create_icon(size)
    img.save(output_path, format='PNG')
    print(f"Created: {output_path}")


def create_icns(output_path: Path):
    """Create a macOS .icns file."""
    # For proper ICNS, we'd need iconutil or a library
    # For now, create the PNG that macOS can use
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    # Create iconset directory
    iconset_dir = output_path.with_suffix('.iconset')
    iconset_dir.mkdir(exist_ok=True)
    
    for size in sizes:
        img = create_icon(size)
        img.save(iconset_dir / f"icon_{size}x{size}.png")
        
        # Also create @2x versions
        if size <= 512:
            img2x = create_icon(size * 2)
            img2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")
    
    print(f"Created iconset at: {iconset_dir}")
    print("To create .icns on macOS, run:")
    print(f"  iconutil -c icns {iconset_dir}")


def main():
    """Generate all icon files."""
    print("Generating BlueWriter icons...")
    print()
    
    # Create PNG icons
    for size in ICON_SIZES:
        create_png(OUTPUT_DIR / f"icon_{size}.png", size)
    
    # Create main icon.png (256px for general use)
    create_png(OUTPUT_DIR / "icon.png", 256)
    
    # Create Windows ICO
    create_ico(OUTPUT_DIR / "icon.ico")
    
    # Create macOS iconset (user can convert to .icns)
    # create_icns(OUTPUT_DIR / "icon.icns")
    
    print()
    print("Done! Icon files created in:", OUTPUT_DIR)
    print()
    print("Files created:")
    for f in OUTPUT_DIR.glob("icon*"):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
