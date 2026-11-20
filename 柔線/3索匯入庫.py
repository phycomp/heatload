# init_quantum_db.py
import psycopg
from psycopg import sql
import json

# 数据库连接配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "uleam",
    "user": "postgres",
    "password": "postgres"
}

# 完整的传输线物理参数数据集
TRANSMISSION_LINES_DATA = {
    "vendors": [
        {"name": "Delft Circuits", "technology": "Superconducting Flexible", "country": "Netherlands"},
        {"name": "Rigetti Computing", "technology": "Superconducting Coaxial", "country": "USA"},
        {"name": "Amphenol RF", "technology": "Coaxial Flexible", "country": "USA"},
        {"name": "Radiall", "technology": "Coaxial High-Density", "country": "France"},
        {"name": "Rosenberger", "technology": "Coaxial High-Frequency", "country": "Germany"},
        {"name": "Fraunhofer EMFT", "technology": "Superconducting Flexible Roll-to-Roll", "country": "Germany" }
    ],
    
    "products": [
        # Delft Circuits - Cri/oFlex Series
        {
            "vendor_name": "Delft Circuits",
            "product_name": "Cri/oFlex-8",
            "product_series": "Cri/oFlex",
            "impedance": 50.0,
            "frequency_max": 12.0,
            "insertion_loss": 1.5,
            "return_loss": 15.0,
            "crosstalk_typical": -25.0,
            "pitch": 1.0,
            "width": 8.0,
            "height": 0.3,
            "material_conductor": "NbTi",
            "material_dielectric": "Polyimide",
            "is_superconducting": True,
            "operating_temp_min": 0.01,
            "operating_temp_max": 4.0,
            "power_handling": 0.001,
            "bend_radius_min": 5.0,
            "shielding_effectiveness": 60.0,
            "application": "Flux Bias, Microwave Drive",
            "notes": "8-channel superconducting flexible cable"
        },
        {
            "vendor_name": "Delft Circuits",
            "product_name": "Cri/oFlex-16",
            "product_series": "Cri/oFlex",
            "impedance": 50.0,
            "frequency_max": 8.0,
            "insertion_loss": 1.8,
            "return_loss": 14.0,
            "crosstalk_typical": -22.0,
            "pitch": 0.8,
            "width": 16.0,
            "height": 0.4,
            "material_conductor": "NbTi",
            "material_dielectric": "Polyimide",
            "is_superconducting": True,
            "operating_temp_min": 0.01,
            "operating_temp_max": 4.0,
            "power_handling": 0.0005,
            "bend_radius_min": 6.0,
            "shielding_effectiveness": 55.0,
            "application": "High-density qubit control",
            "notes": "16-channel high-density version"
        },
        
        # Rigetti Computing - Custom Coaxial
        {
            "vendor_name": "Rigetti Computing",
            "product_name": "Rigetti-Quantum-Coax",
            "product_series": "Quantum Coaxial",
            "impedance": 50.0,
            "frequency_max": 12.0,
            "insertion_loss": 2.2,
            "return_loss": 18.0,
            "crosstalk_typical": -35.0,
            "pitch": 2.54,
            "width": 0.0,
            "height": 2.2,
            "material_conductor": "Beryllium Copper",
            "material_dielectric": "PTFE",
            "is_superconducting": False,
            "operating_temp_min": 0.01,
            "operating_temp_max": 100.0,
            "power_handling": 0.5,
            "bend_radius_min": 15.0,
            "shielding_effectiveness": 90.0,
            "application": "Multi-qubit control",
            "notes": "Custom coax for Rigetti Aspen series"
        },
        
        # Amphenol RF - Micro Coaxial
        {
            "vendor_name": "Amphenol RF",
            "product_name": "TF-047-Semi-Rigid",
            "product_series": "TF-047",
            "impedance": 50.0,
            "frequency_max": 50.0,
            "insertion_loss": 4.5,
            "return_loss": 20.0,
            "crosstalk_typical": -40.0,
            "pitch": 1.397,
            "width": 0.0,
            "height": 1.397,
            "material_conductor": "Silver-plated Copper",
            "material_dielectric": "PTFE",
            "is_superconducting": False,
            "operating_temp_min": -55.0,
            "operating_temp_max": 125.0,
            "power_handling": 2.0,
            "bend_radius_min": 4.0,
            "shielding_effectiveness": 85.0,
            "application": "High-frequency signal",
            "notes": "Ultra-miniature semi-rigid coax"
        },
        {
            "vendor_name": "Amphenol RF",
            "product_name": "Micro-Coax-086",
            "product_series": "Micro-Coax",
            "impedance": 50.0,
            "frequency_max": 26.5,
            "insertion_loss": 3.2,
            "return_loss": 19.0,
            "crosstalk_typical": -38.0,
            "pitch": 2.18,
            "width": 0.0,
            "height": 2.18,
            "material_conductor": "Copper",
            "material_dielectric": "PTFE",
            "is_superconducting": False,
            "operating_temp_min": -55.0,
            "operating_temp_max": 150.0,
            "power_handling": 3.5,
            "bend_radius_min": 6.5,
            "shielding_effectiveness": 80.0,
            "application": "General RF",
            "notes": "Standard micro coax cable"
        },
        
        # Radiall - High Density
        {
            "vendor_name": "Radiall",
            "product_name": "F2C-40-SMA",
            "product_series": "F2C-40",
            "impedance": 50.0,
            "frequency_max": 12.4,
            "insertion_loss": 2.8,
            "return_loss": 22.0,
            "crosstalk_typical": -45.0,
            "pitch": 4.0,
            "width": 0.0,
            "height": 3.5,
            "material_conductor": "Beryllium Copper",
            "material_dielectric": "PTFE",
            "is_superconducting": False,
            "operating_temp_min": -65.0,
            "operating_temp_max": 165.0,
            "power_handling": 5.0,
            "bend_radius_min": 12.0,
            "shielding_effectiveness": 95.0,
            "application": "Test & Measurement",
            "notes": "High-density SMA connector system"
        },
        {
            "vendor_name": "Radiall",
            "product_name": "R125075000-SMA",
            "product_series": "SMA",
            "impedance": 50.0,
            "frequency_max": 12.4,
            "insertion_loss": 1.8,
            "return_loss": 23.0,
            "crosstalk_typical": -50.0,
            "pitch": 5.0,
            "width": 0.0,
            "height": 4.2,
            "material_conductor": "Stainless Steel",
            "material_dielectric": "PTFE",
            "is_superconducting": False,
            "operating_temp_min": -65.0,
            "operating_temp_max": 165.0,
            "power_handling": 8.0,
            "bend_radius_min": 15.0,
            "shielding_effectiveness": 100.0,
            "application": "Standard SMA connector",
            "notes": "Military grade SMA connector"
        },
        
        # Rosenberger - High Frequency
        {
            "vendor_name": "Rosenberger",
            "product_name": "WSMP-32-Multicoax",
            "product_series": "WSMP",
            "impedance": 50.0,
            "frequency_max": 65.0,
            "insertion_loss": 3.5,
            "return_loss": 18.0,
            "crosstalk_typical": -30.0,
            "pitch": 2.45,
            "width": 6.0,
            "height": 50.0,
            "material_conductor": "Non-magnetic Cu Alloy",
            "material_dielectric": "PTFE",
            "is_superconducting": False,
            "operating_temp_min": -55.0,
            "operating_temp_max": 125.0,
            "power_handling": 1.5,
            "bend_radius_min": 8.0,
            "shielding_effectiveness": 75.0,
            "application": "Multi-channel high-frequency",
            "notes": "32 channels in compact array"
        },
        {
            "vendor_name": "Rosenberger",
            "product_name": "RPC-1.35",
            "product_series": "RPC",
            "impedance": 50.0,
            "frequency_max": 110.0,
            "insertion_loss": 4.2,
            "return_loss": 17.0,
            "crosstalk_typical": -28.0,
            "pitch": 1.35,
            "width": 0.0,
            "height": 1.35,
            "material_conductor": "Gold-plated BeCu",
            "material_dielectric": "Air",
            "is_superconducting": False,
            "operating_temp_min": -55.0,
            "operating_temp_max": 85.0,
            "power_handling": 0.8,
            "bend_radius_min": 5.0,
            "shielding_effectiveness": 70.0,
            "application": "Millimeter-wave testing",
            "notes": "1.35mm connector for up to 110GHz"
        },
        {
            "vendor_name": "Fraunhofer EMFT",
            "product_name": "HD-SC-Interconnect-80",
            "product_series": "High Density Superconducting",
            "impedance": 50.0,  # 典型RF系统标准
            "frequency_max": 20.0,  # 预估，适用于量子比特控制
            "insertion_loss": 1.2,  # dB/m @ 6GHz (基于超导材料预估)
            "return_loss": 16.0,
            "crosstalk_typical": -35.0,  # 独立屏蔽提供优良隔离
            "pitch": 0.31,  # 每英寸80线 = 约0.31mm间距
            "width": 25.4,  # 1英寸宽度包含80通道
            "height": 0.095,  # <100μm = 0.095mm
            "material_conductor": "Superconducting Alloy (Proprietary)",
            "material_dielectric": "Polyimide",
            "material_shield": "Individual Per-channel Shielding",
            "is_superconducting": True,
            "operating_temp_min": 0.01,
            "operating_temp_max": 4.0,  # 超导转变温度以下
            "power_handling": 0.0005,
            "bend_radius_min": 3.0,  # 超薄设计，弯曲半径小
            "shielding_effectiveness": 70.0,
            "application": "High-density qubit control, Readout",
            "notes": ">80 individually shielded lines per inch, R2R manufacturing, integrated filter options"
        },
        {
          "vendor_name": "Fraunhofer EMFT",
          "product_name": "HD-SC-Interconnect-Custom",
          "product_series": "High Density Superconducting",
          "impedance": 50.0,
          "frequency_max": 15.0,
          "insertion_loss": 1.0,
          "return_loss": 18.0,
          "crosstalk_typical": -40.0,
          "pitch": 0.25,
          "width": 25.4,
          "height": 0.09,
          "material_conductor": "Superconducting Alloy",
          "material_dielectric": "Polyimide",
          "is_superconducting": True,
          "operating_temp_min": 0.01,
          "operating_temp_max": 4.0,
          "power_handling": 0.0003,
          "bend_radius_min": 2.5,
          "shielding_effectiveness": 75.0,
          "application": "Custom high-density quantum wiring",
          "notes": "Scalable design with integrated lowpass/bandpass filter options"
      }
    ],
    
    "frequency_characteristics": [
        # Delft Circuits frequency response
        {"product_name": "Cri/oFlex-8", "frequency_ghz": 1.0, "s21_db": -1.5, "s31_db": -25.0},
        {"product_name": "Cri/oFlex-8", "frequency_ghz": 4.0, "s21_db": -3.0, "s31_db": -23.0},
        {"product_name": "Cri/oFlex-8", "frequency_ghz": 8.0, "s21_db": -6.0, "s31_db": -20.0},
        {"product_name": "Cri/oFlex-8", "frequency_ghz": 12.0, "s21_db": -9.0, "s31_db": -18.0},
        
        # Amphenol frequency response
        {"product_name": "TF-047-Semi-Rigid", "frequency_ghz": 1.0, "s21_db": -0.5, "s31_db": -45.0},
        {"product_name": "TF-047-Semi-Rigid", "frequency_ghz": 10.0, "s21_db": -1.8, "s31_db": -42.0},
        {"product_name": "TF-047-Semi-Rigid", "frequency_ghz": 30.0, "s21_db": -3.2, "s31_db": -38.0},
        {"product_name": "TF-047-Semi-Rigid", "frequency_ghz": 50.0, "s21_db": -5.5, "s31_db": -35.0},
        
        # Radiall frequency response
        {"product_name": "F2C-40-SMA", "frequency_ghz": 1.0, "s21_db": -0.3, "s31_db": -50.0},
        {"product_name": "F2C-40-SMA", "frequency_ghz": 6.0, "s21_db": -1.2, "s31_db": -47.0},
        {"product_name": "F2C-40-SMA", "frequency_ghz": 12.4, "s21_db": -2.8, "s31_db": -43.0},
        
        # Rosenberger frequency response
        {"product_name": "WSMP-32-Multicoax", "frequency_ghz": 1.0, "s21_db": -0.6, "s31_db": -35.0},
        {"product_name": "WSMP-32-Multicoax", "frequency_ghz": 20.0, "s21_db": -2.1, "s31_db": -32.0},
        {"product_name": "WSMP-32-Multicoax", "frequency_ghz": 40.0, "s21_db": -3.5, "s31_db": -30.0},
        {"product_name": "WSMP-32-Multicoax", "frequency_ghz": 65.0, "s21_db": -5.2, "s31_db": -28.0}
    ]
}

