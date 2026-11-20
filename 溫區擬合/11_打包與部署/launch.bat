@echo off
chcp 65001 >nul
echo 🔬 低溫傳輸線熱負載模擬器
echo ==========================

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安裝
    pause
    exit /b 1
)

REM 檢查虛擬環境
if not exist "venv" (
    echo 📦 建立虛擬環境...
    python -m venv venv
)

REM 啟動虛擬環境
call venv\Scripts\activate.bat

REM 安裝依賴
echo 📦 安裝/更新依賴...
pip install -q -r requirements.txt

REM 啟動 Streamlit
echo 🚀 啟動模擬器...
echo 🌐 開啟瀏覽器訪問: http://localhost:8501
echo.
streamlit run cryo_cable_app.py --server.headless=true --server.port=8501

pause
