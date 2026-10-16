@echo off
setlocal
cd /d "%~dp0"
echo.
echo  TIME CAPSULE - setup and launch
 echo --------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Could not create the environment. Install Python 3.10+ and ensure the Python launcher is available.
    pause
    exit /b 1
  )
)
echo Installing/checking requirements...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and Python installation.
  pause
  exit /b 1
)
echo Launching Time Capsule at http://localhost:8501 ...
".venv\Scripts\python.exe" -m streamlit run app.py
pause
