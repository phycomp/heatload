from matplotlib.pyplot import axhline, figure, grid, plot, savefig, title, xlabel, ylabel
from numpy import max
from random import gauss
import random
import numpy as np
from skrf import Frequency
from skrf.media import DefinedGammaZ0
import matplotlib.pyplot as plt

freq = Frequency(start=4.0, stop=10.0, npoints=201, unit='ghz')
#ref_media = skrf.media.DefinedGammaZ0(frequency=freq, z0=50.0)
ref_media = DefinedGammaZ0(frequency=freq, z0=50.0)
stripline_core = ref_media.line(d=10, unit='mm', z0=50.10)
z_pad = 50.1 * (27.27 / 68.5)
taper_segment = ref_media.line(d=300, unit='um', z0=(50.1 + z_pad)/2)

NUM_SIMULATIONS = 100
passed_count = 0

plt.figure(figsize=(10, 5))
for i in range(NUM_SIMULATIONS):
    l_rand = max(0.1e-9, random.gauss(0.8e-9, 0.15e-9))
    bond_l = ref_media.inductor(L=l_rand)
    bond_r = ref_media.inductor(L=l_rand)
    mc_net = bond_l ** taper_segment ** stripline_core ** taper_segment ** bond_r
    
    max_s11 = np.max(mc_net.s_db[:, 0, 0])
    color_line = 'green' if max_s11 <= -20.0 else 'red'
    if max_s11 <= -20.0: passed_count += 1
    plt.plot(freq.f_ghz, mc_net.s_db[:, 0, 0], color=color_line, alpha=0.3)

plt.axhline(-20, color='black', linestyle='--', label='Quantum Spec (-20 dB)')
plt.title(f"Monte Carlo Tolerance Analysis - Yield: {passed_count}%")
plt.xlabel("Frequency (GHz)")
plt.ylabel("S11 (dB)")
plt.grid(True, alpha=0.3)
plt.savefig('monte_carlo_yield.png', dpi=150)
print("Monte Carlo analysis figure saved.")
