# 1. 產生 DOE 輸入
python tools/generate_doe.py
# -> polar_doe_input.csv

# 2. 用 Polar Excel 填入 Zdiff，另存 polar_doe.csv

# 3. 對標分析
python tools/compare_polar.py

# 4. 擬合修正係數
python tools/fit_correction.py
# -> data/correction_coeffs.json

# 5. 擬合多項式（給 Excel 公式用）
python tools/polyfit_model.py
# -> data/poly_coeffs.json

# 6. 啟動 Streamlit
streamlit run app.py
