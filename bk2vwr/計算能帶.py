from matplotlib.pyplot import figure, plot, show, title, xlabel, ylabel
from numpy import loadtxt, max, unique
import numpy as np
import matplotlib.pyplot as plt
SYSTEM = Bi2Se3
ISTART = 0
ICHARG = 2
INIAR = 1
ENCUT = 400
EDIFF = 1E-7
NELM = 200
ISMEAR = 0
SIGMA = 0.05
LORBIT = 11
ISPIN = 2
LSORBIT = .TRUE.
LMAXMIX = 4
GGA_COMPAT = .F.
PREC = Accurate

*主要參數說明:*
- `LSORBIT = .TRUE.`: 打開自旋軌道耦合 (SOC)
- `ISPIN = 2`: 考慮自旋極化
- `LMAXMIX = 4`: 針對 d/f 軌域混合
- `ENCUT = 400`: 截斷能 (eV)
- `ISMEAR = 0`: 用 Gaussian smearing
- `SIGMA = 0.05`: smearing 寬度

# 能帶圖
def plot_bandstructure():
    # 假設 EIGENVAL 檔案已經產生
    data = np.loadtxt('EIGENVAL', skiprows=8)
    kpoints = np.unique(data[:,0])
    bands = data[:,1]
    nbands = int(np.max(data[:,1]))
    
    plt.figure(figsize=(8,6))
    for i in range(nbands):
        band_data = bands[i::nbands]
        plt.plot(kpoints, band_data)
    plt.xlabel('k-path')
    plt.ylabel('Energy (eV)')
    plt.title('Bi2Se3 Band Structure')
    plt.show()

# DOS 圖
def plot_dos():
    dos_data = np.loadtxt('DOSCAR', skiprows=6)
    energy = dos_data[:,0]
    dos = dos_data[:,1]
    
    plt.figure(figsize=(8,6))
    plt.plot(energy, dos)
    plt.xlabel('Energy (eV)')
    plt.ylabel('DOS')
    plt.title('Bi2Se3 DOS')
    plt.show()

# 主程式
if __name__ == '__main__':
    plot_bandstructure()
    plot_dos()

