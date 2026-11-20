#!/usr/bin/env python
# cf3_batch_generator.py
# 批次產生三視圖

import os
import json
from 傳輸線佈局 import LayoutCalculator
from 主要三視圖 import draw_front_view, draw_side_view, draw_top_view
from xls分頁匯出 import 匯出規格


def batch_generate(config_list, output_dir="output"):
    """
    批次產生三視圖
    
    Args:
        config_list: 參數設定列表
        output_dir: 輸出目錄
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for i, config in enumerate(config_list):
        print(f"\n處理方案 {i+1}/{len(config_list)}:")
        print(f"  通道數: {config.get('n_channels', 8)}")
        print(f"  Pitch: {config.get('pitch_mm', 2.0)} mm")
        print(f"  總寬度: {config.get('total_width_mm', None)} mm")
        
        # 計算
        calc = LayoutCalculator(**config)
        
        # 繪製三視圖
        front_fig = draw_front_view(calc)
        side_fig = draw_side_view(calc)
        top_fig = draw_top_view(calc)
        
        # 儲存 PNG
        prefix = f"{output_dir}/cf3_{i+1:02d}"
        front_fig.savefig(f"{prefix}_front.png", dpi=300, bbox_inches='tight')
        side_fig.savefig(f"{prefix}_side.png", dpi=300, bbox_inches='tight')
        top_fig.savefig(f"{prefix}_top.png", dpi=300, bbox_inches='tight')
        
        # 儲存 Excel
        匯出規格(calc, front_fig, side_fig, top_fig, f"{prefix}_spec.xlsx")
        
        # 關閉圖形
        import matplotlib.pyplot as plt
        # plt.close('all')
        
        print(f"  ✅ 輸出: {prefix}_*.png")
        print(f"  ✅ 輸出: {prefix}_spec.xlsx")


# 批次設定範例
if __name__ == "__main__":
    configs = [
        {
            "n_channels": 8,
            "pitch_mm": 2.0,
            "signal_width_um": 35.0,
            "conductor_material": "NbTi",
        },
        {
            "n_channels": 8,
            "pitch_mm": 2.0,
            "signal_width_um": 35.0,
            "total_width_mm": 16.615,
            "conductor_material": "NbTi",
        },
        {
            "n_channels": 8,
            "pitch_mm": 2.0,
            "signal_width_um": 40.0,
            "total_width_mm": 17.0,
            "conductor_material": "Ag",
        },
        {
            "n_channels": 4,
            "pitch_mm": 3.0,
            "signal_width_um": 50.0,
            "conductor_material": "NbTi",
        },
    ]
    
    batch_generate(configs)
