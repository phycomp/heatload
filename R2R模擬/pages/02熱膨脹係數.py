from matplotlib.pyplot import savefig, show, subplots, tight_layout
from numpy import abs, arange, array, zeros
# Let's create a more detailed analysis with temperature-dependent CTE data
# and provide specific adhesive recommendations

import numpy as np
import matplotlib.pyplot as plt
from streamlit import empty, pyplot, sidebar, text_input, radio, session_state
# Temperature-dependent CTE data (approximate based on literature)
# For cryogenic temperatures, CTE decreases significantly

T_points = array([300, 250, 200, 150, 100, 77, 50, 20, 4, 0.015])

# RO4350B CTE (estimated temperature dependence)
# CTE decreases at low temperatures due to glassy state
ro4350b_cte_x_T = array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]) * 1e-6
ro4350b_cte_y_T = array([12, 11, 10, 9, 7, 6, 5, 4, 3, 2]) * 1e-6
ro4350b_cte_z_T = array([32, 30, 28, 25, 22, 20, 18, 15, 12, 10]) * 1e-6

# Kapton CTE (estimated temperature dependence)
# Polyimide has lower CTE at cryogenic temperatures
kapton_cte_T = array([20, 18, 16, 14, 12, 10, 8, 6, 5, 4]) * 1e-6

# Stycast 2850FT CTE (estimated temperature dependence)
# Filled epoxy maintains relatively stable CTE
stycast_cte_T = array([35, 34, 33, 32, 31, 30, 28, 25, 22, 20]) * 1e-6

# Calculate cumulative thermal contraction
# Using trapezoidal integration

def calculate_contraction(T, cte):
    contraction = zeros(len(T))
    for i in range(1, len(T)):
        # Trapezoidal integration
        dT = T[i-1] - T[i]  # Temperature difference (cooling)
        avg_cte = (cte[i-1] + cte[i]) / 2
        contraction[i] = contraction[i-1] + avg_cte * dT
    return contraction
# Create comprehensive plot
#fig, ((ax1, ax2), (ax3, ax4)) = subplots(2, 2, figsize=(16, 12))

狀態=empty()
MENU, 表單=[], ['計算', 'CTE', '熱膨脹', 'Mismatch', 'Adhesive', '結論']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
  try:
    ro4350b_contraction_x = session_state['ro4350b_contraction_x']
    ro4350b_contraction_y = session_state['ro4350b_contraction_y']
    ro4350b_contraction_z = session_state['ro4350b_contraction_z']
    kapton_contraction = session_state['kapton_contraction']
    stycast_contraction = session_state['stycast_contraction']
    mismatch_x = session_state['mismatch_x']#=abs(ro4350b_contraction_x - kapton_contraction)
    mismatch_y = session_state['mismatch_y']#= abs(ro4350b_contraction_y - kapton_contraction)
    mismatch_z = session_state['mismatch_z']#= abs(ro4350b_contraction_z - kapton_contraction)
    mismatch_stycast_kapton = session_state['mismatch_stycast_kapton']#= abs(stycast_contraction - kapton_contraction)
    mismatch_stycast_ro4350b = session_state['mismatch_stycast_ro4350b']#= abs(stycast_contraction - ro4350b_contraction_x)
  except:
    ro4350b_contraction_x = session_state['ro4350b_contraction_x']=calculate_contraction(T_points, ro4350b_cte_x_T)
    ro4350b_contraction_y = session_state['ro4350b_contraction_y']= calculate_contraction(T_points, ro4350b_cte_y_T)
    ro4350b_contraction_z = session_state['ro4350b_contraction_z']= calculate_contraction(T_points, ro4350b_cte_z_T)
    kapton_contraction = session_state['kapton_contraction']=calculate_contraction(T_points, kapton_cte_T)
    stycast_contraction = session_state['stycast_contraction']=calculate_contraction(T_points, stycast_cte_T)
    mismatch_x = session_state['mismatch_x']=abs(ro4350b_contraction_x - kapton_contraction)
    mismatch_y = session_state['mismatch_y']= abs(ro4350b_contraction_y - kapton_contraction)
    mismatch_z = session_state['mismatch_z']= abs(ro4350b_contraction_z - kapton_contraction)
    mismatch_stycast_kapton = session_state['mismatch_stycast_kapton']= abs(stycast_contraction - kapton_contraction)
    mismatch_stycast_ro4350b = session_state['mismatch_stycast_ro4350b']= abs(stycast_contraction - ro4350b_contraction_x)
