import streamlit as st
import socket
import threading
import queue
import time
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 強制非互動式後端，防止 Linux/X11 記憶體段錯誤
import matplotlib.pyplot as plt
import io
import base64

# --- 1. 初始化執行緒安全的 Queue 與狀態 ---
if "socket_queue" not in st.session_state:
    st.session_state.socket_queue = queue.Queue()
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'last_sim_result' not in st.session_state:
    st.session_state.last_sim_result = None
if 'server_started' not in st.session_state:
    st.session_state.server_started = False

DELIMITER = b"\n<--END_OF_STREAM-->\n"

# --- 2. 模擬引擎核心類別 (後端計算邏輯) ---
class QuantumTransmissionLineSimulator:
    """低溫超導柔性傳輸線電磁與物理參數模擬器"""
    def __init__(self):
        self.mu0 = 4 * np.pi * 1e-7
        self.eps0 = 8.854e-12
        
    def simulate_cpw_impedance(self, w: float, s: float, t: float, h: float, eps_r: float, lambda_L_nm: float) -> dict:
        eps_eff = (eps_r + 1) / 2
        k0 = w / (w + 2 * s)
        
        if k0 < 0.707:
            k_ratio = np.pi / np.log(2 * (1 + np.sqrt(1 - k0**2)) / (1 - np.sqrt(1 - k0**2)))
        else:
            k_ratio = np.log(2 * (1 + np.sqrt(k0)) / (1 - np.sqrt(k0))) / np.pi
            
        C_g = 4 * self.eps0 * eps_eff * k_ratio
        L_g = (self.mu0 / 4) * (1 / k_ratio)
        
        lambda_m = lambda_L_nm * 1e-9
        L_k = (self.mu0 * lambda_m / (w * t)) * (1.0 / np.tanh(t / lambda_m))
        
        L_total = L_g + L_k
        Z0 = np.sqrt(L_total / C_g)
        vp = 1 / np.sqrt(L_total * C_g)
        
        return {
            "characteristic_impedance_ohm": round(float(Z0), 2),
            "geometric_inductance_uH_per_m": round(float(L_g * 1e6), 4),
            "kinetic_inductance_uH_per_m": round(float(L_k * 1e6), 4),
            "capacitance_pF_per_m": round(float(C_g * 1e12), 2),
            "phase_velocity_m_s": float(vp)
        }
        
    def calculate_crosstalk(self, Z0: float, d_center_m: float, w_m: float, length_m: float, freq_ghz: float) -> dict:
        coupling_factor = (w_m / d_center_m) ** 2
        omega = 2 * np.pi * (freq_ghz * 1e9)
        next_db = 20 * np.log10(coupling_factor * (length_m * omega / 3e8) + 1e-15)
        fext_db = next_db - 3.5
        return {
            "frequency_ghz": freq_ghz,
            "coupling_factor": float(coupling_factor),
            "near_end_crosstalk_next_db": round(float(next_db), 2),
            "far_end_crosstalk_fext_db": round(float(fext_db), 2)
        }

def generate_em_field_image_base64(w: float, s: float, d_center: float) -> str:
    """生成 2D 電磁場熱圖並轉換為 Base64 格式"""
    x = np.linspace(-300, 300, 200)
    y = np.linspace(-50, 150, 100)
    X, Y = np.meshgrid(x, y)
    
    w_um, s_um, d_um = w * 1e6, s * 1e6, d_center * 1e6
    
    V1 = 1.0 / np.sqrt((X)**2 + (Y + 1e-5)**2 + 10)
    V_g1 = -0.5 / np.sqrt((X - (w_um/2 + s_um))**2 + Y**2 + 10)
    V_g2 = -0.5 / np.sqrt((X + (w_um/2 + s_um))**2 + Y**2 + 10)
    
    E_field = np.gradient(V1 + V_g1 + V_g2)
    E_mag = np.sqrt(E_field[0]**2 + E_field[1]**2)
    E_mag = E_mag / E_mag.max()

    fig, ax = plt.subplots(figsize=(8, 3.5))
    cp = ax.contourf(X, Y, E_mag, levels=40, cmap='inferno')
    fig.colorbar(cp, ax=ax, label='E-Field Intensity')
    
    # 修正原本括號內留空的錯誤，標註截面結構位置
    ax.plot([-w_um/2, w_um/2], [0, 0], color='cyan', lw=4, label='Signal Core')
    ax.plot([-(w_um/2+s_um)-50, -(w_um/2+s_um)], [0, 0], color='white', lw=4, label='Ground')
    ax.plot([(w_um/2+s_um), (w_um/2+s_um)+50], [0, 0], color='white', lw=4)
    ax.plot([d_um-w_um/2, d_um+w_um/2], [0, 0], color='magenta', lw=2, linestyle='--', label='Victim')

    ax.set_title("Superconducting Flexible Line - E-Field Distribution")
    ax.set_xlabel("X (µm)")
    ax.set_ylabel("Y (µm)")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# --- 3. 底層 Socket 伺服器執行緒 (負責異步監聽與參數解碼) ---
