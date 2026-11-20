from 佈局Util import CF3LayoutCalculator
# 建立計算器 (使用 CF3 標準參數)
from streamlit import empty, pyplot
from streamlit import sidebar, radio, text_input, empty
MENU, 表單=[], ['佈局', '簡例', '示範']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
狀態=empty()
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單):
  pass
elif menu==MENU[0]: #佈局
  calc = CF3LayoutCalculator(
      n_channels=8,
      pitch_mm=2.0,
      signal_width_um=35.0,
  )

  # 列印完整規格
  calc.print_summary()

  # 獲取結構化數據
  summary = calc.get_summary()
  狀態.code(['結構化數據', summary])
  #['結構化數據', {'stackup': {'total_thickness_um': 300, 'total_thickness_mm': 0.3, 'dielectric_thickness_um': 15, 'signal_layer_thickness_um': 2, 'layers': [{'index': 0, 'name': '保護層 (上)', 'material': 'Polyimide', 'thickness_um': 15, 'thickness_mm': 0.015, 'y_bot_um': 0, 'y_top_um': 15, 'y_center_um': 7.5, 'y_bot_mm': 0.0, 'y_top_mm': 0.015, 'y_center_mm': 0.0075, 'is_signal': False, 'is_ground': False, 'is_dielectric': True}, {'index': 1, 'name': '接地層 (上)', 'material': 'NbTi', 'thickness_um': 5, 'thickness_mm': 0.005, 'y_bot_um': 15, 'y_top_um': 20, 'y_center_um': 17.5, 'y_bot_mm': 0.015, 'y_top_mm': 0.02, 'y_center_mm': 0.0175, 'is_signal': False, 'is_ground': True, 'is_dielectric': False}, {'index': 2, 'name': '介電層 (上)', 'material': 'Polyimide', 'thickness_um': 129, 'thickness_mm': 0.129, 'y_bot_um': 20, 'y_top_um': 149, 'y_center_um': 84.5, 'y_bot_mm': 0.02, 'y_top_mm': 0.149, 'y_center_mm': 0.0845, 'is_signal': False, 'is_ground': False, 'is_dielectric': True}, {'index': 3, 'name': '訊號層', 'material': 'NbTi', 'thickness_um': 2, 'thickness_mm': 0.002, 'y_bot_um': 149, 'y_top_um': 151, 'y_center_um': 150.0, 'y_bot_mm': 0.149, 'y_top_mm': 0.151, 'y_center_mm': 0.15, 'is_signal': True, 'is_ground': False, 'is_dielectric': False}, {'index': 4, 'name': '介電層 (下)', 'material': 'Polyimide', 'thickness_um': 129, 'thickness_mm': 0.129, 'y_bot_um': 151, 'y_top_um': 280, 'y_center_um': 215.5, 'y_bot_mm': 0.151, 'y_top_mm': 0.28, 'y_center_mm': 0.2155, 'is_signal': False, 'is_ground': False, 'is_dielectric': True}, {'index': 5, 'name': '接地層 (下)', 'material': 'NbTi', 'thickness_um': 5, 'thickness_mm': 0.005, 'y_bot_um': 280, 'y_top_um': 285, 'y_center_um': 282.5, 'y_bot_mm': 0.28, 'y_top_mm': 0.285, 'y_center_mm': 0.2825, 'is_signal': False, 'is_ground': True, 'is_dielectric': False}, {'index': 6, 'name': '保護層 (下)', 'material': 'Polyimide', 'thickness_um': 15, 'thickness_mm': 0.015, 'y_bot_um': 285, 'y_top_um': 300, 'y_center_um': 292.5, 'y_bot_mm': 0.285, 'y_top_mm': 0.3, 'y_center_mm': 0.2925, 'is_signal': False, 'is_ground': False, 'is_dielectric': True}]}, 'geometry': {'n_channels': 8, 'pitch_mm': 2.0, 'signal_width_um': 35.0, 'signal_width_mm': 0.035, 'base_total_width_mm': 14.035, 'target_total_width_mm': 14.335, 'recommended_total_width_mm': 14.335, 'edge_margin_mm': 0.15000000000000036, 'channel_gap_mm': 1.965, 'channel_positions': [{'index': 0, 'x_center_mm': -7.0, 'x_left_mm': -7.0175, 'x_right_mm': -6.9825}, {'index': 1, 'x_center_mm': -5.0, 'x_left_mm': -5.0175, 'x_right_mm': -4.9825}, {'index': 2, 'x_center_mm': -3.0, 'x_left_mm': -3.0175, 'x_right_mm': -2.9825}, {'index': 3, 'x_center_mm': -1.0, 'x_left_mm': -1.0175, 'x_right_mm': -0.9825}, {'index': 4, 'x_center_mm': 1.0, 'x_left_mm': 0.9825, 'x_right_mm': 1.0175}, {'index': 5, 'x_center_mm': 3.0, 'x_left_mm': 2.9825, 'x_right_mm': 3.0175}, {'index': 6, 'x_center_mm': 5.0, 'x_left_mm': 4.9825, 'x_right_mm': 5.0175}, {'index': 7, 'x_center_mm': 7.0, 'x_left_mm': 6.9825, 'x_right_mm': 7.0175}]}, 'clearance': {'10h_min_mm': 0.15, '10h_min_um': 150.0, '5w_min_mm': 0.17500000000000002, '5w_min_um': 175.00000000000003, 'edge_margin_mm': 0.15000000000000036, 'edge_margin_um': 150.00000000000034, 'channel_gap_mm': 1.965, 'channel_gap_um': 1965.0, 'meets_10h': True, 'meets_5w': True}, 'electrical': {'estimated_crosstalk_db': -40.0, 'estimated_il_db_per_m': 1.5, 'propagation_delay_ns_per_m': 5.6, 'cutoff_frequency_ghz': 18.0}, 'thermal': {'heat_load_ag_uw_per_ch': 125, 'heat_load_nbti_nw_per_ch': 20, 'operating_temp_min_k': 0.001, 'operating_temp_max_k': 400}, 'impedance': {'z0_ohm': -19.710303082411947, 'target_ohm': 50.0, 'deviation_percent': -139.42060616482388, 'epsilon_r': 3.4, 'meets_spec': False}}]
  # 狀態.code(輸入)
  輸入=f"總寬度: {summary['geometry']['target_total_width_mm']:.3f} mm"
  輸入+=f"邊緣 Clearance: {summary['clearance']['edge_margin_mm']:.3f} mm"