def create_tables(conn):
    """创建所有必要的表"""
    with conn.cursor() as cur:
        # 供应商表
        cur.execute("""
            DROP TABLE IF EXISTS frequency_characteristics CASCADE;
            DROP TABLE IF EXISTS transmission_lines CASCADE;
            DROP TABLE IF EXISTS vendors CASCADE;
            DROP TABLE IF EXISTS simulation_logs CASCADE;
        """)
        
        cur.execute("""
            CREATE TABLE vendors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                technology VARCHAR(50),
                country VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 传输线主表
        cur.execute("""
            CREATE TABLE transmission_lines (
                id SERIAL PRIMARY KEY,
                vendor_id INTEGER REFERENCES vendors(id),
                product_name VARCHAR(100) UNIQUE NOT NULL,
                product_series VARCHAR(100),
                
                -- 电气参数
                impedance REAL,
                frequency_max REAL,
                insertion_loss REAL,
                return_loss REAL,
                crosstalk_typical REAL,
                vswr REAL,
                capacitance REAL,
                
                -- 机械参数
                pitch REAL,
                width REAL,
                height REAL,
                weight_per_meter REAL,
                bend_radius_min REAL,
                
                -- 材料参数
                material_conductor VARCHAR(100),
                material_dielectric VARCHAR(100),
                material_shield VARCHAR(100),
                
                -- 环境参数
                is_superconducting BOOLEAN,
                operating_temp_min REAL,
                operating_temp_max REAL,
                power_handling REAL,
                shielding_effectiveness REAL,
                
                -- 应用参数
                application TEXT,
                notes TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 频率特性表 (S参数)
        cur.execute("""
            CREATE TABLE frequency_characteristics (
                id SERIAL PRIMARY KEY,
                transmission_line_id INTEGER REFERENCES transmission_lines(id),
                frequency_ghz REAL,
                s11_db REAL,
                s21_db REAL,
                s31_db REAL,
                s41_db REAL,
                phase_deg REAL,
                group_delay_ps REAL,
                measurement_temp REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 模拟日志表
        cur.execute("""
            CREATE TABLE simulation_logs (
                id SERIAL PRIMARY KEY,
                transmission_line_id INTEGER REFERENCES transmission_lines(id),
                frequency_start_ghz REAL,
                frequency_end_ghz REAL,
                length_m REAL,
                temperature_k REAL,
                calculated_crosstalk_db REAL,
                calculated_loss_db REAL,
                simulation_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引以提高查询性能
        cur.execute("CREATE INDEX idx_tl_vendor ON transmission_lines(vendor_id)")
        cur.execute("CREATE INDEX idx_freq_tl ON frequency_characteristics(transmission_line_id)")
        cur.execute("CREATE INDEX idx_freq_value ON frequency_characteristics(frequency_ghz)")
        
        conn.commit()
        print("✅ 数据库表创建成功")

def import_data(conn):
    """导入所有传输线参数数据"""
    
    # 首先导入供应商
    vendor_map = {}
    with conn.cursor() as cur:
        for vendor in TRANSMISSION_LINES_DATA["vendors"]:
            cur.execute("""
                INSERT INTO vendors (name, technology, country)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE 
                SET technology = EXCLUDED.technology,
                    country = EXCLUDED.country
                RETURNING id
            """, (vendor["name"], vendor["technology"], vendor["country"]))
            vendor_id = cur.fetchone()[0]
            vendor_map[vendor["name"]] = vendor_id
        conn.commit()
    print(f"✅ 导入 {len(vendor_map)} 个供应商")
    
    # 导入传输线产品
    product_map = {}
    with conn.cursor() as cur:
        for product in TRANSMISSION_LINES_DATA["products"]:
            vendor_id = vendor_map[product["vendor_name"]]
            cur.execute("""
                INSERT INTO transmission_lines (
                    vendor_id, product_name, product_series,
                    impedance, frequency_max, insertion_loss, return_loss,
                    crosstalk_typical, pitch, width, height,
                    material_conductor, material_dielectric,
                    is_superconducting, operating_temp_min, operating_temp_max,
                    power_handling, bend_radius_min, shielding_effectiveness,
                    application, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_name) DO UPDATE SET
                    impedance = EXCLUDED.impedance,
                    insertion_loss = EXCLUDED.insertion_loss,
                    crosstalk_typical = EXCLUDED.crosstalk_typical
                RETURNING id
            """, (
                vendor_id, product["product_name"], product.get("product_series"),
                product["impedance"], product["frequency_max"], product["insertion_loss"],
                product["return_loss"], product["crosstalk_typical"], product["pitch"],
                product["width"], product["height"], product["material_conductor"],
                product["material_dielectric"], product["is_superconducting"],
                product["operating_temp_min"], product["operating_temp_max"],
                product["power_handling"], product["bend_radius_min"],
                product["shielding_effectiveness"], product["application"], product["notes"]
            ))
            product_id = cur.fetchone()[0]
            product_map[product["product_name"]] = product_id
        conn.commit()
    print(f"✅ 导入 {len(product_map)} 个产品")
    
    # 导入频率特性数据
    count = 0
    with conn.cursor() as cur:
        for freq_data in TRANSMISSION_LINES_DATA["frequency_characteristics"]:
            if freq_data["product_name"] in product_map:
                tl_id = product_map[freq_data["product_name"]]
                cur.execute("""
                    INSERT INTO frequency_characteristics (
                        transmission_line_id, frequency_ghz, s21_db, s31_db
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    tl_id, freq_data["frequency_ghz"],
                    freq_data["s21_db"], freq_data["s31_db"]
                ))
                count += 1
        conn.commit()
    print(f"✅ 导入 {count} 条频率特性数据")

def verify_data(conn):
    """验证数据导入是否成功"""
    with conn.cursor() as cur:
        # 统计各表数据量
        cur.execute("SELECT COUNT(*) FROM vendors")
        vendor_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM transmission_lines")
        product_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM frequency_characteristics")
        freq_count = cur.fetchone()[0]
        
        print("\n📊 数据库统计:")
        print(f"  供应商数量: {vendor_count}")
        print(f"  产品数量: {product_count}")
        print(f"  频率特性数据点: {freq_count}")
        
        # 显示产品列表
        cur.execute("""
            SELECT v.name, t.product_name, t.frequency_max, t.is_superconducting
            FROM transmission_lines t
            JOIN vendors v ON t.vendor_id = v.id
            ORDER BY v.name, t.product_name
        """)
        
        print("\n📋 已导入产品清单:")
        for row in cur.fetchall():
            sc_status = "🔬超导" if row[3] else "🔌常温"
            print(f"  {row[0]:20} | {row[1]:25} | {row[2]:5.1f} GHz | {sc_status}")

def main():
    """主函数"""
    try:
        # 连接数据库
        conn = psycopg.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        
        # 创建表
        create_tables(conn)
        
        # 导入数据
        import_data(conn)
        
        # 验证数据
        verify_data(conn)
        
        print("\n🎉 所有传输线物理参数导入完成!")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
