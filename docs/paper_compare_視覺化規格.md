# 論文版本比較視覺化規格（Nature-style vs compiled）

> 技能：topic-viz（Format F：規格 + 快照 + 離線工具；離線 HTML 規則已於 2026-11-20 移除）  
> 日期：2026-11-20  
> 來源：`docs/heatload_distill_nature_manuscript.md`（Nature-style）、`docs/heatload-distill_paper_consolidated_final.md`（compiled final）

## 1. 目標與範圍
比較兩個最終論文版本的結構、主張與證據邊界，供作者快速核對「兩者差異」。
- 輸入：兩份 Markdown 論文（唯讀）。
- 輸出： viz_data.json（同源快照）+ demo.xlsx（比較表）。
- 不判定優劣、不改內容、不重擬合。

## 2. 格式識別（Step 0）
F 混合型：A 規格 + D 對照表 + E 交付清單。
- A：`docs/paper_compare_視覺化規格.md`（本檔）
- D：`docs/paper_compare_viz_demo.xlsx`（Axis_Compare / Sections / Stats）
- F 快照：`docs/paper_compare_viz_data.json`

## 3. 資料契約（viz_data.json）
- `meta.generator / created_at / policy`
- `sources`：兩份論文路徑
- `stats`：chars/words/figure_mentions/table_rows/math_tokens（兩版）
- `sections`：各版章節標題 + 字元數（同源抽自 `## ` 標題）
- `axis_comparison`：7 軸（寫作風格/語言/章節/核心主張/新增內容/證據邊界/期刊）
- `evidence_note`：同源比較宣告

## 4. 工具（已移除離線 HTML）
- Excel（stdlib `zipfile+xml`，零外部依賴）：5 工作表（Overview / Axis_Compare / Nature_Sections / Compiled_Sections / Stats）。
- 產生器：`/tmp/opencode/build_compare_viz.py`（暫存；重現命令如下）。

## 5. 驗證
- JSON 可解析；XLSX 5 sheet 存在；stats 與章節數一致（nature 14 / compiled 16 sections）。
- 無 CDN / 外部依賴；唯讀來源。

## 6. 重現命令
```bash
cd ~/量傳線
python3 /tmp/opencode/build_compare_viz.py
python3 -c "import json,zipfile; d=json.load(open('docs/paper_compare_viz_data.json')); print(len(d['axis_comparison']))"
```

## 7. 限制
- 比較為結構/主張層次，非内容品質審查。
- 兩版同源（Nature-style 由 compiled material 寫成），差異主要是寫作風格與章節組織。
- Streamlit 互動展示另行處理（依 topic-viz gate 先提案裁決）。
