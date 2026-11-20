# Create a comprehensive comparison matrix visualization
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Create radar chart for multi-dimensional comparison
from math import pi

def create_radar_chart(cable_db):
    """創建雷達圖比較"""
    # 選擇要比較的線材
    selected_cables = ['Delft_CF2', 'Rigetti_Flex', 'Rosenberger_047', 'Amphenol_SMP']
    
    # 定義比較維度 (數值越大越好，需要正規化)
    categories = ['頻率範圍', '通道密度', '熱效率', '隔離度', '柔性', '相位穩定性']
    N = len(categories)
    
    # 計算分數 (0-10)
    scores = {}
    for key in selected_cables:
        c = cable_db[key]
        score = [
            min(c.attenuation_6ghz / 20, 10),  # 頻率範圍 (反向，越低越好)
            c.channels_per_flex,  # 通道密度
            10 - (c.thermal_load_4k / 50),  # 熱效率 (反向)
            abs(c.isolation_db) / 10,  # 隔離度
            10 - c.bend_radius,  # 柔性 (反向，越小越好)
            8 if 'Excellent' in c.phase_stability else 5  # 相位穩定性
        ]
        scores[f"{c.manufacturer} {c.model}"] = score
    
    # 創建圖表
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # 計算角度
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    # 繪製每個線材
    colors = plt.cm.Set2(np.linspace(0, 1, len(selected_cables)))
    for i, (name, score) in enumerate(scores.items()):
        values = score + score[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=name, color=colors[i])
        ax.fill(angles, values, alpha=0.15, color=colors[i])
    
    # 設置標籤
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], color='grey', size=10)
    ax.grid(True)
    
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
    plt.title('Multi-Dimensional Cable Comparison\\n(雷達圖比較)', 
             fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('/mnt/kimi/output/radar_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ 雷達圖比較已保存: /mnt/kimi/output/radar_comparison.png")
    plt.show()

# 執行雷達圖生成
exec(open('/mnt/kimi/output/crosstalk_calculator.py').read())
cables = get_cable_database()
create_radar_chart(cables)
