#!/bin/bash

echo "========================================"
echo "  設定檔備份工具 - WSL 安裝"
echo "========================================"
echo ""

# 檢查 Python 是否安裝
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 未找到 Python3，請先安裝: sudo apt install python3 python3-pip"
    exit 1
fi

# 安裝依賴套件
echo "[1/3] 安裝依賴套件..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[錯誤] 依賴套件安裝失敗"
    exit 1
fi

# 檢查設定檔
echo "[2/3] 檢查設定檔..."
if [ ! -f config.yaml ]; then
    echo "[警告] config.yaml 不存在，複製範例設定檔..."
    cp config.yaml.example config.yaml
    echo "請編輯 config.yaml 以符合您的需求"
fi

# 設定執行權限
chmod +x backup.py

# 安裝排程
echo "[3/3] 安裝自動排程..."
python3 backup.py --install-schedule
if [ $? -ne 0 ]; then
    echo "[警告] 排程安裝失敗，請手動執行"
fi

echo ""
echo "========================================"
echo "  安裝完成！"
echo ""
echo "  使用方式:"
echo "    python3 backup.py --manual       手動備份"
echo "    python3 backup.py --history      查看歷史"
echo "    python3 backup.py --show-config  查看設定"
echo "========================================"
