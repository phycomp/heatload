@echo off
chcp 65001 >nul
echo 🔬 低溫傳輸線熱負載模擬器 - Docker 建置腳本
echo =================================================

REM 檢查 Docker 是否安裝
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安裝，請先安裝 Docker Desktop
    pause
    exit /b 1
)

echo 📦 建置 Docker 映像檔...
docker build -t cryo-cable-simulator:latest .

if %errorlevel% equ 0 (
    echo ✅ 建置成功！
    echo.
    echo 🚀 啟動模擬器:
    echo    docker run -p 8501:8501 cryo-cable-simulator:latest
    echo.
    echo 🌐 開啟瀏覽器訪問: http://localhost:8501
    echo.
    pause
) else (
    echo ❌ 建置失敗
    pause
    exit /b 1
)