def run_socket_server(msg_queue):
    """異步 Socket 伺服器：接收控制項指令並將任務塞入佇列"""
    HOST = '127.0.0.1'
    PORT = 65432
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    raw_buffer = bytearray()
                    while True:
                        packet = conn.recv(65536)
                        if not packet:
                            break
                        raw_buffer.extend(packet)
                        if DELIMITER in raw_buffer:
                            break
                    
                    if not raw_buffer:
                        continue
                    
                    # 拆分數據本體並解析
                    body = raw_buffer.split(DELIMITER)[0]
                    decoded_str = body.decode('utf-8', errors='replace')
                    payload = json.loads(decoded_str)
                    
                    # 將收到的硬體配置，在背景觸發物理計算引擎
                    config = payload.get("config", {})
                    sim = QuantumTransmissionLineSimulator()
                    
                    imp_res = sim.simulate_cpw_impedance(
                        w=config["wire_width_m"], s=config["gap_spacing_m"], t=config["film_thickness_m"],
                        h=config["substrate_height_m"], eps_r=config["dielectric_constant_r"], lambda_L_nm=config["london_penetration_nm"]
                    )
                    cross_res = sim.calculate_crosstalk(
                        Z0=imp_res["characteristic_impedance_ohm"], d_center_m=config["interline_distance_m"],
                        w_m=config["wire_width_m"], length_m=config["line_length_m"], freq_ghz=config["target_frequency_ghz"]
                    )
                    img_b64 = generate_em_field_image_base64(
                        w=config["wire_width_m"], s=config["gap_spacing_m"], d_center=config["interline_distance_m"]
                    )
                    
                    # 打包完整模擬成果
                    master_output = {
                        "metadata": {"component": "Cryogenic_Flexible_Quantum_Cable", "timestamp": time.time()},
                        "input_physical_parameters": config,
                        "simulation_results": {
                            "impedance_metrics": imp_res,
                            "crosstalk_metrics": cross_res,
                            "visual_simulation_png_b64": img_b64
                        }
                    }
                    
                    # 推送回 UI 執行緒
                    msg_queue.put({"type": "data", "payload": master_output})
                    conn.sendall(json.dumps({"status": "processed"}).encode('utf-8'))
                    
            except Exception as e:
                msg_queue.put({"type": "error", "message": str(e)})
                break

# --- 4. 模擬 Socket 客戶端傳送機制 ---
def trigger_backend_simulation(config_dict):
    """Streamlit 控制項直接向本機 Socket Server 發送參數"""
    try:
        packet = json.dumps({"action": "RUN_SIMULATION", "config": config_dict}, ensure_ascii=False).encode('utf-8') + DELIMITER
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 65432))
            s.sendall(packet)
            s.recv(1024)
        return True
    except ConnectionRefusedError:
        st.error("❌ 無法連接後端 Socket 伺服器，請先確保下方監聽已啟動。")
        return False

# =====================================================================
# --- 5. STREAMLIT 前端互動式 UI 設計 ---
# =====================================================================
st.set_page_config(layout="wide")
st.title("🛡️ 量子低溫柔性傳輸線 — 前端互動控制與物理模擬中樞")
st.markdown("本系統整合了 **Streamlit 前端 UI 參數控制**、**後台 Socket 通訊協定**與**超導量子晶片封裝物理引擎**。")

# 側邊欄：Socket 伺服器生命週期控制
with st.sidebar:
    st.header("⚙️ 基礎通訊架構設定")
    if not st.session_state.server_started:
        if st.button("🚀 啟動底層 Socket 伺服器 (127.0.0.1:65432)", use_container_width=True):
            thread = threading.Thread(target=run_socket_server, args=(st.session_state.socket_queue,), daemon=True)
            thread.start()
            st.session_state.server_started = True
            st.session_state.logs.append("📌 Socket Server 於本地端 65432 端口啟動監聽。")
            st.rerun()
    else:
        st.success("🟢 後端 Socket 伺服器運行中")
    
    st.subheader("📟 Socket 通訊即時日誌")
    st.caption("顯示底層異步事件傳輸狀態：")
    st.text_area("Socket Logs", value="\n".join(st.session_state.logs), height=150, disabled=True)

# 主畫面佈局
col_input, col_display = st.columns([1, 2])

