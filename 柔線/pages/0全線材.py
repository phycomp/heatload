# 繼續建立完整的 PostgreSQL 資料庫結構

database_schema_part2 = '''
-- Delft Circuits (續)
(2, 'Cri/oFlex 3', 'CF3-8CH', 'stripline',
 30, 0.2, 60, 40, 8,
 'NbTi superconducting', 'Kapton', 'NbTi',
 50, 'DC-18', 0.03,
 3, 2.0, 0.2, 0.01, -50,
 'https://delft-circuits.com/product-overview/'),

-- Amphenol
(3, 'Amphenol CryoFlex', 'APH-CF-047', 'coax',
 NULL, 120, NULL, NULL, 1,
 'NbTi', 'PTFE', 'NbTi',
 50, 'DC-18', 0.2,
 10, 1.5, 1.0, 0.01, -35,
 'https://www.amphenol.com'),

(3, 'Amphenol XMA Cryogenic', 'XMA-CR-085', 'coax',
 NULL, 215, NULL, NULL, 1,
 'BeCu', 'PTFE', 'BeCu',
 50, 'DC-26.5', 0.3,
 15, 1.0, 2.0, 4.0, -30,
 'https://www.digikey.com/en/product-highlight/a/amphenol-xma/cryogenic-rf-components'),

-- Radiall
(4, 'Radiall QRYOLink', 'RAD-QRYO-001', 'flex',
 45, 0.35, 90, 100, 4,
 'NbTi/Ag', 'Kapton', 'NbTi',
 50, 'DC-12', 0.08,
 6, 1.2, 0.6, 0.01, -42,
 'https://www.radiall.com/industries/industrial/quantum-technologies.html'),

(4, 'Radiall Cryogenic Switch Cable', 'RAD-SW-CRYO', 'semi_rigid',
 NULL, 200, NULL, NULL, 1,
 'NbTi', 'PTFE', 'Stainless Steel',
 50, 'DC-18', 0.15,
 20, 0.5, 1.5, 0.01, -38,
 'https://www.radiall.com'),

-- Rosenberger
(5, 'Rosenberger WSMP Multichannel 16CH', 'ROS-WSMP-16', 'multichannel',
 200, 400, 450, 500, 16,
 'Cu non-magnetic', 'Ceramic', 'Cu',
 50, 'DC-65', 0.4,
 8, 0.3, 3.0, 4.0, -25,
 'https://www.rosenberger.com/markets/test-measurement/cryogenic-and-quantum-technology/'),

(5, 'Rosenberger WSMP Multichannel 32CH', 'ROS-WSMP-32', 'multichannel',
 200, 400, 450, 600, 32,
 'Cu non-magnetic', 'Ceramic', 'Cu',
 50, 'DC-65', 0.5,
 10, 0.3, 5.0, 4.0, -22,
 'https://www.rosenberger.com/markets/test-measurement/cryogenic-and-quantum-technology/'),

(5, 'Rosenberger UT-047 NbTi', 'ROS-UT047-NBTI', 'semi_rigid',
 120, 120, NULL, NULL, 1,
 'NbTi', 'PTFE', 'NbTi',
 50, 'DC-26.5', 0.1,
 5, 1.0, 0.8, 0.01, -40,
 'https://www.rosenberger.com'),

(5, 'Rosenberger Flexible Cryo', 'ROS-FLEX-CRYO', 'flex',
 50, 150, 200, 250, 4,
 'BeCu', 'Kapton', 'BeCu',
 50, 'DC-18', 0.12,
 8, 1.5, 1.2, 4.0, -35,
 'https://www.rosenberger.com');

-- ============================================================
-- 4. 串擾計算結果資料表
-- ============================================================
CREATE TABLE crosstalk_simulations (
    id SERIAL PRIMARY KEY,
    cable_id INTEGER REFERENCES cable_products(id),
    frequency_ghz FLOAT,
    temperature_k FLOAT,
    length_m FLOAT,
    line_spacing_um FLOAT,
    
    -- 計算結果
    k_capacitive FLOAT, -- 電容耦合係數
    k_inductive FLOAT, -- 電感耦合係數
    k_total FLOAT, -- 總耦合係數
    next_db FLOAT, -- 近端串擾 (dB)
    fet_db FLOAT, -- 遠端串擾 (dB)
    
    -- 傳輸線參數
    capacitance_pf_m FLOAT, -- 電容 (pF/m)
    inductance_nh_m FLOAT, -- 電感 (nH/m)
    impedance_ohm FLOAT, -- 阻抗 (Ω)
    phase_velocity_c FLOAT, -- 相速度 (c)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. 視圖: 產品完整資訊
-- ============================================================
CREATE VIEW cable_products_complete AS
SELECT 
    cp.*,
    m.name as manufacturer_name,
    m.country as manufacturer_country,
    m.website as manufacturer_website
FROM cable_products cp
JOIN manufacturers m ON cp.manufacturer_id = m.id;

-- ============================================================
-- 6. 視圖: 串擾比較
-- ============================================================
CREATE VIEW crosstalk_comparison AS
SELECT 
    cs.*,
    cp.product_name,
    cp.product_code,
    m.name as manufacturer_name,
    cp.num_channels,
    cp.cable_type
FROM crosstalk_simulations cs
JOIN cable_products cp ON cs.cable_id = cp.id
JOIN manufacturers m ON cp.manufacturer_id = m.id;

-- ============================================================
-- 7. 索引
-- ============================================================
CREATE INDEX idx_cable_manufacturer ON cable_products(manufacturer_id);
CREATE INDEX idx_cable_type ON cable_products(cable_type);
CREATE INDEX idx_crosstalk_cable ON crosstalk_simulations(cable_id);
CREATE INDEX idx_crosstalk_freq ON crosstalk_simulations(frequency_ghz);
CREATE INDEX idx_crosstalk_temp ON crosstalk_simulations(temperature_k);

'''

# 儲存資料庫結構
with open('/mnt/kimi/output/quantum_cables_database.sql', 'w', encoding='utf-8') as f:
    f.write(database_schema_part2)

print("✅ PostgreSQL 資料庫結構已生成!")
print("📁 檔案位置: /mnt/kimi/output/quantum_cables_database.sql")
print("\n資料庫包含以下表格:")
print("  1. manufacturers - 廠商資料 (5家)")
print("  2. materials - 材料參數 (12種)")
print("  3. cable_products - 電纜產品 (11款)")
print("  4. crosstalk_simulations - 串擾計算結果")
print("  5. 視圖: cable_products_complete, crosstalk_comparison")
