import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from scipy.optimize import curve_fit

# 設置頁面
st.set_page_config(page_title="傳輸線阻抗溫度穩定性分析", layout="wide")
st.title("傳輸線阻抗溫度穩定性分析與改善策略")
st.markdown("""
## 深度分析傳輸線阻抗與溫度相關性的關鍵因素及改善方法
""")

# 側邊欄 - 輸入參數
st.sidebar.header("分析參數設置")

# 材料選擇
materials = st.sidebar.multiselect(
    "比較材料",
    ["FR-4", "Rogers RO4350B", "Teflon", "Alumina", "自定義1", "自定義2"],
    default=["FR-4", "Rogers RO4350B", "Teflon"]
)

# 溫度範圍
temp_min = st.sidebar.slider("最低溫度 (°C)", -100, 0, -40, 5)
temp_max = st.sidebar.slider("最高溫度 (°C)", 0, 200, 125, 5)

# 材料數據庫
material_properties = {
    "FR-4": {"er_ref": 4.5, "temp_coef": -150e-6, "tan_d_ref": 0.02, "tan_d_coef": 0.0005, "cost": "低", "thermal_stability": "差"},
    "Rogers RO4350B": {"er_ref": 3.48, "temp_coef": -50e-6, "tan_d_ref": 0.0037, "tan_d_coef": 0.0001, "cost": "中", "thermal_stability": "良"},
    "Teflon": {"er_ref": 2.1, "temp_coef": -200e-6, "tan_d_ref": 0.0002, "tan_d_coef": 0.00005, "cost": "高", "thermal_stability": "優"},
    "Alumina": {"er_ref": 9.8, "temp_coef": 100e-6, "tan_d_ref": 0.0001, "tan_d_coef": 0.00002, "cost": "中", "thermal_stability": "優"},
    "自定義1": {"er_ref": 6.0, "temp_coef": -100e-6, "tan_d_ref": 0.001, "tan_d_coef": 0.0002, "cost": "中", "thermal_stability": "良"},
    "自定義2": {"er_ref": 3.0, "temp_coef": -30e-6, "tan_d_ref": 0.0005, "tan_d_coef": 0.00005, "cost": "高", "thermal_stability": "優"}
}

# 允許自定義材料參數
for material in materials:
    if material.startswith("自定義"):
        st.sidebar.subheader(f"{material}參數")
        material_properties[material]["er_ref"] = st.sidebar.slider(f"{material}介電常數", 1.0, 20.0, material_properties[material]["er_ref"], 0.1)
        material_properties[material]["temp_coef"] = st.sidebar.slider(f"{material}溫度系數(ppm/°C)", -500, 500, int(material_properties[material]["temp_coef"]*1e6), 10) * 1e-6
        material_properties[material]["tan_d_ref"] = st.sidebar.slider(f"{material}損耗角正切", 0.0001, 0.05, material_properties[material]["tan_d_ref"], 0.001)
        material_properties[material]["tan_d_coef"] = st.sidebar.slider(f"{material}損耗角溫度系數", 0.00001, 0.001, material_properties[material]["tan_d_coef"], 0.00001)

# 傳輸線參數
width = st.sidebar.slider("線寬 (mm)", 0.1, 5.0, 1.0, 0.1)
height = st.sidebar.slider("基板厚度 (mm)", 0.1, 5.0, 1.6, 0.1)

# 材料特性與溫度的關系函數
def dielectric_constant_vs_temp(er_ref, temp_coef, temp):
    """根據溫度返回介電常數"""
    return er_ref * (1 + temp_coef * (temp - 25))

def loss_tangent_vs_temp(tan_d_ref, tan_d_coef, temp):
    """根據溫度返回損耗角正切"""
    return max(tan_d_ref + tan_d_coef * (temp - 25), 1e-6)

# 微帶線特性阻抗計算
def microstrip_impedance(w, h, er, t=0.035):
    """計算微帶線特性阻抗"""
    w_m = w * 1e-3
    h_m = h * 1e-3
    t_m = t * 1e-3
    
    if w_m/h_m > 1:
        ereff = (er + 1)/2 + (er - 1)/(2*np.sqrt(1 + 12*h_m/w_m))
    else:
        ereff = (er + 1)/2 + (er - 1)/2 * (1/np.sqrt(1 + 12*h_m/w_m) + 0.04*(1 - w_m/h_m)**2)
    
    if w_m/h_m > 1:
        Z0 = 120*np.pi / (w_m/h_m + 1.393 + 2/3*np.log(w_m/h_m + 1.444)) / np.sqrt(ereff)
    else:
        Z0 = 60/np.sqrt(ereff) * np.log(8*h_m/w_m + w_m/(4*h_m))
    
    return Z0, ereff

