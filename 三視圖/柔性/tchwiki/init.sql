-- 啟用 pgvector 擴充功能
CREATE EXTENSION IF NOT EXISTS vector;

-- 建立知識庫主資料表
CREATE TABLE IF NOT EXISTS wiki_pages (
    id SERIAL PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,         -- 檔案相對路徑 (例如: finance/stock_analysis.md)
    title TEXT NOT NULL,                    -- 標題 (可從 Markdown 第一行 # 擷取)
    category TEXT NOT NULL,                 -- 分類 (例如: finance, quantum, python, nvim, snip)
    content TEXT NOT NULL,                  -- Markdown 純文字內文 (供搜尋與顯示備用)
    tsv_content tsvector,                   -- 全文檢索向量 (PostgreSQL 原生)
    embedding vector(384),                  -- AI 向量 (以 All-MiniLM-L6-v2 384維度為例，可依模型調整)
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 建立 tsvector 觸發器：當 content 或 title 更新時自動維護全文檢索索引
CREATE OR REPLACE FUNCTION wiki_pages_tsvector_trigger() RETURNS trigger AS $$
BEGIN
    NEW.tsv_content := 
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.content, '')), 'B');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
    ON wiki_pages FOR EACH ROW EXECUTE FUNCTION wiki_pages_tsvector_trigger();

-- 建立索引以提升搜尋效能
CREATE INDEX IF NOT EXISTS wiki_tsv_idx ON wiki_pages USING gin(tsv_content);
CREATE INDEX IF NOT EXISTS wiki_embedding_idx ON wiki_pages USING hnsw (embedding vector_cosine_ops);
