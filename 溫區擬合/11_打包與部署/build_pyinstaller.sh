#!/bin/bash

echo "🔬 低溫傳輸線熱負載模擬器 - PyInstaller 打包腳本"
echo "==================================================="

# 建立虛擬環境
echo "📦 建立虛擬環境..."
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
echo "📦 安裝依賴..."
pip install -r requirements.txt
pip install pyinstaller

# 建立入口腳本
cat > run_app.py << 'EOF'
import subprocess
import sys
import os

def main():
    # 取得執行檔所在目錄
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(application_path, 'cryo_cable_app.py')

    # 啟動 Streamlit
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', app_path,
        '--server.headless=true',
        '--server.port=8501',
        '--server.address=0.0.0.0'
    ])

if __name__ == '__main__':
    main()
EOF

# 打包
echo "🔨 開始打包..."
pyinstaller     --name "CryoCableSimulator"     --onefile     --add-data "cryo_cable_app.py:."     --add-data "venv/lib/python3.12/site-packages/streamlit:streamlit"     --hidden-import streamlit     --hidden-import numpy     --hidden-import matplotlib     --hidden-import matplotlib.pyplot     --hidden-import matplotlib.patches     run_app.py

if [ $? -eq 0 ]; then
    echo "✅ 打包成功！"
    echo ""
    echo "📦 執行檔位置: dist/CryoCableSimulator"
    echo ""
    echo "🚀 執行方式:"
    echo "   ./dist/CryoCableSimulator"
    echo ""
    echo "🌐 開啟瀏覽器訪問: http://localhost:8501"
else
    echo "❌ 打包失敗"
    exit 1
fi
