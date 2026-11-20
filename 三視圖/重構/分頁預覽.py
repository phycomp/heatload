# ============================================================
# DataFrame 預覽功能 - 在匯出Excel前顯示
# ============================================================
from 佈局計算 import 各層位置, LAYER_DEFS
from streamlit import empty, pyplot
狀態=empty()

import pandas as pd
from streamlit import data_editor

def 規格資框(佈局: LayoutCalculator):
    """建立規格DataFrame"""
    
    data = {"類別":[], "參數":[], "規格值":[], "單位":[], "備註":[], "公差":[] }
    
    # 一般規格
    general_specs = [
        ["一般性", "產品名稱", "U-leam UF1", "", "仿照 Delft Circuits", ""],
        ["一般性", "通道數", 佈局.通道數, "ch", "並列通道", ""],
        ["一般性", "通道間距 (Pitch)", 佈局.訊號間距, "mm", "標準設計", "±0.05"],
        ["一般性", "總寬度", f"{佈局.線總寬:.2f}", "mm", 佈局.線總寬, "±0.1"], #f"{佈局.通道數}ch × {佈局.訊號間距}mm"
        ["一般性", "總厚度", 佈局.線厚度μ, "um", "7層 GSG 結構", "±5"],
        ["一般性", "總長度", 佈局.線長度, "mm", "可客製化", "±1"],
        ["一般性", "線邊緣空白", f"{佈局.邊緣}", "mm", "符合5W/10H規則", ""],
        ["一般性", "最小彎曲半徑", 5, "mm", "動態彎曲", ""],
    ]
    
    # 電氣規格
    electrical_specs = [
        ["電氣", "特性阻抗", 50, "Ohm", "GSG 帶狀線設計", "±2"],
        ["電氣", "頻率範圍", "DC - 18", "GHz", "微波操作", ""],
        ["電氣", "插入損耗", "< 0.5", "dB/m", "@ 10GHz", ""],
        ["電氣", "回波損耗", "> 20", "dB", "@ 10GHz", ""],
        ["電氣", "串擾隔離", "< -60", "dB", "相鄰通道", ""],
        ["電氣", "傳播延遲", "~ 5.6", "ns/m", "Polyimide 介電", "±0.2"],
    ]
    
    # 層結構
    layer_specs = [
        ["層結構", "保護層-上", 15, "um", "Polyimide", "±2"],
        ["層結構", "接地層-上", 5, "um", "Ag/NbTi", "±0.5"],
        ["層結構", "介電層-上", 129, "um", "Polyimide", "±3"],
        ["層結構", "訊號層厚度", 佈局.訊號厚度, "um", "Ag/NbTi", "±0.2"],
        ["層結構", "訊號層寬度", 佈局.訊號寬度, "um", "Ag/NbTi", "±10"],
        ["層結構", "介電層-下", 129, "um", "Polyimide", "±3"],
        ["層結構", "接地層-下", 5, "um", "Ag/NbTi", "±0.5"],
        ["層結構", "保護層-下", 15, "um", "Polyimide", "±2"],
    ]
    
    # 材料規格
    material_specs = [
        #["材料", "導體材料", "Ag / NbTi", "", "銀/鈮鈦超導", ""],
        #["材料", "介電材料", "Polyimide", "", "聚酰亞胺", ""],
        #["材料", "導體電阻率 (Ag)", 1.59, "μΩ·cm", "@ 300K", ""],
        #["材料", "導體電阻率 (NbTi)", 50, "μΩ·cm", "@ 300K", ""],
        ["材料", "導體材料", "Ag / NbTi", "", "銀/鈮鈦超導", ""],
        ["材料", "介電材料", "Polyimide", "", "聚酰亞胺", ""],
        # ["材料", "鈮含量 (Nb)", f'{100-佈局.鈦比例:.0f}', "%", "鈮比例", "±1"],
        # ["材料", "鈦含量 (Ti)", f'{佈局.鈦比例:.0f}', "%", "鈦比例", "±1"],
        ["材料", "鈮鈦比例 (NbTi)", f"{佈局.鈮鈦比例}", "%", "Nb:Ti 比例", "±1"],
        ["材料", "鈮鈦超導轉變溫度 (Tc)", "9.8", "K", "超導臨界溫度", "±0.1"],
        ["材料", "鈮鈦臨界電流密度 (Jc)", "2.5 × 10⁵", "A/cm²", "@ 4.2K, 5T", "±0.3 × 10⁵"],
        # ["材料", "鈮鈦上臨界磁場 (Hc2)", "14.5", "T", "@ 4.2K", "±0.5"],
        ["材料", "導體電阻率 (Ag)", 1.59, "μΩ·cm", "@ 300K", ""],
        ["材料", "導體電阻率 (Ag)", 0.3, "μΩ·cm", "@ 4.2K", "RRR > 100"],
        ["材料", "導體電阻率 (NbTi)", 50, "μΩ·cm", "@ 300K", ""],
        ["材料", "導體電阻率 (NbTi)", 0.5, "μΩ·cm", "@ 10K", "正常態"],
    ]

    # 熱性能
    thermal_specs = [
        #["熱性能", "熱負載 (Ag)", "< 125", "μW/ch", "@ 4-40K, L=0.4m", ""],
        #["熱性能", "熱負載 (NbTi)", "~ 20", "nW/ch", "@ 10-350mK, L=0.2m", ""],
        #["熱性能", "操作溫度", "10^-3 ~ 400", "K", "mK 至 室溫", ""],
        ["熱性能", "熱負載 (Ag)", "< 125", "μW/ch", "@ 4-40K, L=0.2m", ""],
        ["熱性能", "熱負載 (NbTi)", "~ 20", "nW/ch", "@ 4K-9.8K, L=0.2m", ""],
        ["熱性能", "操作溫區", "4K~9.8K", "K", "4K 至 9.8K", ""],
        # ["熱性能", "熱膨脹係數 (Polyimide)", "~ 20", "ppm/K", "CTE", ""],
        # ["熱性能", "熱導率 (Polyimide)", "0.12", "W/m·K", "@ 300K", ""],
        # ["熱性能", "比熱容 (Polyimide)", "1.09", "J/g·K", "@ 300K", ""],
    ]

    # 機械規格
    mechanical_specs = [
        #["機械", "連接器類型", "SMA (f) / SMP (m)", "", "可選直角/直線", ""],
        #["機械", "真空洩漏率", "< 10^-6", "mbar·L/s", "整合式穿通", ""],
        #["機械", "彎曲壽命", "> 1000", "cycles", "R=5mm", ""],
        #["機械", "拉伸強度", "> 50", "N", "軸向拉力", ""],
        ["機械", "連接器類型", "SMA (f) / SMP (m)", "", "直角/直線", ""],
        ["機械", "真空洩漏率", "< 10^-6", "mbar·L/s", "整合式穿通", ""],
        ["機械", "彎曲壽命", "> 1000", "cycles", "R=5mm", ""],
        ["機械", "拉伸強度", "> 50", "N", "軸向拉力", ""],
        ["機械", "楊氏模量 (Polyimide)", "2.5", "GPa", "", ""],
        ["機械", "密度 (Polyimide)", "1.42", "g/cm³", "", ""],
    ]
   
    #連接器規格 = [
    #    ["", "連接器類型", "SMA (f) / SMP (m)", "", "可選直角/直線", ""],
    #]
    # 合併所有規格
    全規格 = (general_specs + electrical_specs + layer_specs + material_specs + thermal_specs + mechanical_specs)
    for spec in 全規格:
        data["類別"].append(spec[0])
        data["參數"].append(spec[1])
        data["規格值"].append(spec[2])
        data["單位"].append(spec[3])
        data["備註"].append(spec[4])
        data["公差"].append(spec[5])
    
    # 狀態.code(data["類別"])
    def 得出順序(列):
      新列=[]
      for 值 in 列:
        if not 新列.count(值): 新列.append(值)
      return 新列
    # 加入分隔行
    categories = 得出順序(data["類別"])
    狀態.code(categories)
    df_list = []
    for category in categories:
        if category:
            mask = [c == category for c in data["類別"]]
            cat_df = pd.DataFrame({
                "類別": [category] + [""] * (sum(mask) - 1),
                "參數": [data["參數"][i] for i in range(len(data["參數"])) if mask[i]],
                "規格值": [data["規格值"][i] for i in range(len(data["規格值"])) if mask[i]],
                "單位": [data["單位"][i] for i in range(len(data["單位"])) if mask[i]],
                "備註": [data["備註"][i] for i in range(len(data["備註"])) if mask[i]],
                "公差": [data["公差"][i] for i in range(len(data["公差"])) if mask[i]],
            })
            df_list.append(cat_df)
            # 加入分隔行
            if category != list(categories)[-1]:
                sep_df = pd.DataFrame([["", "", "", "", "", ""]], columns=["類別", "參數", "規格值", "單位", "備註", "公差"])
                df_list.append(sep_df)
    
    df = pd.concat(df_list, ignore_index=True)
    return df


