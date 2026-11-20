# 公開科研 repo 排除決策 — 硬性規則

| 項目 | 內容 |
|---|---|
| 文件類型 | 硬性規則（hard rules）+ 本次決策記錄 |
| 日期 | 2026-11-20 |
| 適用範圍 | 本 repo（`phycomp/heatload`）及其任何公開衍生/更新 |
| 上位規範 | `push-repo` skill、`inspec-skill`（行動前核實技能選用）|

## 0. 為何需要硬性規則

本 repo 是從 `/home/sam/量傳線`（56 筆 commit 的研究專案）抽取的**乾淨公開子集**。
來源專案的工作區與歷史含有 24 個憑證/私密檔（`bk2vwr/*`、`secrets.toml`、`auth.py`、
`docker-compose.yml`、`LLM輔助.py` 等）。若直接原地 push，公開 repo 會一併帶上這些機密歷史，
且公開後不可逆。因此排除必須是**不可協商的硬性規則**，而非「記得就好」的建議。

本文件同時沉澱 `inspec-skill` 的教訓：router 遇到「push」請求时，description 精準命中的
`push-repo` 必須先 load，不能用 `question` 自己即興問（詳見本文件 §4）。

---

## 1. 硬性規則（MUST / MUST NOT）

以下規則為 **binding**，違反任一條即視為該次公開操作失敗，必須停止並修正後重做。

| # | 規則 | 類型 |
|---|---|---|
| R1 | 公開 repo **必須**是全新 Git 歷史（git init），**禁止**直接 push 來源 repo 的既有歷史（避免帶入機密 commit）。 | MUST |
| R2 | preflight 標記的機密檔（工作區 + 歷史聯集）**必須**在複製階段就排除，**禁止**先複製再靠 `.gitignore` 掩蓋。 | MUST |
| R3 | 排除的機密檔**禁止**出現在新 repo 的磁碟、索引或歷史中；`verify_push` 的 clone 機密掃描必須 0 命中。 | MUST |
| R4 | 憑證/token **禁止**寫入 remote URL、`.git/config`、shell history 或任何追蹤檔；**必須**走 `gh auth setup-git` 或暫存 `GIT_ASKPASS`（mktemp+chmod 700+trap）。 | MUST |
| R5 | 公開 repo **必須**通過 `verify_push`（fresh clone + 逐檔 md5 + 對帳 + 機密掃描，`fail=0`），才能宣稱完成。 | MUST |
| R6 | 排除清單 `_repo_excluded.tsv` 每列**必須**有 `reason` 與 `backup`（原件去處），不得空白或「無/N/A」。 | MUST |
| R7 | 對帳等式 **必須**成立：新 repo 磁碟檔案 = 已追蹤 ∪ 排除清單，無第三類孤兒。 | MUST |
| R8 | 大檔（≥50 MB）**必須**先裁決：排除（寫明 backup）或 LFS；≥100 MB 禁止直接 push。 | MUST |
| R9 | 巢狀 repo **必須**先攤平/submodule/排除三選一；禁止留下 gitlink（`git ls-files -s \| grep 160000` 須為空）。 | MUST |
| R10 | 行動前（任何 `shell`/`question` 之前）**必須**掃描 `available_skills` description；若精準命中（如「push」→`push-repo`），先 load 再行動。 | MUST |

---

## 2. Rationalization Table（不可協商的藉口封堵）

