import asyncpg
import psycopg
import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from streamlit import secrets

class AsyncDatabaseManager:
    def __init__(self, db=None):
        self.db_config = dict(secrets[db]) #{ 'host': 'localhost', 'database': 'test_data', 'user': 'postgres', 'password': 'password', 'port': 5432 }
        print(['db_config', self.db_config])
    
    async def get_async_connection(self) -> asyncpg.Connection:
        """獲取異步連接"""
        return await asyncpg.connect(**self.db_config)
    
    def get_sync_connection(self) -> psycopg.Connection:
        """獲取同步連接（用於 \COPY 操作）"""
        return psycopg.connect(**self.db_config)
    
    async def create_tables(self):
        """異步建立資料表"""
        commands = [
            # Excel 資料表
            """
            CREATE TABLE IF NOT EXISTS excel_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(500) NOT NULL,
                file_path VARCHAR(1000) NOT NULL,
                file_size BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename, file_path)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS excel_sheets (
                id SERIAL PRIMARY KEY,
                excel_file_id INTEGER REFERENCES excel_files(id),
                sheet_name VARCHAR(255) NOT NULL,
                row_count INTEGER,
                column_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS excel_columns (
                id SERIAL PRIMARY KEY,
                sheet_id INTEGER REFERENCES excel_sheets(id),
                column_name VARCHAR(255) NOT NULL,
                data_type VARCHAR(50),
                position_index INTEGER,
                non_null_count INTEGER,
                null_count INTEGER,
                unique_count INTEGER,
                sample_values JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # TXT 測試結果資料表
            """
            CREATE TABLE IF NOT EXISTS test_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(500) NOT NULL,
                file_path VARCHAR(1000) NOT NULL,
                file_type VARCHAR(50),
                test_result VARCHAR(10),
                test_date DATE,
                test_time TIME,
                test_parameters JSONB,
                file_size BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename, file_path)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS test_data (
                id SERIAL PRIMARY KEY,
                test_file_id INTEGER REFERENCES test_files(id),
                row_index INTEGER,
                data_values JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # CSV 阻抗測試資料表
            """
            CREATE TABLE IF NOT EXISTS impedance_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(500) NOT NULL,
                file_path VARCHAR(1000) NOT NULL,
                tx_positive FLOAT,
                rx_positive FLOAT,
                tx_negative FLOAT,
                rx_negative FLOAT,
                channel INTEGER,
                trace INTEGER,
                tdd_value FLOAT,
                file_size BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename, file_path)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS impedance_data (
                id SERIAL PRIMARY KEY,
                impedance_file_id INTEGER REFERENCES impedance_files(id),
                frequency FLOAT,
                amplitude FLOAT,
                phase FLOAT,
                impedance FLOAT,
                voltage FLOAT,
                current FLOAT,
                row_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # 通用資料表（用於 \COPY 匯入）
            """
            CREATE TABLE IF NOT EXISTS raw_data_import (
                id SERIAL PRIMARY KEY,
                source_file VARCHAR(500),
                source_type VARCHAR(50),
                import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            )
            """
        ]
        
        conn = await self.get_async_connection()
        try:
            for command in commands:
                await conn.execute(command)
            logger.info("所有資料表建立完成")
        except Exception as e:
            logger.error(f"建立資料表時發生錯誤: {e}")
        finally:
            await conn.close()
    
    async def analyze_excel_structure(self, file_path: str) -> Dict[str, Any]:
        """分析 Excel 檔案結構"""
        analysis_result = {
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'sheets': []
        }
        
        try:
            xl = pd.ExcelFile(file_path)
            
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_info = {
                    'sheet_name': sheet_name,
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': []
                }
                
                for i, col_name in enumerate(df.columns):
                    col_data = df[col_name]
                    non_null_count = col_data.count()
                    null_count = col_data.isnull().sum()
                    unique_count = col_data.nunique()
                    
                    # 取前5個非空值作為樣本
                    sample_values = col_data.dropna().head(5).tolist()
                    
                    column_info = {
                        'column_name': str(col_name),
                        'position_index': i,
                        'data_type': str(col_data.dtype),
                        'non_null_count': int(non_null_count),
                        'null_count': int(null_count),
                        'unique_count': int(unique_count),
                        'sample_values': sample_values
                    }
                    
                    sheet_info['columns'].append(column_info)
                
                analysis_result['sheets'].append(sheet_info)
                
        except Exception as e:
            logger.error(f"分析 Excel 檔案 {file_path} 時發生錯誤: {e}")
        
        return analysis_result
    
    async def store_excel_analysis(self, analysis_result: Dict[str, Any]):
        """儲存 Excel 分析結果到資料庫"""
        conn = await self.get_async_connection()
        try:
            # 插入 excel_files 記錄
            file_id = await conn.fetchval("""
                INSERT INTO excel_files (filename, file_path, file_size)
                VALUES ($1, $2, $3)
                ON CONFLICT (filename, file_path) DO UPDATE SET
                file_size = EXCLUDED.file_size
                RETURNING id
            """, analysis_result['filename'], analysis_result['file_path'], 
                analysis_result['file_size'])
            
            # 插入 sheet 和 column 資訊
            for sheet_info in analysis_result['sheets']:
                sheet_id = await conn.fetchval("""
                    INSERT INTO excel_sheets 
                    (excel_file_id, sheet_name, row_count, column_count)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, file_id, sheet_info['sheet_name'], 
                    sheet_info['row_count'], sheet_info['column_count'])
                
                for col_info in sheet_info['columns']:
                    await conn.execute("""
                        INSERT INTO excel_columns 
                        (sheet_id, column_name, data_type, position_index, 
                         non_null_count, null_count, unique_count, sample_values)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, sheet_id, col_info['column_name'], col_info['data_type'],
                        col_info['position_index'], col_info['non_null_count'],
                        col_info['null_count'], col_info['unique_count'],
                        json.dumps(col_info['sample_values']))
            
            logger.info(f"成功儲存 Excel 分析結果: {analysis_result['filename']}")
            
        except Exception as e:
            logger.error(f"儲存 Excel 分析結果時發生錯誤: {e}")
        finally:
            await conn.close()
    
    async def analyze_txt_structure(self, file_path: str) -> Dict[str, Any]:
        """分析 TXT 檔案結構"""
        analysis_result = {
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'file_type': 'TXT',
            'test_result': None,
            'test_date': None,
            'test_time': None,
            'test_parameters': {},
            'data_rows': []
        }
        
        try:
            # 解析檔案名稱
            filename = os.path.basename(file_path)
            if 'PASS' in filename:
                analysis_result['test_result'] = 'PASS'
            elif 'FAIL' in filename:
                analysis_result['test_result'] = 'FAIL'
            
            # 解析日期時間
            import re
            date_match = re.search(r'(\d{8})', filename)
            time_match = re.search(r'(\d{6})', filename)
            
            if date_match:
                date_str = date_match.group(1)
                analysis_result['test_date'] = datetime.strptime(date_str, '%Y%m%d').date()
            
            if time_match:
                time_str = time_match.group(1)
                analysis_result['test_time'] = datetime.strptime(time_str, '%H%M%S').time()
            
            # 讀取檔案內容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 分析數據行
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    # 嘗試解析數據
                    values = re.split(r'\s+|,|\t', line)
                    numeric_values = []
                    text_values = []
                    
                    for val in values:
                        if val:
                            try:
                                numeric_val = float(val)
                                numeric_values.append(numeric_val)
                            except ValueError:
                                text_values.append(val)
                    
                    row_data = {
                        'row_index': i,
                        'raw_line': line,
                        'numeric_values': numeric_values,
                        'text_values': text_values,
                        'value_count': len(values)
                    }
                    
                    analysis_result['data_rows'].append(row_data)
            
        except Exception as e:
            logger.error(f"分析 TXT 檔案 {file_path} 時發生錯誤: {e}")
        
        return analysis_result
    
    async def store_txt_analysis(self, analysis_result: Dict[str, Any]):
        """儲存 TXT 分析結果到資料庫"""
        conn = await self.get_async_connection()
        try:
            # 插入 test_files 記錄
            file_id = await conn.fetchval("""
                INSERT INTO test_files 
                (filename, file_path, file_type, test_result, test_date, test_time, test_parameters, file_size)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (filename, file_path) DO UPDATE SET
                file_size = EXCLUDED.file_size,
                test_parameters = EXCLUDED.test_parameters
                RETURNING id
            """, analysis_result['filename'], analysis_result['file_path'],
                analysis_result['file_type'], analysis_result['test_result'],
                analysis_result['test_date'], analysis_result['test_time'],
                json.dumps(analysis_result['test_parameters']), 
                analysis_result['file_size'])
            
            # 插入測試數據
            for row_data in analysis_result['data_rows']:
                await conn.execute("""
                    INSERT INTO test_data 
                    (test_file_id, row_index, data_values)
                    VALUES ($1, $2, $3)
                """, file_id, row_data['row_index'], 
                    json.dumps({
                        'raw_line': row_data['raw_line'],
                        'numeric_values': row_data['numeric_values'],
                        'text_values': row_data['text_values'],
                        'value_count': row_data['value_count']
                    }))
            
            logger.info(f"成功儲存 TXT 分析結果: {analysis_result['filename']}")
            
        except Exception as e:
            logger.error(f"儲存 TXT 分析結果時發生錯誤: {e}")
        finally:
            await conn.close()
    
    async def analyze_csv_structure(self, file_path: str) -> Dict[str, Any]:
        """分析 CSV 檔案結構"""
        analysis_result = {
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'tx_positive': None,
            'rx_positive': None,
            'tx_negative': None,
            'rx_negative': None,
            'channel': None,
            'trace': None,
            'tdd_value': None,
            'columns': [],
            'data_rows': []
        }
        
        try:
            # 解析檔案名稱參數
            filename = os.path.basename(file_path)
            import re
            pattern = r'Tx(\d+)\+_Rx(\d+)\+_Tx(\d+)\-?_Rx(\d+)\-?_Ch(\d+)_Tr(\d+)_TDD(\d+)'
            match = re.search(pattern, filename)
            
            if match:
                analysis_result['tx_positive'] = float(match.group(1))
                analysis_result['rx_positive'] = float(match.group(2))
                analysis_result['tx_negative'] = float(match.group(3))
                analysis_result['rx_negative'] = float(match.group(4))
                analysis_result['channel'] = int(match.group(5))
                analysis_result['trace'] = int(match.group(6))
                analysis_result['tdd_value'] = float(match.group(7))
            
            # 讀取 CSV 檔案
            df = pd.read_csv(file_path)
            
            # 分析欄位
            for col_name in df.columns:
                col_data = df[col_name]
                analysis_result['columns'].append({
                    'column_name': str(col_name),
                    'data_type': str(col_data.dtype),
                    'non_null_count': int(col_data.count()),
                    'null_count': int(col_data.isnull().sum()),
                    'sample_values': col_data.dropna().head(3).tolist()
                })
            
            # 儲取數據行（前100行）
            for i, row in df.head(100).iterrows():
                row_data = {}
                for col in df.columns:
                    row_data[col] = row[col] if pd.notna(row[col]) else None
                analysis_result['data_rows'].append(row_data)
                
        except Exception as e:
            logger.error(f"分析 CSV 檔案 {file_path} 時發生錯誤: {e}")
        
        return analysis_result
    
    async def store_csv_analysis(self, analysis_result: Dict[str, Any]):
        """儲存 CSV 分析結果到資料庫"""
        conn = await self.get_async_connection()
        try:
            # 插入 impedance_files 記錄
            file_id = await conn.fetchval("""
                INSERT INTO impedance_files 
                (filename, file_path, tx_positive, rx_positive, tx_negative, 
                 rx_negative, channel, trace, tdd_value, file_size)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (filename, file_path) DO UPDATE SET
                file_size = EXCLUDED.file_size
                RETURNING id
            """, analysis_result['filename'], analysis_result['file_path'],
                analysis_result['tx_positive'], analysis_result['rx_positive'],
                analysis_result['tx_negative'], analysis_result['rx_negative'],
                analysis_result['channel'], analysis_result['trace'],
                analysis_result['tdd_value'], analysis_result['file_size'])
            
            # 插入阻抗數據
            for row_data in analysis_result['data_rows']:
                # 根據常見的欄位名稱映射
                frequency = row_data.get('frequency') or row_data.get('Frequency') or row_data.get('Freq')
                amplitude = row_data.get('amplitude') or row_data.get('Amplitude') or row_data.get('Amp')
                phase = row_data.get('phase') or row_data.get('Phase')
                impedance = row_data.get('impedance') or row_data.get('Impedance') or row_data.get('Z')
                
                await conn.execute("""
                    INSERT INTO impedance_data 
                    (impedance_file_id, frequency, amplitude, phase, impedance, row_index)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, file_id, frequency, amplitude, phase, impedance, 
                    len(analysis_result['data_rows']))
            
            logger.info(f"成功儲存 CSV 分析結果: {analysis_result['filename']}")
            
        except Exception as e:
            logger.error(f"儲存 CSV 分析結果時發生錯誤: {e}")
        finally:
            await conn.close()
    
    def copy_csv_to_database(self, csv_file_path: str, table_name: str = "raw_data_import"):
        """使用 \\COPY 命令匯入 CSV 檔案"""
        conn = self.get_sync_connection()
        try:
            with conn.cursor() as cur:
                # 建立臨時表
                temp_table = f"temp_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                cur.execute(f"""
                    CREATE TEMP TABLE {temp_table} AS 
                    SELECT * FROM {table_name} WHERE 1=0
                """)
                
                # 使用 COPY 匯入數據
                with open(csv_file_path, 'r') as f:
                    cur.copy_expert(f"""
                        COPY {temp_table} (source_file, source_type, raw_data)
                        FROM STDIN WITH CSV HEADER
                    """, f)
                
                # 插入到目標表
                cur.execute(f"""
                    INSERT INTO {table_name} (source_file, source_type, raw_data)
                    SELECT source_file, source_type, raw_data FROM {temp_table}
                """)
                
                conn.commit()
                logger.info(f"成功使用 COPY 匯入 CSV 檔案: {csv_file_path}")
                
        except Exception as e:
            logger.error(f"使用 COPY 匯入 CSV 時發生錯誤: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    async def bulk_analyze_files(self, directory: str, file_patterns: List[str]):
        """批量分析檔案"""
        import glob
        
        tasks = []
        
        for pattern in file_patterns:
            files = glob.glob(os.path.join(directory, '**', pattern), recursive=True)
            
            for file_path in files:
                if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                    task = asyncio.create_task(
                        self.analyze_and_store_excel(file_path)
                    )
                    tasks.append(task)
                
                elif file_path.endswith('.txt'):
                    task = asyncio.create_task(
                        self.analyze_and_store_txt(file_path)
                    )
                    tasks.append(task)
                
                elif file_path.endswith('.csv'):
                    task = asyncio.create_task(
                        self.analyze_and_store_csv(file_path)
                    )
                    tasks.append(task)
        
        # 等待所有任務完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def analyze_and_store_excel(self, file_path: str):
        """分析並儲存 Excel 檔案"""
        analysis = await self.analyze_excel_structure(file_path)
        await self.store_excel_analysis(analysis)
    
    async def analyze_and_store_txt(self, file_path: str):
        """分析並儲存 TXT 檔案"""
        analysis = await self.analyze_txt_structure(file_path)
        await self.store_txt_analysis(analysis)
    
    async def analyze_and_store_csv(self, file_path: str):
        """分析並儲存 CSV 檔案"""
        analysis = await self.analyze_csv_structure(file_path)
        await self.store_csv_analysis(analysis)
    
    # CRUD 操作
    async def get_excel_files(self) -> List[Dict]:
        """獲取所有 Excel 檔案資訊"""
        conn = await self.get_async_connection()
        try:
            rows = await conn.fetch("""
                SELECT ef.*, COUNT(es.id) as sheet_count
                FROM excel_files ef
                LEFT JOIN excel_sheets es ON ef.id = es.excel_file_id
                GROUP BY ef.id
                ORDER BY ef.created_at DESC
            """)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_excel_sheets(self, file_id: int) -> List[Dict]:
        """獲取 Excel 檔案的工作表"""
        conn = await self.get_async_connection()
        try:
            rows = await conn.fetch("""
                SELECT es.*, COUNT(ec.id) as column_count
                FROM excel_sheets es
                LEFT JOIN excel_columns ec ON es.id = ec.sheet_id
                WHERE es.excel_file_id = $1
                GROUP BY es.id
                ORDER BY es.id
            """, file_id)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_test_files(self, result_type: str = None) -> List[Dict]:
        """獲取測試檔案"""
        conn = await self.get_async_connection()
        try:
            if result_type:
                rows = await conn.fetch("""
                    SELECT * FROM test_files 
                    WHERE test_result = $1
                    ORDER BY test_date DESC, test_time DESC
                """, result_type)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM test_files 
                    ORDER BY test_date DESC, test_time DESC
                """)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def delete_file_analysis(self, file_type: str, file_path: str):
        """刪除檔案分析結果"""
        conn = await self.get_async_connection()
        try:
            if file_type == 'excel':
                await conn.execute("""
                    DELETE FROM excel_files WHERE file_path = $1
                """, file_path)
            elif file_type == 'test':
                await conn.execute("""
                    DELETE FROM test_files WHERE file_path = $1
                """, file_path)
            elif file_type == 'impedance':
                await conn.execute("""
                    DELETE FROM impedance_files WHERE file_path = $1
                """, file_path)
            
            logger.info(f"成功刪除檔案分析: {file_path}")
        except Exception as e:
            logger.error(f"刪除檔案分析時發生錯誤: {e}")
        finally:
            await conn.close()
