#!/bin/bash

echo "🔬 低溫傳輸線熱負載模擬器"
echo "=========================="

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "📦 建立虛擬環境..."
    python3 -m venv venv
fi

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
echo "📦 安裝/更新依賴..."
pip install -q -r requirements.txt

# 啟動 Streamlit
echo "🚀 啟動模擬器..."
echo "🌐 開啟瀏覽器訪問: http://localhost:8501"
echo ""
streamlit run cryo_cable_app.py --server.headless=true --server.port=8501
