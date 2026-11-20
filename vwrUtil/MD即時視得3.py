from streamlit import button, caption, columns, download_button, header, info, markdown, rerun, session_state, set_page_config, sidebar, spinner, stop, subheader, success, tabs, text_area, text_input, title, empty, image as stImage, pdf as PDFVWR, code
from 麥Util import 麥魔
from io import BytesIO
from pathlib import Path
import subprocess, tempfile, pathlib, os, shutil
from base64 import b64encode
from typing import Dict
from tempfile import NamedTemporaryFile, TemporaryDirectory
#del session_state.history
set_page_config(layout="wide", page_title="MD 樹狀總管")
from streamlit import empty, pyplot
狀態=empty()
# ---------- 通用工具 ----------
def load_history() -> Dict[str, str]:
    """回傳 路徑→內容 的歷史紀錄"""
    return session_state.get("history", {})

def save_history(檔: str, content: str):
    """把內容寫進歷史"""
    if "history" not in session_state:
        session_state.history = {}
    if "PDF內容" not in session_state:
        session_state.PDF內容 = {}
    if "current_content" not in session_state:
        session_state.current_content = {}
    session_state.history[檔] = content
    #輸出.text(session_state.history)
#f'pandoc {tmp_md_path} -o {tmp_pdf} --pdf-engine=xelatex -V mainfont="AR PL UMing TW" -V geometry:a4paper,portrait --toc --toc-depth=3 -N --highlight-style tango -V colorlinks=true -V linkcolor=blue -V citecolor=green -V urlcolor=cyan'.split()
檔頭=r'''---
documentclass: article
geometry:
  - top=1.2cm
  - bottom=1.2cm
  - left=1.2cm
  - right=1.2cm
fontsize: 9pt
linestretch: 1.0
header-includes: |
  \usepackage{fvextra}
  \DefineVerbatimEnvironment{Highlighting}{Verbatim}{
    breaklines,
    breaksymbolleft={},
    commandchars=\\\{\}
  }
---
'''

def 馬至匹(檔, 內容: str, TMP:Path=Path('/tmp')) -> bytes: #把 md 字串轉成 PDF bytes
    狀態=empty()
    暫馬=TMP/檔.with_suffix('.md')
    暫匹=TMP/檔.with_suffix('.pdf')
    暫馬.write_text(內容)
    cmd=["pandoc", str(暫馬), "-o", str(暫匹), "--pdf-engine=xelatex",
    "-V", "colorlinks=true", "-V", "linkcolor=blue",
    "-V", "emojifont=Segoe UI Emoji", "-V", "emojifont=EmojiOne Color",
    "-V", "urlcolor=red", "-V", "toccolor=gray",
    "-V", "CJKmainfont=Noto Serif CJK SC",
    "-V", "CJKmonofont=Noto Serif CJK SC",
    "-V", "mainfont=DejaVu Sans", "-V" "monofont=DejaVu Sans",
    "-V", "geometry:top=1.2cm,bottom=1.2cm,left=1.2cm,right=1.2cm",
    "--highlight-style=tango"]
    #cmd = [ "pandoc", str(暫馬), "-o", str(暫匹), "--pdf-engine=xelatex",
    #    "-V", "CJKmainfont=Noto Serif CJK SC",
    #    "-V", "CJKmonofont=Noto Serif CJK SC",
    #    "-V", "mainfont=DejaVu Sans",
    #    "-V", "monofont=DejaVu Sans",
    #    "--highlight-style=tango"
    #]
    #cmd=命令.split()
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        狀態.text(["STDOUT:", e.stdout])
        狀態.text(["STDERR:", e.stderr])
    #pandoc /home/sam/德夫/NbTi薄膜PI.md -o /home/sam/德夫/NbTi薄膜PI.pdf --pdf-engine=xelatex -V colorlinks=true -V linkcolor=blue -V emojifont=Segoe UI Emoji -V emojifont=EmojiOne Color -V urlcolor=red-V toccolor=gray -V CJKmainfont=Noto Serif CJK SC -V CJKmonofont=Noto Serif CJK SC -V mainfont=DejaVu Sans -Vmonofont=DejaVu Sans -V geometry:top=1.2cm,bottom=1.2cm,left=1.2cm,right=1.2cm --highlight-style=tango
    #cmd = ["pandoc", str(tmp_md), "-o", str(tmp_pdf), "--pdf-engine=xelatex", "-V", "CJKmainfont='Noto Serif CJK TC'",
    #"-V", "CJKmonofont='Noto Sans Mono CJK TC'",
    #"-V", "mainfont='DejaVu Sans'", '-V', "monofont='DejaVu Sans'",
    #"--highlight-style=tango"]
    #狀態.text(' '.join(cmd))
    #rslt=subprocess.run(cmd, check=True)
    #狀態.code([rslt.stdout, rslt.stderr])
    #pdf_bytes = tmp_pdf.read_bytes()
    return 暫匹.read_bytes()
        #cmd = ["pandoc", str(tmp_md), "-o", tmp_pdf.name,
        #       "--pdf-engine=xelatex",
        #       '-V geometry:a4paper,portrait --toc --toc-depth=3 -N --highlight-style tango -V colorlinks=true -V linkcolor=blue -V citecolor=green -V urlcolor=cyan',
        #       "-V", "mainfont='Noto Sans CJK SC'",
        #       "-V", "monofont='Noto Sans CJK SC'",
        #       "--highlight-style=tango"]
        #cmd = ["pandoc", str(tmp_md), "-o", str(tmp_pdf), "--pdf-engine=xelatex",
        #"-V", "CJKmainfont=Noto Serif CJK TC",      # 中文襯線（正文）
        #"-V", "CJKmonofont=Noto Sans Mono CJK TC",  # 中文等寬（框線+程式碼）
        #"-V", "mainfont=DejaVu Sans",
        #"-V", "monofont=DejaVu Sans",
        #"--highlight-style=tango" ]
        #cmd = [
        #    "pandoc", str(tmp_md),
        #    "-o", str(tmp_pdf),
        #    "--pdf-engine=xelatex",
        #    "-V", "CJKmainfont=Noto Serif CJK SC",
        #    "-V", "CJKmonofont=Noto Serif CJK SC",
        #    "-V", "mainfont=DejaVu Sans",
        #    "-V", "monofont=DejaVu Sans",
        #    "--highlight-style=tango"
        #]
        #subprocess.run(cmd, check=True, capture_output=True)
        #return tmp_pdf.read_bytes()

