from matplotlib.pyplot import subplots
from numpy import linspace, pi, sqrt, tanh
from streamlit import caption, pyplot, sidebar, subheader, radio, slider, number_input
from matplotlib.pyplot import subplots
from numpy import linspace, pi, sqrt
from matplotlib.pyplot import subplots
import matplotlib.pyplot as plt

MENU, 表單=[], ['', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  # 本益比=slider("最高本益比(PE)", 0, 100, 25)
  # srch=text_input('搜尋', '')
  subheader("📊 訊號線內部電流密度分佈動態視覺化")
  subheader("幾何參數 (Geometric)")
  w = slider("線寬 W (μm)", 50, 300, 150)
  h = slider("介電總厚度 H (μm)", 100, 500, 300)
  t = number_input("NbTi 膜厚 t (nm)", value=100)
  s = slider("通道間距 S (μm)", 200, 1500, 850)
  w_m = w * 1e-6
  t_m = t * 1e-9
  # 物理常數設定
  phi0 = 2.07e-15
  mu0 = 4 * pi * 1e-7
  lambda_L = 200e-9  # 200 nm
  xi = 5e-9          # 5 nm

# 帶入前述計算所得的參數
# w: 線寬 (um), t: 膜厚 (nm), ic_real: 總臨界電流 (A), jd_a_cm2: 解對合極限

# 建立橫向坐標軸 (從 -W/2 到 +W/2，避開剛好等於邊緣導致分母為0的奇異點)
x = linspace(-w_m/2 * 0.999, w_m/2 * 0.999, 500)

jd = phi0 / (3 * sqrt(3) * pi * mu0 * (lambda_L**2) * xi) # A/m^2
jd_a_cm2 = jd / 1e4 # 轉為 A/cm^2

# 2. 計算邊緣擠壓修正因子 (Current Crowding Factor)
# 當 W >> lambda_L 時，修正因子趨近於 sqrt(2.4 * lambda_L / W)
crowding_factor = sqrt((2.4 * lambda_L / w_m) * tanh(w_m / (2 * lambda_L)))

# 3. 計算實際 Ic 與平均 Jc
ic_real = jd * (t_m * w_m) * crowding_factor
jc_avg_a_cm2 = (ic_real / (t_m * w_m)) / 1e4
# 根據倫敦麥克米倫公式計算局部電流密度 J(x)
# J(x) = I / (pi * t * sqrt((W/2)^2 - x^2))
jx = ic_real / (pi * t_m * sqrt((w_m/2)**2 - x**2))
jx_a_cm2 = jx / 1e4 # 轉為 A/cm^2

# 繪製 Matplotlib 圖表
fig, ax = subplots(figsize=(7, 3.5))
ax.plot(x * 1e6, jx_a_cm2 / 1e6, color='#FF4B4B', linewidth=2.5, label="Local Current Density J(x)")
ax.axhline(jd_a_cm2 / 1e6, color='black', linestyle='--', alpha=0.7, label="Depairing Limit $J_d$")

# 美化圖表
ax.set_title("Current Crowding Effect in Cri/oFlex NbTi Trace", fontsize=10, fontweight='bold')
ax.set_xlabel("Position across trace width $x$ ($\mu$m)", fontsize=9)
ax.set_ylabel("Current Density ($MA/cm^2$)", fontsize=9)
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(fontsize=8, loc='upper center')
ax.set_ylim(0, jd_a_cm2 / 1e6 * 1.2)

# 在 Streamlit 中渲染
pyplot(fig)

caption("💡 觀察：當您在側邊欄放大『線寬 W』時，雖然通道能承載的總電流 $I_c$ 變大，但中央凹陷會更深，代表邊緣擠壓效應越明顯。")
