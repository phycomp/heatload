import asyncio
#from streamlit import code
from glob import glob
import pandas as pd
import os
from async_database import AsyncDatabaseManager
from async_file_processor import AsyncFileProcessor
from tempfile import NamedTemporaryFile

async def bulk_import_with_copy(directory: str):
    """使用 \\COPY 批量匯入資料"""
    db_manager = AsyncDatabaseManager(db='bk2')
    file_processor = AsyncFileProcessor()
    
    # 確保資料表存在
    await db_manager.create_tables()
    
    # 收集所有檔案
    patterns = ["*.xlsx", "*.xls", "*.txt", "*.csv"]
    all_files = []
    
    for pattern in patterns:
        files = glob(os.path.join(directory, '**', pattern), recursive=True)
        print(['files=', files])
        all_files.extend(files)
    
    print(f"找到 {len(all_files)} 個檔案進行匯入")
    
    # 為每個檔案建立 CSV 並使用 COPY 匯入
    for i, file_path in enumerate(all_files):
            print(f"處理 {i+1}/{len(all_files)}: {os.path.basename(file_path)}")
        
        #try:
            # 建立臨時 CSV 檔案
            with NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                temp_csv_path = temp_file.name
            
            # 根據檔案類型處理數據
            if file_path.endswith(('.xlsx', '.xls')):
                await process_excel_for_copy(file_path, temp_csv_path)
            elif file_path.endswith('.txt'):
                await process_txt_for_copy(file_path, temp_csv_path)
            elif file_path.endswith('.csv'):
                await process_csv_for_copy(file_path, temp_csv_path)
            
            # 使用 COPY 匯入
            print(['temp_csv_path,', temp_csv_path])
            db_manager.copy_csv_to_database(temp_csv_path)
            
            # 清理臨時檔案
            os.unlink(temp_csv_path)
            
        #except Exception as e:
        #    print(f"匯入檔案 {file_path} 時發生錯誤: {e}")
    
    print("批量匯入完成!")

async def process_excel_for_copy(excel_path: str, output_csv: str):
    """處理 Excel 檔案供 COPY 使用"""
    data = []
    
    try:
        xl = pd.ExcelFile(excel_path)
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            for _, row in df.iterrows():
                data.append({
                    'source_file': os.path.basename(excel_path),
                    'source_type': 'excel',
                    'raw_data': row.to_dict()
                })
    except Exception as e:
        print(f"處理 Excel 檔案 {excel_path} 時發生錯誤: {e}")
    
    # 匯出為 CSV
    if data:
        df_export = pd.DataFrame(data)
        df_export.to_csv(output_csv, index=False)

async def process_txt_for_copy(txt_path: str, output_csv: str):
    """處理 TXT 檔案供 COPY 使用"""
    data = []
    
    try:
        lines = await AsyncFileProcessor.read_txt_async(txt_path)
        
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                data.append({
                    'source_file': os.path.basename(txt_path),
                    'source_type': 'txt',
                    'raw_data': {
                        'line_number': i,
                        'content': line.strip(),
                        'length': len(line)
                    }
                })
    except Exception as e:
        print(f"處理 TXT 檔案 {txt_path} 時發生錯誤: {e}")
    
    # 匯出為 CSV
    if data:
        df_export = pd.DataFrame(data)
        df_export.to_csv(output_csv, index=False)

async def process_csv_for_copy(csv_path: str, output_csv: str):
    """處理 CSV 檔案供 COPY 使用"""
    data = []
    
    try:
        df = await AsyncFileProcessor.read_csv_async(csv_path)
        
        for _, row in df.iterrows():
            data.append({
                'source_file': os.path.basename(csv_path),
                'source_type': 'csv',
                'raw_data': row.to_dict()
            })
    except Exception as e:
        print(f"處理 CSV 檔案 {csv_path} 時發生錯誤: {e}")
    
    # 匯出為 CSV
    if data:
        df_export = pd.DataFrame(data)
        df_export.to_csv(output_csv, index=False)

if __name__ == "__main__":
    #import sys
    #directorydirectory =  #sys.argv[1] if len(sys.argv) > 1 else "./data"
    asyncio.run(bulk_import_with_copy('TDRReportRawData'))
