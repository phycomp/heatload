import socket
import struct
import json

def send_to_socket_server(payload: dict, host: str = '127.0.0.1', port: int = 65432) -> dict:
    """將資料打包並附加 4-byte 長度標頭，嚴謹發送至 Socket 伺服器"""
    try:
        # 1. 強制以 utf-8 將完整的 JSON 轉為 byte 陣列
        json_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        json_len = len(json_bytes)
        
        # 2. 打包長度成 4 位元組二進位資料 (網路位元組序)
        header = struct.pack('!I', json_len)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
            # 3. 先發送 4 位元組 Header，再發送 JSON 本體
            s.sendall(header)
            s.sendall(json_bytes)
            
            # 4. 接收伺服器的回傳確認
            response_packet = s.recv(4096)
            if response_packet:
                return json.loads(response_packet.decode('utf-8'))
            return {"status": "error", "message": "伺服器未回傳確認信號"}
            
    except ConnectionRefusedError:
        return {"status": "error", "message": "連線失敗，請確認 Streamlit 後台已啟動。"}
    except Exception as e:
        return {"status": "error", "message": f"發送端異常: {str(e)}"}

def run_socket_server(msg_queue):
    """具備嚴謹 Header 長度檢查與防錯機制的 Socket 伺服器"""
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
                    # 1. 精確讀取 4 個位元組的 Header
                    header = bytearray()
                    while len(header) < 4:
                        packet = conn.recv(4 - len(header))
                        if not packet:
                            break
                        header.extend(packet)
                    
                    if len(header) < 4:
                        continue
                    
                    # [關鍵修正] 使用 [0] 取得解包後的整數長度
                    data_len = struct.unpack('!I', bytes(header))[0]
                    
                    # 2. 循環讀取，直到完全收滿指定長度
                    raw_data = bytearray()
                    while len(raw_data) < data_len:
                        packet = conn.recv(min(data_len - len(raw_data), 65536))
                        if not packet:
                            break
                        raw_data.extend(packet)
                    
                    if len(raw_data) < data_len:
                        msg_queue.put({"type": "error", "message": f"接收未完成，預期 {data_len} 實際 {len(raw_data)}"})
                        continue
                    
                    # 3. 安全解碼與解析 JSON
                    try:
                        decoded_str = raw_data.decode('utf-8')
                        payload = json.loads(decoded_str)
                        msg_queue.put({"type": "data", "addr": addr, "payload": payload})
                        
                        # 成功回應
                        conn.sendall(json.dumps({"status": "ok"}).encode('utf-8'))
                    except UnicodeDecodeError as ue:
                        msg_queue.put({"type": "error", "message": f"UTF-8 解碼失敗，可能發生資料錯位: {str(ue)}"})
                    except json.JSONDecodeError as je:
                        msg_queue.put({"type": "error", "message": f"JSON 解析失敗: {str(je)}"})
                        
            except Exception as e:
                msg_queue.put({"type": "error", "message": f"Socket底層異常: {str(e)}"})
                break
import struct
import socket
import json

