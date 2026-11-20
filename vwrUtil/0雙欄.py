# app.py - 主應用程式
from streamlit import radio, empty, set_page_config, slider, markdown
import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
import base64
from datetime import datetime
import json

雙欄狀態=empty()
# 設置頁面配置
st.set_page_config(
    page_title="Markdown 雙欄渲染器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
def load_css():
    st.markdown("""
    <style>
    /* 主容器樣式 */
    .main {
        padding: 0rem 0rem;
    }
    
    /* 標題樣式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #3B82F6;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* 雙欄容器 */
    .two-column-container {
        display: flex;
        gap: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 2rem;
    }
    
    .column {
        flex: 1;
        padding: 1.5rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        overflow-wrap: break-word;
        min-height: 600px;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    /* Markdown 內容樣式 */
    .markdown-content h1 {
        font-size: 1.8rem;
        color: #1E3A8A;
        border-left: 4px solid #3B82F6;
        padding-left: 1rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .markdown-content h2 {
        font-size: 1.5rem;
        color: #2563EB;
        border-bottom: 2px solid #60A5FA;
        padding-bottom: 0.5rem;
        margin-top: 1.2rem;
    }
    
    .markdown-content h3 {
        font-size: 1.2rem;
        color: #3B82F6;
        margin-top: 1rem;
    }
    
    .markdown-content p {
        line-height: 1.6;
        margin-bottom: 1rem;
        text-align: justify;
    }
    
    .markdown-content ul, .markdown-content ol {
        margin-left: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .markdown-content li {
        margin-bottom: 0.5rem;
    }
    
    .markdown-content blockquote {
        border-left: 4px solid #10B981;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        background-color: #ECFDF5;
        color: #065F46;
        font-style: italic;
    }
    
    .markdown-content code {
        background-color: #F3F4F6;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 0.9rem;
    }
    
    .markdown-content pre {
        background-color: #1F2937;
        color: #F9FAFB;
        padding: 1rem;
        border-radius: 6px;
        overflow-x: auto;
        margin: 1rem 0;
    }
    
    .markdown-content table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .markdown-content th {
        background-color: #3B82F6;
        color: white;
        padding: 0.75rem;
        text-align: left;
    }
    
    .markdown-content td {
        padding: 0.75rem;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .markdown-content tr:nth-child(even) {
        background-color: #F9FAFB;
    }
    
    /* 響應式設計 */
    @media (max-width: 768px) {
        .two-column-container {
            flex-direction: column;
        }
        
        .column {
            min-height: 400px;
        }
    }
    
    /* 卡片樣式 */
    .card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* 側邊欄樣式 */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1E3A8A 0%, #3B82F6 100%);
    }
    
    /* 進度條 */
    .stProgress > div > div > div > div {
        background-color: #3B82F6;
    }
    
    /* 選項卡樣式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 5px 5px 0 0;
        gap: 1rem;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化 session state
def init_session_state():
    if 'markdown_text' not in st.session_state:
        st.session_state.markdown_text = ""
    if 'columns_data' not in st.session_state:
        st.session_state.columns_data = {"left": [], "right": []}
    if 'render_mode' not in st.session_state:
        st.session_state.render_mode = "balanced"  # balanced, custom, continuous
    if 'split_ratio' not in st.session_state:
        st.session_state.split_ratio = 0.5
    if 'theme' not in st.session_state:
        st.session_state.theme = "light"
    if 'font_size' not in st.session_state:
        st.session_state.font_size = 16
    if 'show_line_numbers' not in st.session_state:
        st.session_state.show_line_numbers = False

# Markdown 解析器
class TwoColumnMarkdownRenderer:
    def __init__(self):
        self.supported_elements = ['heading', 'paragraph', 'list', 'code', 'table', 'quote', 'hr']
    
    def parse_markdown(self, text, mode="balanced", split_ratio=0.5):
        """解析 Markdown 並分割為兩欄"""
        lines = text.split('\n')
        blocks = self._split_into_blocks(lines)
        
        if mode == "balanced":
            left_blocks, right_blocks = self._balance_split(blocks)
        elif mode == "custom":
            split_index = int(len(blocks) * split_ratio)
            left_blocks = blocks[:split_index]
            right_blocks = blocks[split_index:]
        elif mode == "continuous":
            left_blocks, right_blocks = self._continuous_split(blocks)
        else:
            left_blocks, right_blocks = self._balance_split(blocks)
        
        return {
            "left": self._render_blocks(left_blocks),
            "right": self._render_blocks(right_blocks)
        }
    
    def _split_into_blocks(self, lines):
        """將 Markdown 分割為邏輯區塊"""
        blocks = []
        current_block = []
        in_code_block = False
        in_table = False
        
        for line in lines:
            stripped = line.strip()
            
            # 處理代碼區塊
            if stripped.startswith('```'):
                if in_code_block:
                    current_block.append(line)
                    blocks.append(('\n'.join(current_block), 'code'))
                    current_block = []
                    in_code_block = False
                else:
                    if current_block:
                        blocks.append(('\n'.join(current_block), 'text'))
                        current_block = []
                    current_block.append(line)
                    in_code_block = True
                continue
            
            if in_code_block:
                current_block.append(line)
                continue
            
            # 處理表格
            if stripped.startswith('|'):
                if not in_table:
                    if current_block:
                        blocks.append(('\n'.join(current_block), 'text'))
                        current_block = []
                    in_table = True
                current_block.append(line)
                continue
            elif in_table:
                blocks.append(('\n'.join(current_block), 'table'))
                current_block = [line] if stripped else []
                in_table = False
                continue
            
            # 處理空行（區塊分隔符）
            if stripped == '':
                if current_block:
                    blocks.append(('\n'.join(current_block), 'text'))
                    current_block = []
                continue
            
            # 處理標題（單獨成塊）
            if stripped.startswith('#') and not in_code_block:
                if current_block:
                    blocks.append(('\n'.join(current_block), 'text'))
                    current_block = []
                blocks.append((line, 'heading'))
                continue
            
            # 處理水平線
            if stripped in ['---', '***', '___']:
                if current_block:
                    blocks.append(('\n'.join(current_block), 'text'))
                    current_block = []
                blocks.append((line, 'hr'))
                continue
            
            current_block.append(line)
        
        # 添加最後一個區塊
        if current_block:
            blocks.append(('\n'.join(current_block), 'text'))
        
        return blocks
    
    def _balance_split(self, blocks):
        """平衡分割區塊到兩欄"""
        total_lines = sum(len(block[0].split('\n')) for block in blocks)
        target_lines = total_lines // 2
        
        left_blocks = []
        right_blocks = []
        current_lines = 0
        
        for block in blocks:
            block_lines = len(block[0].split('\n'))
            
            # 嘗試保持標題和其內容在一起
            if block[1] == 'heading':
                if abs(current_lines + block_lines - target_lines) < abs(current_lines - target_lines):
                    left_blocks.append(block)
                    current_lines += block_lines
                else:
                    right_blocks.append(block)
            else:
                if current_lines < target_lines:
                    left_blocks.append(block)
                    current_lines += block_lines
                else:
                    right_blocks.append(block)
        
        return left_blocks, right_blocks
    
    def _continuous_split(self, blocks):
        """連續分割（第一欄固定行數）"""
        target_lines = sum(len(block[0].split('\n')) for block in blocks) // 2
        left_blocks = []
        right_blocks = []
        current_lines = 0
        
        for block in blocks:
            block_lines = len(block[0].split('\n'))
            if current_lines < target_lines:
                left_blocks.append(block)
                current_lines += block_lines
            else:
                right_blocks.append(block)
        
        return left_blocks, right_blocks
    
    def _render_blocks(self, blocks):
        """渲染區塊為 HTML"""
        html_parts = []
        
        for content, block_type in blocks:
            if block_type == 'heading':
                html_parts.append(f'<div class="markdown-block heading">{content}</div>')
            elif block_type == 'code':
                html_parts.append(f'<div class="markdown-block code"><pre><code>{content}</code></pre></div>')
            elif block_type == 'table':
                html_parts.append(f'<div class="markdown-block table">{content}</div>')
            elif block_type == 'hr':
                html_parts.append('<hr class="markdown-block hr">')
            else:
                html_parts.append(f'<div class="markdown-block text">{content}</div>')
        
        return '\n'.join(html_parts)

# 工具函數
def create_download_link(content, filename, label):
    """創建下載連結"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{label}</a>'
    return href

def analyze_markdown(text):
    """分析 Markdown 內容"""
    lines = text.split('\n')
    total_lines = len(lines)
    
    # 統計不同元素
    headings = sum(1 for line in lines if line.strip().startswith('#'))
    code_blocks = text.count('```')
    lists = sum(1 for line in lines if line.strip().startswith(('-', '*', '+', '1.', '2.', '3.')))
    tables = sum(1 for line in lines if line.strip().startswith('|'))
    
    return {
        'total_lines': total_lines,
        'headings': headings,
        'code_blocks': code_blocks // 2,  # 開始和結束算一對
        'lists': lists,
        'tables': tables,
        'estimated_pages': total_lines // 50 + 1
    }

# 主應用程式
def main():
    # 加載 CSS 和初始化
    load_css()
    init_session_state()
    
    
    # 頁面標題
    st.markdown('<h1 class="main-title">📚 Markdown 雙欄渲染器</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">即時將 Markdown 轉換為美觀的雙欄格式，支援即時預覽和匯出</p>', unsafe_allow_html=True)
    
    # 側邊欄
    with st.sidebar:
        st.markdown("### ⚙️ 設定")
        
        render_mode = radio( "分割模式", ["balanced", "custom", "continuous"], horizontal=True, index=0)    # 分割模式, help="balanced: 平衡分割 | custom: 自定義比例 | continuous: 連續分割"
        
        st.session_state.render_mode = render_mode
        
        if render_mode == "custom":
            split_ratio = st.slider(
                "分割比例",
                min_value=0.1,
                max_value=0.9,
                value=0.5,
                step=0.1,
                help="左欄內容的比例"
            )
            st.session_state.split_ratio = split_ratio
        
        # 顯示選項
        col1, col2 = st.columns(2)
        with col1:
            show_line_numbers = st.checkbox("顯示行號", value=False)
            st.session_state.show_line_numbers = show_line_numbers
        
        with col2:
            theme = st.selectbox("主題", ["light", "dark"], index=0)
            st.session_state.theme = theme
        
        font_size = st.slider("字體大小", min_value=12, max_value=24, value=16, step=1)
        st.session_state.font_size = font_size
        
        st.markdown("---")
        
        # 快速插入模板
        st.markdown("### 📝 快速模板")
        template=radio("選擇模板", ["空白", "報告模板", "技術文檔", "會議記錄", "論文格式"], horizontal=True, index=0)
        from 範本 import templates
        if template != "空白" and st.button("載入模板"):
            st.session_state.markdown_text = templates[template]
            st.rerun()
            st.markdown("---")
    
# 分析功能
if st.session_state.markdown_text:
  stats = analyze_markdown(st.session_state.markdown_text)
  st.markdown("### 📊 內容分析")
  st.metric("總行數", stats['total_lines'])
  col1, col2 = st.columns(2)
  with col1:
      st.metric("標題數", stats['headings'])
      st.metric("代碼區塊", stats['code_blocks'])
  with col2:
      st.metric("列表項", stats['lists'])
      st.metric("表格數", stats['tables'])

# 渲染器實例
renderer = TwoColumnMarkdownRenderer()
# 主內容區 - 使用選項卡
tab1, tab2, tab3 = st.tabs(["📝 編輯與預覽", "📊 分析與統計", "💾 匯出與分享"])

with tab1:
  # 編輯器和預覽區
  col_editor, col_preview = st.columns([1, 1])
  
  with col_editor:
      st.markdown("### 編輯 Markdown")
      
      # 工具欄
      col_tools = st.columns(6)
      with col_tools[0]:
          if st.button("B", help="粗體"):
              st.session_state.markdown_text += "**粗體文字**"
      with col_tools[1]:
          if st.button("I", help="斜體"):
              st.session_state.markdown_text += "*斜體文字*"
      with col_tools[2]:
          if st.button("H1", help="一級標題"):
              st.session_state.markdown_text += "\n# 標題\n"
      with col_tools[3]:
          if st.button("H2", help="二級標題"):
              st.session_state.markdown_text += "\n## 子標題\n"
      with col_tools[4]:
          if st.button("🔗", help="連結"):
              st.session_state.markdown_text += "[連結文字](https://example.com)"
      with col_tools[5]:
          if st.button("📷", help="圖片"):
              st.session_state.markdown_text += "![替代文字](圖片網址)"
      
      # Markdown 編輯器
      markdown_text = st.text_area(
          "輸入 Markdown 內容",
          value=st.session_state.markdown_text,
          height=400,
          placeholder="在此輸入 Markdown 內容...\n\n範例：\n# 標題\n\n這是一個段落。\n\n- 列表項目1\n- 列表項目2\n\n```python\nprint('Hello World')\n```",
          label_visibility="collapsed"
      )
      
      # 更新 session state
      if markdown_text != st.session_state.markdown_text:
          st.session_state.markdown_text = markdown_text
          st.rerun()
      
      # 文件上傳
      uploaded_file = st.file_uploader("或上傳 Markdown 文件", type=['md', 'txt', 'markdown'])
      if uploaded_file is not None:
          stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
          content = stringio.read()
          st.session_state.markdown_text = content
          st.success(f"已載入檔案: {uploaded_file.name}")
          st.rerun()
  
  with col_preview:
      st.markdown("### 即時預覽")
      
      if markdown_text:
          # 解析 Markdown 為兩欄
          columns_data = renderer.parse_markdown(
              markdown_text,
              mode=st.session_state.render_mode,
              split_ratio=st.session_state.split_ratio
          )
          st.session_state.columns_data = columns_data
          
          雙欄狀態.text(columns_data['left'])
          #雙欄狀態.text(columns_data['right'])
          # 顯示雙欄預覽
          st.markdown("#### 雙欄預覽")
          st.markdown(f"""
              <style>
              .two-column-preview {{
                  display: flex;
                  gap: 20px;
                  margin-top: 20px;
              }}
              .preview-column {{
                  flex: 1;
                  background: green;
                  padding: 20px;
                  border-radius: 10px;
                  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                  max-height: 400px;
                  overflow-y: auto;
                  font-size: {st.session_state.font_size}px;
              }}
              </style>
              
              <div class="two-column-preview">
                  <div class="preview-column">
                      {st.markdown(columns_data["left"], unsafe_allow_html=True)}
                  </div>
                  <div class="preview-column">
                      {st.markdown(columns_data["right"], unsafe_allow_html=True)}
                  </div>
              </div>""", unsafe_allow_html=True)
      else:
          st.info("在左側輸入 Markdown 內容以開始預覽")

with tab2:
  st.markdown("### 內容分析")
  
  if markdown_text:
      # 詳細分析
      stats = analyze_markdown(markdown_text)
      
      col1, col2, col3 = st.columns(3)
      with col1:
          st.metric("總字數", len(markdown_text))
          st.metric("總行數", stats['total_lines'])
      
      with col2:
          st.metric("段落數", len([p for p in markdown_text.split('\n\n') if p.strip()]))
          st.metric("估計頁數", stats['estimated_pages'])
      
      with col3:
          st.metric("閱讀時間", f"{len(markdown_text.split()) // 200 + 1} 分鐘")
      
      # 視覺化
      st.markdown("### 📈 元素分佈")
      
      # 建立數據
      elements = ['標題', '代碼區塊', '列表', '表格', '其他']
      counts = [
          stats['headings'],
          stats['code_blocks'],
          stats['lists'],
          stats['tables'],
          stats['total_lines'] - sum([stats['headings'], stats['code_blocks'], stats['lists'], stats['tables']])
      ]
      
      # 建立圖表
      fig = px.pie(
          names=elements,
          values=counts,
          title="Markdown 元素分佈",
          color_discrete_sequence=px.colors.qualitative.Set3
      )
      fig.update_traces(textposition='inside', textinfo='percent+label')
      st.plotly_chart(fig, use_container_width=True)
      
      # 詳細統計表
      st.markdown("### 📋 詳細統計")
      stats_df = pd.DataFrame({
          '元素類型': elements,
          '數量': counts,
          '百分比': [f"{(c/sum(counts))*100:.1f}%" for c in counts]
      })
      st.dataframe(stats_df, use_container_width=True, hide_index=True)
  else:
      st.info("請先輸入 Markdown 內容以查看分析")

with tab3:
  st.markdown("### 匯出與分享選項")
  
  if markdown_text:
      col_export1, col_export2 = st.columns(2)
      
      with col_export1:
          st.markdown("#### 下載選項")
          
          # 純文本匯出
          if st.button("📥 下載雙欄文本"):
              two_column_text = ""
              left_lines = st.session_state.columns_data["left"].split('\n')
              right_lines = st.session_state.columns_data["right"].split('\n')
              
              max_lines = max(len(left_lines), len(right_lines))
              for i in range(max_lines):
                  left = left_lines[i] if i < len(left_lines) else ""
                  right = right_lines[i] if i < len(right_lines) else ""
                  two_column_text += f"{left:<40}    {right}\n"
              
              st.download_button(
                  label="點擊下載",
                  data=two_column_text,
                  file_name=f"two_column_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                  mime="text/plain"
              )
          
          # HTML 匯出
          if st.button("🌐 下載 HTML"):
              html_content = f"""
              <!DOCTYPE html>
              <html lang="zh-TW">
              <head>
                  <meta charset="UTF-8">
                  <meta name="viewport" content="width=device-width, initial-scale=1.0">
                  <title>雙欄文件 - {datetime.now().strftime('%Y-%m-%d')}</title>
                  <style>
                      body {{
                          font-family: 'Microsoft JhengHei', sans-serif;
                          line-height: 1.6;
                          color: #333;
                          margin: 0;
                          padding: 20px;
                      }}
                      .two-column-container {{
                          display: flex;
                          gap: 40px;
                          max-width: 1200px;
                          margin: 0 auto;
                      }}
                      .column {{
                          flex: 1;
                          padding: 30px;
                          background: #f9f9f9;
                          border-radius: 10px;
                          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                      }}
                      h1, h2, h3 {{
                          color: #2c3e50;
                          border-bottom: 2px solid #3498db;
                          padding-bottom: 10px;
                      }}
                      pre {{
                          background: #2c3e50;
                          color: white;
                          padding: 15px;
                          border-radius: 5px;
                          overflow-x: auto;
                      }}
                      table {{
                          width: 100%;
                          border-collapse: collapse;
                          margin: 15px 0;
                      }}
                      th, td {{
                          border: 1px solid #ddd;
                          padding: 8px;
                          text-align: left;
                      }}
                      @media print {{
                          .two-column-container {{
                              gap: 20px;
                          }}
                          .column {{
                              box-shadow: none;
                              border: 1px solid #ddd;
                          }}
                      }}
                  </style>
              </head>
              <body>
                  <div class="two-column-container">
                      <div class="column">
                          {st.session_state.columns_data["left"]}
                      </div>
                      <div class="column">
                          {st.session_state.columns_data["right"]}
                      </div>
                  </div>
              </body>
              </html>
              """
              
              st.download_button(
                  label="點擊下載 HTML",
                  data=html_content,
                  file_name=f"two_column_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                  mime="text/html"
              )
      
      with col_export2:
          st.markdown("#### 分享選項")
          
          # 生成分享連結（模擬）
          share_url = "https://example.com/share/" + base64.b64encode(
              markdown_text[:100].encode()
          ).decode()[:20]
          
          st.code(share_url, language="text")
          st.info("這是模擬的分享連結。在實際應用中，這裡會生成真實的可分享連結。")
          
          # 複製到剪貼簿
          if st.button("📋 複製分享連結"):
              st.success("已複製到剪貼簿（模擬）")
          
          # 列印預覽
          if st.button("🖨️ 列印預覽"):
              st.info("列印預覽功能需要瀏覽器支援")
          
          # 嵌入程式碼
          st.markdown("#### 嵌入程式碼")
          embed_code = f"""
          <iframe 
              src="{share_url}"
              width="100%"
              height="600"
              frameborder="0"
              scrolling="no">
          </iframe>
          """
          st.code(embed_code, language="html")
  
  else:
      st.info("請先輸入 Markdown 內容以使用匯出功能")

# 頁腳
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem; padding: 20px 0;">
        <p>📚 Markdown 雙欄渲染器 | 使用 Streamlit 構建 | © 2024</p>
        <p>支援標準 Markdown 語法 | 即時預覽 | 響應式設計</p>
    </div>
    """,
    unsafe_allow_html=True
)
main()
