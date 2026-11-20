from streamlit import session_state, set_page_config, title, header, sidebar, write, checkbox, subheader, columns as stCLMN, container, button, divider, caption, text_input, rerun, expander, text_area, code, info, popover, markdown, image as stImage, empty, video, error
輸出=empty()
#from md兩欄 import MarkdownTwoColumnParser
#from markdown import markdown
#from docUtil import 取出圖片, 轉表格, 文件轉md
#from rtrvPPT import slidePPT
from streamlit import pdf as pdfVWR, secrets
from mdUtil import doc2md, 馬克當, 檔頭
import os
from pathlib import Path
from fhndlrUtil import chkMime  #pdfVWR, 
from pandas import read_excel

# 設置頁面配置
set_page_config( page_title="文件浏覽器", page_icon="📁", layout="wide")

#title("📁 遞歸目錄文件浏覽器")
#markdown("使用此應用浏覽本地文件系統的目錄結構并查看文件內容")
# 初始化會話狀態
if 'current_path' not in session_state:
    session_state.current_path = os.getcwd()
if 'history' not in session_state:
    session_state.history = {}
#del session_state.history
# 側邊欄設置
with sidebar:
    #header("設置")
    root_path = text_input("根目錄路徑:", value=session_state.current_path) # 選擇根目錄

    if button("設置為根目錄"):
        if os.path.exists(root_path):
            session_state.current_path = root_path
            session_state.history = {}
            rerun()
        else:
            error("路徑不存在!")


    # 顯示文件擴展名篩選
    #subheader("文件篩選")
    show_hidden = checkbox("顯示隱藏文件", value=False)

    #subheader("當前信息")
    write(f"`{session_state.current_path}`") # 顯示當前路徑信息
    write(f"項目數量: {len(os.listdir(session_state.current_path))}")

# 函數：遞歸獲取目錄結構
def get_directory_structure(rootdir, show_hidden=False):
    """
    遞歸獲取目錄結構
    """
    dir_structure = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1

    for path, dirs, files in os.walk(rootdir):
        # 過濾隱藏文件/文件夾
        if not show_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]

        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], dir_structure)
        parent[folders[-1]] = subdir

    return dir_structure

# 函數：簡化版目錄浏覽（避免遞歸過深導致的性能問題）
def browse_directory(path, show_hidden=False):
    """
    浏覽指定目錄的內容
    """
    try:
        items = os.listdir(path)
        if not show_hidden:
            items = [item for item in items if not item.startswith('.')]

        # 分離目錄和文件
        dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(path, item))]

        return sorted(dirs), sorted(files)
    except PermissionError:
        error("沒有權限訪問此目錄")
        return [], []
    except Exception as e:
        error(f"讀取目錄時出錯: {e}")
        return [], []

