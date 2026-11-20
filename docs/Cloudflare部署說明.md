# Cloudflare 部署說明

## 一、申請 Cloudflare 帳號

1. 前往 https://dash.cloudflare.com/sign-up
2. 註冊帳號（可用 Google/GitHub）
3. 驗證 email
4. 進入 Dashboard

## 二、安裝 Wrangler CLI

```bash
# Node.js >= 18
npm install -g wrangler

# 驗證
wrangler --version

# 登入
wrangler login
# 瀏覽器會開啟授權頁面，確認後回到終端
```

## 三、設定 Secrets

```bash
# 量傳線
cd /home/sam/量傳線
wrangler secret put CLOUDFLARE_API_TOKEN
wrangler secret put CLOUDFLARE_ACCOUNT_ID

# 產學合作
cd /home/sam/產學合作
wrangler secret put CLOUDFLARE_API_TOKEN
wrangler secret put CLOUDFLARE_ACCOUNT_ID
```

API Token 取得：Cloudflare Dashboard → My Profile → API Tokens → Create Token → 選 "Edit Cloudflare Workers" 模板。

Account ID：Dashboard 右側欄。

## 四、部署

### 手動部署
```bash
cd /home/sam/量傳線
bash deploy.sh all
```

### CI/CD（GitHub Actions）
1. 在 GitHub repo 設定 Secrets：`CLOUDFLARE_API_TOKEN`、`CLOUDFLARE_ACCOUNT_ID`
2. push 至 main/master 自動部署（見 `.github/workflows/deploy.yml`）

## 五、Docker 本地測試

```bash
cd /home/sam/量傳線
docker build -t liangchuan-line .
docker run -p 8501:8501 liangchuan-line
# 開啟 http://localhost:8501
```

## 六、多階段建置說明

Dockerfile 使用多階段建置：
- **builder**：安裝 Python 依賴（含編譯）
- **runtime**：僅複製必要套件 + 系統依賴，減少映像大小

## 七、注意事項

- Cloudflare Containers 需 Wrangler >= 3.x
- Streamlit 在容器中需 `--server.address=0.0.0.0`
- LibreOffice 用於 PDF 轉換，映像較大（~1GB）
- 若不需要 PDF 轉換，可移除 libreoffice 以縮小映像
PY