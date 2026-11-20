# ============================================================
# Excel 匯出功能 - 完整規格與放大圖形
# ============================================================
from 佈局計算 import LayoutCalculator
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.dimensions import DimensionHolder
from openpyxl.utils.cell import coordinate_from_string

def 分頁(layout: LayoutCalculator, 前視圖, 側視圖, 上視圖):
    """匯出至Excel - 包含完整規格和放大三視圖"""
    
    wb = openpyxl.Workbook()
    
    # 定義樣式
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    sub_header_fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    sub_header_font = Font(color="FFFFFF", bold=True, size=11)
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # ============================================================
    # Sheet 1: Delft cri/oFlex3 CF3 規格欄位
    # ============================================================
    
    ws1 = wb.active
    ws1.title = "CF3 Specifications"
    
    # 標題
    ws1.merge_cells('A1:F1')
    cell = ws1['A1']
    cell.value = "Delft cri/oFlex3 CF3 - Complete Specifications"
    cell.font = Font(size=16, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 35
    
    # 子標題
    ws1.merge_cells('A2:F2')
    cell = ws1['A2']
    cell.value = f"Channel Configuration: {layout.n_channels} Channels | Pitch: {layout.pitch_mm}mm | Total Width: {layout.total_width_mm:.2f}mm"
    cell.font = Font(size=11, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 28
    
    # 規格表格標題
    row = 4
    headers = ["類別", "參數", "規格值", "單位", "備註", "公差"]
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    
    ws1.row_dimensions[row].height = 25
    row += 1
    
    # 規格數據
    specifications = [
        # 一般規格
        ["一般性", "產品名稱", "cri/oFlex3 CF3", "", "Delft Circuits", ""],
        ["一般性", "通道數", layout.n_channels, "ch", "並列通道", ""],
        ["一般性", "通道間距 (Pitch)", layout.pitch_mm, "mm", "標準設計", "±0.05"],
        ["一般性", "總寬度", f"{layout.total_width_mm:.2f}", "mm", f"{layout.n_channels}ch × {layout.pitch_mm}mm", "±0.1"],
        ["一般性", "總厚度", layout.total_thick_um, "um", "7層 GSG 結構", "±5"],
        ["一般性", "總長度", "200 - 1000", "mm", "可客製化", "±1"],
        ["一般性", "最小彎曲半徑", 5, "mm", "動態彎曲", ""],
        ["", "", "", "", "", ""],
        
        # 電氣規格
        ["電氣", "特性阻抗", 50, "Ohm", "GSG 帶狀線設計", "±2"],
        ["電氣", "頻率範圍", "DC - 18", "GHz", "微波操作", ""],
        ["電氣", "插入損耗", "< 0.5", "dB/m", "@ 10GHz", ""],
        ["電氣", "回波損耗", "> 20", "dB", "@ 10GHz", ""],
        ["電氣", "串擾隔離", "< -60", "dB", "相鄰通道", ""],
        ["電氣", "傳播延遲", "~ 5.6", "ns/m", "Polyimide 介電", "±0.2"],
        ["", "", "", "", "", ""],
        
        # 層結構
        ["層結構", "保護層 (上下)", 15, "um", "Polyimide", "±2"],
        ["層結構", "接地層 (上下)", 5, "um", "Ag/NbTi", "±0.5"],
        ["層結構", "介電層 (上下)", 129, "um", "Polyimide", "±3"],
        ["層結構", "訊號線層", 2, "um", "Ag/NbTi", "±0.2"],
        ["層結構", "訊號線寬度", layout.signal_width_mm * 1000, "um", "中心導體", "±10"],
        ["", "", "", "", "", ""],
        
        # 材料規格
        ["材料", "導體材料", "Ag / NbTi", "", "銀/鈮鈦超導", ""],
        ["材料", "介電材料", "Polyimide", "", "聚酰亞胺", ""],
        ["材料", "導體電阻率 (Ag)", 1.59, "μΩ·cm", "@ 300K", ""],
        ["材料", "導體電阻率 (NbTi)", 50, "μΩ·cm", "@ 300K", ""],
        ["", "", "", "", "", ""],
        
        # 熱性能
        ["熱性能", "熱負載 (Ag)", "< 125", "μW/ch", "@ 4-40K, L=0.4m", ""],
        ["熱性能", "熱負載 (NbTi)", "~ 20", "nW/ch", "@ 10-350mK, L=0.2m", ""],
        ["熱性能", "操作溫度", "10^-3 ~ 400", "K", "mK 至 室溫", ""],
        ["", "", "", "", "", ""],
        
        # 機械規格
        ["機械", "連接器類型", "SMA (f) / SMP (m)", "", "可選直角/直線", ""],
        ["機械", "真空洩漏率", "< 10^-6", "mbar·L/s", "整合式穿通", ""],
        ["機械", "彎曲壽命", "> 1000", "cycles", "R=5mm", ""],
        ["機械", "拉伸強度", "> 50", "N", "軸向拉力", ""],
    ]
    
    # 填入規格數據
    for spec_row in specifications:
        for col, value in enumerate(spec_row, 1):
            cell = ws1.cell(row=row, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left" if col > 1 else "center", 
                                      vertical="center", wrap_text=True)
            
            # 類別欄位背景色
            if col == 1 and value:
                cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                cell.font = Font(bold=True)
        
        # 空行分隔
        if not spec_row[0] and not spec_row[1]:
            row += 1
        
        row += 1
    
    # 設定列寬
    column_widths = {'A': 14, 'B': 22, 'C': 18, 'D': 12, 'E': 32, 'F': 12}
    for col, width in column_widths.items():
        ws1.column_dimensions[col].width = width
    
    # ============================================================
    # Sheet 2: 前視圖 (放大)
    # ============================================================
    
    ws2 = wb.create_sheet("Front View")
    
    # 標題
    ws2.merge_cells('A1:E1')
    cell = ws2['A1']
    cell.value = f"Front View - Cross Section ({layout.n_channels} Channels)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 30
    
    # 子標題
    ws2.merge_cells('A2:E2')
    cell = ws2['A2']
    cell.value = f"GSG 7-Layer Stripline | Width: {layout.total_width_mm:.2f}mm | Thickness: {layout.total_thick_um}um | Pitch: {layout.pitch_mm}mm"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 25
    
    # 將前視圖放大插入 (調整尺寸)
    front_buf = BytesIO()
    前視圖.savefig(front_buf, format='png', dpi=200, facecolor='#0D1117', 
                     edgecolor='none', bbox_inches='tight')
    front_buf.seek(0)
    
    img_front = XLImage(front_buf)
    # 放大圖形 (根據通道數調整)
    if layout.n_channels <= 4:
        img_front.width = 800
        img_front.height = 500
    elif layout.n_channels <= 8:
        img_front.width = 900
        img_front.height = 560
    else:
        img_front.width = 1000
        img_front.height = 620
    
    ws2.add_image(img_front, 'A4')
    
    # 設定列寬和行高
    for col in range(1, 6):
        ws2.column_dimensions[get_column_letter(col)].width = 20
    ws2.row_dimensions[3].height = 10
    
    # ============================================================
    # Sheet 3: 側視圖 (放大)
    # ============================================================
    
    ws3 = wb.create_sheet("Side View")
    
    # 標題
    ws3.merge_cells('A1:E1')
    cell = ws3['A1']
    cell.value = f"Side View - Length Profile ({layout.n_channels} Channels)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 30
    
    # 子標題
    ws3.merge_cells('A2:E2')
    cell = ws3['A2']
    cell.value = f"Length: 400mm | Bend Radius: 5mm | Connector: SMA/SMP"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[2].height = 25
    
    # 側視圖放大插入
    side_buf = BytesIO()
    側視圖.savefig(side_buf, format='png', dpi=200, facecolor='#0D1117', 
                    edgecolor='none', bbox_inches='tight')
    side_buf.seek(0)
    
    img_side = XLImage(side_buf)
    img_side.width = 900
    img_side.height = 420
    
    ws3.add_image(img_side, 'A4')
    
    for col in range(1, 6):
        ws3.column_dimensions[get_column_letter(col)].width = 20
    ws3.row_dimensions[3].height = 10
    
    # ============================================================
    # Sheet 4: 上視圖 (放大)
    # ============================================================
    
    ws4 = wb.create_sheet("Top View")
    
    # 標題
    ws4.merge_cells('A1:E1')
    cell = ws4['A1']
    cell.value = f"Top View - Plan Layout ({layout.n_channels} Channels)"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 30
    
    # 子標題
    ws4.merge_cells('A2:E2')
    cell = ws4['A2']
    cell.value = f"Width: {layout.total_width_mm:.2f}mm | Pitch: {layout.pitch_mm}mm | Integrated Filtering"
    cell.font = Font(size=10, italic=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[2].height = 25
    
    # 上視圖放大插入
    top_buf = BytesIO()
    上視圖.savefig(top_buf, format='png', dpi=200, facecolor='#0D1117', 
                   edgecolor='none', bbox_inches='tight')
    top_buf.seek(0)
    
    img_top = XLImage(top_buf)
    img_top.width = 900
    img_top.height = 500
    
    ws4.add_image(img_top, 'A4')
    
    for col in range(1, 6):
        ws4.column_dimensions[get_column_letter(col)].width = 20
    ws4.row_dimensions[3].height = 10
    
    # ============================================================
    # Sheet 5: Layer Stack-up
    # ============================================================
    
    ws5 = wb.create_sheet("Layer Stack-up")
    
    # 標題
    ws5.merge_cells('A1:F1')
    cell = ws5['A1']
    cell.value = "Layer Stack-up Detail"
    cell.font = Font(size=14, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 30
    
    # 表格標題
    row = 3
    headers = ["Layer No.", "Layer Name", "Material", "Thickness (um)", "Thickness (mm)", "Function"]
    for col, header in enumerate(headers, 1):
        cell = ws5.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws5.row_dimensions[row].height = 25
    row += 1
    
    # 層數據
    layer_functions = [
        'Mechanical protection',
        'EM shielding / Return path',
        'Dielectric isolation',
        f'Signal ({layout.n_channels} channels)',
        'Dielectric isolation',
        'EM shielding / Return path',
        'Mechanical protection'
    ]
    
    layer_colors = {
        '保護層': 'E8D5C4',
        '接地層': '8B9CAD',
        '介電層': 'C4956A',
        '訊號線': 'FFD700'
    }
    
    layer_positions, _ = calculate_layer_positions(LAYER_DEFS)
    
    for i, (layer_def, pos) in enumerate(zip(LAYER_DEFS, layer_positions), 1):
        # 確定層類別
        layer_type = '介電層'
        if '保護' in layer_def['name']:
            layer_type = '保護層'
        elif '接地' in layer_def['name']:
            layer_type = '接地層'
        elif '訊號' in layer_def['name']:
            layer_type = '訊號線'
        
        data = [
            i,
            layer_def['name'],
            layer_def['material'],
            layer_def['thick_um'],
            round(layer_def['thick_um'] / 1000, 4),
            layer_functions[i-1]
        ]
        
        for col, value in enumerate(data, 1):
            cell = ws5.cell(row=row, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center" if col <= 4 else "left", 
                                      vertical="center", wrap_text=True)
            
            # 根據層類型著色
            if layer_type in layer_colors:
                cell.fill = PatternFill(start_color=layer_colors[layer_type], 
                                       end_color=layer_colors[layer_type], 
                                       fill_type="solid")
        
        row += 1
    
    # 總計行
    total_row = row
    ws5.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=2)
    cell = ws5.cell(row=total_row, column=1, value="TOTAL")
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=3, value="")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=4, value=layout.total_thick_um)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=5, value=round(layout.total_thick_um / 1000, 4))
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
    
    cell = ws5.cell(row=total_row, column=6, value="")
    cell.border = thin_border
    
    # 設定列寬
    column_widths = {'A': 12, 'B': 28, 'C': 18, 'D': 18, 'E': 16, 'F': 35}
    for col, width in column_widths.items():
        ws5.column_dimensions[col].width = width
    
    # 儲存Excel
    excel_buf = BytesIO()
    wb.save(excel_buf)
    excel_buf.seek(0)
    
    return excel_buf.getvalue()


