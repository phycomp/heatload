@echo off
chcp 65001 >nul
echo 🔬 低溫傳輸線熱負載模擬器 - PyInstaller 打包腳本 (Windows)
echo ===========================================================

REM 建立虛擬環境
echo 📦 建立虛擬環境...
python -m venv venv
call venv\Scripts\activate.bat

REM 安裝依賴
echo 📦 安裝依賴...
pip install -r requirements.txt
pip install pyinstaller

REM 建立入口腳本
echo import subprocess > run_app.py
echo import sys >> run_app.py
echo import os >> run_app.py
echo. >> run_app.py
echo def main(): >> run_app.py
echo     if getattr(sys, 'frozen', False): >> run_app.py
echo         application_path = os.path.dirname(sys.executable) >> run_app.py
echo     else: >> run_app.py
echo         application_path = os.path.dirname(os.path.abspath(__file__)) >> run_app.py
echo     app_path = os.path.join(application_path, 'cryo_cable_app.py') >> run_app.py
echo     subprocess.run([sys.executable, '-m', 'streamlit', 'run', app_path, '--server.headless=true', '--server.port=8501']) >> run_app.py
echo. >> run_app.py
echo if __name__ == '__main__': >> run_app.py
echo     main() >> run_app.py

REM 打包
echo 🔨 開始打包...
pyinstaller --name "CryoCableSimulator" --onefile --add-data "cryo_cable_app.py;." --hidden-import streamlit --hidden-import numpy --hidden-import matplotlib run_app.py

if %errorlevel% equ 0 (
    echo ✅ 打包成功！
    echo.
    echo 📦 執行檔位置: dist\CryoCableSimulator.exe
    echo.
    echo 🚀 執行方式:
    echo    dist\CryoCableSimulator.exe
    echo.
    echo 🌐 開啟瀏覽器訪問: http://localhost:8501
    pause
) else (
    echo ❌ 打包失敗
    pause
    exit /b 1
)
