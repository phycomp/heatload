# =====================================================================
# 任務 ③：獨立 2D FEM 靜電場解器（Speedstack 無法在本環境執行，以此為第三方基準）
# 模型：帶狀線橫截面，介質在 x 方向由 FR4 (εr=4.2) 突變為 PI (εr=3.3)
#       → 模擬剛撓交界；求 Z0 階躍與交界過剩電容
# =====================================================================
import numpy as np

def fem_stripline_junction(w_trace, b, er_left, er_right, L=4.0, nx=240, ny=160,
                           max_iter=30000, tol=1e-9):
    """2D Laplace 有限差分（Jacobi 向量化＋混合介質面元 ε）。
    回傳 Z0 左/右區、交界過剩電容等效長度、網格收斂資訊。"""
    dx, dy = L / nx, b / ny
    x = (np.arange(nx) + 0.5) * dx
    er_cells = np.where(x < L/2, er_left, er_right)          # 單元介電常數
    er2d = np.tile(er_cells, (ny, 1))

    # 導體邊界遮罩：上下平面 V=0；中央走線 V=1
    trace = np.zeros((ny, nx), dtype=bool)
    jt = ny // 2
    trace[jt, (np.abs(x - L/2) <= w_trace/2)] = True

    def solve_V(er_field):
        V = np.zeros((ny + 1, nx + 1))
        V[jt + 1, 1:-1][0] if False else None
        V[1:-1, 1:-1][trace] = 1.0
        fixed = np.zeros((ny + 1, nx + 1), dtype=bool)
        fixed[0, :] = fixed[ny, :] = True
        fixed[1:-1, 1:-1][trace] = True
        V[0, :] = V[ny, :] = 0.0
        # 面元 ε（交錯網格）
        ePx = 0.5 * (er_field + np.roll(er_field, -1, axis=1))
        ePy = 0.5 * (er_field + np.roll(er_field, -1, axis=0))
        r = (dx / dy) ** 2
        for it in range(1, max_iter + 1):
            Vc = V[1:-1, 1:-1]
            aW = np.hstack([ePx[:, :1], ePx[:, :-1]])
            aE = ePx
            aS = np.vstack([ePy[:1, :], ePy[:-1, :]])
            aN = ePy
            Vnew = (aW * V[:-2, 1:-1] + aE * V[2:, 1:-1] + r * (aS * V[1:-1, :-2] + aN * V[1:-1, 2:])) \
                   / (aW + aE + r * (aS + aN))
            Vnew[trace] = 1.0
            diff = np.max(np.abs(Vnew - Vc)) if not np.all(fixed[1:-1,1:-1]) else 0.0
            V[1:-1, 1:-1] = Vnew
            if diff < tol:
                break
        return V, it

    def capacitance(V, er_field):
        Ex = -(V[1:-1, 1:] - V[1:-1, :-1]) / dx          # (ny, nx)
        Ey = -(V[1:, 1:-1] - V[:-1, 1:-1]) / dy
        ePx = 0.5 * (er_field + np.roll(er_field, -1, axis=1))
        ePy = 0.5 * (er_field + np.roll(er_field, -1, axis=0))
        W = 0.5 * EPS0 * (np.sum(ePx * Ex**2) * dy + np.sum(ePy * Ey**2) * dx)
        return 2.0 * W                                  # C = 2W/V², V=1

    Vd, itd = solve_V(er2d)
    Cair = capacitance(Vd, np.ones_like(er2d))
    Cd   = capacitance(Vd, er2d)
    L_uH = MU0 * Cair / EPS0                            # H/m
    Z = np.sqrt(L_uH / Cd)

    # 分區 Z0：以能量密度對 x 積分取遠區
    Ex = -(Vd[1:-1, 1:] - Vd[1:-1, :-1]) / dx
    Ey = -(Vd[1:, 1:-1] - Vd[:-1, 1:-1]) / dy
    col_e = EPS0 * (np.sum(0.5*(er2d+np.roll(er2d,-1,axis=1))*Ex**2, axis=0)*dy
                  + np.sum(0.5*(er2d+np.roll(er2d,-1,axis=0))*Ey**2, axis=0)*dx) / dx   # F/m per col
    n_left, n_right = int(0.15*nx), int(0.85*nx)
    c_far_l, c_far_r = col_e[:n_left].mean(), col_e[n_right:].mean()
    Z_l = np.sqrt(MU0 * Cair / (Cd * 0)) if False else np.sqrt((MU0*Cair/EPS0) / (col_e[:n_left].mean()*EPS0*0+0)) if False else None
    # 分區 Z0 用各區「局部電容」配合同一 L（非磁性 ⇒ L 與介質無關）
    Z_left  = np.sqrt(L_uH / (c_far_l * dx * 0 + c_far_l)) if False else np.sqrt(L_uH / c_far_l)
    Z_right = np.sqrt(L_uH / c_far_r)
    # 交界過剩電容等效長度
    c_far = np.where(np.arange(nx) < nx//2, c_far_l, c_far_r)
    L_ex = np.sum(np.maximum(col_e - c_far, 0.0)) * dx / min(c_far_l, c_far_r)
    return dict(Z_left=Z_left, Z_right=Z_right, Z_mean=Z, L_excess_um=L_ex*1e6,
                Cair=Cair, Cd=Cd, iters=itd, col_e=col_e)

# --- 網格收斂檢查（240×160 vs 360×240）---
r1 = fem_stripline_junction(0.143, 0.4, 4.2, 4.2, nx=240, ny=160)   # 均質：驗證用
r2 = fem_stripline_junction(0.143, 0.4, 4.2, 4.2, nx=360, ny=240)
z_ipc = tls.stripline_z0(0.143, 0.2, 0.0, 4.2)
print("均質 FR4 驗證：FEM Z0 = %.2f / %.2f Ω（240/360 網格）| IPC 解析 = %.2f Ω | 偏差 %.1f%% / %.1f%%"
      % (r1["Z_mean"], r2["Z_mean"], z_ipc,
         abs(r1["Z_mean"]-z_ipc)/z_ipc*100, abs(r2["Z_mean"]-z_ipc)/z_ipc*100))

# --- 剛撓交界：FR4 (4.2) → PI (3.3) ---
rj = fem_stripline_junction(0.143, 0.4, 4.2, 3.3, nx=360, ny=240)
dZ_pct = (rj["Z_right"] - rj["Z_left"]) / rj["Z_left"] * 100
first_order = (4.2 - 3.3) / (2 * 4.2) * 100
print("\n剛撓交界（FR4→PI）:")
print("  Z0(FR4 區) = %.2f Ω | Z0(PI 區) = %.2f Ω | 階躍 ΔZ = %+.2f%%" % (rj["Z_left"], rj["Z_right"], dZ_pct))
print("  一階公式 ΔZ/Z ≈ (ε₁−ε₂)/(2ε₁) = %+.2f%%  → FEM/公式比 = %.2f" % (first_order, dZ_pct/first_order))
print("  交界過剩電容等效長度 L_excess = %.1f µm" % rj["L_excess_um"])
import json as _json
_json.dump(dict(grid_check=dict(fem240=r1["Z_mean"], fem360=r2["Z_mean"], ipc=z_ipc),
                 junction=dict(Z_left=rj["Z_left"], Z_right=rj["Z_right"],
                               dZ_pct=dZ_pct, first_order_pct=first_order,
                               L_excess_um=rj["L_excess_um"])),
           open('/mnt/agents/output/fem_flexrigid.json', 'w'), indent=1)
