def 網絡(pk='1'):
  conn=pgCnnct(**dbConfig)
  狀態=empty()
  with conn.cursor() as cur:
      cur.execute(f"""SELECT 檔,皮可 FROM "snp皮可" WHERE id={pk}""")
      #if row is None: return None
      檔名,緩衝=cur.fetchone()
      狀態.code([檔名, 緩衝])
      #緩衝=gzDcmprss(緩衝)
      net=pcklLoads(緩衝)
      return net
      #buf.name=檔名
      #buf.seek(0)
      #狀態.code(data)
      #except Exception as e: 狀態.code(e)
      try: net = Network(buf)
      except Exception as e:
        pass
        #狀態.code([">>> 真正錯誤：", e])


