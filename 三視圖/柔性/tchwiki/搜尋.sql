-- 使用先前建立的 HNSW 索引進行餘弦相似度 (Cosine Distance) 排序
SELECT title, category, (1 - (embedding <=> %s)) AS similarity
FROM wiki_pages
ORDER BY embedding <=> %s
LIMIT 5;
