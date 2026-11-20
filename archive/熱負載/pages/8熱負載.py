from matplotlib.pyplot import savefig, show, tight_layout
from numpy import array, exp, linspace
from matplotlib.pyplot import savefig, show, subplots, tight_layout
from numpy import array, exp, linspace
from streamlit import empty, pyplot, sidebar, radio, text_input
from matplotlib.pyplot import rcParams, savefig, show, subplots, tight_layout
狀態=empty()
#狀態.code()
#import numpy as np
#import matplotlib.pyplot as plt

def thermal_population(E, T):
    """Thermal population of a state with energy E above ground state"""
    if T == 0:
        return 0
    return exp(-E / (k_B * T))

def thermal_photon_number(f, T):
    """Average thermal photon number for frequency f at temperature T"""
    if T == 0:
        return 0
    x = h * f / (k_B * T)
    if x > 50:  # Avoid overflow
        return 0
    return 1 / (exp(x) - 1)

with sidebar:
    # Constants
    h = 6.626e-34  # Planck's constant (J·s)
    k_B = 1.381e-23  # Boltzmann constant (J/K)

    # Transmon parameters (typical values)
    # Transition frequency f01 ~ 5-6 GHz
    f01 = 5.5e9  # Hz (typical transmon frequency)
    E01 = h * f01  # Energy of 0->1 transition (J)

    # Anharmonicity alpha ~ -200 to -300 MHz (typical for transmon)
    alpha = -250e6  # Hz
    E_alpha = h * abs(alpha)  # Anharmonicity energy (J)

    # Temperature range
    T_min = 0.010  # 10 mK
    T_max = 0.350  # 350 mK
    T_range = linspace(T_min, T_max, 1000)

    # Calculate thermal population and thermal photon number
    # For a harmonic oscillator at temperature T
    # n_th = 1 / (exp(hf/kT) - 1)
    # For transmon, we care about thermal excitation to |1> and |2>

    # Calculate thermal populations at each temperature
    pop_1 = array([thermal_population(E01, T) for T in T_range])
    pop_2 = array([thermal_population(E01 + h*abs(alpha), T) for T in T_range])
    n_th = array([thermal_photon_number(f01, T) for T in T_range])

    # Critical thresholds
    # For quantum computing, typically want thermal population < 1%
    # and thermal photon number < 0.01
    threshold_pop = 0.01
    threshold_n_th = 0.01

    # Find temperature where population exceeds threshold
    T_critical_pop = None
    T_critical_n_th = None

    for i, T in enumerate(T_range):
        if pop_1[i] > threshold_pop and T_critical_pop is None:
            T_critical_pop = T
        if n_th[i] > threshold_n_th and T_critical_n_th is None:
            T_critical_n_th = T

MENU, 表單=[], ['基礎', '熱負載', '熱光子']		#, '錯綜複雜', '二十四節氣'
for ndx, Menu in enumerate(表單): MENU.append(f'{ndx}{Menu}')
with sidebar:
  menu=radio('表單', MENU, horizontal=True, index=0)
  #欄股=multiselect('股市欄位', 股欄, default=股欄[0])
  srch=text_input('搜尋', '預設值', placeholder='搜尋')
if menu==len(表單): #
  pass
elif menu==MENU[2]: #
    fig, ax2= subplots(figsize=(10, 6))
    # Plot 2: Thermal photon number
    #ax2 = axes[1]
    ax2.semilogy(T_range * 1000, n_th, 'purple', linewidth=2, label='Thermal photon number n_th')
    ax2.axhline(y=threshold_n_th, color='gray', linestyle=':', label='0.01 threshold')
    ax2.axvline(x=T_critical_n_th*1000, color='green', linestyle='--', alpha=0.7)
    ax2.set_xlabel('Temperature (mK)', fontsize=12)
    ax2.set_ylabel('Average Thermal Photon Number', fontsize=12)
    ax2.set_title('Thermal Photon Number vs Temperature', fontsize=13)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 350])
    pyplot(fig)
elif menu==MENU[1]: #
    fig, ax1= subplots(figsize=(10, 6))
    # Plot
    # Plot 1: Thermal population vs temperature
    #ax1 = axes[0]
    ax1.semilogy(T_range * 1000, pop_1, 'b-', linewidth=2, label='|1⟩ population')
    ax1.semilogy(T_range * 1000, pop_2, 'r--', linewidth=2, label='|2⟩ population')
    ax1.axhline(y=threshold_pop, color='gray', linestyle=':', label='1% threshold')
    ax1.axvline(x=T_critical_pop*1000, color='green', linestyle='--', alpha=0.7)
    ax1.set_xlabel('Temperature (mK)', fontsize=12)
    ax1.set_ylabel('Thermal Population', fontsize=12)
    ax1.set_title('Transmon Thermal Population vs Temperature', fontsize=13)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 350])
    pyplot(fig)

elif menu==MENU[0]: #熱負載

#tight_layout()
#savefig('/mnt/agents/output/transmon_thermal_analysis.png', dpi=150, bbox_inches='tight')
#show()

    輸出=f"Transmon frequency: {f01/1e9:.1f} GHz\n"
    輸出+=f"Anharmonicity: {alpha/1e6:.0f} MHz\n"
    輸出+=f"0->1 transition energy: {E01/(h*1e9):.1f} GHz\n"
    輸出+=f"1->2 transition energy: {E01/(h*1e9) + abs(alpha)/1e9:.3f} GHz\n"
    輸出+=f"Temperature where thermal population |1> exceeds 1%: {T_critical_pop*1000:.1f} mK\n"
    輸出+=f"Temperature where thermal photon number exceeds 0.01: {T_critical_n_th*1000:.1f} mK\n"

    # At 350mK
    T_test = 0.350
    pop_1_350mK = thermal_population(E01, T_test)
    pop_2_350mK = thermal_population(E01 + h*abs(alpha), T_test)
    n_th_350mK = thermal_photon_number(f01, T_test)

    輸出+=f"\nAt 350 mK:"
    輸出+=f"  Thermal population of |1>: {pop_1_350mK:.4f} ({pop_1_350mK*100:.2f}%)"
    輸出+=f"  Thermal population of |2>: {pop_2_350mK:.6f}"
    輸出+=f"  Thermal photon number: {n_th_350mK:.4f}"

    # At 10mK
    T_test = 0.010
    pop_1_10mK = thermal_population(E01, T_test)
    n_th_10mK = thermal_photon_number(f01, T_test)

    輸出+=f"\nAt 10 mK:"
    輸出+=f"  Thermal population of |1>: {pop_1_10mK:.6f} ({pop_1_10mK*100:.4f}%)\n"
    輸出+=f"  Thermal photon number: {n_th_10mK:.6f}\n"
    輸出+=f"\nFigure saved to /mnt/agents/output/transmon_thermal_analysis.png"
    狀態.code(輸出)