# ============================================================
# 更新主程式 - 增加匯出功能
# ============================================================

def main():
    set_page_config(page_title="智慧三視圖 - Excel匯出", page_icon="📐",
                   layout="wide", initial_sidebar_state="expanded")
    
    st.title("📐 智慧三視圖系統 - Excel匯出功能")
    st.markdown("*完整規格表 + 放大三視圖*")
    st.markdown("---")
    
    with sidebar:
        subheader("⚙️ 參數設定")
        
        n_channels = slider("通道數", 2, 16, 8, 2)
        pitch_mm = slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
        signal_width = slider("信號線寬度 (mm)", 0.1, 1.0, 0.4, 0.05)
        
        st.markdown("---")
        subheader("🔤 字型控制")
        font_scale = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
        
        st.markdown("---")
        total_w = n_channels * pitch_mm
        
        temp_layout = LayoutCalculator(n_channels, pitch_mm, signal_width, font_scale)
        st.info(f"""
        **尺寸資訊**
        - 總寬度: {total_w:.2f} mm
        - 總厚度: 300 um (0.3 mm)
        - 通道數: {n_channels} ch
        - 基礎字型: {temp_layout.base_font_size:.1f} pt
        """)
        
        st.markdown("---")
        st.subheader("📥 Excel 匯出")
        st.caption("包含以下分頁:")
        st.caption("1. CF3 Specifications")
        st.caption("2. Front View (放大)")
        st.caption("3. Side View (放大)")
        st.caption("4. Top View (放大)")
        st.caption("5. Layer Stack-up")
    
    layout = LayoutCalculator(n_channels, pitch_mm, signal_width, font_scale)
    
    # 繪製三視圖
    前視圖 = draw_front_view(layout)
    側視圖 = draw_side_view(layout)
    上視圖 = draw_top_view(layout)
    
    MENU = ['📐 前視圖', '📐 側視圖', '📐 上視圖', '📥 匯出Excel']
    menu = radio('選擇功能', MENU, horizontal=True, index=0)
    
    if menu == MENU[0]:
        st.subheader("🔲 前視圖 Front View")
        st.caption(f"總寬度: {layout.total_width_mm:.2f}mm | 總厚度: {layout.total_thick_um}um")
        pyplot(前視圖)
        
    elif menu == MENU[1]:
        st.subheader("🔲 側視圖 Side View")
        pyplot(側視圖)
        
    elif menu == MENU[2]:
        st.subheader("🔲 上視圖 Top View")
        pyplot(上視圖)
        
    elif menu == MENU[3]:
        st.subheader("📥 匯出 Excel 規格書")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            ### 匯出內容包含
            
            **1. CF3 Specifications (規格欄位)**
            - 一般規格 (通道數、尺寸、彎曲半徑等)
            - 電氣規格 (阻抗、頻率、損耗等)
            - 層結構詳細 (各層厚度、材料)
            - 材料規格 (導體、介電)
            - 熱性能與機械規格
            
            **2. Front View (前視圖 - 放大)**
            - GSG 7層結構橫截面
            - 各層標註與厚度
            
            **3. Side View (側視圖 - 放大)**
            - 長度方向輪廓
            - 彎曲半徑標示
            
            **4. Top View (上視圖 - 放大)**
            - 平面佈局
            - 通道配置
            
            **5. Layer Stack-up**
            - 完整層疊結構表
            """
            )
        
        with col2:
            st.markdown("### 匯出設定")
            st.caption(f"通道數: {n_channels}")
            st.caption(f"總寬度: {layout.total_width_mm:.2f}mm")
            st.caption(f"圖形解析度: 200 DPI")
            
            if st.button("📊 產生並下載 Excel", type="primary", use_container_width=True):
                with spinner("正在產生 Excel 檔案，請稍候..."):
                    excel_data = 分頁(layout, 前視圖, 側視圖, 上視圖)
                
                st.download_button(
                    label="⬇️ 下載 CF3_Specification.xlsx",
                    data=excel_data,
                    file_name=f"CF3_Spec_{n_channels}ch_{layout.total_width_mm:.1f}mm.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                success("✅ Excel 檔案已產生!")
    
    st.markdown("---")
    cols = columns(4)
    with cols[0]:
        caption(f"📐 通道數: {n_channels}")
    with cols[1]:
        caption(f"📏 Pitch: {pitch_mm:.1f}mm")
    with cols[2]:
        caption(f"📐 總寬度: {layout.total_width_mm:.2f}mm")
    with cols[3]:
        caption(f"📏 總厚度: {layout.total_thick_um}um")


if __name__ == "__main__":
    main()
