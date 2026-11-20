from pandas import DataFrame, ExcelWriter
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from io import BytesIO

def apply_excel_styling(worksheet, font_size=11, header_font_size=12):
    """
    套用 Excel 字型大小與格式設定
    
    Parameters:
    - worksheet: openpyxl worksheet 物件
    - font_size: 一般儲存格字型大小 (預設 11)
    - header_font_size: 標題列字型大小 (預設 12)
    """
    # 定義邊框樣式
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 標題列背景色
    header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
    
    # 設定所有儲存格的字型
    for row in worksheet.iter_rows():
        for cell in row:
            # 設定字型大小
            if row[0].row == 1:  # 標題列
                cell.font = Font(
                    size=header_font_size, 
                    bold=True, 
                    name='Calibri'
                )
                cell.fill = header_fill
            else:  # 資料列
                cell.font = Font(
                    size=font_size, 
                    name='Calibri'
                )
            # 設定邊框
            cell.border = thin_border
            # 設定對齊方式
            cell.alignment = Alignment(
                horizontal='center', 
                vertical='center',
                wrap_text=True
            )

def 匯出表單(dataframes, file_name, font_size=11, header_font_size=12, include_changelog=True):
    """
    匯出 Excel 檔案，包含字型大小設定
    
    Parameters:
    - dataframes: 字典，key 為分頁名稱，value 為 DataFrame
    - file_name: 檔案名稱
    - font_size: 一般儲存格字型大小
    - header_font_size: 標題列字型大小
    - include_changelog: 是否加入更新紀錄分頁
    """
    output = BytesIO()
    
    with ExcelWriter(output, engine='openpyxl') as writer:
        # 寫入所有資料表
        for sheet_name, df in dataframes.items():
            # 將所有欄位轉為字串，避免數值格式問題
            df_copy = df.copy()
            for col in df_copy.columns:
                if df_copy[col].dtype == 'object':
                    df_copy[col] = df_copy[col].astype(str)
            df_copy.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 取得 worksheet 並套用格式
            worksheet = writer.sheets[sheet_name]
            
            # 調整欄寬（自動根據內容長度）
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        # 計算內容長度（中文字算 2 個字元寬度）
                        cell_value = str(cell.value)
                        length = sum(2 if ord(char) > 127 else 1 for char in cell_value)
                        if length > max_length:
                            max_length = length
                    except:
                        pass
                # 設定欄寬，至少 10，最多 40
                adjusted_width = min(max(max_length + 2, 10), 40)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # 套用字型大小與格式
            apply_excel_styling(worksheet, font_size, header_font_size)
        
        # 加入更新紀錄分頁
        if include_changelog:
            changelog_data = [
                ['版本', 'v2.0'],
                ['更新日期', '2026-08-20'],
                ['更新內容', '補充 FPC 疊構缺失的 DK/DF/厚度數值'],
                ['備註', '所有數值為合理推估值'],
                ['字型大小', f'一般: {font_size}pt, 標題: {header_font_size}pt']
            ]
            df_changelog = DataFrame(changelog_data, columns=['項目', '說明'])
            df_changelog.to_excel(writer, sheet_name='更新紀錄', index=False)
            
            # 設定更新紀錄格式
            worksheet = writer.sheets['更新紀錄']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        cell_value = str(cell.value)
                        length = sum(2 if ord(char) > 127 else 1 for char in cell_value)
                        if length > max_length:
                            max_length = length
                    except:
                        pass
                adjusted_width = min(max(max_length + 2, 10), 40)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # 套用格式到更新紀錄
            apply_excel_styling(worksheet, font_size, header_font_size)
    
    output.seek(0)
    return output

