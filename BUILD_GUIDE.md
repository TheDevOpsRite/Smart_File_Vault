# Smart File Vault - Build and Installation Guide

## Overview
This guide walks you through building a professional installer for Smart File Vault using PyInstaller and Inno Setup.

## Prerequisites

### Required Software
1. **Python 3.8+** - Download from [python.org](https://www.python.org/)
2. **Inno Setup 6.x** - Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)
3. **PyInstaller** - Installed via pip (see below)

### Required Python Packages
The `build.py` script will auto-install these if missing:
- `PyInstaller` - Converts Python to standalone .exe
- `cryptography` - For secure file encryption
- `PySide6` - GUI framework

## Build Process

The build process is highly optimized to create a lean, efficient executable:

### Optimization Features
- ✅ **Stripped Binary** - Removes debugging symbols for smaller file size
- ✅ **UPX Compression** - Further compresses the executable
- ✅ **Excluded Unused Modules** - Removes matplotlib, numpy, scipy, tensorflow, torch, pytest, unittest, and other unnecessary libraries
- ✅ **Cleaned Build Artifacts** - Removes .pyc, __pycache__, TCL/TK, and test directories
- ✅ **Selective Dependencies** - Only includes cryptography and PySide6 (required for operation)
- ✅ **No Source Code in Installer** - All Python code is compiled into the executable; source files are not shipped

### File Inclusion Strategy
**Included in Final Build:**
- SmartFileVault.exe - Compiled executable with all dependencies
- appLogo.png - Application icon
- LICENSE - License file

**NOT Included (saves ~150+ MB):**
- ❌ Python source files (.py files)
- ❌ requirements.txt (not needed by end users)
- ❌ Build artifacts (__pycache__, .pyc, .dist-info)
- ❌ TCL/TK libraries (not used in this GUI app)
- ❌ Test directories and test data
- ❌ Development documentation

#### Step 1: Run the Build Script
```bash
cd "C:\Users\Shivam\Desktop\Smart File Vault"
python build.py
```

This script will:
- ✓ Check and install missing dependencies
- ✓ Clean previous builds
- ✓ Generate PyInstaller configuration
- ✓ Build the standalone executable
- ✓ Create `dist/SmartFileVault.exe`

#### Step 2: Create the Installer
1. Open **Inno Setup Compiler** (iscc.exe)
2. Open the file: `SmartFileVault.iss`
3. Click **Compile** button
4. Wait for compilation to complete
5. The installer will be created as: `dist/SmartFileVault-1.0.0-Setup.exe`

---

### Option 2: Manual Build

#### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
pip install pyinstaller
```

#### Step 2: Create PyInstaller Spec File
Run PyInstaller on main.py:
```bash
pyinstaller --onefile --windowed --icon=appLogo.png --name=SmartFileVault main.py
```

#### Step 3: Compile with Inno Setup
1. Open Inno Setup Compiler
2. Open `SmartFileVault.iss`
3. Click **Compile**

---

## What's Included in the Installer

### Application Files
- ✓ Compiled executable (SmartFileVault.exe) - Contains all Python code, no external dependencies needed
- ✓ Application logo (appLogo.png)
- ✓ License file (MIT)

### NOT Included (Optimized Away)
- ❌ Python source code files - All compiled into the executable
- ❌ requirements.txt - Not needed by end users
- ❌ Build artifacts and cache files

### Installation Features
- ✓ Professional wizard-based installer
- ✓ Custom installation directory selection
- ✓ Start Menu shortcuts
- ✓ Desktop shortcut option
- ✓ .vault file association
- ✓ Uninstall utility
- ✓ Windows Registry integration

### User Data
- ✓ AppData storage location: `C:\Users\<username>\AppData\Roaming\SmartFileVault`
- ✓ Encrypted vault storage: `C:\Users\<username>\AppData\Roaming\SmartFileVault\vault_data`
- ✓ Configuration file: `config.json`

---

## Installation Details

### Default Locations
- **Program Files**: `C:\Program Files\Smart File Vault`
- **User Data**: `%APPDATA%\SmartFileVault`
- **Shortcuts**: Start Menu → Smart File Vault

### System Requirements
- **OS**: Windows 7 SP1 or later
- **Disk Space**: ~150 MB (including Python runtime)
- **RAM**: 512 MB minimum
- **Processor**: Any modern x86/x64 processor

### Install Options
During installation, users can select:
1. Desktop icon (optional)
2. File association for .vault files (optional)

---

## Configuration

### ISS Script Settings

Edit `SmartFileVault.iss` to customize:

```ini
; Application Information
#define MyAppName "Smart File Vault"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "The DevOps Rite"
#define MyAppURL "https://thedevopsrite.in"