def SEND_TO_SOCKET_SERVER(payload: dict, host: str = '127.0.0.1', port: int = 65432) -> dict:
    """將資料打包並附加 4-byte 長度標頭，發送至 Socket 伺服器"""
    try:
        # 1. 將 JSON 轉為位元組數據
        json_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        json_len = len(json_bytes)
        
        # 2. 打包 4 位元組的網路位元組序 (Big-endian) 整數作為 Header
        header = struct.pack('!I', json_len)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
            # 3. 先發送 4 位元組長度，再發送完整的 JSON 資料
            s.sendall(header)
            s.sendall(json_bytes)
            
            # 接收伺服器確認回應
            data = s.recv(1024)
            return json.loads(data.decode('utf-8'))
    except ConnectionRefusedError:
        return {"status": "error", "message": "無法連線，請確認 Streamlit 伺服器已啟動。"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import matplotlib
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

# 關鍵修正 1：強制 matplotlib 使用非互動式後端，防止 Gdk/X11 記憶體區段錯誤
matplotlib.use('Agg')

def generate_em_field_image_base64(w: float, s: float, d_center: float) -> str:
    """產生 2D 電磁場模擬圖，並轉換為 base64 字串，不打開任何視窗"""
    # 建立 2D 網格空間
    x = np.linspace(-300, 300, 200)
    y = np.linspace(-50, 150, 100)
    X, Y = np.meshgrid(x, y)
    
    w_um = w * 1e6
    s_um = s * 1e6
    d_um = d_center * 1e6
    
    # 模擬主傳輸線與接地層
    V1 = 1.0 / np.sqrt((X)**2 + (Y + 1e-5)**2 + 10)
    V_g1 = -0.5 / np.sqrt((X - (w_um/2 + s_um))**2 + Y**2 + 10)
    V_g2 = -0.5 / np.sqrt((X + (w_um/2 + s_um))**2 + Y**2 + 10)
    
    E_field = np.gradient(V1 + V_g1 + V_g2)
    E_mag = np.sqrt(E_field[0]**2 + E_field[1]**2)
    E_mag = E_mag / E_mag.max()

    # 開始繪圖 (注意：這裡不會跳出視窗)
    fig, ax = plt.subplots(figsize=(10, 4))
    cp = ax.contourf(X, Y, E_mag, levels=50, cmap='inferno')
    fig.colorbar(cp, ax=ax, label='Normalized Electric Field Intensity (E)')
    
    # 標註物理結構
    ax.plot([-w_um/2, w_um/2], [0, 0], color='cyan', lw=4, label='Signal Core (NbTi)')
    ax.plot([-(w_um/2+s_um)-50, -(w_um/2+s_um)], [0, 0], color='white', lw=4, label='Ground Plane')
    ax.plot([(w_um/2+s_um), (w_um/2+s_um)+50], [0, 0], color='white', lw=4)
    ax.plot([d_um-w_um/2, d_um+w_um/2], [0, 0], color='magenta', lw=2, linestyle='--', label='Victim Line (Crosstalk)')

    ax.set_title("Cryogenic Flexible CPW Quantum Line - 2D E-Field Simulation", fontsize=12)
    ax.set_xlabel("X Position (µm)")
    ax.set_ylabel("Y Position (µm) Substrate")
    ax.legend(loc='upper right')
    
    # 關鍵修正 2：將 opacity=0.2 改為正確的 alpha=0.2
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    
    # 關鍵修正 3：將圖片記憶體緩衝區轉換為 Base64 字串
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig) # 釋放內存
    buf.seek(0)
    
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64

"""
import socket
import json

def SEND_TO_SOCKET_SERVER(payload: dict, host: str = '127.0.0.1', port: int = 65432) -> dict:
    #將模擬結果或指令發送至 Streamlit 底層 Socket 伺服器
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            # 序列化並發送
            s.sendall(json.dumps(payload).encode('utf-8'))
            # 接收伺服器確認回應
            data = s.recv(1024)
            return json.loads(data.decode('utf-8'))
    except ConnectionRefusedError:
        return {"status": "error", "message": "無法連線至 Socket 伺服器，請確認 Streamlit 後台已啟動。"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

"""

import numpy as np

class QuantumTransmissionLineSimulator:
    """低溫超導柔性傳輸線電磁與物理參數模擬器"""
    
    def __init__(self):
        # 物理常數
        self.mu0 = 4 * np.pi * 1e-7  # 真空磁導率 (H/m)
        self.eps0 = 8.854e-12        # 真空介電常數 (F/m)
        
    def simulate_cpw_impedance(self, w: float, s: float, t: float, h: float, eps_r: float, lambda_L_nm: float) -> dict:
        """
        計算考慮超導動態電感後的特徵阻抗 (Z0)
        :param w: 導線寬度 (m)
        :param s: 導線與接地間隙 (m)
        :param t: 超導薄膜厚度 (m)
        :param h: 介電層厚度 (m)
        :param eps_r: 介電常數 (如 PTFE 約 2.0)
        :param lambda_L_nm: 倫敦穿透深度 (奈米, NbTi 約 240nm)
        """
        # 1. 有效介電常數估算 (Coplanar Waveguide with finite substrate)
        eps_eff = (eps_r + 1) / 2
        
        # 2. 幾何電容與幾何電感 (利用共形映射保角變換簡化公式)
        # k0 = w / (w + 2*s)
        k0 = w / (w + 2 * s)
        # 使用精簡形式的完整橢圓積分比值逼近
        if k0 < 0.707:
            k_ratio = np.pi / np.log(2 * (1 + np.sqrt(1 - k0**2)) / (1 - np.sqrt(1 - k0**2)))
        else:
            k1 = np.sqrt(1 - k0**2)
            k_ratio = np.log(2 * (1 + np.sqrt(k0)) / (1 - np.sqrt(k0))) / np.pi
            
        C_g = 4 * self.eps0 * eps_eff * k_ratio
        L_g = (self.mu0 / 4) * (1 / k_ratio)
        
        # 3. 超導動態電感 (Kinetic Inductance) 計算
        lambda_m = lambda_L_nm * 1e-9
        # 當厚度 t 與 lambda 接近時的動態電感修正
        #L_k = (self.mu0 * lambda_m / (w * t)) * np.coth(t / lambda_m)
        L_k = (self.mu0 * lambda_m / (w * t)) * (1. / np.tanh(t / lambda_m))

        
        # 總電感與總阻抗
        L_total = L_g + L_k
        Z0 = np.sqrt(L_total / C_g)
        vp = 1 / np.sqrt(L_total * C_g) # 相速度
        
        return {
            "characteristic_impedance_ohm": float(Z0),
            "geometric_inductance_H_per_m": float(L_g),
            "kinetic_inductance_H_per_m": float(L_k),
            "capacitance_F_per_m": float(C_g),
            "phase_velocity_m_s": float(vp)
        }
        
    def calculate_crosstalk(self, Z0: float, d_center_m: float, w_m: float, length_m: float, freq_ghz: float) -> dict:
        """
        計算相鄰兩條傳輸線之間的電磁串擾 (Crosstalk)
        :param d_center_m: 兩線中心距 (m)
        :param length_m: 耦合長度 (m)
        :param freq_ghz: 微波頻率 (GHz)
        """
        # 互感與互容的簡化偶極矩逼近
        # 串擾係數與 (w / d_center)^2 成正比
        coupling_factor = (w_m / d_center_m) ** 2
        
        # 近端串擾 (NEXT) 與遠端串擾 (FEXT)
        omega = 2 * np.pi * (freq_ghz * 1e9)
        next_db = 20 * np.log10(coupling_factor * (length_m * omega / 3e8) + 1e-15)
        # 超導低溫下介質損耗極低，主要考慮幾何隔離
        fext_db = next_db - 3.5  # 經驗修正值
        
        return {
            "frequency_ghz": freq_ghz,
            "coupling_factor": float(coupling_factor),
            "near_end_crosstalk_next_db": float(next_db),
            "far_end_crosstalk_fext_db": float(fext_db)
        }
