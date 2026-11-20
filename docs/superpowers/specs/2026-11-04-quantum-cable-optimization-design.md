# 量子傳輸線多目標優化設計文件

**日期**：2026-11-04
**主題**：量子低溫傳輸線（CF3/FPC）串擾與熱負載多目標優化

## 1. Intent & Why

將現有 量傳線 平台的串擾模擬與熱負載計算整合為一個**可優化的設計系統**，使工程師能自動搜尋 Pareto 最優設計，並以 AI 代理加速設計迭代。CF3 為基準，FPC 為應用目標。

## 2. Goals / Non-goals / Anti-goals

**Goals**
- 自動搜尋 Pareto 最優設計（串擾 vs 熱負載）
- Phase 1：超參數搜尋 (Optuna) + RL 閉環 (PPO)
- Phase 2：代理模型 (XGBoost/GP) + LLM 輔助
- 視覺化 Pareto front 與設計權衡
- 可匯出優化結果至 Excel

**Non-goals**
- 不重寫物理模擬核心（重用現有模組）
- 不做 3D 電磁模擬（HFSS）

**Anti-goals**
- 不允許優化結果違反製程約束（最小線寬、最大厚度）
- 不允許冷端溫度超過臨界值

## 3. Constraints

- 製程：最小線寬 ≥ 10 μm，最大厚度 ≤ 300 μm
- 通道數：CF3=8, FPC=16（固定）
- Pitch：CF3 ≥ 1.0 mm, FPC ≥ 0.5 mm
- 冷端溫度 < 100 mK
- 串擾目標：NEXT/FEXT < -60 dB @ 10 GHz

## 4. Approaches

### Approach 1：雙層優化架構（採用）
- Phase 1A：Optuna 多目標優化（串擾 vs 熱負載）
- Phase 1B：PPO RL 閉環（狀態=參數，動作=調整，獎勵=多目標評分）
- Phase 2A：XGBoost/GP 代理模型
- Phase 2B：LLM 輔助生成初始參數

### Approach 2：單一 RL 代理
- 端到端，訓練不穩，難解釋。捨棄。

### Approach 3：代理模型 + NSGA-II
- 穩定但無 RL 閉環。Phase 2 可考慮。

**選擇 Approach 1**，理由：分階段可驗證、可解釋、可逐步擴充。

## 5. 設計細節

### 5.1 參數空間
- w (線寬 μm): [10, 100]
- s (間距 μm): [50, 500]
- h (介電厚度 mm): [0.05, 0.3]
- t (訊號厚度 μm): [1, 20]
- pitch (mm): CF3 [1.0, 3.0], FPC [0.5, 2.0]

### 5.2 目標函數
- minimize f1 = max(NEXT, FEXT) dB（串擾）
- minimize f2 = 熱負載 μW/ch
- 約束：冷端 T < 100 mK, 製程限制

### 5.3 多目標優化
- Optuna NSGA-II sampler
- Pareto front 視覺化
- 匯出 Excel（Pareto 解集）

### 5.4 RL 閉環
- State: [w, s, h, t, pitch]
- Action: Δw, Δs, Δh, Δt, Δpitch（連續）
- Reward: -α·f1 - β·f2 + 約束懲罰
- Algorithm: PPO (stable-baselines3)
- Episode: 50 步，終止條件：收斂或違反約束

### 5.5 代理模型（Phase 2）
- 訓練資料：Optuna 探索結果
- 模型：XGBoost / Gaussian Process
- 用途：加速 RL 評估

### 5.6 LLM 輔助（Phase 2）
- 自然語言 → 參數組合（prompt template）
- 用 LLM 生成初始設計，優化器精修

## 6. 實作計畫（Phase 1）

1. 建立 `src/量傳線設計/核心/優化.py`：Optuna 多目標優化
2. 建立 `pages/21優化.py`：UI + Pareto front 視覺化
3. 建立 `src/量傳線設計/核心/RL代理.py`：PPO 閉環
4. 建立 `pages/22RL優化.py`：UI + 訓練進度
5. 測試 + 文件

## 7. 未決問題

- Optuna vs SciPy：Optuna 支援多目標，優先
- RL 框架：stable-baselines3（需安裝）
- LLM：本地 Ollama 或 OpenAI API（需確認）

## 8. 成功標準

- Phase 1A：Pareto front 產出，至少 10 個非支配解
- Phase 1B：RL 收斂，獎勵提升
- 匯出 Excel + 視覺化
PY