import streamlit as st
import socket
import threading
import queue
import time
import json

# --- 核心修正：使用 Queue 進行執行緒安全通訊 ---
# 1. 建立一個持久的 Queue 佇列
if "socket_queue" not in st.session_state:
    st.session_state.socket_queue = queue.Queue()

# 2. 初始化儲存 UI 資料的 Session State
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'last_command' not in st.session_state:
    st.session_state.last_command = None
if 'server_started' not in st.session_state:
    st.session_state.server_started = False

def run_socket_server(msg_queue):
    """在背景運行的 Socket 伺服器，僅透過 queue 傳遞資料"""
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
                    data = conn.recv(65536) # 增加接收緩衝區
                    if not data: continue
                    payload = json.loads(data.decode('utf-8'))
                    # 安全地將資料放入 Queue，而非直接操作 st.session_state
                    msg_queue.put({"type": "data", "addr": addr, "payload": payload})
                    conn.sendall(json.dumps({"status": "ok"}).encode('utf-8'))
            except Exception as e:
                msg_queue.put({"type": "error", "message": str(e)})
                break

# === Streamlit 介面與資料處理邏輯 ===
st.title("量子傳輸線控制中樞")

# 啟動按鈕
if not st.session_state.server_started:
    if st.button("啟動 Socket 伺服器"):
        thread = threading.Thread(
            target=run_socket_server, 
            args=(st.session_state.socket_queue,), 
            daemon=True
        )
        thread.start()
        st.session_state.server_started = True
        st.rerun()

# 關鍵修正 2：在主執行緒定期從 Queue 中取出資料更新 UI
while not st.session_state.socket_queue.empty():
    msg = st.session_state.socket_queue.get()
    if msg["type"] == "data":
        st.session_state.logs.append(f"收到資料: {msg['addr']}")
        st.session_state.last_command = msg["payload"]
    elif msg["type"] == "error":
        st.session_state.logs.append(f"錯誤: {msg['message']}")

import struct

def run_socket_server(msg_queue):
    """具備 Header 長度檢查的 Socket 伺服器 (安全接收大封包)"""
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
                    # 1. 先讀取 4 個位元組的 Header，得知接下來的 JSON 總長度
                    header = conn.recv(4)
                    if not header or len(header) < 4:
                        continue
                    
                    # 使用 struct 解包成不分正負的 32 位元整數 (Big-endian)
                    data_len = struct.unpack('!I', header)[0]
                    
                    # 2. 循環讀取，直到收滿 data_len 所指定的位元組數
                    raw_data = bytearray()
                    while len(raw_data) < data_len:
                        packet = conn.recv(min(data_len - len(raw_data), 65536))
                        if not packet:
                            raise ConnectionError("Socket 傳輸中途斷開")
                        raw_data.extend(packet)
                    
                    # 3. 完全收齊後再進行 JSON 解析
                    payload = json.loads(raw_data.decode('utf-8'))
                    msg_queue.put({"type": "data", "addr": addr, "payload": payload})
                    
                    # 回應客戶端成功
                    conn.sendall(json.dumps({"status": "ok"}).encode('utf-8'))
            except Exception as e:
                msg_queue.put({"type": "error", "message": f"Socket解析出錯: {str(e)}"})
                break

# === UI 顯示 ===
st.text_area("執行日誌", value="\n".join(st.session_state.logs), height=150)
if st.session_state.last_command:
    st.json(st.session_state.last_command)

# 自動刷新以達成即時效果
if st.session_state.server_started:
    time.sleep(1)
    st.rerun()