import matplotlib.pyplot as plt

def plot_electromagnetic_field(w: float, s: float, d_center: float):
    """繪製 2D 傳輸線橫截面電場模擬模擬圖"""
    # 建立 2D 網格空間 (微米單位)
    x = np.linspace(-300, 300, 200)
    y = np.linspace(-50, 150, 100)
    X, Y = np.meshgrid(x, y)
    
    # 模擬主傳輸線 (中心在 X=0) 與 鄰近傳輸線 (中心在 X=d_center)
    # 計算電位場 V (簡化多極電荷模型)
    w_um = w * 1e6
    s_um = s * 1e6
    d_um = d_center * 1e6
    
    # 主線訊號源
    V1 = 1.0 / np.sqrt((X)**2 + (Y + 1e-5)**2 + 10)
    # 遮蔽接地層效應 (邊緣降低)
    V_g1 = -0.5 / np.sqrt((X - (w_um/2 + s_um))**2 + Y**2 + 10)
    V_g2 = -0.5 / np.sqrt((X + (w_um/2 + s_um))**2 + Y**2 + 10)
    
    # 總電場強度 (梯度的模)
    E_field = np.gradient(V1 + V_g1 + V_g2)
    E_mag = np.sqrt(E_field[0]**2 + E_field[1]**2)
    # 正規化
    E_mag = E_mag / E_mag.max()

    plt.figure(figsize=(10, 4))
    # 繪製電場熱圖
    cp = plt.contourf(X, Y, E_mag, levels=50, cmap='inferno')
    plt.colorbar(cp, label='Normalized Electric Field Intensity (E)')
    
    # 標註物理結構位置
    plt.plot([-w_um/2, w_um/2], [0, 0], color='cyan', lw=4, label='Signal Core (NbTi)')
    plt.plot([-(w_um/2+s_um)-50, -(w_um/2+s_um)], [0, 0], color='white', lw=4, label='Ground Plane')
    plt.plot([(w_um/2+s_um), (w_um/2+s_um)+50], [0, 0], color='white', lw=4)
    
    # 鄰近被耦合線
    plt.plot([d_um-w_um/2, d_um+w_um/2], [0, 0], color='magenta', lw=2, linestyle='--', label='Victim Line (Crosstalk)')

    plt.title("Cryogenic Flexible CPW Quantum Line - 2D E-Field Simulation", fontsize=12)
    plt.xlabel("X Position (µm)")
    plt.ylabel("Y Position (µm) Substrate")
    plt.legend(loc='upper right')
    plt.grid(opacity=0.2)
    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    # 1. 初始化模擬與參數 (修正之前的 coth 錯誤)
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
    
    sim = QuantumTransmissionLineSimulator()
    
    # 阻抗計算 (注意：內部必須已改為 1.0 / np.tanh)
    imp_results = sim.simulate_cpw_impedance(
        w=config["wire_width_m"], s=config["gap_spacing_m"], t=config["film_thickness_m"],
        h=config["substrate_height_m"], eps_r=config["dielectric_constant_r"], lambda_L_nm=config["london_penetration_nm"]
    )
    
    crosstalk_results = sim.calculate_crosstalk(
        Z0=imp_results["characteristic_impedance_ohm"], d_center_m=config["interline_distance_m"],
        w_m=config["wire_width_m"], length_m=config["line_length_m"], freq_ghz=config["target_frequency_ghz"]
    )
    
    # 2. 生成不會報錯且安全的 base64 模擬圖形
    print("[Simulation] 正在背景計算 2D 電磁場分佈...")
    image_data_b64 = generate_em_field_image_base64(
        w=config["wire_width_m"], s=config["gap_spacing_m"], d_center=config["interline_distance_m"]
    )
    
    # 3. 整合至 master_output
    master_output = {
        "metadata": {
            "component": "Cryogenic_Flexible_Quantum_Cable",
            "status": "Simulation_Completed"
        },
        "input_physical_parameters": config,
        "simulation_results": {
            "impedance_metrics": imp_results,
            "crosstalk_metrics": crosstalk_results,
            "visual_simulation_png_b64": image_data_b64  # 安全附加圖片資料
        }
    }
    
    # 4. 發送至 Streamlit Socket 伺服器
    print("[Socket] 正在同步數據至底層控制中樞...")
    server_response = send_to_socket_server(master_output)
    print(f"伺服器回應: {server_response}")
