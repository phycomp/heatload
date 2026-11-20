# syntax=docker/dockerfile:1

# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder

WORKDIR /build

# 系統建置依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim AS runtime

WORKDIR /app

# 執行期系統依賴（LibreOffice for PDF, pandoc for md->pptx/pdf）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice pandoc fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 從 builder 複製 Python 套件
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 專案檔案
COPY . .

# 安裝 skills（可選）
RUN bash install_skills.sh /app 2>/dev/null || true

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
PY