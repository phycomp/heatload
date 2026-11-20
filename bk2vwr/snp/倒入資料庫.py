# build_astbk.py
import os, glob, 
from datetime import datetime
import numpy as np
from psycopg import connect as pgCnnct
:dbConfig={'port':5432, 'user':'postgres', 'password':'postgres', 'dbname':'astpack', 'host' :'192.168.13.127'}
import skrf as rf
import psycopg2, json
from tqdm import tqdm

def to_pg_array(arr):
    """把 numpy 陣列轉成 PostgreSQL 字面量格式"""
    return str(arr.tolist()).replace('[','{').replace(']','}')

def 匯入(cur, 檔):
    net = Network(檔)
    n = net.nports
    freq = net.frequency.f
    s = net.s                        # shape=(n_freq, n_out, n_in)
    s_flat = s.reshape(s.shape[0], -1) # 攤平成 2-D：每列 n_freq 點，每行 n_ports*n_ports 個複數
    file_name = 檔.name   #os.path.basename()
    日期  = datetime.fromtimestamp(os.path.getmtime(檔)).date()
    cur.execute(
        """INSERT INTO snp_files(file_name,file_path,mfg_date,n_ports,freq_hz,s_complex)
           VALUES (%s,%s,%s,%s,%s,%s)
           ON CONFLICT (file_name,mfg_date) DO NOTHING""",
        (檔.name, 檔.parent, 日期, n,
         to_pg_array(freq),           # 1-D double[]
         to_pg_array(s_flat))         # 2-D complex[]
    )
    cur.execute(
        "INSERT INTO snp_upload_log(file_path,username) VALUES (%s,%s)",
        (path, os.getenv("USER","unknown"))
    )
MENU, 表單=[], ['倒入', '', '']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[1]: #
  pass
elif menu==MENU[0]: #倒入
  根=Path('FAIL__20251230_141506_13cm')
  檔=radio('檔案', 根.rglob("*.s4p"), horizontal=True)
  if 檔:
    with pgCnnct(**dbConfig) as conn:
      with conn.cursor() as cur:
        for fp in tqdm(根.rglob("*.s4p")files):
            try: 匯入(cur, fp)
            except Exception as e: print("跳過", fp, e)
        conn.commit()
    print("匯入完成，共", len(files), "筆")

if __name__ == "__main__":
    main()
