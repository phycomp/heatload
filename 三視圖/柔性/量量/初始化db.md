# 1. 建數據庫和用戶
createdb quantum_sop
psql quantum_sop -f schema.sql

# 2. 創建第一個 admin 用戶（bcrypt hash）
python -c "import bcrypt; print(bcrypt.hashpw(b'josh123', bcrypt.gensalt()).decode())"
psql quantum_sop -c "INSERT INTO users (username, password_hash, role) VALUES ('josh', '<粘貼上一步輸出>', 'admin');"

# 3. 安裝依賴并運行
pip install -r requirements.txt
streamlit run app.py

# 4. 打包
zip -r quantum_sop.zip .
