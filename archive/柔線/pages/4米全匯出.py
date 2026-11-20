
# export_quantum_db.py
import psycopg
import json
import pandas as pd
from datetime import datetime
from streamlit import secrets

#DB_CONFIG = { "host": "localhost", "port": 5432, "dbname": "quantum_db", "user": "postgres", "password": "your_password" }
scrt=secrets['uleam']
# ============================================
# 完整數據導出
# ============================================

def export_complete_database():
    """導出完整的6家供應商傳輸線參數數據庫"""
    
    with psycopg.connect(**scrt) as conn:
        
        # 1. 導出供應商清單
        vendors_df = pd.read_sql("""
            SELECT id, name, technology, country, created_at
            FROM vendors
            ORDER BY id
        """, conn)
        
        # 2. 導出所有傳輸線產品參數
        products_df = pd.read_sql("""
            SELECT 
                v.name as vendor_name,
                t.product_name,
                t.product_series,
                t.impedance,
                t.frequency_max,
                t.insertion_loss,
                t.return_loss,
                t.crosstalk_typical,
                t.vswr,
                t.capacitance,
                t.pitch,
                t.width,
                t.height,
                t.weight_per_meter,
                t.bend_radius_min,
                t.material_conductor,
                t.material_dielectric,
                t.material_shield,
                t.is_superconducting,
                t.operating_temp_min,
                t.operating_temp_max,
                t.power_handling,
                t.shielding_effectiveness,
                t.application,
                t.notes
            FROM transmission_lines t
            JOIN vendors v ON t.vendor_id = v.id
            ORDER BY v.name, t.product_name
        """, conn)
        
        # 3. 導出頻率特性數據
        freq_df = pd.read_sql("""
            SELECT 
                v.name as vendor_name,
                t.product_name,
                f.frequency_ghz,
                f.s11_db,
                f.s21_db,
                f.s31_db,
                f.s41_db,
                f.phase_deg,
                f.group_delay_ps,
                f.measurement_temp
            FROM frequency_characteristics f
            JOIN transmission_lines t ON f.transmission_line_id = t.id
            JOIN vendors v ON t.vendor_id = v.id
            ORDER BY v.name, t.product_name, f.frequency_ghz
        """, conn)
        
        return vendors_df, products_df, freq_df

# ============================================
# 導出爲多種格式
# ============================================