# 計算溫度敏感性指標
def calculate_temperature_sensitivity(impedances, temperatures):
    """計算阻抗溫度敏感性"""
    # 線性藕合斜率
    if len(temperatures) > 1:
        slope, _ = np.polyfit(temperatures, impedances, 1)
        sensitivity_ppm = abs(slope / np.mean(impedances)) * 1e6
    else:
        sensitivity_ppm = 0
    
    # 總變化率
    total_variation = (max(impedances) - min(impedances)) / np.mean(impedances) * 100
    
    return sensitivity_ppm, total_variation

# 主分析函數
def analyze_materials(materials, temp_range, width, height):
    results = {}
    
    for material in materials:
        props = material_properties[material]
        impedances = []
        dielectric_constants = []
        loss_tangents = []
        effective_er = []
        
        for temp in temp_range:
            er = dielectric_constant_vs_temp(props["er_ref"], props["temp_coef"], temp)
            tan_d = loss_tangent_vs_temp(props["tan_d_ref"], props["tan_d_coef"], temp)
            Z0, ereff = microstrip_impedance(width, height, er)
            
            impedances.append(Z0)
            dielectric_constants.append(er)
            loss_tangents.append(tan_d)
            effective_er.append(ereff)
        
        # 計算溫度敏感性
        sensitivity_ppm, total_variation = calculate_temperature_sensitivity(impedances, temp_range)
        
        results[material] = {
            "impedances": impedances,
            "dielectric_constants": dielectric_constants,
            "loss_tangents": loss_tangents,
            "effective_er": effective_er,
            "sensitivity_ppm": sensitivity_ppm,
            "total_variation": total_variation,
            "properties": props
        }
    
    return results

