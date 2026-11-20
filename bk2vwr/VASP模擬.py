from streamlit import button, download_button, error, file_uploader, pyplot, spinner, subheader, title
from matplotlib.pyplot import subplots
from numpy import loadtxt, max, unique
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import os

st.title("VASP 模擬計算")

# 上傳檔案
poscar = st.file_uploader("上傳 POSCAR", type="txt")
incar = st.file_uploader("上傳 INCAR", type="txt")
kpath = st.file_uploader("上傳 KPATH", type="txt")

if st.button("執行計算"):
    # 儲存檔案
    with open("POSCAR", "wb") as f:
        f.write(poscar.read())
    with open("INCAR", "wb") as f:
        f.write(incar.read())
    with open("KPATH", "wb") as f:
        f.write(kpath.read())
    
    # 執行 VASP
    with st.spinner("計算中..."):
        subprocess.run("vasp_std", shell=True)
    
    # 畫能帶圖
    st.subheader("能帶圖")
    try:
        data = np.loadtxt('EIGENVAL', skiprows=8)
        kpoints = np.unique(data[:,0])
        bands = data[:,1]
        nbands = int(np.max(data[:,1]))
        fig, ax = plt.subplots(figsize=(8,6))
        for i in range(nbands):
            band_data = bands[i::nbands]
            ax.plot(kpoints, band_data)
        ax.set_xlabel('k-path')
        ax.set_ylabel('Energy (eV)')
        ax.set_title('Bi2Se3 Band Structure')
        st.pyplot(fig)
    except:
        st.error("EIGENVAL 檔案錯誤")
    
    # 畫 DOS 圖
    st.subheader("DOS 圖")
    try:
        dos_data = np.loadtxt('DOSCAR', skiprows=6)
        energy = dos_data[:,0]
        dos = dos_data[:,1]
        fig, ax = plt.subplots(figsize=(8,6))
        ax.plot(energy, dos)
        ax.set_xlabel('Energy (eV)')
        ax.set_ylabel('DOS')
        ax.set_title('Bi2Se3 DOS')
        st.pyplot(fig)
    except:
        st.error("DOSCAR 檔案錯誤")

# 下載結果
st.subheader("下載結果")
if os.path.exists("EIGENVAL"):
    st.download_button("下載 EIGENVAL", open("EIGENVAL", "rb"))
if os.path.exists("DOSCAR"):
    st.download_button("下載 DOSCAR", open("DOSCAR", "rb"))