with col_input:
    st.subheader("📐 1. 輸入傳輸線幾何與物理參數")
    st.markdown("調整下方控制項以改變超導共面波導 (CPW) 的物理特性：")
    
    w_um = st.slider("導線核心寬度 Width (µm)", min_value=10, max_value=200, value=50, step=5)
    s_um = st.slider("核心與接地間隙 Gap (µm)", min_value=10, max_value=150, value=30, step=5)
    d_um = st.slider("相鄰線中心距 Distance (µm)", min_value=100, max_value=500, value=150, step=10)
    
    st.divider()
    
    t_nm = st.number_input("超導薄膜厚度 Thickness (nm)", min_value=50, max_value=1000, value=200, step=50)
    h_um = st.number_input("柔性基材厚度 Substrate Height (µm)", min_value=25, max_value=500, value=127, step=1)
    eps_r = st.selectbox("介電質基材種類 (Dielectric Constant)", options=[2.1, 3.4, 11.9], format_func=lambda x: f"PTFE (εr=2.1)" if x==2.1 else (f"Polyimide (εr=3.4)" if x==3.4 else f"Silicon (εr=11.9)"))
    lambda_L = st.number_input("倫敦穿透深度 London Depth (nm)", min_value=50, max_value=500, value=240, help="NbTi一般約為240nm")
    freq = st.slider("微波操作頻率 Frequency (GHz)", min_value=1.0, max_value=12.0, value=6.0, step=0.5)
    length = st.number_input("耦合長度 Length (m)", min_value=0.01, max_value=1.0, value=0.15, step=0.01)

if __name__ == "__main__":
    current_config = {"wire_width_m": w_um * 1e-6,
      "gap_spacing_m": s_um * 1e-6,
      "interline_distance_m": d_um * 1e-6,
      "film_thickness_m": t_nm * 1e-9,
      "substrate_height_m": h_um * 1e-6,
      "dielectric_constant_r": eps_r,
      "london_penetration_nm": float(lambda_L),
      "target_frequency_ghz": freq,
      "line_length_m": length}
    st.write("")
    if st.button("⚡ 送出參數至 Socket 並執行物理模擬", type="primary", use_container_width=True):
      if st.session_state.server_started:
        st.session_state.logs.append(f"📡 前端送出控制項參數：Width={w_um}µm, Gap={s_um}µm")
        with st.spinner("後端模擬引擎計算中..."):
          trigger_backend_simulation(current_config)
      else:st.error("請先在左側面板啟動底層 Socket 伺服器！")
#檢查 Queue 更新 UI 狀態
      while not st.session_state.socket_queue.empty():
        msg = st.session_state.socket_queue.get()
        if msg["type"] == "data":
          st.session_state.last_sim_result = msg["payload"]
          st.session_state.logs.append("🎉 收到後端解算完成的完整封包。")
        elif msg["type"] == "error":
          st.session_state.logs.append(f"❌ 錯誤: {msg['message']}")
        with col_display:st.subheader("🔮 2. 物理模擬解算結果與圖形渲染")
          if st.session_state.last_sim_result is None:
            st.info("💡 尚未收到模擬數據。請調整左側參數並點擊「送出參數並執行物理模擬」。")
          else:res = st.session_state.last_sim_result["simulation_results"]
            imp = res["impedance_metrics"]
            cross = res["crosstalk_metrics"]
      m_col1, m_col2, m_col3 = st.columns(3)
      with m_col1:
        st.metric(label="🎯 特徵阻抗 Characteristic Impedance", value=f"{imp['characteristic_impedance_ohm']} Ω", delta=f"{round(imp['characteristic_impedance_ohm']-50.0, 2)} Ω 對齊目標(50Ω)")
      with m_col2:
        st.metric(label="🛑 近端微波串擾 NEXT (6 GHz)", value=f"{cross['near_end_crosstalk_next_db']} dB")
      with m_col3:
        st.metric(label="🌀 超導動態電感 Kinetic Inductance", value=f"{imp['kinetic_inductance_uH_per_m']} µH/m")
      g_col1, g_col2 = st.columns([1, 1])
      with g_col1:
        st.markdown("2D 橫截面電場洩漏與鄰近線耦合熱圖 (E-Field Distribution)")
        img_b64 = res["visual_simulation_png_b64"]
        st.image(f"data:image/png;base64,{img_b64}", use_container_width=True)
      with g_col2:st.markdown("詳細電磁學參數矩陣")
        st.json(st.session_state.last_sim_result)
        st.divider()
        json_string = json.dumps(st.session_state.last_sim_result, indent=2, ensure_ascii=False)
        st.download_button(label="💾 匯出並下載所有模擬參數 (JSON)",file_name=f"quantum_cable_sim_{int(time.time())}.json",mime="application/json",data=json_string,use_container_width=True)
      定期自動刷新畫面，維持 Socket 與網頁即時連動
      if st.session_state.server_started:
        time.sleep(0.3)st.rerun()
