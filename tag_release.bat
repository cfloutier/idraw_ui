@echo off
setlocal

call .venv\Scripts\activate.bat

for /f "delims=" %%v in ('.venv\Scripts\python.exe -c "import tomllib; v=tomllib.load(open(\"pyproject.toml\",\"rb\"))[\"project\"][\"version\"]; print(v)"') do set VERSION=%%v

echo Tagging v%VERSION% ...
git tag v%VERSION%
if errorlevel 1 (
    echo ERROR: tag already exists or git failed.
    exit /b 1
)
echo Done. Pushing tag v%VERSION% ...
git push origin v%VERSION%
