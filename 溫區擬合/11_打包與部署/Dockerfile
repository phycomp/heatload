FROM python:3.12-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y     build-essential     && rm -rf /var/lib/apt/lists/*

# 複製 requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY cryo_cable_app.py .

# 暴露 Streamlit 預設埠
EXPOSE 8501

# 設定環境變數
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# 啟動命令
CMD ["streamlit", "run", "cryo_cable_app.py", "--server.address=0.0.0.0"]
