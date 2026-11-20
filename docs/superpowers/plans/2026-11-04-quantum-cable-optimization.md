# Quantum Cable Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立量子低溫傳輸線多目標優化系統（串擾 vs 熱負載），Phase 1A (Optuna) + Phase 1B (PPO RL)。

**Architecture:** 在 `src/量傳線設計/核心/` 新增 `優化.py`（Optuna 多目標）與 `RL代理.py`（PPO 閉環），在 `pages/` 新增對應 UI。重用現有串擾/熱負載模組作為評估函數。

**Tech Stack:** Python 3.14, Optuna, stable-baselines3, Streamlit, matplotlib, pytest

**Spec:** `docs/superpowers/specs/2026-11-04-quantum-cable-optimization-design.md`

## Global Constraints
- 製程：最小線寬 ≥ 10 μm，最大厚度 ≤ 300 μm
- 通道數：CF3=8, FPC=16（固定）
- Pitch：CF3 ≥ 1.0 mm, FPC ≥ 0.5 mm
- 冷端溫度 < 100 mK
- 串擾目標：NEXT/FEXT < -60 dB @ 10 GHz
- 不重寫物理模擬核心

## Review Focus
- 約束違反時目標函數回傳 inf（非 NaN）
- Pareto front 至少 10 個非支配解
- RL 狀態/動作空間維度一致
- 冷端溫度計算使用正確的熱負載模型
- 製程約束在優化器與 RL 中一致

---

### Task 1: 建立優化核心模組

**Files:**
- Create: `src/量傳線設計/核心/優化.py`
- Test: `tests/test_優化.py`

**Interfaces:**
- Produces: `多目標優化(spec, n_trials) -> List[dict]`（含 Pareto 解集）、`評估設計(params, spec) -> (f1, f2)`

- [ ] **Step 1: Write failing test**

```python
def test_評估設計_CF3():
    from 量傳線設計.核心.優化 import 評估設計
    params = {"w": 35, "s": 100, "h": 0.129, "t": 2, "pitch": 2.0}
    f1, f2 = 評估設計(params, "CF3")
    assert isinstance(f1, float)
    assert isinstance(f2, float)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m pytest tests/test_優化.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `評估設計` and `多目標優化`**

```python
"""多目標優化（Optuna NSGA-II）"""
import optuna
from 量傳線設計.核心.低溫超導 import 模擬NbTi串擾
from 量傳線設計.核心.熱負載 import 回推溫區長度

SPEC_CONFIG = {
    "CF3": {"channels": 8, "pitch_min": 1.0, "pitch_max": 3.0},
    "FPC": {"channels": 16, "pitch_min": 0.5, "pitch_max": 2.0},
}

def 評估設計(params, spec_name):
    spec = SPEC_CONFIG[spec_name]
    # 串擾
    res = 模擬NbTi串擾(w_um=params["w"], d_nm=params["t"]*1000, s_um=params["s"],
                       length_m=0.2, lambda_L_nm=200, er=3.4)
    f1 = max(res["next_db"].max(), res["fext_db"].max())  # 越低越好（dB）
    # 熱負載（簡化：用回推長度反推）
    L = 回推溫區長度(熱導率=0.1, 截面積=1e-6, 溫差=50.0, 熱負載_W=1e-6)
    f2 = 1.0 / (L + 1e-9)  # 越低越好
    # 約束檢查
    if params["w"] < 10 or params["t"]*1000 > 300*1000:
        return float("inf"), float("inf")
    return float(f1), float(f2)

def 多目標優化(spec_name, n_trials=50):
    spec = SPEC_CONFIG[spec_name]
    def objective(trial):
        params = {
            "w": trial.suggest_float("w", 10, 100),
            "s": trial.suggest_float("s", 50, 500),
            "h": trial.suggest_float("h", 0.05, 0.3),
            "t": trial.suggest_float("t", 1, 20),
            "pitch": trial.suggest_float("pitch", spec["pitch_min"], spec["pitch_max"]),
        }
        f1, f2 = 評估設計(params, spec_name)
        return f1, f2
    study = optuna.create_study(directions=["minimize", "minimize"],
                               sampler=optuna.samplers.NSGAIISampler())
    study.optimize(objective, n_trials=n_trials)
    return study.best_trials
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python -m pytest tests/test_優化.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/量傳線設計/核心/優化.py tests/test_優化.py
git commit -m "feat: add multi-objective optimization (Optuna)"
```

---

### Task 2: 建立優化 UI 頁面

**Files:**
- Create: `pages/21優化.py`

- [ ] **Step 1: Create page**

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import streamlit as st
import matplotlib.pyplot as plt
from 量傳線設計.核心.優化 import 多目標優化, SPEC_CONFIG

st.set_page_config(page_title="多目標優化", layout="wide")
st.title("多目標優化（串擾 vs 熱負載）")

spec_name = st.selectbox("規格", list(SPEC_CONFIG.keys()))
n_trials = st.slider("試驗次數", 10, 200, 50)
if st.button("開始優化"):
    with st.spinner("優化中..."):
        trials = 多目標優化(spec_name, n_trials=n_trials)
    st.success(f"完成，共 {len(trials)} 個 Pareto 解")
    xs = [t.values[0] for t in trials]
    ys = [t.values[1] for t in trials]
    fig, ax = plt.subplots()
    ax.scatter(xs, ys)
    ax.set_xlabel("串擾 (dB)"); ax.set_ylabel("熱負載 (μW/ch)")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
```

