from streamlit import caption, columns, error, file_uploader, pyplot, radio, set_page_config, sidebar, slider, stop, title
from matplotlib.pyplot import subplots
from numpy import abs, exp, fft, linspace, log, log10, ones_like, pi, e, log10, sin
from scipy.fft import fft, ifft, fftshift, fftfreq
from pygmsh.occ import Geometry
from skfem import Basis, ElementTriP1, BilinearForm, asm
#$import rfssweep  # pip install scikit-rf 亦可直接讀 .s2p，這裡簡化自己算
from skfem import Mesh, ElementTriP1, InteriorBasis, bilinear_form, LinearForm, asm, condense, solve

set_page_config(layout="wide")

def mesh_pair(w, d, h, res=2):
    """
    產生微帶雙線 2-D 截面 (x∈[-w/2-d, w/2+d], y∈[0, h+200 µm])
    單位：µm
    """
    geom = Geometry()
    model = geom.__enter__()
    rect = model.add_rectangle([-w/2-d, 0, 0], w+2*d, h)
    strip1 = model.add_rectangle([-w/2-d, h, 0], w, 1e-3)
    strip2 = model.add_rectangle([d, h, 0], w, 1e-3)
    model.synchronize()
    geom.set_mesh_size_callback(
        lambda dim, tag, x, y, z: res if y < h+10 else res*5)
    mesh = geom.generate_mesh()
    geom.__exit__()
    return mesh

def extract_Cm_Lm(w, d, h, er):
    mesh = mesh_pair(w, d, h)
    basis = Basis(mesh, ElementTriP1())
    # 計算電容矩陣
    @BilinearForm
    def cform(u, v, w):
        return sum(v*y for y in u.grad) * (er if w.y[0]<h else 1.)
    C = asm(cform, basis)
    dof0 = basis.get_dofs(lambda x: x[1] > h-1e-6)  # 導體1
    dof1 = basis.get_dofs(lambda x: (x[0]>d-1e-6) & (x[1]>h-1e-6))  # 導體2
    # 單位長度 Cm = (C12) / length
    Cm = abs(C[dof0, dof1].mean()) * 1e12 * 1e-2  # pF/cm
    # 計算電感（假設 µr=1）
    @BilinearForm
    def lform(u, v, w):
        return sum(v*y for y in u.grad)
    L = asm(lform, basis)
    Lm = abs(L[dof0, dof1].mean()) * 1e9 * 1e-2     # nH/cm
    return Cm, Lm

with sidebar:
    title("傳輸線模擬：頻域 S 參數 ↔ 時域脈衝")
    基板=["Rogers4350B", "FR-4", "BCB", "Megtron6"]
    mode = radio("資料來源", ["理想模型", "上傳 .s2p"])
    if mode == "理想模型":
        L   = slider("線長 (cm)", 1, 50, 10)
        att = slider("衰減常數 α (dB/m@1GHz)", 0.1, 5.0, 1.0)
        Z0  = slider("標稱阻抗 Z₀ (Ω)", 40, 60, 50)
        vel = slider("相對速度 v/c", 0.3, 1.0, 0.6)
        w   = slider("線寬 w (µm)", 100, 1000, 400)
        d   = slider("線間距 d (µm)", 50, 500, 100)
        sub = radio("基板", 基板, horizontal=True)
        freq = linspace(0.05, 20, 401)  # GHz ---- 產生或讀取 S 參數 ----
    else:
        f = file_uploader("選擇 .s2p", type=["s2p"])
if mode == "理想模型":
    beta = 2*pi*freq*1e9 / (vel*3e8)          # 相位常數
    alpha = att * log(10)/20 * (L/100)        # 轉成線性 Np
    S21 = exp(-alpha*L/100 - 1j*beta*L/100)   # 簡單指數模型
    S11 = (Z0-50)/(Z0+50) * ones_like(freq)   # 單點不連續反射
else:
    try:
        import skrf as rf
        nw = rf.Network(f)
        freq = nw.f*1e-9  # 轉 GHz
        S11, S21 = nw.s[:,0,0], nw.s[:,0,1]
    except Exception as e:
        error("讀檔失敗"); stop()

def 微帶線互容(w, d, h, er):
    """
    微帶線互容 Cm [pF / cm]
    w,d,h 單位皆為 µm
    """
    w, d, h = w*1e-3, d*1e-3, h*1e-3          # 轉成 mm
    x = (w/h)**0.8 * (d/h)**-1.2 * sqrt(er)
    Cm = 0.035 * x**1.25 * exp(-0.9*d/w)   # pF/cm
    return Cm

def 微帶線互感(w, d, h):
    """
    微帶線互感 Lm [nH / cm]
    """
    w, d, h = w*1e-3, d*1e-3, h*1e-3
    k = 0.002 * log(1 + (2*h/d)**1.5) * (w/h)**-0.3
    Lm = k * 1e3                                # nH/cm
    return Lm
# ---- 繪圖 ----
col1, col2 = columns(2)
with col1:
    fig, ax = subplots(figsize=(4,3))
    ax.plot(freq, 20*log10(abs(S11)), label='S11 (RL)')
    ax.plot(freq, 20*log10(abs(S21)), label='S21 (IL)')
    ax.set_xlabel("Freq (GHz)"); ax.set_ylabel("Magnitude (dB)")
    ax.legend(); ax.grid(); pyplot(fig)

with col2:
    # 時域：對 S21 做 IFFT → 脈衝響應
    df = freq[1]-freq[0]
    t = fftfreq(len(freq), df)
    pulse = ifft(S21)
    fig, ax = subplots(figsize=(4,3))
    ax.plot(t*1e9, abs(pulse))
    ax.set_xlabel("Time (ns)"); ax.set_ylabel("|h(t)|")
    ax.grid(); pyplot(fig)

    # 互容 / 互感 lookup（1 cm 長度，d=gap, h=substrate）
    C_m = 微帶線互容(w, d, h, er)      # pF/cm
    L_m = 微帶線互感(w, d, h)          # nH/cm
    beta = 2*pi*f*1e9/c * sqrt(er_eff)
    NEXT = 0.5*(C_m*Z0 + L_m/Z0) * f*1e9 * 1e-12 * 20*log10(e)
    FEXT = 0.5*(C_m*Z0 - L_m/Z0) * f*1e9 * sin(beta*L/100)/(beta*L/100) * 1e-12 * 20*log10(e)
caption("左圖：頻域回損/插損；右圖：時域脈衝響應（走線後訊號變多胖）")
