#!/bin/bash

echo "🔬 低溫傳輸線熱負載模擬器 - Docker 建置腳本"
echo "================================================"

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

echo "📦 建置 Docker 映像檔..."
docker build -t cryo-cable-simulator:latest .

if [ $? -eq 0 ]; then
    echo "✅ 建置成功！"
    echo ""
    echo "🚀 啟動模擬器:"
    echo "   docker run -p 8501:8501 cryo-cable-simulator:latest"
    echo ""
    echo "🌐 開啟瀏覽器訪問: http://localhost:8501"
    echo ""
    echo "或使用 docker-compose:"
    echo "   docker-compose up -d"
else
    echo "❌ 建置失敗"
    exit 1
fi