if menu==len(表單): #
  pass
elif menu==MENU[5]: #
  # Print final values at 15mK
  #輸出="\n" + "=" * 80
  輸出="FINAL THERMAL CONTRACTION AT 15mK (from 300K)"
  #輸出+="=" * 80
  輸出+=f"\nRO4350B X-axis: {ro4350b_contraction_x[-1]*100:.4f}%"
  輸出+=f"\nRO4350B Y-axis: {ro4350b_contraction_y[-1]*100:.4f}%"
  輸出+=f"\nRO4350B Z-axis: {ro4350b_contraction_z[-1]*100:.4f}%"
  輸出+=f"\nKapton (PI):     {kapton_contraction[-1]*100:.4f}%"
  輸出+=f"\nStycast 2850FT:  {stycast_contraction[-1]*100:.4f}%"

  輸出+=f"\nMismatch at 15mK:"
  輸出+=f"\nRO4350B X vs Kapton: {mismatch_x[-1]*100:.4f}%"
  輸出+=f"\nRO4350B Y vs Kapton: {mismatch_y[-1]*100:.4f}%"
  輸出+=f"\nRO4350B Z vs Kapton: {mismatch_z[-1]*100:.4f}%"
  輸出+=f"\nStycast vs Kapton:   {mismatch_stycast_kapton[-1]*100:.4f}%"
  輸出+=f"\nStycast vs RO4350B:  {mismatch_stycast_ro4350b[-1]*100:.4f}%"
  狀態.code(輸出)
elif menu==MENU[4]: #
  fig, ax4=subplots(figsize=(10, 6))
  # Plot 4: Adhesive Selection Matrix
  adhesives = ['Stycast\n2850FT', 'KB 1631\nHTC-1', 'Polyimide\nAdhesive', 'Epoxy/PI\nBlend']
  cte_values = [35, 15, 20, 25]  # ppm/°C (approximate)
  thermal_cond = [1.25, 1.5, 0.3, 0.8]  # W/m·K
  outgassing = [0.25, 0.1, 0.05, 0.15]  # TML %

  x_pos = arange(len(adhesives))
  width = 0.25

  bars1 = ax4.bar(x_pos - width, cte_values, width, label='CTE (ppm/°C)', color='skyblue', alpha=0.8)
  bars2 = ax4.bar(x_pos, thermal_cond, width, label='Thermal Cond. (W/m·K)', color='lightcoral', alpha=0.8)
  bars3 = ax4.bar(x_pos + width, outgassing, width, label='Outgassing TML (%)', color='lightgreen', alpha=0.8)

  ax4.set_xlabel('Adhesive Type', fontsize=12)
  ax4.set_ylabel('Property Value', fontsize=12)
  ax4.set_title('Adhesive Comparison for Cryogenic Use', fontsize=14, fontweight='bold')
  ax4.set_xticks(x_pos)
  ax4.set_xticklabels(adhesives, fontsize=10)
  ax4.legend(fontsize=10, loc='upper right')
  ax4.grid(True, alpha=0.3, axis='y')
  pyplot(fig)