with sidebar: # ---------- 側邊欄：導航 ----------
    root_input = text_input("絕對路徑：", value=str(Path.cwd()))
    if button("設定根") or "root_dir" not in session_state:
        session_state.root_dir = Path(root_input).expanduser().resolve()
        session_state.cur_dir  = session_state.root_dir   # 目前瀏覽位置
        session_state.history  = load_history()              # 讀歷史（重開頁面時）

    root: Path = session_state.get("root_dir")
    if not root:
        stop()

    #success(f"根目錄：{root}")

    #header("2️⃣ 瀏覽 / 選檔")
    cur: Path = session_state.cur_dir

    # 顯示目前路徑 & 上層按鈕
    caption(f"目前資料夾：{cur.relative_to(root)}")
    if cur != root:
        if button("⬆ 返回上層"):
            session_state.cur_dir = cur.parent
            rerun()

    # 列出子資料夾 + .md 檔
    folders = sorted([p for p in cur.iterdir() if p.is_dir()])
    檔案= sorted([p for p in cur.iterdir() if p.is_file()]) # and p.suffix.lower()==".md"

    for f in folders:
        if button(f"📁 {f.name}/", key=f"dir_{f}"):
            session_state.cur_dir = f
            rerun()

    for 檔 in 檔案:
        if button(f"📄 {檔.name}", key=f"{檔}"):
            # 載入檔案 & 寫入歷史
            mimeType=session_state['mimeType']=麥魔(檔)
            #if 'pdf' in mimeType:
            #  pdfVWR(檔)
            #elif 'image' in mimeType:
            #  stImage(檔)
            #elif 'video' in mimeType:
            #  video(檔)
            #elif 'html' in mimeType:
            #  markdown(檔)
            #elif 麥魔(檔) in ['.py', 'txt']:
            #  markdown(檔)
            #elif 'markdown' in mimeType:
            #  markdown(檔)
            狀態.code(檔)
            if 'pdf' in mimeType:
              #code(mimeType)
              content = 檔.read_bytes()
              #PDFVWR(檔)
            else:
              content = 檔.read_text(encoding="utf-8")
              session_state.current_content = content
            session_state.current_path = str(檔)
            save_history(str(檔), content)
# ---------- 主畫面：編輯 / 預覽 / PDF ----------
if session_state.get("current_path"):
    檔 = Path(session_state.current_path)
    mimeType=session_state['mimeType']
    狀態.code(檔)
    if 'pdf' in mimeType:
      PDFVWR(檔)
      stop()
    elif 檔.is_file:
      content = session_state.current_content
      sidebar.subheader(f"編輯中：{檔.relative_to(root)}")

    # 使用 tabs 讓畫面簡潔
    #tab_edit, tab_pdf = tabs(["✏️ 編輯預覽", "📄 PDF"])

    #with tab_edit:
    # 即時同步回 session

    col1, col2 = columns([2, 4])
    with col1:
      修改 = text_area("編輯區", value=content, height='stretch', placeholder='編輯區')
      if button("💾 存檔（覆蓋）"):
          檔.write_text(修改, encoding="utf-8")
          success("已存檔！")
    with col2:
#狀態=empty()
    #with tab_pdf:
      #左, 右=columns([1, 9])  #['產生', '預視']
      session_state.pdf_name=PDF檔名=檔.with_suffix('.pdf')  #stem + ".pdf"
      #狀態.code(PDF檔名)
      #with 左:
          #if button("🔄 產生 PDF"):
              #with spinner("Pandoc 轉檔中…"):
          #if "pdf_bytes" not in session_state:
      session_state.pdf_bytes=pdf內容=馬至匹(檔, 修改)
      b64=session_state['PDF內容']=b64encode(pdf內容).decode()
      download_button(label="⬇ 下載 PDF", data=pdf內容, file_name=str(PDF檔名), mime="application/pdf")
      #with 右:
      if "PDF內容" in session_state:
        PDF編碼=session_state['PDF內容']
        #PDF檔名=BytesIO(PDF編碼.encode('utf-8'))
        PDFVWR(PDF檔名)
        #markdown(
        #    f'<iframe src="data:application/pdf;base64,{PDF編碼}" '
        #    'width="100%" height="800" type="application/pdf"></iframe>',
        #    unsafe_allow_html=True
        #)
        #pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
        #pdfVWR(session_state.pdf_name)
      #markdown(修改, unsafe_allow_html=True)
      new_name = text_input("另存新檔名（含 .md）：", value="copy.md")
      if button("另存新檔"):
          save_path = 檔.parent/new_name
          save_path.write_text(修改, encoding="utf-8")
          success(f"已另存為 {save_path.relative_to(root)}")
      session_state.current_content = 修改
      save_history(str(檔), 修改)
else:
    info("請從左側樹狀目錄選擇一個 Markdown 檔案")

with sidebar:
  title("📂 樹狀 MD 總管 + 歷史編輯器")
  subheader("1️⃣ 設定根目錄")
