from streamlit import button, download_button, file_uploader, pyplot, subheader, title
from matplotlib.pyplot import subplots
from numpy import loadtxt, max, unique
import subprocess

title("VASP 模擬計算")

# 上傳檔案
poscar = file_uploader("上傳 POSCAR", type="txt")
incar = file_uploader("上傳 INCAR", type="txt")
kpath = file_uploader("上傳 KPATH", type="txt")

if button("執行計算"):
    # 儲存檔案
    with open("POSCAR", "wb") as f:
        f.write(poscar.read())
    with open("INCAR", "wb") as f:
        f.write(incar.read())
    with open("KPATH", "wb") as f:
        f.write(kpath.read())
    
    # 執行 VASP
    subprocess.run("vasp_std", shell=True)
    
    # 畫圖
    subheader("能帶圖")
    data = np.loadtxt('EIGENVAL', skiprows=8)
    kpoints = np.unique(data[:,0])
    bands = data[:,1]
    nbands = int(np.max(data[:,1]))
    fig, ax = plt.subplots()
    for i in range(nbands):
        band_data = bands[i::nbands]
        ax.plot(kpoints, band_data)
    pyplot(fig)
    
    subheader("DOS 圖")
    dos_data = np.loadtxt('DOSCAR', skiprows=6)
    energy = dos_data[:,0]
    dos = dos_data[:,1]
    fig, ax = plt.subplots()
    ax.plot(energy, dos)
    pyplot(fig)

# 下載結果
subheader("下載結果")
download_button("下載 EIGENVAL", "EIGENVAL")
download_button("下載 DOSCAR", "DOSCAR")
