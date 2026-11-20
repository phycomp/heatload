drop table 皮可 cascade;
drop TABLE 日誌 CASCADE;
drop TABLE 環境 CASCADE;
drop TABLE 操作員 CASCADE;

CREATE TABLE 操作員(
  id SERIAL PRIMARY KEY,
  操作員 TEXT default '操作員'
);

CREATE TABLE 環境 (
  id      SERIAL PRIMARY KEY,
  儀器   TEXT NOT NULL,        -- e.g. 'MS4647B_200317'
  校正參數     TEXT,                 -- e.g. '36585K'
  --溫度      NUMERIC(4,1),         -- 度C
  --偏差      NUMERIC(6,2),         -- V
  操作員_id  INT REFERENCES 操作員,
  備註        TEXT,
  UNIQUE(儀器, 校正參數)  --, 溫度, 偏差
);

-- 2. 測試日誌 ‑- 每「一批檔案」建一筆（對應到當天/當次資料夾）
CREATE TABLE 日誌 (
  id      SERIAL PRIMARY KEY,
  環境_id      INT REFERENCES 環境,
  料號      TEXT,                 -- 客戶料號/批號
  測試日期   DATE NOT NULL,
  測試結果   Boolean default true,
  路徑 TEXT,                 -- 原始路徑，方便回頭找檔
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(環境_id, 路徑)
);

CREATE TABLE 皮可(
    id      SERIAL PRIMARY KEY,
    日誌_id      INT REFERENCES 日誌,
    檔     TEXT NOT NULL,
    皮可  BYTEA NOT NULL,
    上傳時間 TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (日誌_id, 檔)          -- ← 這行一定要有
);
