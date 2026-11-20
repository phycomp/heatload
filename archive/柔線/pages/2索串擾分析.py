# query_transmission_lines.py
from streamlit import empty, markdown, secrets
from psycopg import connect as pgCnnct
import pandas as pd
scrt=secrets['uleam']
DB_CONFIG = {
    #**scrt
    "host": "localhost",
    "port": 5432,
    "dbname": "uleam",
    "user": "postgres",
    "password": "postgres"
}
def get_superconducting_lines():
    """查詢超導傳輸線"""
    with pgCnnct(**scrt) as conn:
        query = """
            SELECT v.name as vendor,
                   t.product_name,
                   t.frequency_max,
                   t.insertion_loss,
                   t.crosstalk_typical,
                   t.pitch,
                   t.material_conductor
            FROM transmission_lines t
            JOIN vendors v ON t.vendor_id = v.id
            WHERE t.is_superconducting = true
            ORDER BY t.frequency_max DESC
        """
        return pd.read_sql(query, conn)
def compare_crosstalk(min_frequency=1.0, max_frequency=10.0):
    """比較不同產品的串擾性能"""
    with pgCnnct(**scrt) as conn:
        query = """
            SELECT v.name as vendor,
                   t.product_name,
                   t.crosstalk_typical,
                   t.frequency_max,
                   t.pitch,
                   t.shielding_effectiveness
            FROM transmission_lines t
            JOIN vendors v ON t.vendor_id = v.id
            WHERE t.frequency_max >= %s
            ORDER BY t.crosstalk_typical DESC
        """
        return pd.read_sql(query, conn, params=(min_frequency,))
def get_frequency_response(product_name):
    """獲取特定產品的頻率響應"""
    with pgCnnct(**scrt) as conn:
        query = """
            SELECT f.frequency_ghz,
                   f.s21_db as insertion_loss,
                   f.s31_db as crosstalk
            FROM frequency_characteristics f
            JOIN transmission_lines t ON f.transmission_line_id = t.id
            WHERE t.product_name = %s
            ORDER BY f.frequency_ghz
        """
        return pd.read_sql(query, conn, params=(product_name,))

# 在 calculate_crosstalk 函數中添加 shielding_factor
def calculate_crosstalk_advanced(freqs, pitch_mm, length_m, material, shielding_type):
    """
    增強版串擾計算，支持獨立屏蔽結構
    """
    pitch_m = pitch_mm / 1000.0
    
    K_base = 0.1 * (1 / (pitch_m ** 2)) * (freqs / 1e9) # 基礎耦合系數
    
    # 屏蔽因子：獨立屏蔽 vs 無獨立屏蔽
    shielding_factors = {
        "individual": 0.15,   # 獨立屏蔽（如 Fraunhofer EMFT）
        "common": 0.6,        # 公共屏蔽（如帶狀線）
        "none": 1.0           # 無屏蔽
    }
    
    shielding_factor = shielding_factors.get(shielding_type, 0.5)
    
    K = K_base * shielding_factor # 應用屏蔽因子
    K = np.clip(K, 0, 0.3)  # 獨立屏蔽上限更低
    
    isolation = -20 * np.log10(K + 1e-6) - (0.08 * length_m) 串擾隔離度
    return isolation, K
if __name__ == "__main__":
    markdown("🔬 超導傳輸線:")
    狀態=empty()
    結果=get_superconducting_lines()
    狀態.code(結果)
    #輸出+=
    markdown("\n📊 串擾性能比較 (10GHz以上):")
    #輸出+=
    串態=empty()
    串態.code(compare_crosstalk(10.0))
    markdown("\n📈 Cri/oFlex-8 頻率響應:")
    頻態=empty()  #率響應
    頻態.code(get_frequency_response("Cri/oFlex-8"))
    #狀態.code(輸出)
