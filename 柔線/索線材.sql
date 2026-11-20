-- 创建供应商表
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    technology VARCHAR(50) -- 'Superconducting', 'Coaxial'
);

-- 创建产品参数表
CREATE TABLE transmission_lines (
    id SERIAL PRIMARY KEY,
    vendor_id INT REFERENCES vendors(id),
    product_name VARCHAR(100),
    impedance REAL, -- 目标阻抗 (Ohms)
    frequency_max REAL, -- GHz
    insertion_loss REAL, -- dB/m
    pitch REAL, -- 通道间距 (mm)
    material VARCHAR(50), -- 'NbTi', 'Copper'
    is_superconducting BOOLEAN
);
