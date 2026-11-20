from streamlit import caption, columns, error, header, info, markdown, pyplot, set_page_config, sidebar, subheader, success, table, tabs, title, write, number_input, slider, radio
from matplotlib.pyplot import Rectangle, subplots, subplots_adjust
from numpy import linspace, random, round, sin
from numpy.random import seed, normal, uniform
from pandas import DataFrame
from matplotlib.pyplot import rcParams, savefig, subplots, tight_layout
from streamlit import pyplot
#import streamlit as st
#import numpy as np
#import pandas as pd
#import matplotlib.pyplot as plt

# 頁面配置
set_page_config(
    page_title="低溫量子讀取傳輸線模擬器 (Cri/oFlex3 規格)",
    page_icon="🧊",
    layout="wide"
)

with sidebar:
# ==========================================
# 側邊欄：參數設定 (Sidebar Inputs)
# ==========================================
  subheader("⚙️ 傳輸線與系統參數")

# 1. 頻段設定
  freq_start = number_input("起始頻率 (GHz)", value=4.0, step=0.5)
  freq_stop = number_input("結束頻率 (GHz)", value=8.0, step=0.5)
  num_points = slider("頻率採樣點數", 100, 1000, 400)
  freq = linspace(freq_start, freq_stop, num_points)
#
# 側邊欄新增：幾何尺寸參數 (新增部分)
#
  subheader("📐 傳輸線幾何尺寸參數")
  線寬 = slider("傳輸線寬度 Width (mm)", 10.0, 50.0, 20.0, step=1.0)
  總厚度 = slider("基板總厚度 Thickness (mm)", 0.5, 3.0, 1.0, step=0.1)
  熱沉長度 = slider("熱沉區塊長度 Heat-sink (mm)", 10.0, 40.0, 20.0, step=5.0)

# 2. 通道與材質設定
  num_channels = radio("通道數量 (Channels)", [8, 16], index=0, horizontal=True)
  material = radio("導體材質 (Conductor)", ["CuNi 鍍金", "NbTi 超導 (極低溫段)"], horizontal=True)
  cable_length = slider("傳輸線總長度 (m)", 0.2, 1.0, 0.5, step=0.05)

# 3. 輸入/輸出鏈路設定
  subheader("📉 輸入鏈衰減器 (Input Chain)")
  att_4k = number_input("300K -> 4K 衰減器 (dB)", value=20)
  att_still = number_input("4K -> 100mK 衰減器 (dB)", value=10)
  att_mxc = number_input("100mK -> 10mK 衰減器 (dB)", value=20)
  total_input_att = att_4k + att_still + att_mxc

  subheader("📈 輸出鏈放大器 (Output Chain)")
  hemt_gain = number_input("4K HEMT 增益 (dB)", value=35)
  hemt_tn = number_input("HEMT 噪聲溫度 Tn (K)", value=3.0, step=0.5)

# 4. 相位規格驗證門檻
  subheader("🎯 驗收門檻 (Acceptance Targets)")
  target_s11 = number_input("S11 目標值 (dB <)", value=-15)
  target_phase_dev = number_input("相位匹配容許偏差 (°)", value=5.0)

# ==========================================
# 主分頁 (Tabs)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = tabs([
    "📊 鏈路預算 (Link Budget)",
    "📈 射頻 S 參數與串擾",
    "🧭 相位匹配與穩定度",
    "❄️ 低溫熱負載評估",
    "📐 幾何尺寸與三視圖"
])

#
# Tab 1: 鏈路預算 (Link Budget)
#
with tab1:
    header("訊號鏈配置與熱光子數 (Link Budget)")

    col1, col2, col3 = columns(3)
    col1.metric("輸入鏈總衰減量", f"{total_input_att} dB", delta="目標: 50 dB" if total_input_att == 50 else None)
    col2.metric("4K HEMT 放大增益", f"{hemt_gain} dB")
    col3.metric("HEMT 噪聲溫度 $T_n$", f"{hemt_tn} K")

    markdown("---")
    subheader("溫層架構示意與衰減/放大分佈")

    stages = ["300 K (室溫)", "4 K (K-Stage)", "100 mK (Still)", "10 mK (MXC / Qubit)"]
    input_att_list = [0, -att_4k, -att_4k - att_still, -total_input_att]

    fig, ax = subplots(figsize=(9, 3.5))
    ax.plot(stages, input_att_list, marker='o', linewidth=2, color='#1f77b4', label="Input Line Power Level (dB)")
    ax.axhline(-50, color='red', linestyle='--', alpha=0.6, label="Target Attenuation (-50 dB)")
    ax.set_ylabel("Relative Power (dB)")
    ax.set_title("Input Chain Attenuation Across Temperature Stages")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    pyplot(fig)