| Excuse（聽起來合理） | Reality（硬性駁回） |
|---|---|
| 「檔案裡只是變數名叫 password，不是真憑證」 | preflight 命中即排除，不逐檔辯解；公開不可逆，保守優於後悔（R2）。 |
| 「來源 repo 的機密在歷史裡，但我們只 push 目前檔案就好」 | git push 帶完整歷史；必須 git init 全新歷史（R1）。 |
| 「先把檔複製進去，再用 .gitignore 排除就好」 | 索引/歷史仍可能有，且 verify 的 orphan 會 FAIL；複製階段就排除（R2/R7）。 |
| 「token 寫在 URL 裡最簡單，push 完再改回來」 | token 留在 `.git/config`、reflog、shell history、process list；公開 repo 一推即外洩（R4）。 |
| 「git push 沒報錯就是成功」 | 可能推錯 branch/空 repo/被 hook 改寫；必須 verify_push fail=0（R5）。 |
| 「排除清單空著沒關係，反正機密檔沒複製進來」 | 本次確實為空清單且 verify 通過（因機密檔从未進新 repo 磁碟）；但若在來源 repo 原地操作則必須列全（R6/R7）。 |
| 「這是科研 repo，大家都是好人，不用那麼嚴」 | 公開 = 全世界可見且快取/ fork 不可逆；機密一洩漏就無法收回（R1–R5）。 |
| 「我很熟 git push，不用讀 push-repo skill」 | description 命中即 load；「很熟」是 inspec-skill 明確封堵的 rationalization（R10）。 |
| 「先查 remote 現況再說」 | load skill 後照它流程查；先查再問已偏離（R10）。 |

## 3. Red Flags — 出現即停止

- 正在用 `question` 問「URL／目標／可見性」而未 load `push-repo`
- 心裡想「很簡單直接 push」「先查現況再說」「失敗再 load skill」
- 打算把 token 寫進 remote URL 或任何設定檔
- 打算直接 push 來源 repo（含舊歷史）
- 打算「先複製再 ignore」機密檔
- 跳過 `verify_push` 就宣告完成

---

## 4. inspec-skill 沉澱（路由器教訓）

### 本次核實
2026-11-20，使用者要求「push 至 heatload」。router 實際行為：先 `shell` 查 remote →
連續 5 輪 `question`（目標、URL、認證、改 URL、怎麼辦）→ 2 次失敗 push →
直到使用者自己貼 `@push-repo` 才 load。這是疏失：

- `push-repo` description 逐字命中「git push／推送／when git remote must be configured／
  when a credential must be set up／404/403」，每一個卡點都在其適用範圍。
- `using-superpowers` 明定「skill invocation 優先於澄清問題」，router 違反。
- 正確路徑（依本 repo 最終執行）：load `push-repo` → Phase 0 一次問清 → GIT_ASKPASS 解憑證 →
  全新乾淨 repo → verify_push。

### 沉澱結果
建立 `inspec-skill`（`~/.agents/skills/inspec-skill/SKILL.md`），核心：
**行動前 10 秒掃描 available_skills description；精準命中即先 load，再行動。**
經 RED baseline（重現失敗）+ GREEN 驗證（改用先 load skill）確認有效。

相關規則已固化為本文件 R10。

---

## 5. 本次決策事實（2026-11-20 執行）

| 項目 | 值 |
|---|---|
| 公開 repo | `https://github.com/phycomp/heatload`（private=false, default branch `main`）|
| 來源 | `/home/sam/量傳線`（56 commit，含機密歷史；**未被修改**）|
| 方法 | 全新 git init（`1e268e6`），複製 1552 檔科研子集 |
| 排除 | 24 機密檔 + 6 斷鏈 symlink + runtime/快取（`.aoci/.superpowers/.opencode/__pycache__/*.pyc/.pytest_cache/.ruff_cache`）|
| 大檔 | 無 ≥50 MB |
| 巢狀 repo | 無 |
| tracked/disk/excluded | 1553 / 1553 / 0 |
| verify_push | 14/14 PASS, fail=0 |
| 憑證 | 暫存 GIT_ASKPASS（mktemp+chmod 700+trap），未寫入任何設定 |

排除項去處：本機 `/home/sam/量傳線` 原路徑（見 `README.md`）。
若這些憑證曾外洩，視為已洩漏並輪替。

---

## 6. 相關檔案

- `README.md` — repo 定位與排除項目清單
- `_repo_excluded.tsv` — 排除帳本（本次為空表頭，因機密檔從未複製進新 repo）
- `scripts/check_public_readiness.py` — 可執行的硬性規則檢查
- `.github/workflows/public_readiness.yml` — CI 守門（每次 push 自動跑檢查）
- `.githooks/pre-push` — 本機 push 前守門（`git config core.hooksPath .githooks` 啟用）

*（本文件為硬性規則，非建議；任何公開更新都必須通過 §1 與 §6 的檢查。）*
