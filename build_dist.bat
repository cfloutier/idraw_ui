@echo off
setlocal

set DIST_NAME=idraw_ui
set IDRAW2_SRC=C:\dev\__tracer\idraw2_internal

call .venv\Scripts\activate.bat

echo === Reading version from pyproject.toml ===
for /f "delims=" %%v in ('.venv\Scripts\python.exe -c "import tomllib; v=tomllib.load(open(\"pyproject.toml\",\"rb\"))[\"project\"][\"version\"]; print(v)"') do set VERSION=%%v
set ZIP_NAME=idraw_ui_v%VERSION%.zip
echo Version: %VERSION% ^| Archive: %ZIP_NAME%

echo === Reinstalling idraw2_0internal non-editable for bundling ===
pip install --no-deps "%IDRAW2_SRC%" --quiet
if errorlevel 1 (
    echo ERROR: could not install idraw2_0internal from %IDRAW2_SRC%
    exit /b 1
)

echo === Building standalone bundle ===
set PYTHONPATH=src
pyinstaller idraw_ui.spec --clean --noconfirm
if errorlevel 1 (
    echo BUILD FAILED - restoring editable install
    pip install --no-deps -e "%IDRAW2_SRC%" --quiet
    exit /b 1
)

echo === Restoring editable install for development ===
pip install --no-deps -e "%IDRAW2_SRC%" --quiet

echo === Creating zip archive ===
powershell -Command "Compress-Archive -Path 'dist\%DIST_NAME%\*' -DestinationPath '%ZIP_NAME%' -Force"

echo.
echo Done. Distribute: %ZIP_NAME%
echo User only needs to unzip and run: %DIST_NAME%\idraw_ui.exe