#
# Tab 2: 射頻 S 參數與串擾 (RF Performance)
#
with tab2:
    header("RF 傳輸特徵模擬 (4 - 8 GHz)")

    # 模擬計算 S11, S21, Crosstalk
    seed(42)
    # S21 隨頻率增加損耗，基礎損耗約 2.5 dB/m
    attenuation_rate = 1.8 if "NbTi" in material else 2.5
    s21_base = -attenuation_rate * cable_length - (freq - freq_start) * 0.15
    s21 = s21_base + normal(0, 0.05, num_points)

    # S11 反射損耗 (需小於 -15 dB)
    s11 = -18 - 3 * sin(freq * 2) + normal(0, 0.4, num_points)

    # 鄰近通道串擾 Crosstalk (需小於 -40 dB)
    crosstalk = -48 - 2 * (freq / freq_stop) + normal(0, 0.8, num_points)

    col1, col2 = columns(2)

    with col1:
        subheader("S11 反射損耗 & S21 插入損耗")
        fig, ax = subplots(figsize=(6, 4))
        ax.plot(freq, s21, label="S21 (Insertion Loss)", color="green")
        ax.plot(freq, s11, label="S11 (Return Loss)", color="orange")
        ax.axhline(target_s11, color="red", linestyle="--", label=f"S11 Target ({target_s11} dB)")
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        pyplot(fig)

    with col2:
        subheader("鄰近通道串擾 (Crosstalk)")
        fig, ax = subplots(figsize=(6, 4))
        ax.plot(freq, crosstalk, label="Adjacent Channel Crosstalk", color="purple")
        ax.axhline(-40, color="red", linestyle="--", label="Target Limit (-40 dB)")
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("Isolation (dB)")
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        pyplot(fig)

#
# Tab 3: 相位匹配與穩定度 (Phase Metrics)
#
with tab3:
    header("跨通道相位匹配與穩定度 (Phase Performance)")
    write(f"模擬 **{num_channels} 通道** 柔性板在 4–8 GHz 頻段內的相位特性：")

    # 模擬多通道相位偏差
    phase_data = {}
    base_phase = 360 * (freq / 6.0) * cable_length * 1.5

    seed(10)
    for ch in range(1, num_channels + 1):
        # 每個通道有些微長度與介電不勻性引發的相位漂移
        ch_offset = uniform(-target_phase_dev * 0.6, target_phase_dev * 0.6)
        ch_ripple = 1.2 * sin(freq * (ch + 1))
        phase_data[f"CH {ch}"] = ch_offset + ch_ripple

    df_phase = DataFrame(phase_data, index=round(freq, 2))

    fig, ax = subplots(figsize=(10, 4))
    for ch in range(1, num_channels + 1):
        ax.plot(freq, df_phase[f"CH {ch}"], alpha=0.7, label=f"CH {ch}" if ch <= 4 else "")

    ax.axhline(target_phase_dev, color="red", linestyle="--", label=f"+{target_phase_dev}° Spec Limit")
    ax.axhline(-target_phase_dev, color="red", linestyle="--", label=f"-{target_phase_dev}° Spec Limit")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Phase Deviation from Mean (°)")
    ax.set_title(f"Cross-Channel Phase Matching ({num_channels} Channels)")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc="upper right")
    pyplot(fig)

    # 相位統計判定
    max_dev = df_phase.abs().max().max()
    if max_dev <= target_phase_dev:
        success(f"✅ **驗收通過**：所有通道最大相位偏差為 **±{max_dev:.2f}°**（合格門檻 ±{target_phase_dev}°）。")
    else:
        error(f"❌ **驗收未通過**：最大相位偏差為 **±{max_dev:.2f}°**，超過標準！")

