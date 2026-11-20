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
    f1 = float(max(res["next_db"].max(), res["fext_db"].max()))
    # 熱負載（簡化）
    L = 回推溫區長度(熱導率=0.1, 截面積=1e-6, 溫差=50.0, 熱負載_W=1e-6)
    f2 = 1.0 / (L + 1e-9)
    # 約束檢查
    if params["w"] < 10 or params["t"]*1000 > 300*1000:
        return float("inf"), float("inf")
    return float(f1), float(f2)

def 多目標優化(spec_name, n_trials=50, use_proxy=False):
    spec = SPEC_CONFIG[spec_name]
    proxy = None
    if use_proxy:
        from 量傳線設計.核心.代理模型 import 生成訓練資料, 訓練代理模型
        samples = 生成訓練資料(spec_name, n=20)
        if len(samples) >= 5:
            proxy = 訓練代理模型(samples)
    def objective(trial):
        params = {
            "w": trial.suggest_float("w", 10, 100),
            "s": trial.suggest_float("s", 50, 500),
            "h": trial.suggest_float("h", 0.05, 0.3),
            "t": trial.suggest_float("t", 1, 20),
            "pitch": trial.suggest_float("pitch", spec["pitch_min"], spec["pitch_max"]),
        }
        if proxy is not None:
            from 量傳線設計.核心.代理模型 import 預測
            f1, f2 = 預測(proxy, params)
        else:
            f1, f2 = 評估設計(params, spec_name)
        return f1, f2
    study = optuna.create_study(directions=["minimize", "minimize"],
                               sampler=optuna.samplers.NSGAIISampler())
    study.optimize(objective, n_trials=n_trials)
    return study.best_trials

def 批次優化(spec_names, n_trials=30, use_proxy=False):
    """批次優化多個規格，回傳 {spec: trials}。"""
    result = {}
    for name in spec_names:
        result[name] = 多目標優化(name, n_trials=n_trials, use_proxy=use_proxy)
    return result

def 產生報告(trials, spec_name):
    """產生含 Pareto 圖的 PDF 報告 bytes。"""
    import io
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        # Page 1: Pareto
        fig, ax = plt.subplots()
        xs = [t.values[0] for t in trials]
        ys = [t.values[1] for t in trials]
        ax.scatter(xs, ys)
        ax.set_xlabel("串擾 (dB)")
        ax.set_ylabel("熱負載")
        ax.set_title(f"Pareto Front - {spec_name}")
        ax.grid(True, alpha=0.3)
        pdf.savefig(fig)
        plt.close(fig)
        # Page 2: 參數表
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.axis("off")
        params = [t.params for t in trials]
        if params:
            cols = list(params[0].keys())
            rows = [[p[c] for c in cols] + [t.values[0], t.values[1]] for p, t in zip(params, trials)]
            header = cols + ["f1", "f2"]
            table = ax2.table(cellText=rows, colLabels=header, loc="center")
            table.auto_set_font_size(False)
            table.set_fontsize(8)
        ax2.set_title(f"參數表 - {spec_name}")
        pdf.savefig(fig2)
        plt.close(fig2)
    buf.seek(0)
    return buf.getvalue()
