import pandas as pd
import os
import re
import asyncio
from typing import List, Dict, Any
from datetime import datetime

class AsyncFileProcessor:
    @staticmethod
    async def read_excel_async(file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """異步讀取 Excel 檔案（使用線程池）"""
        loop = asyncio.get_event_loop()
        if sheet_name:
            df = await loop.run_in_executor(
                None, pd.read_excel, file_path, sheet_name
            )
        else:
            df = await loop.run_in_executor(
                None, pd.read_excel, file_path
            )
        return df
    
    @staticmethod
    async def read_csv_async(file_path: str, **kwargs) -> pd.DataFrame:
        """異步讀取 CSV 檔案"""
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, pd.read_csv, file_path, kwargs
        )
        return df
    
    @staticmethod
    async def read_txt_async(file_path: str) -> List[str]:
        """異步讀取 TXT 檔案"""
        loop = asyncio.get_event_loop()
        
        def read_file():
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()
        
        return await loop.run_in_executor(None, read_file)
    
    @staticmethod
    def parse_test_filename(filename: str) -> Dict[str, Any]:
        """解析測試檔案名稱"""
        patterns = [
            r'(PASS|FAIL)__(\d{8})_(\d{6})(?:_(.*))?\.txt',
            r'(PASS|FAIL)__(\d{8})_(\d{6})_(.*)_Result\.txt',
            r'(PASS|FAIL)__(\d{8})_(\d{6})_(.*)_Debug\.txt'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, filename)
            if match:
                return {
                    'result': match.group(1),
                    'date': datetime.strptime(match.group(2), '%Y%m%d').date(),
                    'time': datetime.strptime(match.group(3), '%H%M%S').time(),
                    'test_type': match.group(4) if match.group(4) else 'General'
                }
        
        return {}
    
    @staticmethod
    def parse_impedance_filename(filename: str) -> Dict[str, Any]:
        """解析阻抗測試檔案名稱"""
        pattern = r'Tx(\d+)\+_Rx(\d+)\+_Tx(\d+)\-?_Rx(\d+)\-?_Ch(\d+)_Tr(\d+)_TDD(\d+)'
        match = re.search(pattern, filename)
        
        if match:
            return {
                'tx_positive': float(match.group(1)),
                'rx_positive': float(match.group(2)),
                'tx_negative': float(match.group(3)),
                'rx_negative': float(match.group(4)),
                'channel': int(match.group(5)),
                'trace': int(match.group(6)),
                'tdd_value': float(match.group(7))
            }
        return {}
    
    @staticmethod
    async def export_to_csv_for_copy(data: List[Dict], output_path: str):
        """匯出數據為 CSV 格式供 \\COPY 使用"""
        loop = asyncio.get_event_loop()
        
        def write_csv():
            if data:
                df = pd.DataFrame(data)
                df.to_csv(output_path, index=False)
        
        await loop.run_in_executor(None, write_csv)
