@echo off
call .venv\Scripts\activate.bat
set PYTHONPATH=src
python -m idraw_ui.app