- [ ] **Step 2: Smoke test**

Run: `timeout 40 streamlit run app.py --server.headless true --server.port 8517 2>&1 | tail -3`
Expected: app starts

- [ ] **Step 3: Commit**

```bash
git add pages/21優化.py
git commit -m "feat: add optimization UI page"
```

---

### Task 3: RL 閉環代理（Phase 1B）

**Files:**
- Create: `src/量傳線設計/核心/RL代理.py`
- Create: `pages/22RL優化.py`
- Test: `tests/test_RL代理.py`

**Interfaces:**
- Produces: `訓練RL(spec_name, total_timesteps) -> model`, `評估RL(model, params) -> (f1, f2)`

- [ ] **Step 1: Write failing test**

```python
def test_RL環境建立():
    from 量傳線設計.核心.RL代理 import 建立環境
    env = 建立環境("CF3")
    assert env is not None
```

- [ ] **Step 2: Implement RL environment + PPO training**

```python
"""RL 閉環優化（PPO）"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import PPO
from 量傳線設計.核心.優化 import 評估設計, SPEC_CONFIG

class 傳輸線環境(gym.Env):
    def __init__(self, spec_name):
        super().__init__()
        self.spec_name = spec_name
        self.spec = SPEC_CONFIG[spec_name]
        self.action_space = spaces.Box(low=-0.1, high=0.1, shape=(5,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32)
        self.params = {"w": 35, "s": 100, "h": 0.129, "t": 2, "pitch": 2.0}
        self.steps = 0

    def reset(self, seed=None):
        self.params = {"w": 35, "s": 100, "h": 0.129, "t": 2, "pitch": 2.0}
        self.steps = 0
        return self._obs(), {}

    def _obs(self):
        return np.array([self.params["w"]/100, self.params["s"]/500, self.params["h"]/0.3,
                         self.params["t"]/20, self.params["pitch"]/3.0], dtype=np.float32)

    def step(self, action):
        self.params["w"] = max(10, min(100, self.params["w"] + action[0]*10))
        self.params["s"] = max(50, min(500, self.params["s"] + action[1]*50))
        self.params["h"] = max(0.05, min(0.3, self.params["h"] + action[2]*0.05))
        self.params["t"] = max(1, min(20, self.params["t"] + action[3]*2))
        self.params["pitch"] = max(self.spec["pitch_min"], min(self.spec["pitch_max"],
                                 self.params["pitch"] + action[4]*0.5))
        f1, f2 = 評估設計(self.params, self.spec_name)
        reward = -0.5*f1 - 0.5*f2
        if f1 == float("inf"):
            reward -= 10
        self.steps += 1
        done = self.steps >= 50
        return self._obs(), reward, done, False, {}

def 建立環境(spec_name):
    return 傳輸線環境(spec_name)

def 訓練RL(spec_name, total_timesteps=10000):
    env = 建立環境(spec_name)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=total_timesteps)
    return model
```

- [ ] **Step 3: Run test**

Run: `PYTHONPATH=src python -m pytest tests/test_RL代理.py -v`
Expected: PASS

- [ ] **Step 4: Create UI page**

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import streamlit as st
from 量傳線設計.核心.RL代理 import 訓練RL

st.set_page_config(page_title="RL 優化", layout="wide")
st.title("RL 閉環優化（PPO）")
spec_name = st.selectbox("規格", ["CF3", "FPC"])
timesteps = st.slider("訓練步數", 1000, 50000, 10000)
if st.button("開始訓練"):
    with st.spinner("訓練中..."):
        model = 訓練RL(spec_name, total_timesteps=timesteps)
    st.success("訓練完成")
```

- [ ] **Step 5: Commit**

```bash
git add src/量傳線設計/核心/RL代理.py pages/22RL優化.py tests/test_RL代理.py
git commit -m "feat: RL closed-loop optimization (PPO)"
```

---

### Task 4: 依賴安裝

- [ ] **Step 1: Update requirements.txt**

加入 `optuna`, `stable-baselines3`, `gymnasium`

- [ ] **Step 2: Install**

```bash
pip install optuna stable-baselines3 gymnasium -q
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add optuna, stable-baselines3, gymnasium"
```

---

### Task 5: 整合測試與文件

- [ ] **Step 1: 全量測試**

Run: `PYTHONPATH=src python -m pytest tests/ -q`
Expected: all pass

- [ ] **Step 2: Streamlit smoke**

Run: `timeout 60 streamlit run app.py --server.headless true --server.port 8518 2>&1 | tail -3`

- [ ] **Step 3: 更新 docs/使用說明.md**

加入優化與 RL 頁面說明

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: integrate optimization + RL into platform"
```
PY