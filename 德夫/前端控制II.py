import socket
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 強制非互動式後端，防止 Linux/X11 段錯誤
import matplotlib.pyplot as plt
import io
import base64

DELIMITER = b"\n<--END_OF_STREAM-->\n"

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
        # [修復原 coth 報錯]: 改用 1.0 / np.tanh
        L_k = (self.mu0 * lambda_m / (w * t)) * (1.0 / np.tanh(t / lambda_m))
        
        L_total = L_g + L_k
        Z0 = np.sqrt(L_total / C_g)
        vp = 1 / np.sqrt(L_total * C_g)
        
        return {
            "characteristic_impedance_ohm": float(Z0),
            "geometric_inductance_H_per_m": float(L_g),
            "kinetic_inductance_H_per_m": float(L_k),
            "capacitance_F_per_m": float(C_g),
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
            "near_end_crosstalk_next_db": float(next_db),
            "far_end_crosstalk_fext_db": float(fext_db)
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
    
    ax.plot([-w_um/2, w_um/2], [0, 0], color='cyan', lw=4, label='Signal Core')
    ax.plot([-(w_um/2+s_um)-50, -(w_um/2+s_um)], [0, 0], color='white', lw=4, label='Ground')
    ax.plot([(w_um/2+s_um), (w_um/2+s_um)+50], [0, 0], color='white', lw=4)
    ax.plot([d_um-w_um/2, d_um+w_um/2], [0, 0], color='magenta', lw=2, linestyle='--', label='Victim')

    ax.set_title("Superconducting Flexible Line - E-Field Distribution")
    ax.set_xlabel("X (µm)")
    ax.set_ylabel("Y (µm)")
    ax.legend(loc='upper right')
    
    # [修復原 opacity 報錯]: 改用 alpha
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def send_to_socket_server(payload: dict, host: str = '127.0.0.1', port: int = 65432) -> dict:
    """發送完整 JSON 並加上結束定界符號"""
    try:
        # 強制用 utf-8 編碼 JSON 字串
        json_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        # 組合資料本體與終端符號
        full_packet = json_bytes + DELIMITER
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(full_packet)
            
            response = s.recv(1024)
            return json.loads(response.decode('utf-8'))
    except ConnectionRefusedError:
        return {"status": "error", "message": "無法連線，請先在 Streamlit 點擊啟動伺服器。"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    config = {
        "wire_width_m": 50e-6,
        "gap_spacing_m": 30e-6,
        "film_thickness_m": 200e-9,
        "substrate_height_m": 127e-6,
        "dielectric_constant_r": 2.1,
        "london_penetration_nm": 240.0,
        "line_length_m": 0.15,
        "interline_distance_m": 150e-6,
        "target_frequency_ghz": 6.0
    }
    
    print("[1/3] 正在進行低溫超導物理特徵阻抗及串擾計算...")
    sim = QuantumTransmissionLineSimulator()
    imp_res = sim.simulate_cpw_impedance(
        w=config["wire_width_m"], s=config["gap_spacing_m"], t=config["film_thickness_m"],
        h=config["substrate_height_m"], eps_r=config["dielectric_constant_r"], lambda_L_nm=config["london_penetration_nm"]
    )
    cross_res = sim.calculate_crosstalk(
        Z0=imp_res["characteristic_impedance_ohm"], d_center_m=config["interline_distance_m"],
        w_m=config["wire_width_m"], length_m=config["line_length_m"], freq_ghz=config["target_frequency_ghz"]
    )
    
    print("[2/3] 正在背景繪製 2D 向量電磁模擬場分佈圖...")
    img_b64 = generate_em_field_image_base64(
        w=config["wire_width_m"], s=config["gap_spacing_m"], d_center=config["interline_distance_m"]
    )
    
    master_output = {
        "metadata": {"component": "Cryogenic_Flexible_Quantum_Cable", "status": "Simulation_Completed"},
        "input_physical_parameters": config,
        "simulation_results": {
            "impedance_metrics": imp_res,
            "crosstalk_metrics": cross_res,
            "visual_simulation_png_b64": img_b64
        }
    }
    
    print("[3/3] 正在建立 Socket 管道並推送安全定界數據封包...")
    reply = send_to_socket_server(master_output)
    print(f"📡 伺服器回應確認：{reply}")
