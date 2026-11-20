@echo off
echo ========================================
echo  設定檔備份工具 - Windows 安裝
echo ========================================
echo.

:: 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python，請先安裝 Python 3.6+
    echo 下載位置: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 安裝依賴套件
echo [1/3] 安裝依賴套件...
pip install -r requirements.txt
if errorlevel 1 (
    echo [錯誤] 依賴套件安裝失敗
    pause
    exit /b 1
)

:: 檢查設定檔
echo [2/3] 檢查設定檔...
if not exist config.yaml (
    echo [警告] config.yaml 不存在，複製範例設定檔...
    copy config.yaml.example config.yaml
    echo 請編輯 config.yaml 以符合您的需求
)

:: 安裝排程
echo [3/3] 安裝自動排程...
python backup.py --install-schedule
if errorlevel 1 (
    echo [警告] 排程安裝失敗，請手動執行
)

echo.
echo ========================================
echo  安裝完成！
echo.
echo  使用方式:
echo    python backup.py --manual       手動備份
echo    python backup.py --history      查看歷史
echo    python backup.py --show-config  查看設定
echo ========================================
pause