elif menu==MENU[3]: #
  # Plot 3: Mismatch Analysis
  fig, ax3= subplots(figsize=(10, 6))
  mismatch_x = session_state['mismatch_x']=abs(ro4350b_contraction_x - kapton_contraction)
  mismatch_y = session_state['mismatch_y']= abs(ro4350b_contraction_y - kapton_contraction)
  mismatch_z = session_state['mismatch_z']= abs(ro4350b_contraction_z - kapton_contraction)
  mismatch_stycast_kapton = session_state['mismatch_stycast_kapton']= abs(stycast_contraction - kapton_contraction)
  mismatch_stycast_ro4350b = session_state['mismatch_stycast_ro4350b']= abs(stycast_contraction - ro4350b_contraction_x)

  ax3.plot(T_points, mismatch_x*100, 'b-o', label='RO4350B X vs Kapton', linewidth=2, markersize=6)
  ax3.plot(T_points, mismatch_y*100, 'b--s', label='RO4350B Y vs Kapton', linewidth=2, markersize=6)
  ax3.plot(T_points, mismatch_z*100, 'b:^', label='RO4350B Z vs Kapton', linewidth=2, markersize=6)
  ax3.plot(T_points, mismatch_stycast_kapton*100, 'g-s', label='Stycast vs Kapton', linewidth=2, markersize=6)
  ax3.plot(T_points, mismatch_stycast_ro4350b*100, 'g--d', label='Stycast vs RO4350B', linewidth=2, markersize=6)
  ax3.set_xlabel('Temperature (K)', fontsize=12)
  ax3.set_ylabel('Thermal Mismatch (%)', fontsize=12)
  ax3.set_title('Thermal Expansion Mismatch', fontsize=14, fontweight='bold')
  ax3.legend(fontsize=10, loc='upper left')
  ax3.grid(True, alpha=0.3)
  ax3.set_xlim(0, 300)

  pyplot(fig)
elif menu==MENU[2]: #
  fig, ax2= subplots(figsize=(10, 6))
  # Plot 2: Cumulative Thermal Contraction
  #ro4350b_contraction_x=session_state['ro4350b_contraction_x']
  #ro4350b_contraction_y=session_state['ro4350b_contraction_y']
  #ro4350b_contraction_z=session_state['ro4350b_contraction_z']
  #kapton_contraction=session_state['kapton_contraction']
  #stycast_contraction = session_state['stycast_contraction']
  ax2.plot(T_points, ro4350b_contraction_x*100, 'b-o', label='RO4350B X', linewidth=2, markersize=6)
  ax2.plot(T_points, ro4350b_contraction_y*100, 'b--s', label='RO4350B Y', linewidth=2, markersize=6)
  ax2.plot(T_points, ro4350b_contraction_z*100, 'b:^', label='RO4350B Z', linewidth=2, markersize=6)
  ax2.plot(T_points, kapton_contraction*100, 'r-o', label='Kapton (PI)', linewidth=2, markersize=6)
  ax2.plot(T_points, stycast_contraction*100, 'g-s', label='Stycast 2850FT', linewidth=2, markersize=6)
  ax2.set_xlabel('Temperature (K)', fontsize=12)
  ax2.set_ylabel('Cumulative Contraction (%)', fontsize=12)
  ax2.set_title('Thermal Contraction During Cooling', fontsize=14, fontweight='bold')
  ax2.legend(fontsize=10, loc='upper left')
  ax2.grid(True, alpha=0.3)
  ax2.set_xlim(0, 300)

  pyplot(fig)
elif menu==MENU[1]: #
  pass
  fig, ax1= subplots(figsize=(10, 6))
  # Plot 1: CTE vs Temperature
  ax1.semilogy(T_points, ro4350b_cte_x_T*1e6, 'b-o', label='RO4350B X', linewidth=2, markersize=6)
  ax1.semilogy(T_points, ro4350b_cte_y_T*1e6, 'b--s', label='RO4350B Y', linewidth=2, markersize=6)
  ax1.semilogy(T_points, ro4350b_cte_z_T*1e6, 'b:^', label='RO4350B Z', linewidth=2, markersize=6)
  ax1.semilogy(T_points, kapton_cte_T*1e6, 'r-o', label='Kapton (PI)', linewidth=2, markersize=6)
  ax1.semilogy(T_points, stycast_cte_T*1e6, 'g-s', label='Stycast 2850FT', linewidth=2, markersize=6)
  ax1.set_xlabel('Temperature (K)', fontsize=12)
  ax1.set_ylabel('CTE (ppm/°C)', fontsize=12)
  ax1.set_title('Temperature-Dependent CTE', fontsize=14, fontweight='bold')
  ax1.legend(fontsize=10, loc='upper right')
  ax1.grid(True, alpha=0.3)
  ax1.set_xlim(0, 300)
  pyplot(fig)
elif menu==MENU[0]: #熱膨脹
  狀態.code([ro4350b_contraction_x, ro4350b_contraction_y, ro4350b_contraction_z, kapton_contraction, stycast_cte_T])


#tight_layout()
#savefig('/mnt/agents/output/cryogenic_adhesive_analysis.png', dpi=150, bbox_inches='tight')
#show()