# 函數：讀取文件內容
def read_file_content(file_path):
    """
    讀取文件內容，嘗試多種編碼
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'gbk']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read(), encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return None, f"讀取文件時出錯: {e}"

    return None, "無法解碼文件（可能是二進制文件）"

# 主界面
col1, col2 = stCLMN([1, 2])

with sidebar:

    current_path = session_state.current_path # 導航路徑
    path_parts = current_path.split(os.sep)

    # 創建面包屑導航

    # 顯示上級目錄按鈕
    parent_dir = os.path.dirname(current_path)
    if parent_dir != current_path:
        if button("⬆️ 上級目錄"):
            session_state.current_path = parent_dir
            session_state.history.update({current_path:None})
            rerun()

    # 顯示歷史記錄
    # 顯示當前目錄內容
    #subheader(f"內容: {os.path.basename(current_path) or '根目錄'}")

    dirs, files = browse_directory(current_path, show_hidden)

    # 顯示目錄
    if dirs:
        markdown("**目錄**")
        for d in dirs:
            dir_path = os.path.join(current_path, d)
            if button(f"📁 {d}", key=f"dir_{d}"):
                session_state.current_path = dir_path
                session_state.history.update({current_path:None})
                rerun()

    # 顯示文件
    if files:
        #markdown("**文件**")
        for f in files:
            file_path = os.path.join(current_path, f)
            if button(f"📄 {f}", key=f"file_{f}"):
                session_state.selected_file = file_path
                rerun()

#with col2:
#subheader("文件預覽")
    if session_state.history:
      pass
      #with expander("歷史記錄"):
      #  for i, path in enumerate(reversed(session_state.history[-5:])):
      #    if button(f"{i+1}. {os.path.basename(path)}", key=f"hist_{i}"):
      #      session_state.current_path = path
      #      rerun()


if 'selected_file' in session_state and os.path.exists(session_state.selected_file):
    file_path = session_state.selected_file
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    with sidebar:
      #with popover('文件資訊'):
      #write(f"{file_name}")
      #write(f"{file_size}字節")
      write(f"`{file_path}`")

    mimeType=chkMime(file_path) # 讀取文件內容
    #輸出.text(mimeType)
    #stCode(['mimeType', mimeType, mimeType=='application/vnd.openxmlformats-officedocument.wordprocessingml.document'])
    if mimeType in ['text/plain', 'text/x-python']:  #'text/plain'
      with open(file_path) as fin:
        內容=fin.read()
      輸出.code(內容, width='stretch')
    elif mimeType in ['video/mp4', 'video/x-matroska', 'video/webm']:  #'text/plain'
      #with open(file_path, 'rb') as fin:
        #vidByte=.read()
      video(file_path)   #fin.read()
      #輸出.text(len(vidByte))
      #輸出.text(['路徑=', file_path])
    elif mimeType=='text/html':  #'text/plain'
      with open(file_path) as fin:
        內容=fin.read()
      markdown(內容)
    elif mimeType=='text/markdown':  #'text/plain'
      with open(file_path) as fin:
        內容=fin.read()
      #write(內容)
      #解析器=MarkdownTwoColumnParser(column_width=10, gap_width=4, alignment='left', wrap_text=True)   #ColumnAlignment.JUSTIFY
      #雙欄=解析器.parse_markdown(內容)
      #輸出.text(['mimeType=', 雙欄])
      #markdown(內容, unsafe_allow_html=True)
      馬克當(Path(file_path), 內容)
    elif mimeType in ['image/webp', 'image/jpeg', 'image/png']:
      stImage(file_path)
    elif mimeType=='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
      try: 資框=session_state[file_path]
      except: 資框=session_state[file_path]=read_excel(file_path)
      資框
    elif mimeType=='application/pdf':
      #pdfVWR('.', file_path)
      pdfVWR(Path(file_path), height="stretch")  #, Path(file_name))
    elif mimeType in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:# or mimeType=='application/vnd.openxmlformats-officedocument.wordprocessingml.document':
      #stCode(['文件轉md'])
      內文, 圖片集 = 文件轉md(file_path)
      write(內文)
      #doc2md(file_path)
    elif mimeType=='application/vnd.ms-powerpoint' or mimeType=='application/vnd.openxmlformats-officedocument.presentationml.presentation':
      slidePPT(Path(file_path))
    content, encoding = read_file_content(file_path)
    #if content is not None:
    #    write(f"**編碼:** {encoding}")
    #    text_area("文件內容", content, height=400)     # 顯示文件內容
    #else:
    #    warning(encoding)
    #    if download_button(
    #        label="下載文件",
    #        data=open(file_path, "rb").read(),
    #        file_name=file_name,
    #        mime="application/octet-stream"
    #    ):
    #        success("文件下載準備就緒")
else:
    info("請從左側選擇文件進行預覽")

with sidebar:
    subheader("目錄瀏覽器")
    breadcrumb = container()
    with breadcrumb:
        cols = stCLMN(len(path_parts) + 1)
        with cols[0]:
            if button("🏠", help="根目錄"):
                session_state.current_path = os.path.abspath(os.sep)
                session_state.history.update({current_path:None})
                rerun()

        for i, part in enumerate(path_parts):
            if part:  # 跳過空部分
                path_so_far = os.sep.join(path_parts[:i+1])
                with cols[i+1]:
                    if button(part, help=path_so_far):
                        session_state.current_path = path_so_far
                        session_state.history.append(current_path)
                        rerun()
# 頁腳
#divider()
caption("遞歸目錄文件浏覽器 - 使用Streamlit構建")
