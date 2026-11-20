CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('viewer','executor','admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS 類型 (
    id SERIAL PRIMARY KEY,
    sop_code VARCHAR(50) UNIQUE NOT NULL,
    sop_type VARCHAR(20) NOT NULL CHECK (sop_type IN ('electrical','thermal','process')),
    sop_name TEXT NOT NULL,
    owner VARCHAR(100),
    plan_start DATE,
    plan_end DATE,
    actual_start DATE,
    actual_end DATE,
    is_on_schedule BOOLEAN DEFAULT FALSE,
    delay_reasons JSONB DEFAULT '[]',
    delay_notes TEXT,
    status VARCHAR(20) DEFAULT 'not_started',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS 電性 (
    sop_instance_id INT PRIMARY KEY REFERENCES 類型(id) ON DELETE CASCADE,
    vna_power_dbm NUMERIC(6,2),
    estimated_dut_power_dbm NUMERIC(6,2),
    temp_stability_k NUMERIC(4,2),
    calibration_method VARCHAR(20),
    s21_phase_shift_deg NUMERIC(6,2)
);

CREATE TABLE IF NOT EXISTS 熱負載 (
    sop_instance_id INT PRIMARY KEY REFERENCES 類型(id) ON DELETE CASCADE,
    vacuum_leak_rate NUMERIC(10,6),
    cooldown_rate_k_per_min NUMERIC(6,3),
    static_load_mw NUMERIC(8,3),
    dynamic_load_mw NUMERIC(8,3)
);

CREATE TABLE IF NOT EXISTS sop_process (
    sop_instance_id INT PRIMARY KEY REFERENCES 類型(id) ON DELETE CASCADE,
    contact_resistance_ohm NUMERIC(8,4),
    junction_area_um2 NUMERIC(8,2),
    film_thickness_nm NUMERIC(6,2)
);

CREATE TABLE IF NOT EXISTS checklist_items (
    id SERIAL PRIMARY KEY,
    sop_instance_id INT NOT NULL REFERENCES 類型(id) ON DELETE CASCADE,
    item_order INT NOT NULL,
    description TEXT NOT NULL,
    related_decision VARCHAR(10),
    pass_criteria TEXT,
    measured_value TEXT,
    procedure_status VARCHAR(20) DEFAULT 'not_started',
    criteria_status VARCHAR(20) DEFAULT 'not_executed',
    executor VARCHAR(100),
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_checklist_sop ON checklist_items(sop_instance_id);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    row_id INT,
    column_name VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ DEFAULT NOW()
);
