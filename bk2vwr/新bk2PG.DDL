-- 1. 操作員維度
CREATE TABLE 操作員 (
    id   SERIAL PRIMARY KEY,
    名稱 TEXT NOT NULL UNIQUE
);

-- 2. VNA 主機維度
CREATE TABLE 主機 (
    id         SERIAL PRIMARY KEY,
    主機名     TEXT NOT NULL,
    ip         INET,
    說明       TEXT,
    UNIQUE(主機名)
);

-- 3. 檔案主表（含 pickle）
CREATE TABLE 皮可 (
    id         SERIAL PRIMARY KEY,
    操作員_id  INT REFERENCES 操作員,
    主機_id INT REFERENCES 主機,
    目錄夾     TEXT NOT NULL,          -- 遠端相對路徑
    檔案名稱   TEXT NOT NULL,
    副檔名     TEXT CHECK (副檔名 IN ('s1p','s2p','s3p','s4p','snp','csv')),
    皮可     BYTEA NOT NULL,         -- skrf.Network 序列化
    上傳時間   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(操作員_id, 主機_id, 目錄夾, 檔案名稱)
);