#
# Tab 4: 低溫熱負載估算 (Thermal Load)
#
with tab4:
    header("低溫熱傳導與熱負載估算 (Thermal Load Breakdown)")
    info("熱負載主要由 Polyimide 基板與金屬導體傳導產生，良好的熱沉 (Thermal Anchoring) 能確保 10 mK 溫層不被加熱。")

    # 簡單熱導性模型 (mW 單位)
    factor = 0.4 if "NbTi" in material else 1.0
    q_4k = 15.0 * (num_channels / 8) * factor
    q_still = 1.2 * (num_channels / 8) * factor
    q_mxc = 0.008 * (num_channels / 8) * factor  # ~8 uW

    col1, col2, col3 = columns(3)
    col1.metric("4 K 溫層導熱負載", f"{q_4k:.2f} mW")
    col2.metric("100 mK (Still) 導熱負載", f"{q_still:.3f} mW")
    col3.metric("10 mK (MXC) 導熱負載", f"{q_mxc * 1000:.2f} µW", delta="極低熱漏" if "NbTi" in material else None)

    markdown("""
    #### 熱沉 (Thermal Anchoring) 設計檢核：
    - [x] **4 K 溫層：** 採用一體化紫銅無氧銅 (OFC) 熱沉夾具壓接接地層。
    - [x] **100 mK 溫層：** 經由高密度穿孔 (Via Array) 熱錨定。
    - [x] **10 mK 溫層：** 柔性板表面鍍金與 MXC 冷盤直接螺絲緊固。
    """)