def 層疊結構(佈局: LayoutCalculator):
    """建立層疊結構DataFrame"""
    
    layer_functions = [
        'Mechanical protection',
        'EM shielding / Return path',
        'Dielectric isolation',
        f'Signal ({佈局.通道數} channels)',
        'Dielectric isolation',
        'EM shielding / Return path',
        'Mechanical protection'
    ]
    
    data = { "層號": [], "層名稱": [], "材料": [], "厚度 (um)": [], "厚度 (mm)": [], "功能": [] }
    # data = { "Layer No.": [], "Layer Name": [], "Material": [], "Thickness (um)": [], "Thickness (mm)": [], "Function": [] }
    
    layer_positions, _ = 各層位置(LAYER_DEFS)
    
    for i, (layer_def, pos) in enumerate(zip(LAYER_DEFS, layer_positions), 1):
        data["層號"].append(i)
        data["層名稱"].append(layer_def['name'])
        data["材料"].append(layer_def['material'])
        data["厚度 (um)"].append(layer_def['thick_um'])
        data["厚度 (mm)"].append(round(layer_def['thick_um'] / 1000, 4))
        data["功能"].append(layer_functions[i-1])
    
    df = pd.DataFrame(data)
    
    # 加入總計行
    total_row = pd.DataFrame([{
        "層號": "TOTAL",
        "層名稱": "",
        "材料": "",
        "厚度 (um)": 佈局.線厚度μ,
        "厚度 (mm)": round(佈局.線厚度μ / 1000, 4),
        "功能": ""
    }])
    
    df = pd.concat([df, total_row], ignore_index=True)
    return df


