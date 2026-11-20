import streamlit as st
import socket
import threading
import json
import time

# 設定 Socket 伺服器參數
HOST = '127.0.0.1'
PORT = 65432

# 初始化 Streamlit Session State
if 'server_status' not in st.session_state:
    st.session_state.server_status = "未啟動"
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'last_command' not in st.session_state:
    st.session_state.last_command = None
# 在您的 Streamlit 程式碼中追加：
if st.session_state.last_command and "simulation_results" in st.session_state.last_command:
    results = st.session_state.last_command["simulation_results"]
    
    if "visual_simulation_png_b64" in results:
        st.write("### 📊 2D 量子傳輸線電磁模擬圖 (即時接收)")
        # 解碼並顯示圖片
        img_b64 = results["visual_simulation_png_b64"]
        st.image(f"data:image/png;base64,{img_b64}", use_column_width=True)

def run_socket_server():
    """在後台執行的 Socket 伺服器"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        st.session_state.server_status = f"運行中 (監聽 {HOST}:{PORT})"
        
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(4096)
                    if not data:
                        continue
                    
                    # 解析接收到的指令 (預期為 JSON 格式)
                    payload = json.loads(data.decode('utf-8'))
                    st.session_state.logs.append(f"收到來自 {addr} 的資料: {payload}")
                    st.session_state.last_command = payload
                    
                    # 回應給客戶端
                    response = {"status": "success", "message": "Command received by Streamlit infrastructure."}
                    conn.sendall(json.dumps(response).encode('utf-8'))
            except Exception as e:
                st.session_state.logs.append(f"錯誤: {str(e)}")
                break

# === Streamlit 介面設計 ===
st.title("🤖 本地開源模型與硬體控制中樞")
st.subheader("底層 Socket 伺服器狀態")

col1, col2 = st.columns(2)
with col1:
    st.metric(label="伺服器狀態", value=st.session_state.server_status)

with col2:
    if st.button("啟動底層 Socket 伺服器"):
        if st.session_state.server_status == "未啟動":
            thread = threading.Thread(target=run_socket_server, daemon=True)
            thread.start()
            st.session_state.server_status = "啟動中..."
            st.rerun()

# 顯示最後收到的指令與日誌
st.divider()
st.subheader("📥 即時控制指令摘要 (Last Command)")
if st.session_state.last_command:
    st.json(st.session_state.last_command)
else:
    st.info("尚無指令傳入。")

st.subheader("📜 伺服器執行日誌 (Logs)")
st.text_area("Socket Logs", value="\n".join(st.session_state.logs), height=200)