; Installation Paths
DefaultDirName={autopf}\{#MyAppName}

; License
LicenseFile={#SourceDir}\LICENSE
```

### Rebuild Distribution
To rebuild the installer with version changes:

1. Update version in `config.py`:
   ```python
   APP_VERSION = "1.1"
   ```

2. Update `SmartFileVault.iss`:
   ```ini
   #define MyAppVersion "1.1.0"
   ```

3. Run: `python build.py`
4. Recompile with Inno Setup

---

## Troubleshooting

### Issue: "PyInstaller not found"
**Solution**: Run `pip install pyinstaller`

### Issue: "Python not in PATH"
**Solution**: Add Python installation directory to Windows PATH:
1. Win + X → System Settings
2. Environment Variables → Edit
3. Add Python path (e.g., `C:\Python313`)

### Issue: "Icon file not found"
**Solution**: Ensure `appLogo.png` exists in project directory

### Issue: "Inno Setup not found"
**Solution**: 
1. Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)
2. Run installer and follow prompts
3. Default path: `C:\Program Files (x86)\Inno Setup 6`

### Issue: Installer won't run after compilation
**Solution**: 
1. Verify SmartFileVault.exe exists in `dist` folder
2. Run `build.py` again
3. Check for virus scanner false positives

---

## Advanced Options

### Code Signing
To sign the installer (optional):

1. Obtain an EV Code Signing Certificate
2. Edit `SmartFileVault.iss`:
   ```ini
   SignTool=signtool sign /f "certificate.pfx" /p password /t "http://timestamp.server" /d "Smart File Vault"
   ```

### Custom Branding
Modify installer appearance:
- **Icon**: Replace `appLogo.png`
- **Welcome Text**: Edit `english.WelcomeLabel1` in ISS file
- **Colors**: Modify `WizardStyle=modern` setting

### Multi-Language Support
Add languages in ISS file:
```ini
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Spanish.isl"
Name: "french"; MessagesFile: "compiler:French.isl"
```

---

## Distribution

### Release Package Contents
- ✓ `SmartFileVault-1.0.0-Setup.exe` (Installer)
- ✓ `LICENSE` (MIT License)
- ✓ `README.md` (Documentation)
- ✓ Release notes and changelog

### Recommended Distribution Methods
1. **Website**: Host on thedevopsrite.in
2. **Direct Download**: Provide direct link to .exe
3. **GitHub Releases**: Upload to GitHub releases page
4. **Installer Hosting**: Use specialized services (e.g., SourceForge, Softpedia)

---

## Uninstallation

Users can uninstall through:
1. **Control Panel** → Programs and Features → Smart File Vault → Uninstall
2. **Start Menu** → Smart File Vault → Uninstall Smart File Vault
3. **Command Line**: 
   ```cmd
   "C:\Program Files\Smart File Vault\unins000.exe" /VERYSILENT
   ```

### Data Retention
- User data in AppData is NOT automatically deleted on uninstall
- Users can manually delete: `C:\Users\<username>\AppData\Roaming\SmartFileVault`

---

## Support

For issues or questions:
- **Website**: https://thedevopsrite.in
- **Email**: support@thedevopsrite.in

---

**Last Updated**: June 13, 2026
**Version**: 1.0.0
