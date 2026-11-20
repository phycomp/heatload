from typing import List, Dict, Any, Optional
import asyncio
import pandas as pd
import os
import glob
from async_database import AsyncDatabaseManager
import tempfile
import json

async def bulk_import_with_copy_fixed(directory: str):
    """使用修正的 COPY 方法批量匯入資料"""
    db_manager = AsyncDatabaseManager()
    
    # 確保資料表存在
    await db_manager.create_tables()
    
    # 收集所有檔案
    patterns = ["*.xlsx", "*.xls", "PASS__*.txt", "FAIL__*.txt", "*_Debug.txt", "*impedance*.csv"]
    all_files = []
    
    for pattern in patterns:
        files = glob.glob(os.path.join(directory, '**', pattern), recursive=True)
        all_files.extend(files)
    
    print(f"找到 {len(all_files)} 個檔案進行匯入")
    
    for i, file_path in enumerate(all_files):
        print(f"處理 {i+1}/{len(all_files)}: {os.path.basename(file_path)}")
        
        try:
            # 準備數據
            data = []
            source_type = ""
            
            if file_path.endswith(('.xlsx', '.xls')):
                source_type = "excel"
                data = await prepare_excel_data(file_path)
            elif file_path.endswith('.txt'):
                source_type = "txt"
                data = await prepare_txt_data(file_path)
            elif file_path.endswith('.csv'):
                source_type = "csv"
                data = await prepare_csv_data(file_path)
            
            if data:
                # 使用批量複製方法
                columns = ['source_file', 'source_type', 'raw_data']
                await db_manager.export_to_csv_and_copy(data, 'raw_data_import', columns)
                
        except Exception as e:
            print(f"匯入檔案 {file_path} 時發生錯誤: {e}")
    
    print("批量匯入完成!")

async def prepare_excel_data(file_path: str) -> List[Dict]:
    """準備 Excel 數據"""
    data = []
    try:
        xl = pd.ExcelFile(file_path)
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            for _, row in df.iterrows():
                data.append({
                    'source_file': os.path.basename(file_path),
                    'source_type': 'excel',
                    'raw_data': {
                        'sheet_name': sheet_name,
                        'data': row.where(pd.notna(row), None).to_dict()
                    }
                })
    except Exception as e:
        print(f"準備 Excel 數據時發生錯誤: {e}")
    
    return data

async def prepare_txt_data(file_path: str) -> List[Dict]:
    """準備 TXT 數據"""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                data.append({
                    'source_file': os.path.basename(file_path),
                    'source_type': 'txt',
                    'raw_data': {
                        'line_number': i,
                        'content': line.strip(),
                        'length': len(line)
                    }
                })
    except Exception as e:
        print(f"準備 TXT 數據時發生錯誤: {e}")
    
    return data

async def prepare_csv_data(file_path: str) -> List[Dict]:
    """準備 CSV 數據"""
    data = []
    try:
        df = pd.read_csv(file_path)
        
        for _, row in df.iterrows():
            data.append({
                'source_file': os.path.basename(file_path),
                'source_type': 'csv',
                'raw_data': row.where(pd.notna(row), None).to_dict()
            })
    except Exception as e:
        print(f"準備 CSV 數據時發生錯誤: {e}")
    
    return data

if __name__ == "__main__":
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else "TDRReportRawData"
    asyncio.run(bulk_import_with_copy_fixed(directory))
