import streamlit as st
import socket
import threading
import queue
import time
import json

# 初始化執行緒安全的 Queue 
if "socket_queue" not in st.session_state:
    st.session_state.socket_queue = queue.Queue()

if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'last_command' not in st.session_state:
    st.session_state.last_command = None
if 'server_started' not in st.session_state:
    st.session_state.server_started = False

DELIMITER = b"\n<--END_OF_STREAM-->\n"

def run_socket_server(msg_queue):
    """使用定界符號 (Delimiter) 機制的安全 Socket 伺服器"""
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
                        # 每次讀取 64KB 數據
                        packet = conn.recv(65536)
                        if not packet:
                            break
                        raw_buffer.extend(packet)
                        
                        # 檢查是否包含結束定界符號
                        if DELIMITER in raw_buffer:
                            break
                    
                    if not raw_buffer:
                        continue
                        
                    # 移除定界符號並進行 UTF-8 安全解碼
                    data_to_decode = raw_buffer.split(DELIMITER)[0]
                    
                    try:
                        # 使用 errors='ignore' 或 'replace' 防止編碼錯誤導致伺服器崩潰
                        decoded_str = data_to_decode.decode('utf-8', errors='replace')
                        payload = json.loads(decoded_str)
                        
                        msg_queue.put({"type": "data", "addr": addr, "payload": payload})
                        conn.sendall(json.dumps({"status": "ok"}).encode('utf-8'))
                    except json.JSONDecodeError as je:
                        msg_queue.put({"type": "error", "message": f"JSON 格式損壞: {str(je)}"})
                        conn.sendall(json.dumps({"status": "error", "message": "JSON_INVALID"}).encode('utf-8'))
                        
            except Exception as e:
                msg_queue.put({"type": "error", "message": f"底層連線異常: {str(e)}"})
                break

# === Streamlit 網頁主 UI ===
st.title("🎛️ 量子傳輸線資料整合中樞")

if not st.session_state.server_started:
    if st.button("🚀 啟動底層 Socket 伺服器"):
        thread = threading.Thread(
            target=run_socket_server, 
            args=(st.session_state.socket_queue,), 
            daemon=True
        )
        thread.start()
        st.session_state.server_started = True
        st.success("伺服器背景監聽中...")
        st.rerun()

# 主執行緒非同步撈取 Queue 資料
while not st.session_state.socket_queue.empty():
    msg = st.session_state.socket_queue.get()
    if msg["type"] == "data":
        st.session_state.logs.append(f"✅ 成功接收來自 {msg['addr']} 的大封包數據")
        st.session_state.last_command = msg["payload"]
    elif msg["type"] == "error":
        st.session_state.logs.append(f"❌ 錯誤: {msg['message']}")

# UI 佈局渲染
st.subheader("📜 系統執行日誌 (Logs)")
st.text_area("Socket Logs", value="\n".join(st.session_state.logs), height=150)

if st.session_state.last_command:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("### 📊 2D 電磁場模擬即時渲染")
        if "simulation_results" in st.session_state.last_command:
            res = st.session_state.last_command["simulation_results"]
            if "visual_simulation_png_b64" in res:
                img_b64 = res["visual_simulation_png_b64"]
                st.image(f"data:image/png;base64,{img_b64}", use_container_width=True)
    with col2:
        st.write("### 📋 匯出的完整模擬參數 JSON")
        st.json(st.session_state.last_command)

# 背景保持定時刷新整理
if st.session_state.server_started:
    time.sleep(0.5)
    st.rerun()