if __name__ == "__MAIN__":
    # === 2. 設計傳輸線幾何與材料物理參數 ===
    # 適合 10mK 稀釋製冷機環境的超導柔性微帶/共面波導線
    config = {
        "wire_width_m": 50e-6,          # 導線寬度 50 µm
        "gap_spacing_m": 30e-6,         # 隙寬 30 µm
        "film_thickness_m": 200e-9,     # NbTi 薄膜厚度 200 nm
        "substrate_height_m": 127e-6,    # 柔性 PTFE 基材厚度 127 µm (5 mil)
        "dielectric_constant_r": 2.1,   # PTFE 介電常數
        "london_penetration_nm": 240.0, # NbTi 在極低溫下的倫敦穿透深度
        "line_length_m": 0.15,          # 傳輸線長度 15 cm
        "interline_distance_m": 150e-6, # 兩組量子傳輸線中心距 150 µm
        "target_frequency_ghz": 6.0     # 量子位元讀取常用的微波頻率 6 GHz
    }
    
    # 初始化模擬器
    sim = QuantumTransmissionLineSimulator()
    
    # 執行阻抗模擬
    imp_results = sim.simulate_cpw_impedance(
        w=config["wire_width_m"],
        s=config["gap_spacing_m"],
        t=config["film_thickness_m"],
        h=config["substrate_height_m"],
        eps_r=config["dielectric_constant_r"],
        lambda_L_nm=config["london_penetration_nm"]
    )
    
    # 執行串擾模擬
    crosstalk_results = sim.calculate_crosstalk(
        Z0=imp_results["characteristic_impedance_ohm"],
        d_center_m=config["interline_distance_m"],
        w_m=config["wire_width_m"],
        length_m=config["line_length_m"],
        freq_ghz=config["target_frequency_ghz"]
    )
    
    # === 5. 匯出所有的模擬參數為 JSON 格式 ===
    master_output = {
        "metadata": {
            "component": "Cryogenic_Flexible_Quantum_Cable",
            "status": "Simulation_Completed",
            "unit_system": "SI"
        },
        "input_physical_parameters": config,
        "simulation_results": {
            "impedance_metrics": imp_results,
            "crosstalk_metrics": crosstalk_results
        }
    }
    
    # 輸出至終端機確認
    print("================== 模擬結果 JSON 匯出 ==================")
    json_string = json.dumps(master_output, indent=2, ensure_ascii=False)
    print(json_string)
    
    # === 4. 展示電磁模擬圖形 ===
    print("\n[圖形展示] 正在生成 2D 電磁場洩漏與串擾範圍交互作用圖...")
    plot_electromagnetic_field(
        w=config["wire_width_m"],
        s=config["gap_spacing_m"],
        d_center=config["interline_distance_m"]
    )
    
    # === 1. 嘗試發送至 Streamlit Socket 伺服器 ===
    print("\n[Socket 通訊] 正在將數據同步至底層控制中樞...")
    server_response = send_to_socket_server(master_output)
    print(f"伺服器回應: {server_response}")
