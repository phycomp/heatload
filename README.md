# heatload — 低溫熱負載與量子傳輸線科研資料

公開科研資料集，供低溫工程、超導量子互連與熱負載估算領域的研究者交流使用。

## 內容來源

本 repo 為 `/home/sam/量傳線` 研究專案的**乾淨公開子集**，於 2026-11-20 建立。
內容為該專案累積的科研文件、腳本、資料快照與視覺化產物（共 1552 檔），
以全新 Git 歷史建立，故不含來源專案的历史提交。

## 研究主題

- 9 係數 κ(T) log-log 擬合於低溫熱負載估算之溯源與可靠度（Heatload-Distill）
- 溫區擬合（temperature-zone fitting）：分溫階傅立葉導熱、積分比回推、mK 安全長度
- NbTi / 超導量子傳輸線之熱、電、幾何設計與量測 SOP
- 同源自覺（evidence-bounded）之視覺化快照、離線 HTML/Excel 與Streamlit 展示

詳細重點見 `docs/` 與 `AGENTS.md`。核心邊界：SSOT D4=A、no refit、no invented coefficients、
不宣稱新量測（見 `docs/核實_原始資料與係數驗證.md`、`docs/溫區擬合_科學成果沉澱.md`）。

## 排除項目與去向（重要）

下列項目**未包含**於本公開 repo（來源仍完整保留於本機 `/home/sam/量傳線`）：

### 機密與憑證（24 檔，基於 push-repo preflight）
`bk2vwr/*`（資料庫連線工具）、`三視圖/柔性/量量/.streamlit/secrets.toml`、
`三視圖/柔性/量量/auth.py`、`三視圖/柔性/tchwiki/{docker-compose.yml,ai模型.py,sync_wiki.py,主程式.py,同步向量.py}`、
`src/量傳線設計/核心/LLM輔助.py`、`archive/柔線/pages/0全傳輸線材模擬.py`、
`柔線/{pages/0全傳輸線材模擬.py,五家傳輸線.md,金傳輸線材參數.md}`、
`三視圖/柔性/pages/08md2簡報.py`。
原因：含 password / token / api_key / PASSWORD 等欄位模式，且部分曾出現在來源專案歷史提交中。
去處：本機唯一，位於 `/home/sam/量傳線` 原路徑。若這些憑證曾外洩，請當作已洩漏並輪替。

### 工具執行期與快取
`.git/`、`.aoci/`、`.superpowers/`、`.opencode/`、`__pycache__/`、`*.pyc`、
`.pytest_cache/`、`.ruff_cache/` — 可重建或屬 agent 工作紀錄，非科研內容。
去處：由工具重建 / 本機 `/home/sam/量傳線`。

### 斷鏈符號連結（6 個）
`德夫/pages/MD即時視得3.py` 等 6 個指向不存在目標的 symlink — 排除以免 clone 後成空/null 連結。
去處：本機 `/home/sam/量傳線`。

本公開 repo 的 `_repo_excluded.tsv` 因此為空表頭：所有被排除項目在建立時即未複製進來，
故新 repo 的磁碟檔案 = 已追蹤檔案，沒有第三類孤兒。

## 授權與引用

使用本資料請引用對應的科研脈絡；κ(T) 係數源自 NIST/Marquardt/Bradley/Simon/Flynn 與 Raicu et al. (2025)
等既有來源（詳見 `docs/heatload-distill_paper.md` 參考文獻），本 repo 不主張新材料物性量測。