# 運行分析
if st.sidebar.button("開始分析"):
    temp_range = np.linspace(temp_min, temp_max, 100)
    
    # 執行分析
    results = analyze_materials(materials, temp_range, width, height)
    
    # 創建可視化
    st.header("阻抗溫度特性比較")
    
    # 阻抗 vs 溫度
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    for material in materials:
        ax1.plot(temp_range, results[material]["impedances"], 
                label=f"{material} ({results[material]['sensitivity_ppm']:.0f} ppm/°C)", 
                linewidth=2)
    
    ax1.set_xlabel('溫度 (°C)')
    ax1.set_ylabel('特性阻抗 (Ω)')
    ax1.set_title('不同材料傳輸線阻抗溫度特性比較')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)
    
    # 介電常數 vs 溫度
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    for material in materials:
        ax2.plot(temp_range, results[material]["dielectric_constants"], 
                label=material, linewidth=2)
    
    ax2.set_xlabel('溫度 (°C)')
    ax2.set_ylabel('介電常數')
    ax2.set_title('不同材料介電常數溫度特性')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)
    
    # 詳細分析結果
    st.header("關鍵參數分析")
    
    # 創建比較表格
    st.subheader("材料性能比較表")
    comparison_data = []
    for material in materials:
        result = results[material]
        props = result["properties"]
        
        comparison_data.append({
            "材料": material,
            "介電常數": f"{props['er_ref']:.2f}",
            "溫度系數": f"{props['temp_coef']*1e6:.0f} ppm/°C",
            "損耗角正切": f"{props['tan_d_ref']:.4f}",
            "阻抗變化率": f"{result['total_variation']:.2f}%",
            "溫度敏感性": f"{result['sensitivity_ppm']:.0f} ppm/°C",
            "熱穩定性": props["thermal_stability"],
            "成本": props["cost"]
        })
    
    st.table(comparison_data)
    
    # 關鍵因素分析
    st.header("📊 阻抗溫度相關性的關鍵因素分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("主要影響因素")
        
        factors = [
            {"因素": "介電常數溫度系數", "影響程度": "高", "說明": "直接影響有效介電常數和阻抗"},
            {"因素": "材料熱膨脹系數", "影響程度": "中", "說明": "影響物理尺寸，間接影響阻抗"},
            {"因素": "損耗角正切溫度特性", "影響程度": "中", "說明": "影響信號質量和高頻性能"},
            {"因素": "初始介電常數", "影響程度": "中", "說明": "高介電常數材料通常對溫度更敏感"},
            {"因素": "傳輸線幾何結構", "影響程度": "低", "說明": "寬線比對溫度敏感性有調節作用"}
        ]
        
        for factor in factors:
            with st.expander(f"{factor['因素']} - 影響程度: {factor['影響程度']}"):
                st.write(factor["說明"])
    
    with col2:
        st.subheader("材料熱穩定性排名")
        
        # 按溫度敏感性排序
        sorted_materials = sorted(materials, key=lambda x: results[x]["sensitivity_ppm"])
        
        for i, material in enumerate(sorted_materials):
            sensitivity = results[material]["sensitivity_ppm"]
            variation = results[material]["total_variation"]
            
            st.metric(
                label=f"{i+1}. {material}",
                value=f"{sensitivity:.0f} ppm/°C",
                delta=f"{variation:.2f}% 總變化"
            )
    
    # 改善建議
    st.header("💡 改善阻抗溫度穩定性的建議")
    
    tab1, tab2, tab3, tab4 = st.tabs(["材料選擇", "設計優化", "補償技術", "系統級策略"])
    
    with tab1:
        st.subheader("材料選擇策略")
        
        st.markdown("""
        ### 優選材料特性：
        - **低溫度系數材料**: 選擇溫度系數絕對值 < 50 ppm/°C 的材料
        - **穩定介電常數**: Rogers系列、陶瓷基板等高溫穩定性材料
        - **低損耗材料**: 降低損耗角正切及其溫度依賴性
        
        ### 推薦材料：
        """)
        
        # 推薦材料列表
        good_materials = [m for m in materials if abs(material_properties[m]["temp_coef"]*1e6) < 100]
        for material in good_materials:
            st.write(f"✅ **{material}**: 溫度系數 {material_properties[material]['temp_coef']*1e6:.0f} ppm/°C")
    
    with tab2:
        st.subheader("設計優化方法")
        
        st.markdown("""
        ### 幾何結構優化：
        - **適當線寬比**: 優化w/h比率以降低溫度敏感性
        - **多層結構**: 使用對稱結構抵消熱應力
        - **熱管理設計**: 優化散熱路徑，降低溫度梯度
        
        ### 參數調整：
        """)
        
        # 計算最佳線寬建議
        optimal_width = height * 0.8  # 經驗值
        st.write(f"📏 **建議線寬**: {optimal_width:.2f} mm (基于當前基板厚度 {height} mm)")
        st.write(f"📐 **寬厚比**: {optimal_width/height:.2f} (目標範圍: 0.5-1.2)")
    
    with tab3:
        st.subheader("溫度補償技術")
        
        st.markdown("""
        ### 主動補償：
        - **溫度傳感器**: 實時監測PCB溫度
        - **可調匹配網絡**: 使用變容二極管或數字電容陣列
        - **自適應算法**: 基于溫度調整匹配參數
        
        ### 被動補償：
        - **材料組合**: 使用正負溫度系數材料組合
        - **機械補償**: 利用熱膨脹進行物理補償
        - **電路拓撲**: 選擇對溫度不敏感的電路結構
        """)
    
    with tab4:
        st.subheader("系統級策略")
        
        st.markdown("""
        ### 系統設計：
        - **熱隔離**: 將敏感電路與熱源隔離
        - **溫度控制**: 對關鍵區域進行主動溫控
        - **冗余設計**: 提供足夠的阻抗容差
        
        ### 測試驗證：
        - **溫度循環測試**: 驗證全溫度範圍性能
        - **加速老化測試**: 評估長期穩定性
        - **統計容差分析**: 考慮制造公差和溫度變化的綜合影響
        """)
    
    # 高級分析
    st.header("🔬 高級分析工具")
    
    if st.checkbox("顯示敏感性分析"):
        st.subheader("參數敏感性分析")
        
        # 分析不同參數對溫度敏感性的影響
        param_ranges = {
            "線寬變化": np.linspace(width*0.5, width*2, 10),
            "基板厚度變化": np.linspace(height*0.5, height*2, 10)
        }
        
        for param_name, param_range in param_ranges.items():
            sensitivities = []
            
            for param_val in param_range:
                if "線寬" in param_name:
                    temp_results = analyze_materials(["FR-4", "Rogers RO4350B"], temp_range, param_val, height)
                else:
                    temp_results = analyze_materials(["FR-4", "Rogers RO4350B"], temp_range, width, param_val)
                
                avg_sensitivity = np.mean([temp_results[m]["sensitivity_ppm"] for m in temp_results])
                sensitivities.append(avg_sensitivity)
            
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(param_range, sensitivities, 'o-', linewidth=2)
            ax.set_xlabel(param_name)
            ax.set_ylabel('平均溫度敏感性 (ppm/°C)')
            ax.set_title(f'{param_name}對溫度敏感性的影響')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

else:
    st.info("請在左側選擇要比較的材料，然後點擊'開始分析'按鈕")

# 添加總結
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 關鍵發現
1. **介電常數溫度系數**是影響阻抗溫度穩定性的最主要因素
2. **低損耗材料**通常具有更好的溫度穩定性
3. **幾何優化**可以部分補償溫度影響
4. **系統級熱管理**對高頻應用至關重要
""")
