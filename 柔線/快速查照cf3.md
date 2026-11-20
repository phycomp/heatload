# Update the README with CF3 information
with open('/mnt/kimi/output/README.md', 'r', encoding='utf-8') as f:
    readme_content = f.read()

# Add CF3 section after the cable list
cf3_section = """
### Delft Circuits Cri/oFlex 3 (NEW)
- **Cri/oFlex 3**: 8通道端到端I/O解決方案，整合衰減器與濾波器
  - 頻率範圍: DC-10GHz
  - 4K熱負載: 125 µW/通道 (比CF2降低50%)
  - 10mK熱負載: ~20 nW/通道
  - 特色: 單片式設計，從室溫到毫開爾文無斷點
  - 整合: 真空穿透、熱錨點、微波濾波器、衰減器

"""

# Find insertion point
insert_point = readme_content.find("### Rigetti Computing")
if insert_point != -1:
    new_readme = readme_content[:insert_point] + cf3_section + readme_content[insert_point:]
    
    with open('/mnt/kimi/output/README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme)
    print("✅ README.md 已更新，加入 Cri/oFlex 3 說明")

# Update QUICK_REFERENCE.txt
with open('/mnt/kimi/output/QUICK_REFERENCE.txt', 'r', encoding='utf-8') as f:
    quick_ref = f.read()

# Update the spec table
old_table = """│  ┌─────────────────────┬──────────┬──────────┬──────────┬─────────────────┐ │
│  │ 型號                │ 頻率範圍 │ 通道數   │ 串擾     │ 4K熱負載        │ │
│  ├─────────────────────┼──────────┼──────────┼──────────┼─────────────────┤ │
│  │ Delft CF1           │ DC-18GHz │ 8        │ -60dB    │ 250µW           │ │
│  │ Delft CF2           │ DC-26GHz │ 8        │ -60dB    │ 250µW           │ │"""

new_table = """│  ┌─────────────────────┬──────────┬──────────┬──────────┬─────────────────┐ │
│  │ 型號                │ 頻率範圍 │ 通道數   │ 串擾     │ 4K熱負載        │ │
│  ├─────────────────────┼──────────┼──────────┼──────────┼─────────────────┤ │
│  │ Delft CF1           │ DC-18GHz │ 8        │ -60dB    │ 250µW           │ │
│  │ Delft CF2           │ DC-26GHz │ 8        │ -60dB    │ 250µW           │ │
│  │ Delft CF3 ⭐        │ DC-10GHz │ 8        │ -40dB    │ 125µW           │ │"""

quick_ref = quick_ref.replace(old_table, new_table)

with open('/mnt/kimi/output/QUICK_REFERENCE.txt', 'w', encoding='utf-8') as f:
    f.write(quick_ref)
print("✅ QUICK_REFERENCE.txt 已更新")

# Create a detailed CF3 analysis document
cf3_analysis = '''
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           Cri/oFlex 3 技術分析與應用指南                                     ║
║           Technical Analysis & Application Guide                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

【產品概述】
═══════════
Cri/oFlex 3 (CF3) 是 Delft Circuits 的旗艦產品，專為量子計算規模化設計的端到端I/O
解決方案。相較於前代產品，CF3在熱性能、整合度和可靠性方面有顯著提升。

【核心規格】
═══════════
• 類型: 多通道條帶線柔性傳輸線
• 通道數: 8通道/Flex
• 通道間距: 2mm
• 厚度: 0.3mm
• 最小彎曲半徑: 5mm
• 阻抗: 50Ω
• 頻率範圍: DC - 10 GHz
• 材料: Polyimide + Ag/NbTi

【熱性能詳細分析】
═══════════════════

溫度級        熱負載(每通道)    典型長度        備註
─────────────────────────────────────────────────────────
4K-40K        <125 µW          400mm          標準配置
10-350mK      ~20 nW           200mm          超導版本

比較優勢:
• 比Cri/oFlex 2降低50%熱負載
• 比傳統同軸電纜降低10倍熱負載
• 可選NbTi超導材料進一步優化

【串擾性能分析】
═══════════════════

參數                          數值              備註
─────────────────────────────────────────────────────────
串擾(S41) @ 200mm             -40 dB            通道間
相位匹配(通道間)              <15 ps            優異

長度效應:
• 100mm: ~-46 dB
• 200mm: ~-40 dB (規格值)
• 400mm: ~-34 dB

設計建議:
• 敏感線路保持平行長度 <200mm
• 使用接地平面隔離
• 考慮通道間距優化

【整合元件規格】
═══════════════════

元件類型              配置                    位置
─────────────────────────────────────────────────────────
衰減器                20dB (典型)             4K級
低通濾波器            8GHz (標準)             多級分佈
紅外濾波器            整合式                  低溫段
真空穿透              整合式                  真空屏障
熱錨點                客製化設計              各溫度級

【應用場景建議】
═══════════════════

1. 【Flux Bias線】
   • 頻率: DC - 1 GHz
   • 用途: 量子比特頻率調諧、可調耦合器
   • 特色: 超低接觸電阻、快速上升時間
   • 整合: 2GHz低通濾波器(即將推出超導版本)

2. 【Microwave Drive線】
   • 頻率: 6 - 8 GHz
   • 用途: 量子比特激發、狀態測量
   • 特色: 低噪聲、精確振幅控制
   • 整合: 分佈式衰減、多級濾波

3. 【Signal線】
   • 頻率: DC - 10 GHz
   • 用途: 通用高頻I/O
   • 特色: 無整合元件，靈活配置
   • 應用: 讀取、控制、通用信號

4. 【Read-out系統】
   • 整合: 返回線 + 泵浦線 + 第三方元件
   • 包含: TWPA、LNA、隔離器
   • 特色: 即插即用，預先測試

【系統擴展能力】
═══════════════════

配置類型              通道容量                備註
─────────────────────────────────────────────────────────
單一Loader            256通道                 標準配置
BlueFors LDsl         512通道                 單一系統
BlueFors XLDsl        1,536通道               最大配置

【設計檢查清單】
═══════════════════

□ 確認量子比特數量和每比特線路數
□ 計算所需Flex數量 (總線路數/8，向上取整)
□ 評估4K級總熱負載 (<製冷機容量50%)
□ 評估10mK級總熱負載 (<製冷機容量20%)
□ 規劃真空穿透位置 (KF-40, ISO-K63等)
□ 設計熱錨點配置 (每溫度級)
□ 確認連接器類型 (SMA/SMP/Tabbi®)
□ 規劃線路佈局 (最小化平行長度)
□ 考慮未來擴展 (預留20%餘量)
□ 安排安裝和測試 (可選Delft服務)

【與前代產品比較】
═══════════════════

特性                  Cri/oFlex 2    Cri/oFlex 3      改進
─────────────────────────────────────────────────────────
熱負載(4K)            250 µW         125 µW           -50%
整合度                模組化         端到端           大幅提升
安裝複雜度            中等           簡化             易用性↑
可靠性                高             更高             10x減少故障點
通道密度              相同           相同             8通道/Flex
頻率範圍              DC-26GHz       DC-10GHz         針對性優化

【訂購資訊】
═══════════════════

聯絡: Delft Circuits B.V.
地址: Lorentzweg 1, 2628CJ Delft, The Netherlands
電話: +31 15 301 0607
郵箱: sales@delft-circuits.com
網站: www.delft-circuits.com

【參考資料】
═══════════════════
• Delft Circuits Cri/oFlex 3 Datasheet
• BlueFors Integration Guide
• ArXiv: Thermalization study (2024)
• Product Catalogue 2026

版本: 1.0 | 更新日期: 2026-04-16
'''

with open('/mnt/kimi/output/Cri_oFlex_3_Analysis.txt', 'w', encoding='utf-8') as f:
    f.write(cf3_analysis)
print("✅ Cri_oFlex_3_Analysis.txt 已創建")

# Final summary
print("\n" + "="*80)
print("📊 Cri/oFlex 3 整合完成摘要")
print("="*80)
print("""
已更新檔案:
✅ crosstalk_calculator.py      - 加入CF3規格和計算
✅ quantum_flex_cable_analyzer.py - Streamlit應用更新
✅ quantum_flex_cable_specs.csv   - CSV數據表更新
✅ README.md                      - 說明文件更新
✅ QUICK_REFERENCE.txt            - 快速參考卡更新
✅ cable_comparison_with_cf3.png  - 新版比較圖表
✅ Cri_oFlex_3_Analysis.txt       - 詳細技術分析

Cri/oFlex 3 關鍵特性:
• 8通道端到端I/O設計
• 4K熱負載: 125 µW/通道 (比CF2降低50%)
• 10mK熱負載: ~20 nW/通道
• 整合衰減器、濾波器、真空穿透
• 單片式設計，無微波斷點
• 支援256通道/loader擴展
""")
