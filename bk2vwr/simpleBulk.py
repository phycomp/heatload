from typing import List, Dict, Any, Optional
from bkUtil import rcrsvFiles
from streamlit import radio, code, sidebar
from glob import glob
import asyncio
import pandas as pd
import os
from async_database import AsyncDatabaseManager
import json

async def simple_bulk_import(directory: str, pttrn=None):
    """使用簡單的批量插入方法匯入資料"""
    db_manager = AsyncDatabaseManager(db='bk2')
    
    # 確保資料表存在
    await db_manager.create_tables()
    
    # 收集所有檔案
    all_files, PTTRN =[], ["*/*.xlsx", "*/*.xls", "*/*.txt", "*/*.csv"]
    for pttrn in PTTRN:
      目錄結構=rcrsvFiles(directory, pttrn='*.txt')
      all_files.extends(目錄結構)
    #for pattern in patterns:
    #    files = glob(os.path.join(directory, '**', pattern), recursive=True)
    #    all_files.extend(files)
    
    #code(f"找到 {len(all_files)} 個檔案進行匯入")
    
    all_data = []
    
    for i, file_path in enumerate(all_files):
        #code(f"處理 {i+1}/{len(all_files)}: {os.path.basename(file_path)}")
        
        try:
            data = []
            
            code(['file_path', file_path])
            if file_path.endswith(('.xlsx', '.xls')):
                data = await prepare_excel_data(file_path)
            elif file_path.endswith('.txt'):
                data = await prepare_txt_data(file_path)
            elif file_path.endswith('.csv'):
                data = await prepare_csv_data(file_path)
            
            all_data.extend(data)
                
        except Exception as e:
            code(f"處理檔案 {file_path} 時發生錯誤: {e}")
    
    # 使用高效的批量插入
    if all_data:
        #code(f"開始匯入 {len(all_data)} 筆記錄...")
        await db_manager.efficient_bulk_insert(all_data, 'raw_data_import', batch_size=500)
        code("批量匯入完成!")
    else:
        code("沒有找到可匯入的數據")

async def prepare_excel_data(file_path: str) -> List[Dict]:
    """準備 Excel 數據"""
    data = []
    try:
        xl = pd.ExcelFile(file_path)
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 只取前100行避免數據過大
            for _, row in df.head(100).iterrows():
                data.append({
                    'source_file': os.path.basename(file_path),
                    'source_type': 'excel',
                    'raw_data': {
                        'sheet_name': sheet_name,
                        'data': row.where(pd.notna(row), None).to_dict()
                    }
                })
    except Exception as e:
        code(f"準備 Excel 數據時發生錯誤: {e}")
    
    #code(['file_path', file_path, data])
    return data

async def prepare_txt_data(file_path: str) -> List[Dict]:
    """準備 TXT 數據"""
    data = []
    #code(['file_path', file_path])
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 只取前100行避免數據過大
        for i, line in enumerate(lines[:100]):
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
        code(f"準備 TXT 數據時發生錯誤: {e}")
    
    return data

async def prepare_csv_data(file_path: str) -> List[Dict]:
    """準備 CSV 數據"""
    data = []
    try:
        df = pd.read_csv(file_path)
        
        # 只取前100行避免數據過大
        for _, row in df.head(100).iterrows():
            data.append({
                'source_file': os.path.basename(file_path),
                'source_type': 'csv',
                'raw_data': row.where(pd.notna(row), None).to_dict()
            })
    except Exception as e:
        code(f"準備 CSV 數據時發生錯誤: {e}")
    
    return data

if __name__ == "__main__":
    #import sys
    #directory = sys.argv[1] if len(sys.argv) > 1 else "TDRReportRawData"
    目錄夾=['TDRReportRawData', 'TDR_Fail', 'SMPlug2PlugCable80mm']
    with sidebar:
      目錄=radio('目錄夾', 目錄夾, horizontal=True, index=0)
    if 目錄:
      asyncio.run(simple_bulk_import(目錄))
