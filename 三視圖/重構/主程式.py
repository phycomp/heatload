from streamlit import button, download_button, markdown, session_state, sidebar, spinner, subheader, success, slider, set_page_config, radio, pyplot, empty, columns, metric, caption, info, expander, checkbox
from matplotlib.pyplot import close, figure, subplots, tight_layout, rcParams
from matplotlib.gridspec import GridSpec
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image as XLImage
from 三視圖Util import 繪制三視, 繪製前視, 繪製上視, 繪製側視
from 佈局計算 import LayoutCalculator #, 各層位置

set_page_config(page_title="智慧三視圖 - 清晰文字", page_icon="📐", layout="wide", initial_sidebar_state="expanded")
狀態=empty()
with sidebar:
    subheader("📐 智慧三視圖系統 - 清晰文字標註")
    subheader("⚙️ 參數設定")
    通道數 = slider("通道數", 2, 16, 8, 2)
    訊號間距 = slider("Pitch(mm)", .5, 5., 2., .2)
    訊號寬度 = slider("訊號寬度(μm)", 10, 40, 35, 5)

    # markdown("---")
    subheader("🔤 字型控制")
    caption("最小字型限制: 8pt (確保可讀)")
    字型縮放 = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)

    # markdown("---")
    # total_w = 通道數 * 訊號間距

    態狀=empty()
    # 顯示當前字型大小
    佈局 = LayoutCalculator(通道數=通道數, 訊號間距=訊號間距, 訊號寬度=訊號寬度) #, 字型縮放=字型縮放)
    # 佈局 = LayoutCalculator(通道數, 訊號間距, 訊號寬度, 字型縮放)
    狀態.code(f'{佈局.訊號寬度}mm')
    總寬度, 邊緣=佈局.線總寬, 佈局.邊緣
    # 層, 位置=各層位置(佈局)
    # 狀態.code(佈局.線厚度m)
    態狀.code(['層位置', 佈局.層位置])
    #[{'y_bot_um': -150.0, 'y_top_um': -135.0, 'y_bot_mm': -0.15, 'y_top_mm': -0.135, 'center_mm': -0.1425, 'thick_mm': 0.015, 'thick_um': 15}, {'y_bot_um': -135.0, 'y_top_um': -130.0, 'y_bot_mm': -0.135, 'y_top_mm': -0.13, 'center_mm': -0.1325, 'thick_mm': 0.005, 'thick_um': 5}, {'y_bot_um': -130.0, 'y_top_um': -1.0, 'y_bot_mm': -0.13, 'y_top_mm': -0.001, 'center_mm': -0.0655, 'thick_mm': 0.129, 'thick_um': 129}, {'y_bot_um': -1.0, 'y_top_um': 1.0, 'y_bot_mm': -0.001, 'y_top_mm': 0.001, 'center_mm': 0.0, 'thick_mm': 0.002, 'thick_um': 2}, {'y_bot_um': 1.0, 'y_top_um': 130.0, 'y_bot_mm': 0.001, 'y_top_mm': 0.13, 'center_mm': 0.0655, 'thick_mm': 0.129, 'thick_um': 129}, {'y_bot_um': 130.0, 'y_top_um': 135.0, 'y_bot_mm': 0.13, 'y_top_mm': 0.135, 'center_mm': 0.1325, 'thick_mm': 0.005, 'thick_um': 5}, {'y_bot_um': 135.0, 'y_top_um': 150.0, 'y_bot_mm': 0.135, 'y_top_mm': 0.15, 'center_mm': 0.1425, 'thick_mm': 0.015, 'thick_um': 15}]
    # info(佈局.__dict__)
    #info(f"""
    #**尺寸資訊**
    #- 總寬度: {總寬度:.2f}mm
    #- 總厚度: 300 um (.3 mm)
    #- 通道數: {通道數}ch
    #- 線邊緣: {邊緣}mm
    #- 基礎字型: {佈局.base_font_size:.1f} pt
    #- 最小字型: {min(佈局.layer_font_sizes):.1f} pt
    #""")

    # 創建佈局計算器
    前視圖, 側視圖, 上視圖=繪制三視(佈局)

    MENU = ['📐 前視圖', '📐 側視圖', '📐 上視圖', '匯出分頁']
    menu = radio('選擇視圖', MENU, horizontal=True, index=0)

if menu == MENU[0]:
    subheader("🔲 前視圖 Front View")
    # caption(f"總寬度: {佈局.線總寬:.2f}mm | 總厚度: {佈局.total_thick_um}um | 字型縮放: {字型縮放:.1f}x")
    # 前視圖= session_state['前視圖']
    前視圖=繪製前視(佈局)
    前視圖
    # pyplot(前視圖)
elif menu == MENU[1]:
    subheader("🔲 側視圖 Side View")
    側視圖=session_state['側視圖']
    pyplot(側視圖)
elif menu == MENU[1]:
    subheader("🔲 上視圖 Top View")
    上視圖 = session_state['上視圖']
    pyplot(上視圖)
else:
    # from 分頁Util import 分頁
    from 分頁預覽 import 規格資框, 層疊結構
    from 匯出鈮鈦 import 匯出分頁
    資框規格=規格資框(佈局)
    資框規格
    層疊規格 = 層疊結構(佈局)
    層疊規格
    # 分頁()
    試算表=匯出分頁(佈局, 前視圖, 側視圖, 上視圖, 規格=資框規格, 層疊=層疊規格)
    subheader("📥 匯出 Excel 規格書")
    
    col1, col2 = columns([2, 1])
    with col1:
        markdown("""
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
        markdown("### 匯出設定")
        caption(f"通道數: {通道數}")
        caption(f"總寬度: {佈局.線總寬:.2f}mm")
        caption(f"圖形解析度: 200 DPI")
        
        #if button("📊 產生並下載 Excel", type="primary", use_container_width=True):
        #    with spinner("正在產生 Excel 檔案，請稍候..."):
        # 資框 = 分頁(佈局, 前視圖, 側視圖, 上視圖)
        # 資框
        
        download_button(
            label="⬇️UF1柔性線材規格.xlsx",
            data=試算表,
            file_name=f"UF1_{通道數}通道_長寬高{佈局.長寬高}mm.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        success("✅ Excel 檔案已產生!")

    # markdown("---")
    cols = columns(4)
    with cols[0]:
        caption(f"📐 通道數: {佈局.通道數}")
    with cols[1]:
        caption(f"📏 Pitch: {佈局.訊號間距:.1f}mm")
    with cols[2]:
        caption(f"📐 總寬度: {佈局.線總寬:.2f}mm")
    with cols[3]:
        caption(f"📏 總厚度: 300um")
# if __name__ == "__main__": main()
