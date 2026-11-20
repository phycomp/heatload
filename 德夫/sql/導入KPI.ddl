--# 1. SQL Schema - PostgreSQL DDL
--sql_schema = """
-- ============================================================
-- KPI Ticket Tracking System - PostgreSQL Schema
-- ============================================================

-- Drop tables if exist (for clean setup)
DROP TABLE IF EXISTS kpi_progress CASCADE;
DROP TABLE IF EXISTS kpi_tickets CASCADE;
DROP TABLE IF EXISTS kpi_categories CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- 1. Users Table (for authentication & assignment)
-- ============================================================
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    role            VARCHAR(20) DEFAULT 'member' CHECK (role IN ('admin', 'manager', 'member')),
    department_id   INTEGER,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. Departments Table
-- ============================================================
CREATE TABLE departments (
    dept_id         SERIAL PRIMARY KEY,
    dept_name       VARCHAR(50) NOT NULL UNIQUE,
    dept_code       VARCHAR(10) NOT NULL UNIQUE,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. KPI Categories Table (sub-categories)
-- ============================================================
CREATE TABLE kpi_categories (
    category_id     SERIAL PRIMARY KEY,
    dept_id         INTEGER NOT NULL REFERENCES departments(dept_id) ON DELETE CASCADE,
    category_name   VARCHAR(100) NOT NULL,
    category_code   VARCHAR(20) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dept_id, category_name)
);

-- ============================================================
-- 4. KPI Tickets Table (main KPI items)
-- ============================================================
CREATE TABLE kpi_tickets (
    ticket_id       SERIAL PRIMARY KEY,
    year_num        INTEGER NOT NULL CHECK (year_num IN (1, 2, 3)),
    category_id     INTEGER NOT NULL REFERENCES kpi_categories(category_id) ON DELETE CASCADE,
    kpi_item        VARCHAR(255) NOT NULL,
    target_value    VARCHAR(255) NOT NULL,
    weight          INTEGER NOT NULL CHECK (weight BETWEEN 1 AND 10),
    status          VARCHAR(20) DEFAULT 'pending' 
                        CHECK (status IN ('pending', 'in_progress', 'completed', 'delayed', 'cancelled')),
    priority        VARCHAR(10) DEFAULT 'medium' 
                        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    assigned_to     INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    start_date      DATE,
    due_date        DATE,
    completed_date  DATE,
    actual_value    VARCHAR(255),
    progress_pct    DECIMAL(5,2) DEFAULT 0.0 CHECK (progress_pct BETWEEN 0 AND 100),
    notes           TEXT,
    created_by      INTEGER REFERENCES users(user_id),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. KPI Progress Table (tracking history)
-- ============================================================
CREATE TABLE kpi_progress (
    progress_id     SERIAL PRIMARY KEY,
    ticket_id       INTEGER NOT NULL REFERENCES kpi_tickets(ticket_id) ON DELETE CASCADE,
    progress_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    progress_pct    DECIMAL(5,2) NOT NULL CHECK (progress_pct BETWEEN 0 AND 100),
    actual_value    VARCHAR(255),
    notes           TEXT,
    recorded_by     INTEGER REFERENCES users(user_id),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Indexes for performance
-- ============================================================
CREATE INDEX idx_tickets_year ON kpi_tickets(year_num);
CREATE INDEX idx_tickets_status ON kpi_tickets(status);
CREATE INDEX idx_tickets_category ON kpi_tickets(category_id);
CREATE INDEX idx_tickets_assigned ON kpi_tickets(assigned_to);
CREATE INDEX idx_progress_ticket ON kpi_progress(ticket_id);
CREATE INDEX idx_progress_date ON kpi_progress(progress_date);

-- ============================================================
-- Views for reporting
-- ============================================================

-- View: KPI Summary with department & category
CREATE OR REPLACE VIEW v_kpi_summary AS
SELECT 
    t.ticket_id,
    t.year_num,
    d.dept_name,
    d.dept_code,
    c.category_name,
    t.kpi_item,
    t.target_value,
    t.weight,
    t.status,
    t.priority,
    t.progress_pct,
    t.actual_value,
    t.start_date,
    t.due_date,
    t.completed_date,
    u.full_name AS assigned_to_name,
    t.notes
FROM kpi_tickets t
JOIN kpi_categories c ON t.category_id = c.category_id
JOIN departments d ON c.dept_id = d.dept_id
LEFT JOIN users u ON t.assigned_to = u.user_id;

-- View: Monthly Achievement Rate
CREATE OR REPLACE VIEW v_monthly_achievement AS
SELECT 
    year_num,
    dept_name,
    DATE_TRUNC('month', COALESCE(completed_date, CURRENT_DATE)) AS report_month,
    COUNT(*) AS total_tickets,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / NULLIF(COUNT(*), 0), 
        2
    ) AS achievement_rate,
    ROUND(
        SUM(weight * progress_pct) / NULLIF(SUM(weight), 0), 
        2
    ) AS weighted_progress
FROM v_kpi_summary
GROUP BY year_num, dept_name, DATE_TRUNC('month', COALESCE(completed_date, CURRENT_DATE))
ORDER BY year_num, dept_name, report_month;

-- View: Period Achievement (for mid-term & annual)
CREATE OR REPLACE VIEW v_period_achievement AS
SELECT 
    year_num,
    dept_name,
    CASE 
        WHEN EXTRACT(MONTH FROM CURRENT_DATE) <= 6 THEN 'mid_year'
        ELSE 'annual'
    END AS period_type,
    COUNT(*) AS total_tickets,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / NULLIF(COUNT(*), 0), 
        2
    ) AS achievement_rate,
    ROUND(
        SUM(weight * progress_pct) / NULLIF(SUM(weight), 0), 
        2
    ) AS weighted_progress,
    SUM(weight) FILTER (WHERE status = 'completed') AS completed_weight,
    SUM(weight) AS total_weight
FROM v_kpi_summary
GROUP BY year_num, dept_name
ORDER BY year_num, dept_name;

-- ============================================================
-- Sample Data Insertion
-- ============================================================

-- Insert departments
INSERT INTO departments (dept_name, dept_code, description) VALUES
('研發部', 'R&D', 'Research & Development - Transmission Line Design, Simulation, Material, Prototype'),
('製程部', 'MFG', 'Manufacturing - R2R Process, Capacity, Automation, Validation'),
('應用工程', 'AE', 'Application Engineering - Demo Platform, Customer Technical Support'),
('品保部', 'QA', 'Quality Assurance - Electrical, Thermal, Reliability Validation, Quality System');

-- Insert users
INSERT INTO users (username, email, full_name, role, department_id) VALUES
('admin', 'admin@company.com', '系統管理員', 'admin', 1),
('rd_manager', 'rd@company.com', '研發部經理', 'manager', 1),
('mfg_manager', 'mfg@company.com', '製程部經理', 'manager', 2),
('ae_manager', 'ae@company.com', '應用工程經理', 'manager', 3),
('qa_manager', 'qa@company.com', '品保部經理', 'manager', 4),
('rd_engineer1', 'rd1@company.com', '研發工程師A', 'member', 1),
('rd_engineer2', 'rd2@company.com', '研發工程師B', 'member', 1),
('mfg_engineer1', 'mfg1@company.com', '製程工程師A', 'member', 2),
('ae_engineer1', 'ae1@company.com', '應用工程師A', 'member', 3),
('qa_engineer1', 'qa1@company.com', '品保工程師A', 'member', 4);

-- Insert categories for Year 1
INSERT INTO kpi_categories (dept_id, category_name, category_code, description) VALUES
(1, '傳輸線設計', 'R&D-DES', 'Transmission line architecture design'),
(1, '電性模擬', 'R&D-EM', 'Electrical simulation & crosstalk analysis'),
(1, '熱模擬', 'R&D-TH', 'Thermal simulation & heat load analysis'),
(1, '材料開發', 'R&D-MAT', 'Material selection & validation'),
(1, '原型開發', 'R&D-PROT', 'Prototype development & verification'),
(2, 'R2R製程開發', 'MFG-R2R', 'Roll-to-roll process development'),
(2, '產能建置', 'MFG-CAP', 'Capacity building & ramp-up'),
(2, '製程驗證', 'MFG-VAL', 'Process validation & capability study'),
(3, '展示平台', 'AE-DEMO', 'Demo platform development'),
(3, '客戶技術支援', 'AE-SUP', 'Customer technical support'),
(4, '電性驗證', 'QA-EL', 'Electrical validation & measurement'),
(4, '熱驗證', 'QA-TH', 'Thermal validation & testing'),
(4, '可靠度驗證', 'QA-REL', 'Reliability validation'),
(4, '品質系統', 'QA-SYS', 'Quality management system');

-- Insert sample KPI tickets for Year 1
INSERT INTO kpi_tickets (year_num, category_id, kpi_item, target_value, weight, status, priority, assigned_to, start_date, due_date, progress_pct, created_by) VALUES
(1, 1, 'Stripline架構設計完成', '設計凍結', 5, 'completed', 'high', 6, '2026-01-01', '2026-03-31', 100.0, 1),
(1, 1, '微帶線架構設計完成', '設計凍結', 5, 'completed', 'high', 6, '2026-01-01', '2026-03-31', 100.0, 1),
(1, 1, '差動對傳輸線設計', '設計凍結', 5, 'completed', 'medium', 6, '2026-02-01', '2026-04-30', 100.0, 1),
(1, 2, 'HFSS 3D電磁模擬平台建置', '建置完成', 5, 'completed', 'high', 7, '2026-01-01', '2026-04-30', 100.0, 1),
(1, 2, 'CST Studio模擬平台建置', '建置完成', 5, 'completed', 'high', 7, '2026-01-01', '2026-04-30', 100.0, 1),
(1, 2, 'S參數模擬驗證 (S11<-20dB)', 'S11<-20dB', 8, 'completed', 'high', 7, '2026-03-01', '2026-06-30', 100.0, 1),
(1, 2, '串擾模擬驗證 (<-30dB @ 8GHz)', '<-30dB', 10, 'in_progress', 'critical', 7, '2026-04-01', '2026-07-31', 75.0, 1),
(1, 2, '近端串擾(NEXT)模擬分析', '分析完成', 5, 'in_progress', 'medium', 7, '2026-04-01', '2026-07-31', 60.0, 1),
(1, 3, '熱傳導模擬平台建置 (COMSOL)', '建置完成', 5, 'completed', 'high', 6, '2026-01-01', '2026-05-31', 100.0, 1),
(1, 3, '熱負載模擬驗證 (<4μW/通道 @ 3K→0.7K)', '<4μW/通道', 10, 'in_progress', 'critical', 6, '2026-04-01', '2026-08-31', 65.0, 1),
(1, 3, '熱梯度分佈模擬分析', '分析完成', 5, 'pending', 'medium', 6, '2026-06-01', '2026-09-30', 0.0, 1),
(1, 4, 'Polyimide基板材料選型', '選型完成', 5, 'completed', 'medium', 6, '2026-01-01', '2026-03-31', 100.0, 1),
(1, 4, 'Ag導體材料特性驗證', '驗證完成', 5, 'completed', 'medium', 6, '2026-02-01', '2026-05-31', 100.0, 1),
(1, 5, '8通道Flex原型Layout設計', 'Layout完成', 8, 'completed', 'high', 6, '2026-03-01', '2026-06-30', 100.0, 1),
(1, 5, '阻抗控制設計 (50Ω ±3%)', '50Ω±3%', 8, 'completed', 'high', 6, '2026-03-01', '2026-06-30', 100.0, 1),
(1, 5, '頻寬設計驗證 (DC~18GHz)', 'DC~18GHz', 8, 'in_progress', 'high', 6, '2026-05-01', '2026-08-31', 80.0, 1),
(1, 6, 'R2R捲對捲製程參數DOE', 'DOE完成', 8, 'completed', 'high', 8, '2026-01-01', '2026-05-31', 100.0, 1),
(1, 6, 'R2R蝕刻製程參數開發', '參數凍結', 8, 'completed', 'high', 8, '2026-02-01', '2026-06-30', 100.0, 1),
(1, 6, 'R2R電鍍製程參數開發', '參數凍結', 8, 'in_progress', 'high', 8, '2026-03-01', '2026-07-31', 85.0, 1),
(1, 7, 'R2R試產線建置完成', '建置完成', 5, 'completed', 'high', 8, '2026-01-01', '2026-04-30', 100.0, 1),
(1, 7, '試產良率達成 (≥70%)', '≥70%', 10, 'in_progress', 'critical', 8, '2026-04-01', '2026-08-31', 72.0, 1),
(1, 7, '月產能建立 (≥100條/月)', '≥100條/月', 5, 'pending', 'medium', 8, '2026-06-01', '2026-09-30', 0.0, 1),
(1, 8, '製程能力指數 Cpk≥1.33', 'Cpk≥1.33', 8, 'in_progress', 'high', 8, '2026-05-01', '2026-09-30', 45.0, 1),
(1, 9, '展示平台硬體建置完成', '建置完成', 5, 'completed', 'medium', 9, '2026-02-01', '2026-05-31', 100.0, 1),
(1, 9, '電性串擾即時量測展示模組', '模組上線', 8, 'completed', 'high', 9, '2026-04-01', '2026-07-31', 100.0, 1),
(1, 9, '熱負載即時監控展示模組', '模組上線', 8, 'in_progress', 'high', 9, '2026-05-01', '2026-08-31', 70.0, 1),
(1, 10, '客戶技術規格諮詢 (≥10家)', '≥10家', 5, 'completed', 'medium', 9, '2026-01-01', '2026-06-30', 100.0, 1),
(1, 11, 'S參數量測驗證 (VNA)', '量測完成', 8, 'completed', 'high', 10, '2026-03-01', '2026-06-30', 100.0, 1),
(1, 11, '阻抗量測驗證 (TDR)', '量測完成', 8, 'completed', 'high', 10, '2026-03-01', '2026-06-30', 100.0, 1),
(1, 11, '串擾量測驗證 (≥8通道)', '量測完成', 8, 'in_progress', 'high', 10, '2026-05-01', '2026-08-31', 55.0, 1),
(1, 12, '熱負載量測驗證 (≥8通道)', '量測完成', 8, 'pending', 'high', 10, '2026-06-01', '2026-09-30', 0.0, 1),
(1, 12, '熱循環測試 (300K↔4K, 100 cycles)', '通過100 cycles', 10, 'pending', 'critical', 10, '2026-07-01', '2026-10-31', 0.0, 1),
(1, 13, '彎折壽命測試 (≥10,000次)', '≥10,000次', 5, 'pending', 'medium', 10, '2026-06-01', '2026-10-31', 0.0, 1),
(1, 14, '進料檢驗規範建立', '規範發行', 3, 'completed', 'low', 10, '2026-01-01', '2026-03-31', 100.0, 1),
(1, 14, '製程檢驗規範建立', '規範發行', 3, 'completed', 'low', 10, '2026-02-01', '2026-04-30', 100.0, 1),
(1, 14, '出貨檢驗規範建立', '規範發行', 3, 'completed', 'low', 10, '2026-02-01', '2026-04-30', 100.0, 1);

-- Insert progress history for some tickets
INSERT INTO kpi_progress (ticket_id, progress_date, progress_pct, actual_value, notes, recorded_by) VALUES
(7, '2026-04-15', 25.0, '初步模擬中', '完成初步3D建模', 7),
(7, '2026-05-15', 50.0, '模擬進行中', '完成50%通道模擬', 7),
(7, '2026-06-15', 75.0, '-28dB初步結果', '優化屏蔽設計中', 7),
(10, '2026-04-15', 20.0, '模型建立中', 'COMSOL熱模型初版', 6),
(10, '2026-05-15', 45.0, '3.5μW初步結果', '材料參數調整中', 6),
(10, '2026-06-15', 65.0, '3.8μW', '接近目標，持續優化', 6),
(19, '2026-04-15', 30.0, '參數測試中', '完成第一輪DOE', 8),
(19, '2026-05-15', 60.0, '參數收斂中', '關鍵參數確定', 8),
(19, '2026-06-15', 85.0, '參數凍結', '最終驗證進行中', 8),
(21, '2026-05-15', 40.0, '68%', '製程調整中', 8),
(21, '2026-06-15', 72.0, '72%', '達成目標，持續監控', 8);

-- Update users with department references
UPDATE users SET department_id = 1 WHERE user_id IN (2, 6, 7);
UPDATE users SET department_id = 2 WHERE user_id IN (3, 8);
UPDATE users SET department_id = 3 WHERE user_id IN (4, 9);
UPDATE users SET department_id = 4 WHERE user_id IN (5, 10);

-- Verify data
SELECT 'Departments' AS table_name, COUNT(*) AS count FROM departments
UNION ALL SELECT 'Users', COUNT(*) FROM users
UNION ALL SELECT 'Categories', COUNT(*) FROM kpi_categories
UNION ALL SELECT 'Tickets', COUNT(*) FROM kpi_tickets
UNION ALL SELECT 'Progress', COUNT(*) FROM kpi_progress;
