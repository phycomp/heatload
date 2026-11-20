import sqlite3
# 數據庫初始化
def init_database():
    conn = sqlite3.connect('physics_platform.db', check_same_thread=False)
    c = conn.cursor()
    
    # 創建用戶表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bio TEXT,
            avatar BLOB
        )
    ''')
    
    # 創建博客表
    c.execute('''
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            author_id INTEGER,
            category TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # 創建問題表
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            author_id INTEGER,
            category TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0,
            solved BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # 創建回答表
    c.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            content TEXT,
            author_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            likes INTEGER DEFAULT 0,
            is_accepted BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (question_id) REFERENCES questions (id),
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # 創建評論表
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id INTEGER,
            content TEXT,
            author_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (blog_id) REFERENCES blogs (id),
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    return conn

# 初始化數據庫
conn = init_database()
# 數據庫操作函數
def get_latest_blogs(limit=5):
    c = conn.cursor()
    c.execute("SELECT * FROM blogs ORDER BY created_at DESC LIMIT ?", (limit,))
    return c.fetchall()

def get_blogs_by_category(category=None):
    c = conn.cursor()
    if category:
        c.execute("SELECT * FROM blogs WHERE category = ? ORDER BY created_at DESC", (category,))
    else:
        c.execute("SELECT * FROM blogs ORDER BY created_at DESC")
    return c.fetchall()

def get_username(user_id):
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    return result[0] if result else "未知用戶"

def create_blog(title, content, author_id, category, tags):
    c = conn.cursor()
    c.execute("INSERT INTO blogs (title, content, author_id, category, tags) VALUES (?, ?, ?, ?, ?)",
             (title, content, author_id, category, tags))
    conn.commit()

def get_user_blogs(user_id):
    c = conn.cursor()
    c.execute("SELECT * FROM blogs WHERE author_id = ? ORDER BY created_at DESC", (user_id,))
    return c.fetchall()

def delete_blog(blog_id):
    c = conn.cursor()
    c.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
    conn.commit()

def get_questions(category=None, status=None):
    c = conn.cursor()
    query = "SELECT * FROM questions"
    params = []
    
    if category or status:
        query += " WHERE"
        conditions = []
        if category:
            conditions.append(" category = ?")
            params.append(category)
        if status == "已解決":
            conditions.append(" solved = 1")
        elif status == "未解決":
            conditions.append(" solved = 0")
        
        query += " AND".join(conditions)
    
    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    return c.fetchall()

def create_question(title, content, author_id, category, tags):
    c = conn.cursor()
    c.execute("INSERT INTO questions (title, content, author_id, category, tags) VALUES (?, ?, ?, ?, ?)",
             (title, content, author_id, category, tags))
    conn.commit()

def get_user_questions(user_id):
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE author_id = ? ORDER BY created_at DESC", (user_id,))
    return c.fetchall()

def get_user_answers(user_id):
    c = conn.cursor()
    c.execute("SELECT * FROM answers WHERE author_id = ?", (user_id,))
    return c.fetchall()

def like_blog(blog_id):
    c = conn.cursor()
    c.execute("UPDATE blogs SET likes = likes + 1 WHERE id = ?", (blog_id,))
    conn.commit()

def view_blog_detail(blog_id):
    c = conn.cursor()
    c.execute("UPDATE blogs SET views = views + 1 WHERE id = ?", (blog_id,))
    c.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
    blog = c.fetchone()
    conn.commit()
    
    if blog:
        st.session_state.viewing_blog = blog
        st.session_state.page = "博客詳情"
        st.experimental_rerun()

def view_question_detail(question_id):
    c = conn.cursor()
    c.execute("UPDATE questions SET views = views + 1 WHERE id = ?", (question_id,))
    c.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    question = c.fetchone()
    conn.commit()
    
    if question:
        st.session_state.viewing_question = question
        st.session_state.page = "問題詳情"
        st.experimental_rerun()

