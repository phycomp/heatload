-- # 建立 PostgreSQL 資料庫架構 SQL
-- sql_schema = """
-- 柔性傳輸線材物理參數資料庫架構
-- 適用於量子計算、微波、射頻應用的串擾計算模擬

-- 啟用 UUID 擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 製造商資料表
CREATE TABLE manufacturers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(50),
    website VARCHAR(255),
    specialties TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 線材類別資料表
CREATE TABLE cable_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    typical_applications TEXT[],
    temperature_range_min DECIMAL(6,2), -- Kelvin
    temperature_range_max DECIMAL(6,2),   -- Kelvin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 主要線材資料表
CREATE TABLE cables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID REFERENCES manufacturers(id),
    category_id UUID REFERENCES cable_categories(id),
    model_name VARCHAR(100) NOT NULL,
    part_number VARCHAR(100),
    description TEXT,
    
    -- 幾何參數
    outer_diameter_mm DECIMAL(6,3),
    inner_conductor_diameter_mm DECIMAL(6,3),
    dielectric_diameter_mm DECIMAL(6,3),
    thickness_mm DECIMAL(6,3),
    
    -- 材料參數
    conductor_material VARCHAR(50),
    dielectric_material VARCHAR(50),
    shield_material VARCHAR(50),
    jacket_material VARCHAR(50),
    
    -- 電氣參數
    impedance_ohm DECIMAL(5,1) DEFAULT 50.0,
    capacitance_pf_m DECIMAL(6,2),
    inductance_nh_m DECIMAL(6,2),
    velocity_factor_percent DECIMAL(5,2),
    
    -- 頻率響應
    frequency_range_min_hz DECIMAL(15,0),
    frequency_range_max_hz DECIMAL(15,0),
    
    -- 損耗參數 (頻率相關，存為 JSON)
    attenuation_db_m JSONB, -- {frequency_hz: attenuation_db}
    
    -- 熱參數
    thermal_conductivity_w_m_k DECIMAL(8,4),
    heat_load_per_channel_uw JSONB, -- {temperature_k: heat_load_uw}
    
    -- 機械參數
    min_bending_radius_mm DECIMAL(6,2),
    max_flex_cycles INTEGER,
    weight_g_m DECIMAL(6,2),
    
    -- 屏蔽效能
    shielding_effectiveness_db DECIMAL(5,1),
    
    -- 串擾參數
    near_end_crosstalk_db DECIMAL(5,1),
    far_end_crosstalk_db DECIMAL(5,1),
    
    -- 認證與標準
    certifications TEXT[],
    compliance_standards TEXT[],
    
    -- 應用場景
    typical_applications TEXT[],
    max_channels_per_flex INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(manufacturer_id, model_name)
);

-- 頻率響應詳細資料表 (用於精確的 S 參數)
CREATE TABLE cable_frequency_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cable_id UUID REFERENCES cables(id) ON DELETE CASCADE,
    frequency_hz DECIMAL(15,0) NOT NULL,
    s11_db DECIMAL(6,2), -- 反射係數
    s21_db DECIMAL(6,2), -- 傳輸係數
    s41_db DECIMAL(6,2), -- 遠端串擾
    phase_delay_deg DECIMAL(8,3),
    temperature_k DECIMAL(6,2),
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(cable_id, frequency_hz, temperature_k)
);

-- 串擾計算專案資料表
CREATE TABLE crosstalk_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    cable_configuration JSONB, -- 線材佈局設定
    frequency_range_start_hz DECIMAL(15,0),
    frequency_range_end_hz DECIMAL(15,0),
    temperature_k DECIMAL(6,2),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 串擾計算結果資料表
CREATE TABLE crosstalk_simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES crosstalk_projects(id) ON DELETE CASCADE,
    frequency_hz DECIMAL(15,0) NOT NULL,
    
    -- 計算結果
    coupling_coefficient DECIMAL(10,6),
    near_end_crosstalk_db DECIMAL(8,3),
    far_end_crosstalk_db DECIMAL(8,3),
    power_sum_crosstalk_db DECIMAL(8,3),
    alien_crosstalk_db DECIMAL(8,3),
    
    -- 參數詳情
    calculation_params JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 線材組合/捆束資料表
CREATE TABLE cable_bundles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES crosstalk_projects(id) ON DELETE CASCADE,
    name VARCHAR(100),
    cable_id UUID REFERENCES cables(id),
    quantity INTEGER DEFAULT 1,
    spacing_mm DECIMAL(6,3), -- 線間距
    twist_pitch_mm DECIMAL(6,2), -- 扭絞節距
    shield_type VARCHAR(50), -- 屏蔽類型
    position_x DECIMAL(8,3), -- 佈局座標
    position_y DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_cables_manufacturer ON cables(manufacturer_id);
CREATE INDEX idx_cables_category ON cables(category_id);
CREATE INDEX idx_cables_frequency ON cables(frequency_range_max_hz);
CREATE INDEX idx_freq_response_cable ON cable_frequency_responses(cable_id);
CREATE INDEX idx_freq_response_freq ON cable_frequency_responses(frequency_hz);
CREATE INDEX idx_crosstalk_project ON crosstalk_simulations(project_id);
CREATE INDEX idx_crosstalk_freq ON crosstalk_simulations(frequency_hz);

-- 觸發器：自動更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_cables_updated_at BEFORE UPDATE ON cables
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON crosstalk_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入製造商資料
INSERT INTO manufacturers (name, country, website, specialties) VALUES
('Rigetti Computing', 'USA', 'https://www.rigetti.com', 
 ARRAY['Quantum Computing', 'Superconducting Qubits', 'Cryogenic Systems']),
('Delft Circuits', 'Netherlands', 'https://delft-circuits.com', 
 ARRAY['Cryogenic Cabling', 'Cri/oFlex', 'Quantum I/O', 'Superconducting Flex']),
('Amphenol RF', 'USA', 'https://www.amphenolrf.com', 
 ARRAY['RF Connectors', 'Coaxial Cables', 'Microwave Components']),
('Radiall', 'France', 'https://www.radiall.com', 
 ARRAY['RF Interconnects', 'Aerospace', 'Defense', 'Non-Magnetic Connectors']),
('Rosenberger', 'Germany', 'https://www.rosenberger.com', 
 ARRAY['High Frequency', 'Automotive', 'Test & Measurement', 'Quantum Technologies']);

-- 插入線材類別
INSERT INTO cable_categories (name, description, typical_applications, temperature_range_min, temperature_range_max) VALUES
('Cryogenic Flexible Microwave', '專為量子計算設計的柔性微波線材，可在毫開爾文溫度下運作', 
 ARRAY['Quantum Computing', 'Superconducting Qubits', 'Dilution Refrigerators'], 0.01, 300),
('Semi-Rigid Coaxial', '半剛性同軸電纜，適合高頻應用', 
 ARRAY['Microwave Test', 'Quantum Control Lines', 'Cryogenic RF'], 0.01, 400),
('Ultra-Flexible RF', '超柔性射頻電纜，適合動態應用', 
 ARRAY['Aerospace', 'Satcom', 'Test Equipment'], 200, 400),
('High-Density Flex', '高密度柔性線材，多通道設計', 
 ARRAY['Quantum I/O', 'High-Density Interconnects', 'Cryogenic Systems'], 0.01, 300),
('Low-Loss Microwave', '低損耗微波傳輸線', 
 ARRAY['5G', 'Radar', 'Test & Measurement'], 200, 400);

-- 插入線材資料
INSERT INTO cables (
    manufacturer_id, category_id, model_name, part_number, description,
    outer_diameter_mm, inner_conductor_diameter_mm, dielectric_diameter_mm, thickness_mm,
    conductor_material, dielectric_material, shield_material, jacket_material,
    impedance_ohm, capacitance_pf_m, inductance_nh_m, velocity_factor_percent,
    frequency_range_min_hz, frequency_range_max_hz,
    attenuation_db_m, thermal_conductivity_w_m_k, heat_load_per_channel_uw,
    min_bending_radius_mm, max_flex_cycles, weight_g_m,
    shielding_effectiveness_db, near_end_crosstalk_db, far_end_crosstalk_db,
    certifications, compliance_standards, typical_applications, max_channels_per_flex
) 
SELECT 
    m.id, c.id, 'Cri/oFlex 3 NbTi', 'CF3-NBTI-8CH', 
    'Superconducting flexible 8-channel stripline for quantum computing',
    0.3, 0.05, 0.2, 0.3,
    'Niobium-Titanium (NbTi)', 'Polyimide (Kapton)', 'NbTi Ground Plane', 'Polyimide',
    50.0, 29.4, 70.0, 70.0,
    0, 18000000000,
    '{"1000000000": 0.5, "6000000000": 1.5, "10000000000": 2.5}'::jsonb,
    0.001, '{"3": 4.0, "0.7": 0.7}'::jsonb,
    5.0, 10000, 15.0,
    -100, -60, -70,
    ARRAY['RoHS', 'Cryogenic Qualified'], ARRAY['Quantum Computing Standard'],
    ARRAY['Flux Bias', 'Microwave Drive', 'Read-out'], 8
FROM manufacturers m, cable_categories c
WHERE m.name = 'Delft Circuits' AND c.name = 'Cryogenic Flexible Microwave';

INSERT INTO cables (
    manufacturer_id, category_id, model_name, part_number, description,
    outer_diameter_mm, inner_conductor_diameter_mm, dielectric_diameter_mm, thickness_mm,
    conductor_material, dielectric_material, shield_material, jacket_material,
    impedance_ohm, capacitance_pf_m, inductance_nh_m, velocity_factor_percent,
    frequency_range_min_hz, frequency_range_max_hz,
    attenuation_db_m, thermal_conductivity_w_m_k, heat_load_per_channel_uw,
    min_bending_radius_mm, max_flex_cycles, weight_g_m,
    shielding_effectiveness_db, near_end_crosstalk_db, far_end_crosstalk_db,
    certifications, compliance_standards, typical_applications, max_channels_per_flex
) 
SELECT 
    m.id, c.id, 'Cri/oFlex 3 Silver', 'CF3-AG-8CH', 
    'Silver-based flexible 8-channel stripline',
    0.3, 0.05, 0.2, 0.3,
    'Silver (Ag)', 'Polyimide (Kapton)', 'Ag Ground Plane', 'Polyimide',
    50.0, 29.4, 70.0, 70.0,
    0, 18000000000,
    '{"1000000000": 1.0, "6000000000": 3.0, "10000000000": 5.0}'::jsonb,
    0.5, '{"3": 40.0, "0.7": 7.0}'::jsonb,
    5.0, 10000, 15.0,
    -100, -55, -65,
    ARRAY['RoHS'], ARRAY['Quantum Computing Standard'],
    ARRAY['Signal Lines', 'General I/O'], 8
FROM manufacturers m, cable_categories c
WHERE m.name = 'Delft Circuits' AND c.name = 'Cryogenic Flexible Microwave';

INSERT INTO cables (
    manufacturer_id, category_id, model_name, part_number, description,
    outer_diameter_mm, inner_conductor_diameter_mm, dielectric_diameter_mm, thickness_mm,
    conductor_material, dielectric_material, shield_material, jacket_material,
    impedance_ohm, capacitance_pf_m, inductance_nh_m, velocity_factor_percent,
    frequency_range_min_hz, frequency_range_max_hz,
    attenuation_db_m, thermal_conductivity_w_m_k, heat_load_per_channel_uw,
    min_bending_radius_mm, max_flex_cycles, weight_g_m,
    shielding_effectiveness_db, near_end_crosstalk_db, far_end_crosstalk_db,
    certifications, compliance_standards, typical_applications, max_channels_per_flex
) 
SELECT 
    m.id, c.id, 'SC-086/50-SCN-CN', 'SC08650SCNCN', 
    'Semi-rigid coaxial cable for quantum control lines',
    2.2, 0.51, 1.68, 2.2,
    'Silver-plated Copper', 'PTFE (Teflon)', 'Silver-plated Copper Braid', 'FEP',
    50.0, 95.0, 250.0, 70.0,
    0, 18000000000,
    '{"1000000000": 0.4, "6000000000": 1.2, "10000000000": 2.0}'::jsonb,
    0.5, '{"300": 500.0, "4": 50.0, "0.01": 0.1}'::jsonb,
    10.0, 100, 35.0,
    -90, -50, -60,
    ARRAY['MIL-PRF-17', 'Cryogenic Qualified'], ARRAY['MIL-C-17'],
    ARRAY['Quantum Control', 'Readout Lines'], 1
FROM manufacturers m, cable_categories c
WHERE m.name = 'Rigetti Computing' AND c.name = 'Semi-Rigid Coaxial';

INSERT INTO cables (
    manufacturer_id, category_id, model_name, part_number, description,
    outer_diameter_mm, inner_conductor_diameter_mm, dielectric_diameter_mm, thickness_mm,
    conductor_material, dielectric_material, shield_material, jacket_material,
    impedance_ohm, capacitance_pf_m, inductance_nh_m, velocity_factor_percent,
    frequency_range_min_hz, frequency_range_max_hz,
    attenuation_db_m, thermal_conductivity_w_m_k, heat_load_per_channel_uw,
    min_bending_radius_mm, max_flex_cycles, weight_g_m,
    shielding_effectiveness_db, near_end_crosstalk_db, far_end_crosstalk_db,
    certifications, compliance_standards, typical_applications, max_channels_per_flex
) 
SELECT 
    m.id, c.id, 'RTK Flex 047', 'RTK-FLEX-047', 
    'High-performance flexible cable up to 70 GHz',
    1.2, 0.29, 0.9, 1.2,
    'Silver-plated Copper', 'PTFE', 'Silver-plated Copper Braid', 'FEP',
    50.0, 82.0, 200.0, 70.0,
    0, 70000000000,
    '{"1000000000": 0.6, "10000000000": 2.0, "40000000000": 4.5}'::jsonb,
    0.3, '{"300": 200.0}'::jsonb,
    5.0, 5000, 20.0,
    -100, -45, -55,
    ARRAY['RoHS', 'High Frequency'], ARRAY['IEC 61169'],
    ARRAY['Test & Measurement', 'Quantum Technologies'], 1
FROM manufacturers m, cable_categories c
WHERE m.name = 'Rosenberger' AND c.name = 'Low-Loss Microwave';

INSERT INTO cables (
    manufacturer_id, category_id, model_name, part_number, description,
    outer_diameter_mm, inner_conductor_diameter_mm, dielectric_diameter_mm, thickness_mm,
    conductor_material, dielectric_material, shield_material, jacket_material,
    impedance_ohm, capacitance_pf_m, inductance_nh_m, velocity_factor_percent,
    frequency_range_min_hz, frequency_range_max_hz,
    attenuation_db_m, thermal_conductivity_w_m_k, heat_load_per_channel_uw,
    min_bending_radius_mm, max_flex_cycles, weight_g_m,
    shielding_effectiveness_db, near_end_crosstalk_db, far_end_crosstalk_db,
    certifications, compliance_standards, typical_applications, max_channels_per_flex
) 
SELECT 
    m.id, c.id, 'SHF3 UF', 'SHF3-UF-KA', 
    'Ultra-flexible Ka-band cable for aerospace',
    3.6, 0.99, 2.66, 3.6,
    'Silver-plated Copper', 'PTFE', 'Silver-plated Copper Double Braid', 'Black FEP',
    50.0, 86.0, 230.0, 66.0,
    0, 32000000000,
    '{"17500000000": 1.5, "22000000000": 2.0, "27000000000": 2.5}'::jsonb,
    0.4, '{"300": 300.0}'::jsonb,
    20.0, 100000, 35.0,
    -110, -50, -60,
    ARRAY['ARINC 791', 'ARINC 792', 'Aerospace'], ARRAY['MIL-DTL-17'],
    ARRAY['Satcom', 'Aerospace', 'Ka-band Systems'], 1
FROM manufacturers m, cable_categories c
WHERE m.name = 'Radiall' AND c.name = 'Ultra-Flexible RF';

INSERT INTO cables (
    manufacturer_id, category_id, model_name, part_number, description,
    outer_diameter_mm, inner_conductor_diameter_mm, dielectric_diameter_mm, thickness_mm,
    conductor_material, dielectric_material, shield_material, jacket_material,
    impedance_ohm, capacitance_pf_m, inductance_nh_m, velocity_factor_percent,
    frequency_range_min_hz, frequency_range_max_hz,
    attenuation_db_m, thermal_conductivity_w_m_k, heat_load_per_channel_uw,
    min_bending_radius_mm, max_flex_cycles, weight_g_m,
    shielding_effectiveness_db, near_end_crosstalk_db, far_end_crosstalk_db,
    certifications, compliance_standards, typical_applications, max_channels_per_flex
) 
SELECT 
    m.id, c.id, 'LMR-UF UltraFlex', 'LMR-UF-400', 
    'Ultra-flexible low-loss cable for industrial applications',
    10.3, 2.74, 7.24, 10.3,
    'Silver-plated Aluminum', 'Foam PE', 'Aluminum Tape + Tinned Braid', 'PE',
    50.0, 78.0, 180.0, 85.0,
    0, 3000000000,
    '{"100000000": 0.1, "1000000000": 0.5, "3000000000": 1.0}'::jsonb,
    0.2, '{"300": 150.0}'::jsonb,
    25.0, 1000, 100.0,
    -90, -40, -50,
    ARRAY['RoHS', 'Industrial'], ARRAY['MIL-PRF-17'],
    ARRAY['Industrial', 'Antenna', 'Wireless Communications'], 1
FROM manufacturers m, cable_categories c
WHERE m.name = 'Amphenol RF' AND c.name = 'Ultra-Flexible RF';

-- 插入頻率響應數據範例 (Delft Cri/oFlex 3 NbTi)
INSERT INTO cable_frequency_responses (cable_id, frequency_hz, s11_db, s21_db, s41_db, phase_delay_deg, temperature_k)
SELECT 
    c.id, freq, 
    CASE WHEN freq < 1000000000 THEN -25 ELSE -20 END, -- S11
    -1.5 * (freq / 6000000000), -- S21 approximation
    -70 - 10 * LOG(freq / 1000000000+.00000000001), -- S41
    0.12 * (freq / 1000000000), -- Phase delay
    0.01
FROM cables c, 
     (SELECT generate_series(100000000, 18000000000, 100000000) as freq) f
WHERE c.model_name = 'Cri/oFlex 3 NbTi';

-- 視圖：線材完整資訊
CREATE VIEW cable_full_info AS
SELECT 
    c.*,
    m.name as manufacturer_name,
    m.country as manufacturer_country,
    cat.name as category_name
FROM cables c
JOIN manufacturers m ON c.manufacturer_id = m.id
JOIN cable_categories cat ON c.category_id = cat.id;

-- 視圖：串擾計算摘要
CREATE VIEW crosstalk_summary AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.frequency_range_start_hz,
    p.frequency_range_end_hz,
    p.temperature_k,
    COUNT(cs.id) as simulation_points,
    MIN(cs.near_end_crosstalk_db) as min_next_db,
    MAX(cs.near_end_crosstalk_db) as max_next_db,
    MIN(cs.far_end_crosstalk_db) as min_fext_db,
    MAX(cs.far_end_crosstalk_db) as max_fext_db
FROM crosstalk_projects p
LEFT JOIN crosstalk_simulations cs ON p.id = cs.project_id
GROUP BY p.id, p.name, p.frequency_range_start_hz, p.frequency_range_end_hz, p.temperature_k;
-- """
-- 
-- # 儲存 SQL 檔案
-- with open('/mnt/kimi/output/flexible_cable_crosstalk_sim/sql/init_schema.sql', 'w') as f:
--     f.write(sql_schema)
-- 
-- print("✅ SQL 資料庫架構已建立")
-- print(f"檔案位置: /mnt/kimi/output/flexible_cable_crosstalk_sim/sql/init_schema.sql")
-- print(f"總行數: {len(sql_schema.split(chr(10)))}")