elif menu==MENU[1]: #
  pass
elif menu==MENU[2]: #
# ============================================================
# 使用範例
# ============================================================

    """示範使用方式"""
    
    # 1. 使用 CF3 標準參數
    輸入="\n" + "=" * 70
    輸入+="範例 1: CF3 標準設計"
    # 輸入+="=" * 70
    
    calc1 = CF3LayoutCalculator(
        n_channels=8,
        pitch_mm=2.0,
        signal_width_um=35.0,
        conductor_material='NbTi',
        use_5w_rule=True,
        use_10h_rule=True,
    )
    第一=calc1.print_summary()
    狀態.code(第一)
    
    # 2. 自訂總寬度
    # 輸入+="\n" + "=" * 70
    輸入+="範例 2: 自訂總寬度 16mm\n"
    # 輸入+="=" * 70
    
    calc2 = CF3LayoutCalculator(
        n_channels=8,
        pitch_mm=2.0,
        signal_width_um=35.0,
        total_width_mm=16.0,
        conductor_material='Ag',
    )
    態狀=empty()
    第二=calc2.print_summary()
    態狀.code(第二)
    
    # 3. 自訂通道數與 Pitch
    # 輸入+="\n" + "=" * 70
    輸入="範例 3: 4 通道, Pitch 3mm\n"
    # 輸入+="=" * 70
    
    calc3 = CF3LayoutCalculator(
        n_channels=4,
        pitch_mm=3.0,
        signal_width_um=50.0,
        conductor_material='NbTi',
    )
    第三=calc3.print_summary()
    詳述=empty()
    詳述.code(第三)
    
    # 4. 獲取結構化數據
    # 輸入+="\n" + "=" * 70
    輸入="範例 4: 獲取結構化數據 (JSON 格式)\n"
    # 輸入+="=" * 70
    
    述詳=empty()
    import json
    summary = calc1.get_summary()
    
    # 簡化輸出
    輸入=json.dumps({'geometry':summary['geometry'], 'clearance':summary['clearance'], 'impedance':summary['impedance'], }, indent=2, default=str)
    述詳.code(輸入)
