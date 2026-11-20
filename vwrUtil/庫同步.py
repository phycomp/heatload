from psycopg import connect as pgCnnct
from pathlib import Path
from streamlit import empty
#from streamlit import secrets, cache_data as stCache
from tomllib import load as tmlLoad
from re import search
狀態=empty()

def zip2pgConn(db):
  return ' '.join(['='.join(v) for v in list(db)])

#@stCache(hash_funcs={"_thread.RLock":lambda _:None, "builtins.weakref":lambda _:None})
#@stCache(hash_funcs={"_thread.RLock":lambda _:None})
def 祕庫():  #astpack
  祕=Path('~/.streamlit/secrets.toml')
  with open(祕.expanduser(), 'rb') as fin:
    dbConfig=tmlLoad(fin)
  return dbConfig

def 連線(db=None):
  祕=祕庫()
  conn=pgCnnct(**祕[db])
  return conn

def runQuery(conn, query, commitType='select'):     #db='postgres', mode='scrt', 表=None 在每次查詢後都明確提交或回滾
  with conn.cursor() as cur:
    try:
      cur.execute(query)
      if commitType == 'select':
        result = cur.fetchall()
        return result
      else:
        conn.commit()
        return cur.rowcount
    except Exception as e:
      conn.rollback()
      raise e
    finally:
      if commitType == 'select': conn.commit()  # 即使是 SELECT 也要提交
  #  if commitType=='select':
  #    cur.execute(query)
  #    return cur.fetchall()
  #  else:
  #    cur.execute(query)
  #    conn.commit()

def dbCLMN(tblSchm='public', tblName=None, db=None): #, mode=None
  clmnQuery=f'''select column_name from information_schema.columns WHERE table_schema = '{tblSchm}' AND table_name = '{tblName}';'''
  with 連線(db=db) as conn:
    CLMN=runQuery(conn, clmnQuery)
  #狀態.code(CLMN)
  CLMN=map(lambda x:x[0], CLMN)#[v[0] for v in CLMN]
  #res = any(ele.isupper() for ele in test_str)
  newCLMN=[]
  for clmn in CLMN:
    if any(e.isupper() for e in clmn): newCLMN.append(f'"{clmn}"')
    #if search('[A-Z]', clmn):newCLMN.append(f'"{clmn}"')
    else: newCLMN.append(clmn)
  return newCLMN

def clmnDF(CLMN):
  return [clmn.replace('"', '')for clmn in CLMN]