def export_to_json(vendors_df, products_df, freq_df):
    """導出爲JSON格式"""
    
    # 構建完整的數據結構
    export_data = {
        "export_date": datetime.now().isoformat(),
        "database_name": "Quantum Transmission Lines Database",
        "total_vendors": len(vendors_df),
        "total_products": len(products_df),
        "total_frequency_points": len(freq_df),
        "vendors": vendors_df.to_dict(orient='records'),
        "transmission_lines": products_df.to_dict(orient='records'),
        "frequency_characteristics": freq_df.to_dict(orient='records')
    }
    
    # 保存JSON文件
    with open('quantum_transmission_lines.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
    
    print("✅ JSON導出完成: quantum_transmission_lines.json")
    return export_data

def export_to_excel(vendors_df, products_df, freq_df):
    """導出爲Excel文件（多工作表）"""
    
    output_file = 'quantum_transmission_lines.xlsx'
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 供應商工作表
        vendors_df.to_excel(writer, sheet_name='供應商', index=False)
        
        # 傳輸線參數工作表
        products_df.to_excel(writer, sheet_name='傳輸線物理參數', index=False)
        
        # 頻率特性工作表
        freq_df.to_excel(writer, sheet_name='頻率特性_S參數', index=False)
        
        # 統計信息工作表
        summary = pd.DataFrame({
            '統計項': ['供應商數量', '產品型號數量', '頻率特性數據點'],
            '數值': [len(vendors_df), len(products_df), len(freq_df)]
        })
        summary.to_excel(writer, sheet_name='統計信息', index=False)
        
        # 按供應商分類統計
        vendor_stats = products_df.groupby('vendor_name').agg({
            'product_name': 'count',
            'is_superconducting': lambda x: x.sum(),
            'frequency_max': 'max'
        }).rename(columns={
            'product_name': '產品數量',
            'is_superconducting': '超導產品數量',
            'frequency_max': '最高頻率(GHz)'
        })
        vendor_stats.to_excel(writer, sheet_name='供應商統計')
    
    print(f"✅ Excel導出完成: {output_file}")

def export_to_csv(vendors_df, products_df, freq_df):
    """導出爲CSV文件（多個文件）"""
    
    vendors_df.to_csv('vendors.csv', index=False, encoding='utf-8-sig')
    products_df.to_csv('transmission_lines.csv', index=False, encoding='utf-8-sig')
    freq_df.to_csv('frequency_characteristics.csv', index=False, encoding='utf-8-sig')
    
    print("✅ CSV導出完成:")
    print("   - vendors.csv")
    print("   - transmission_lines.csv")
    print("   - frequency_characteristics.csv")

def export_to_markdown(products_df):
    """導出爲Markdown表格格式"""
    
    with open('transmission_lines_parameters.md', 'w', encoding='utf-8') as f:
        f.write("# 量子傳輸線物理參數數據庫\n\n")
        f.write(f"導出時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 6家供應商傳輸線詳細參數\n\n")
        f.write("| 供應商 | 產品型號 | 阻抗(Ω) | 最高頻率(GHz) | 插入損耗(dB/m) | 串擾(dB) | 間距(mm) | 超導 | 材料 |\n")
        f.write("|--------|---------|---------|---------------|----------------|----------|----------|------|------|\n")
        
        for _, row in products_df.iterrows():
            sc_mark = "✓" if row['is_superconducting'] else "—"
            f.write(f"| {row['vendor_name']} | {row['product_name']} | {row['impedance']} | {row['frequency_max']} | {row['insertion_loss']} | {row['crosstalk_typical']} | {row['pitch']} | {sc_mark} | {row['material_conductor']} |\n")
    
    print("✅ Markdown導出完成: transmission_lines_parameters.md")

# ============================================
# 數據驗證與展示
# ============================================

def display_database_summary(vendors_df, products_df, freq_df):
    """在控制台顯示數據庫摘要"""
    
    print("\n" + "="*80)
    print("📊 量子傳輸線數據庫 - 完整摘要")
    print("="*80)
    
    print(f"\n📦 數據庫統計:")
    print(f"   ├─ 供應商數量: {len(vendors_df)}")
    print(f"   ├─ 產品型號數量: {len(products_df)}")
    print(f"   └─ 頻率特性數據點: {len(freq_df)}")
    
    print(f"\n🏭 供應商清單:")
    for _, vendor in vendors_df.iterrows():
        tech_icon = "🔬" if "Superconducting" in vendor['technology'] else "🔌"
        print(f"   {tech_icon} {vendor['name']:25} | {vendor['technology']:35} | {vendor['country']}")
    
    print(f"\n📡 傳輸線產品詳情:")
    for vendor_name in products_df['vendor_name'].unique():
        vendor_products = products_df[products_df['vendor_name'] == vendor_name]
        print(f"\n   【{vendor_name}】")
        for _, product in vendor_products.iterrows():
            sc_tag = "🔬超導" if product['is_superconducting'] else "🔌常溫"
            print(f"      ├─ {product['product_name']:30} | {sc_tag} | {product['frequency_max']:5.1f}GHz | 串擾:{product['crosstalk_typical']:4.0f}dB | 間距:{product['pitch']:5.2f}mm")
    
    print("\n" + "="*80)

# ============================================
# 主函數
# ============================================

def main():
    """主函數"""
    try:
        print("🔄 正在從數據庫讀取數據...")
        
        # 導出數據
        廠商資框, 產品資框, 頻率響應 = export_complete_database()
        #vendors_df, products_df, freq_df
        廠商資框
        產品資框
        頻率響應
        
        # 顯示摘要
        display_database_summary(vendors_df, products_df, freq_df)
        
        # 導出爲各種格式
        print("\n📁 開始導出文件...")
        export_to_json(vendors_df, products_df, freq_df)
        export_to_excel(vendors_df, products_df, freq_df)
        export_to_csv(vendors_df, products_df, freq_df)
        export_to_markdown(products_df)
        
        print("\n🎉 所有導出完成！")
        
    except Exception as e:
        print(f"❌ 導出失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
