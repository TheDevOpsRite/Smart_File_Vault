@echo off
REM Smart File Vault - Build Batch Script
REM This script automates the build process for creating the installer

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Smart File Vault - Build Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version

REM Check if we're in the correct directory
if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run this script from the Smart File Vault project directory
    pause
    exit /b 1
)

echo [OK] Project directory verified

REM Create dist directory if it doesn't exist
if not exist "dist" (
    mkdir dist
    echo [OK] Created dist directory
)

REM Run the Python build script
echo.
echo Running build process...
echo.
python build.py

if errorlevel 1 (
    echo.
    echo ERROR: Build process failed
    echo Please check the output above for details
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build completed successfully!
echo ============================================================
echo.
echo Next Steps:
echo 1. Open Inno Setup Compiler
echo 2. Open: SmartFileVault.iss
echo 3. Click Compile button
echo 4. The installer will be created in: dist\
echo.
echo For detailed instructions, see: BUILD_GUIDE.md
echo.
pause
exit /b 0
