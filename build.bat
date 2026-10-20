@echo off
cd /d "%~dp0"

echo ========================================
echo Building hmkkAI
echo ========================================

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment tidak ditemukan.
    pause
    exit /b 1
)

.venv\Scripts\python.exe -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --name hmkkAI ^
    --collect-all ultralytics ^
    --collect-all cv2 ^
    --collect-all torch ^
    --collect-all torchvision ^
    --collect-all fastapi ^
    --collect-all uvicorn ^
    --collect-all tzdata ^
    main.py

if errorlevel 1 (
    echo.
    echo BUILD GAGAL.
    pause
    exit /b 1
)

copy /Y config.ini "dist\hmkkAI\config.ini"
copy /Y yolo26n.pt "dist\hmkkAI\yolo26n.pt"

echo.
echo BUILD SELESAI.
echo Lokasi aplikasi: dist\hmkkAI\
pause