# ============================================================
# 更新主程式 - 加入DataFrame預覽
# ============================================================

def main():
    set_page_config(page_title="智慧三視圖 - Excel匯出", page_icon="📐",
                   佈局="wide", initial_sidebar_state="expanded")
    
    st.title("📐 智慧三視圖系統 - Excel匯出功能")
    st.markdown("*完整規格表 + 放大三視圖 + DataFrame預覽*")
    st.markdown("---")
    
    with sidebar:
        subheader("⚙️ 參數設定")
        
        通道數 = slider("通道數", 2, 16, 8, 2)
        訊號間距 = slider("Pitch (mm)", 0.5, 5.0, 2.0, 0.1)
        signal_width = slider("信號線寬度 (mm)", 0.1, 1.0, 0.4, 0.05)
        
        st.markdown("---")
        subheader("🔤 字型控制")
        font_scale = slider("字型縮放比例", 0.5, 2.0, 1.0, 0.1)
        
        st.markdown("---")
        total_w = 通道數 * 訊號間距
        
        temp_佈局 = LayoutCalculator(通道數, 訊號間距, signal_width, font_scale)
        st.info(f"""
        **尺寸資訊**
        - 總寬度: {total_w:.2f} mm
        - 總厚度: 300 um (0.3 mm)
        - 通道數: {通道數} ch
        - 基礎字型: {temp_佈局.base_font_size:.1f} pt
        """)
        
        st.markdown("---")
        st.subheader("📥 Excel 匯出")
        st.caption("包含以下分頁:")
        st.caption("1. CF3 Specifications")
        st.caption("2. Front View (放大)")
        st.caption("3. Side View (放大)")
        st.caption("4. Top View (放大)")
        st.caption("5. Layer Stack-up")
    
    佈局 = LayoutCalculator(通道數, 訊號間距, signal_width, font_scale)
    
    # 繪製三視圖
    front_fig = draw_front_view(佈局)
    side_fig = draw_side_view(佈局)
    top_fig = draw_top_view(佈局)
    
    MENU = ['📐 前視圖', '📐 側視圖', '📐 上視圖', '📥 匯出Excel']
    menu = radio('選擇功能', MENU, horizontal=True, index=0)
    
    if menu == MENU[0]:
        st.subheader("🔲 前視圖 Front View")
        st.caption(f"總寬度: {佈局.線總寬:.2f}mm | 總厚度: {佈局.線厚度μ}um")
        pyplot(front_fig)
        
    elif menu == MENU[1]:
        st.subheader("🔲 側視圖 Side View")
        pyplot(side_fig)
        
    elif menu == MENU[2]:
        st.subheader("🔲 上視圖 Top View")
        pyplot(top_fig)
        
    elif menu == MENU[3]:
        st.subheader("📥 匯出 Excel 規格書")
        
        # 建立DataFrames
        spec_df = 規格資框(佈局)
        layer_df = 層疊結構(佈局)
        
        # 顯示預覽選項
        preview_tab1, preview_tab2, preview_tab3 = st.tabs([
            "📋 規格預覽", 
            "📊 層疊結構預覽",
            "📐 匯出設定"
        ])
        
        with preview_tab1:
            st.markdown("### CF3 規格表預覽")
            st.caption(f"共 {len(spec_df)} 筆規格數據")
            
            # 使用st.dataframe顯示規格表
            st.dataframe(
                spec_df,
                use_container_width=True,
                height=400,
                column_config={
                    "類別": st.column_config.TextColumn("類別", width="small"),
                    "參數": st.column_config.TextColumn("參數", width="medium"),
                    "規格值": st.column_config.TextColumn("規格值", width="medium"),
                    "單位": st.column_config.TextColumn("單位", width="small"),
                    "備註": st.column_config.TextColumn("備註", width="large"),
                    "公差": st.column_config.TextColumn("公差", width="small"),
                }
            )
            
            # 顯示統計資訊
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("總規格數", len(spec_df))
            with col2:
                categories = len(set([c for c in spec_df["類別"] if c]))
                st.metric("規格類別", categories)
            with col3:
                st.metric("通道數", f"{通道數} ch")
        
        with preview_tab2:
            st.markdown("### 層疊結構預覽")
            st.caption(f"共 {len(layer_df)} 層 (含總計)")
            
            # 使用st.dataframe顯示層疊結構
            st.dataframe(
                layer_df,
                use_container_width=True,
                height=300,
                column_config={
                    "Layer No.": st.column_config.TextColumn("層號", width="small"),
                    "Layer Name": st.column_config.TextColumn("層名稱", width="medium"),
                    "Material": st.column_config.TextColumn("材料", width="medium"),
                    "Thickness (um)": st.column_config.NumberColumn("厚度 (um)", width="medium"),
                    "Thickness (mm)": st.column_config.NumberColumn("厚度 (mm)", width="medium", format="%.4f"),
                    "Function": st.column_config.TextColumn("功能", width="large"),
                }
            )
            
            # 顯示總計資訊
            total_row = layer_df[layer_df["Layer No."] == "TOTAL"]
            if not total_row.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("總厚度", f"{total_row['Thickness (um)'].values[0]} um")
                with col2:
                    st.metric("總厚度", f"{total_row['Thickness (mm)'].values[0]:.4f} mm")
                with col3:
                    st.metric("層數", f"{len(layer_df) - 1}")
        
        with preview_tab3:
            st.markdown("### 匯出設定與預覽")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**匯出內容包含:**")
                st.markdown("""
                - ✅ CF3 Specifications (完整規格表)
                - ✅ Front View (前視圖 - 放大)
                - ✅ Side View (側視圖 - 放大)
                - ✅ Top View (上視圖 - 放大)
                - ✅ Layer Stack-up (層疊結構)
                """)
                
                st.markdown("**圖形解析度:** 200 DPI")
                st.markdown(f"**檔案名稱:** CF3_Spec_{通道數}ch_{佈局.線總寬:.1f}mm.xlsx")
            
            with col2:
                st.markdown("**規格統計:**")
                st.metric("規格總數", len(spec_df))
                st.metric("層數", len(layer_df) - 1)
                st.metric("通道數", 通道數)
            
            # 匯出按鈕
            if st.button("📊 產生並下載 Excel", type="primary", use_container_width=True):
                with st.spinner("正在產生 Excel 檔案，請稍候..."):
                    excel_data = export_to_excel(佈局, front_fig, side_fig, top_fig)
                
                st.download_button(
                    label="⬇️ 下載 CF3_Specification.xlsx",
                    data=excel_data,
                    file_name=f"CF3_Spec_{通道數}ch_{佈局.線總寬:.1f}mm.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ Excel 檔案已產生!")
                st.balloons()
    
    st.markdown("---")
    cols = columns(4)
    with cols[0]:
        caption(f"📐 通道數: {通道數}")
    with cols[1]:
        caption(f"📏 Pitch: {訊號間距:.1f}mm")
    with cols[2]:
        caption(f"📐 總寬度: {佈局.線總寬:.2f}mm")
    with cols[3]:
        caption(f"📏 總厚度: {佈局.線厚度μ}um")


if __name__ == "__main__":
    main()