#
# Tab 5: 幾何尺寸與三視圖 (新功能實作)
#
with tab5:
    # 參數轉換 (m -> mm)
    L = cable_length * 1000.0  # 總長度 (mm)
    W = 線寬            # 寬度 (mm)
    T = 總厚度        # 厚度 (mm)
    HS_L = 熱沉長度     # 熱沉長度 (mm)

    # 計算各溫層熱沉位置 (相對座標 mm)
    pos_300k = 0
    pos_4k = L * 0.33
    pos_still = L * 0.66
    pos_mxc = L
    全視=['上視', '側視', '前視', '匯出尺寸']
    視=radio('三視圖尺寸', 全視, horizontal=True)
    ch_spacing = W / (num_channels + 1)

    if 視==全視[0]: # 建立 Matplotlib 三視圖 Canvas
      fig, ax1= subplots(figsize=(10, 6))
      #fig, ax1 = subplots(3, 1, figsize=(11, 8), gridspec_kw={'height_ratios': [2, 1.2, 1.2]})
      subplots_adjust(hspace=0.5)

      #
      # 1. 上視圖 (Top View - XY 面)
      #
      #ax1 = axes[0]
      # 繪製傳輸線本體 (Polyimide Base)
      #rect_top_base = Rectangle((0, -W/2), L, W, color='#D2B48C', alpha=0.6, label='Polyimide Substrate')
      #ax1.add_patch(rect_top_base)
      #
      ## 繪製微帶線/帶狀線通道 (Channels)
      #for i in range(1, num_channels + 1):
      #    y_pos = -W/2 + i * ch_spacing
      #    ax1.plot([0, L], [y_pos, y_pos], color='#B8860B', linestyle='-', linewidth=1.2, label='Signal Channels (CuNi/NbTi)' if i == 1 else "")

      ## 繪製各溫層銅熱沉區塊 (Heat Sink Blocks)
      #for pos, label in zip([pos_4k, pos_still, pos_mxc], ['4K Anchor', 'Still Anchor', 'MXC Anchor']):
      #    hs_rect = Rectangle((pos - HS_L/2, -W/2 - 2), HS_L, W + 4, color='#B87333', edgecolor='black', alpha=0.8)
      #    ax1.add_patch(hs_rect)
      #    ax1.text(pos, W/2 + 4, label, fontsize=8, ha='center', fontweight='bold')

      #ax1.set_xlim(-HS_L, L + HS_L)
      #ax1.set_ylim(-W*1.5, W*1.8)
      #ax1.set_title("上視圖 (Top View - XY Plane)", fontsize=11, fontweight='bold')
      #ax1.set_xlabel("Length X (mm)")
      #ax1.set_ylabel("Width Y (mm)")
      #ax1.grid(True, linestyle=':', alpha=0.5)
      #ax1.legend(loc='upper right', fontsize=8)

      rect_top_base = Rectangle((0, -W/2), L, W, color='#D2B48C', alpha=0.6, label='Polyimide Substrate')
      ax1.add_patch(rect_top_base)

      ch_spacing = W / (num_channels + 1)
      for i in range(1, num_channels + 1):
          y_pos = -W/2 + i * ch_spacing
          ax1.plot([0, L], [y_pos, y_pos], color='#B8860B', linestyle='-', linewidth=1.2,
                      label=f'Signal Channels ({material})' if i == 1 else "")

      for pos, label in zip([pos_4k, pos_still, pos_mxc], ['4K Anchor', 'Still Anchor', 'MXC Anchor']):
          hs_rect = Rectangle((pos - HS_L/2, -W/2 - 2), HS_L, W + 4, color='#B87333', edgecolor='black', alpha=0.8)
          ax1.add_patch(hs_rect)
          ax1.text(pos, W/2 + 4, label, fontsize=8, ha='center', fontweight='bold')

      ax1.set_xlim(-HS_L, L + HS_L)
      ax1.set_ylim(-W*1.5, W*1.8)
      ax1.set_title("上視圖 (Top View - XY Plane)", fontsize=11, fontweight='bold')
      ax1.set_xlabel("Length X (mm)")
      ax1.set_ylabel("Width Y (mm)")
      ax1.grid(True, linestyle=':', alpha=0.5)
      ax1.legend(loc='upper right', fontsize=8)
      pyplot(fig)
    elif 視==全視[1]:
      fig, ax2= subplots(figsize=(10, 6))
      #
      # 2. 前視圖/側視圖 (Side View - XZ 面)
      #
      #ax2 = axes[1]
      # 繪製傳輸線剖面厚度
      #rect_side_base = Rectangle((0, -T/2), L, T, color='#D2B48C', alpha=0.8)
      #ax2.add_patch(rect_side_base)

      ## 繪製上下金屬熱沉夾具結構
      #for pos in [pos_4k, pos_still, pos_mxc]:
      #    # 上夾板
      #    hs_top = Rectangle((pos - HS_L/2, T/2), HS_L, T*2, color='#B87333', edgecolor='black')
      #    # 下夾板
      #    hs_bot = Rectangle((pos - HS_L/2, -T/2 - T*2), HS_L, T*2, color='#B87333', edgecolor='black')
      #    ax2.add_patch(hs_top)
      #    ax2.add_patch(hs_bot)

      #ax2.set_xlim(-HS_L, L + HS_L)
      #ax2.set_ylim(-T*5, T*5)
      #ax2.set_title("前視圖 (Side View - XZ Plane)", fontsize=11, fontweight='bold')
      #ax2.set_xlabel("Length X (mm)")
      #ax2.set_ylabel("Thickness Z (mm)")
      #ax2.grid(True, linestyle=':', alpha=0.5)

      rect_side_base = Rectangle((0, -T/2), L, T, color='#D2B48C', alpha=0.8)
      ax2.add_patch(rect_side_base)

      # 溫層與衰減器設定資料
      att_stages = [
          {"pos": pos_4k, "att_val": att_4k, "temp": "300K → 4K", "cum_att": att_4k},
          {"pos": pos_still, "att_val": att_still, "temp": "4K → 100mK", "cum_att": att_4k + att_still},
          {"pos": pos_mxc, "att_val": att_mxc, "temp": "100mK → 10mK", "cum_att": total_input_att}
      ]

      for stage in att_stages:
          pos = stage["pos"]
          att_val = stage["att_val"]
          cum_att = stage["cum_att"]

          # 上下銅熱沉夾板
          hs_top = Rectangle((pos - HS_L/2, T/2), HS_L, T*2, color='#B87333', edgecolor='black')
          hs_bot = Rectangle((pos - HS_L/2, -T/2 - T*2), HS_L, T*2, color='#B87333', edgecolor='black')
          ax2.add_patch(hs_top)
          ax2.add_patch(hs_bot)

          # 繪製衰減器元件圖示 (Attenuator Component Icon) - 位於熱沉上方
          att_w = HS_L * 0.8
          att_h = T * 2.2
          att_rect = Rectangle((pos - att_w/2, T/2 + T*2.5), att_w, att_h,
                                   color='#D9534F', edgecolor='black', alpha=0.9)
          ax2.add_patch(att_rect)
          ax2.text(pos, T/2 + T*2.5 + att_h/2, f"-{att_val}dB",
                       color='white', fontsize=7, ha='center', va='center', fontweight='bold')

          # 標註溫層過渡與累積衰減量
          ax2.text(pos, -T/2 - T*4.5, f"{stage['temp']}\n-{att_val} dB (總計 -{cum_att} dB)",
                       fontsize=8, ha='center', va='top', bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec="gray", lw=0.8))

      ax2.set_xlim(-HS_L, L + HS_L)
      ax2.set_ylim(-T*10, T*9)
      ax2.set_title("前視圖 (Side View - XZ Plane) [含各溫層衰減器配置]", fontsize=11, fontweight='bold')
      ax2.set_xlabel("Length X (mm)")
      ax2.set_ylabel("Thickness Z (mm)")
      ax2.grid(True, linestyle=':', alpha=0.5)
      pyplot(fig)
    elif 視==全視[2]:
      fig, ax3= subplots(figsize=(10, 6))
      #
      # 3. 前端端面截面圖 (Cross-Section View - YZ 面)
      #
      #ax3 = axes[2]
      # 繪製基板剖面
      #rect_cross = Rectangle((-W/2, -T/2), W, T, color='#D2B48C', edgecolor='black', alpha=0.8, label='Polyimide')
      #ax3.add_patch(rect_cross)

      # 繪製通道導體橫截面 (Conductive Traces)
      #trace_w = ch_spacing * 0.4
      #trace_h = T * 0.2
      #for i in range(1, num_channels + 1):
      #    y_pos = -W/2 + i * ch_spacing
      #    rect_trace = Rectangle((y_pos - trace_w/2, -trace_h/2), trace_w, trace_h, color='#FFD700', edgecolor='black')
      #    ax3.add_patch(rect_trace)

      #ax3.set_xlim(-W*0.8, W*0.8)
      #ax3.set_ylim(-T*3, T*3)
      #ax3.set_title(f"橫截面圖 (Cross-Section - YZ Plane) [{num_channels} Channels Microstrip]", fontsize=11, fontweight='bold')
      #ax3.set_xlabel("Width Y (mm)")
      #ax3.set_ylabel("Thickness Z (mm)")
      #ax3.grid(True, linestyle=':', alpha=0.5)

      rect_cross = Rectangle((-W/2, -T/2), W, T, color='#D2B48C', edgecolor='black', alpha=0.8, label='Polyimide')
      ax3.add_patch(rect_cross)

      trace_w = ch_spacing * 0.4
      trace_h = T * 0.2
      for i in range(1, num_channels + 1):
          y_pos = -W/2 + i * ch_spacing
          rect_trace = Rectangle((y_pos - trace_w/2, -trace_h/2), trace_w, trace_h, color='#FFD700', edgecolor='black')
          ax3.add_patch(rect_trace)

      ax3.set_xlim(-W*0.8, W*0.8)
      ax3.set_ylim(-T*3, T*3)
      ax3.set_title(f"橫截面圖 (Cross-Section - YZ Plane) [{num_channels} Channels Stripline]", fontsize=11, fontweight='bold')
      ax3.set_xlabel("Width Y (mm)")
      ax3.set_ylabel("Thickness Z (mm)")
      ax3.grid(True, linestyle=':', alpha=0.5)
      pyplot(fig) # 在 Streamlit 中渲染畫布
    elif 視==全視[3]:
      # 幾何尺寸數據表格彙整
      #markdown("#### 📐 傳輸線實體尺寸匯總")
      #資框 = DataFrame({
      #    "幾何參數 (Geometric Parameter)": ["總長度 L", "總寬度 W", "基板厚度 T", "通道數量", "熱沉區塊長度", "溫層節點數"],
      #    "數值 (Value)": [f"{L:.1f} mm", f"{W:.1f} mm", f"{T:.2f} mm", f"{num_channels} CH", f"{HS_L:.1f} mm", "3 Stages (4K / Still / MXC)"]
      #})
      #table()
      markdown("#### 📐 傳輸線實體尺寸與材料規格彙整")
      資框 = DataFrame({
          "規格/幾何參數 (Parameter)": [
              "導體材質 (Conductor)",
              "總長度 L",
              "總寬度 W",
              "基板厚度 T",
              "通道數量 (Channels)",
              "熱沉區塊長度 (Heat-sink)",
              "輸入鏈總衰減量 (Total Input Attenuation)"
          ],
          "數值 / 規格 (Value / Spec)": [
              f"**{material}**",
              f"{L:.1f} mm",
              f"{W:.1f} mm",
              f"{T:.2f} mm",
              f"{num_channels} CH",
              f"{HS_L:.1f} mm",
              f"-{total_input_att} dB (-{att_4k}dB @4K / -{att_still}dB @Still / -{att_mxc}dB @MXC)"
          ]
      })
      資框
    with sidebar:
      subheader("📐 低溫柔性傳輸線三視圖動態繪製 (2D Orthographic Views)")
      caption("根據側邊欄輸入的傳輸線幾何尺寸 (長度、寬度、厚度與通道數) 動態生成標準三視圖結構圖。")

with sidebar:
  subheader("🧊 低溫量子讀取傳輸線模擬與效能評估系統")
  caption("Based on Delft Cri/oFlex® 3 Architecture | 4 - 8 GHz Readout Chain")

