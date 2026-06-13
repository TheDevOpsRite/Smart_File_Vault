#!/usr/bin/env python
"""
Build script for Smart File Vault
Generates a lean standalone .exe using PyInstaller and prepares it for Inno Setup
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def log(message: str, level: str = "INFO") -> None:
    """Print a formatted log message"""
    print(f"[{level}] {message}")

def run_command(cmd: list[str], description: str) -> bool:
    """Execute a shell command and handle errors"""
    log(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log(f"✓ {description}", level="SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        log(f"✗ {description} failed", level="ERROR")
        if e.stdout:
            log(f"stdout: {e.stdout}")
        if e.stderr:
            log(f"stderr: {e.stderr}")
        return False

def cleanup_dist_directory(dist_dir: Path) -> None:
    """Remove unnecessary files from dist directory to reduce installer size"""
    log("\n[Optimization] Cleaning up unnecessary files...")
    
    unnecessary_patterns = [
        "*.pyc",          # Compiled Python files
        "__pycache__",    # Python cache directories
        "*.pyo",          # Optimized Python files
        "*.dist-info",    # Package metadata
        "*.egg-info",     # Egg metadata
        "tcl",            # TCL files (not needed for our app)
        "tk",             # Tk files (not needed)
        "tests",          # Test directories
        "test",           # Test directories
        "*.txt",          # Text documentation (except required ones)
    ]
    
    app_dir = dist_dir / "SmartFileVault"
    removed_size = 0
    
    if app_dir.exists():
        for pattern in unnecessary_patterns:
            for item in app_dir.rglob(pattern):
                try:
                    if item.is_dir():
                        size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                        shutil.rmtree(item)
                        removed_size += size
                        log(f"  ✓ Removed directory: {item.name}")
                    elif item.is_file():
                        removed_size += item.stat().st_size
                        item.unlink()
                        log(f"  ✓ Removed file: {item.name}")
                except Exception as e:
                    log(f"  ⚠ Could not remove {item.name}: {e}", level="WARN")
    
    if removed_size > 0:
        removed_mb = removed_size / (1024 * 1024)
        log(f"✓ Freed {removed_mb:.2f} MB of space")

def ensure_windows_icon(project_root: Path) -> Path:
    """Create a Windows .ico file from the app logo for installer and exe branding."""
    from PIL import Image

    png_path = project_root / "appLogo.png"
    ico_path = project_root / "appLogo.ico"

    image = Image.open(png_path).convert("RGBA")
    image.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    return ico_path

def ensure_installer_images(project_root: Path) -> tuple[Path, Path]:
    """Create Inno Setup wizard bitmaps from the app logo."""
    from PIL import Image, ImageOps

    png_path = project_root / "appLogo.png"
    wizard_image_path = project_root / "WizardImage.bmp"
    wizard_small_image_path = project_root / "WizardSmallImage.bmp"

    source = Image.open(png_path).convert("RGBA")

    def make_panel(size: tuple[int, int], logo_size: int) -> Image.Image:
        panel = Image.new("RGBA", size, (24, 34, 52, 255))
        logo = ImageOps.contain(source, (logo_size, logo_size), Image.Resampling.LANCZOS)
        x = (size[0] - logo.width) // 2
        y = max(28, (size[1] - logo.height) // 3)
        panel.alpha_composite(logo, (x, y))
        return panel.convert("RGB")

    make_panel((164, 314), 108).save(wizard_image_path, format="BMP")
    make_panel((55, 58), 42).save(wizard_small_image_path, format="BMP")

    return wizard_image_path, wizard_small_image_path

def main() -> int:
    """Main build process"""
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    log("=" * 60)
    log("Smart File Vault Build Process", level="BUILD")
    log("=" * 60)

    # Ensure the installer and executable use a proper Windows icon format.
    icon_path = ensure_windows_icon(project_root)
    wizard_image_path, wizard_small_image_path = ensure_installer_images(project_root)

    # Step 1: Check dependencies
    log("\n[Step 1/5] Checking dependencies...")
    required_packages = ["pyinstaller", "cryptography", "PySide6"]
    missing_packages = []

    try:
        import pyinstaller
        log("✓ PyInstaller is installed")
    except ImportError:
        missing_packages.append("pyinstaller")
        log("✗ PyInstaller not found", level="WARN")

    try:
        import cryptography
        log("✓ cryptography is installed")
    except ImportError:
        missing_packages.append("cryptography")
        log("✗ cryptography not found", level="WARN")

    try:
        from PySide6 import QtWidgets
        log("✓ PySide6 is installed")
    except ImportError:
        missing_packages.append("PySide6")
        log("✗ PySide6 not found", level="WARN")

    if missing_packages:
        log(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        if not run_command(
            [sys.executable, "-m", "pip", "install"] + missing_packages,
            f"Install {', '.join(missing_packages)}"
        ):
            log("Failed to install dependencies", level="ERROR")
            return 1

    # Step 2: Clean previous builds
    log("\n[Step 2/5] Cleaning previous builds...")
    for directory in [dist_dir, build_dir]:
        if directory.exists():
            shutil.rmtree(directory)
            log(f"✓ Removed {directory}")

    dist_dir.mkdir(exist_ok=True)
    log(f"✓ Created {dist_dir}")

    # Step 3: Generate optimized PyInstaller spec file
    log("\n[Step 3/6] Generating optimized PyInstaller configuration...")
    
    # Use forward slashes to avoid Unicode escape errors in spec file
    main_py = (project_root / "main.py").as_posix()
    logo_png = (project_root / "appLogo.png").as_posix()
    logo_ico = icon_path.as_posix()
    wizard_image = wizard_image_path.as_posix()
    wizard_small_image = wizard_small_image_path.as_posix()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Smart File Vault - Optimized

a = Analysis(
    ['{main_py}'],
    pathex=[],
    binaries=[],
    datas=[
        ('{logo_png}', '.'),
    ],
    hiddenimports=[
        'cryptography.hazmat.primitives.ciphers.aead',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.hashes',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludedimports=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
        'pytest',
        'unittest',
        'test',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SmartFileVault',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{logo_ico}',
)
'''

    spec_file = project_root / "SmartFileVault.spec"
    spec_file.write_text(spec_content)
    log(f"✓ Created {spec_file}")

    # Step 4: Build with PyInstaller
    log("\n[Step 4/6] Building executable with PyInstaller...")
    if not run_command(
        [sys.executable, "-m", "PyInstaller", str(spec_file), "--distpath", str(dist_dir)],
        "PyInstaller build"
    ):
        log("PyInstaller build failed", level="ERROR")
        return 1

    # Step 5: Cleanup unnecessary files
    log("\n[Step 5/6] Optimizing build size...")
    cleanup_dist_directory(dist_dir)

    # Step 6: Verify build
    log("\n[Step 6/6] Verifying build...")
    exe_path = dist_dir / "SmartFileVault.exe"
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # Convert to MB
        log(f"✓ Executable created: {exe_path} ({file_size:.2f} MB)", level="SUCCESS")
    else:
        log(f"✗ Executable not found at {exe_path}", level="ERROR")
        return 1

    # Summary
    log("\n" + "=" * 60)
    log("Build Complete!", level="SUCCESS")
    log("=" * 60)
    log(f"\nNext steps:")
    log(f"1. Open Inno Setup Compiler")
    log(f"2. Open: {project_root / 'SmartFileVault.iss'}")
    log(f"3. Click 'Compile' to build the installer")
    log(f"\nThe installer will be created in: {dist_dir}")
    log(f"Executable location: {exe_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
