# 🔬 低溫傳輸線熱負載模擬器

基於 Wiedemann-Franz 定律的低溫傳輸線熱負載與長度估算工具，支援 Aluminum Shield 計算。

## 📋 功能特色

- **多溫度段分析**: 300K → 50K → 4K → 0.6K → 100mK → 10mK
- **多種線材支援**: Ag, NbTi, CuNi (Constantan)
- **Aluminum Shield 計算**: 含熱傳導分流與熱輻射估算
- **互動式調整**: 即時調整長度反算熱負載
- **視覺化圖表**: 熱負載、長度比較、系統示意圖
- **AWG 線規選擇**: 32/34/36/38/40 AWG

## 🚀 快速開始

### 方法一：Docker (推薦)

```bash
# 建置並啟動
docker-compose up -d

# 訪問 http://localhost:8501
```

### 方法二：直接執行

```bash
# Linux/Mac
./launch.sh

# Windows
launch.bat
```

### 方法三：Python 虛擬環境

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run cryo_cable_app.py
```

## 📦 打包成執行檔

### Docker 映像檔

```bash
./build.sh
```

### PyInstaller 獨立執行檔

```bash
# Linux/Mac
./build_pyinstaller.sh

# Windows
build_pyinstaller.bat
```

## 📐 計算原理

### Wiedemann-Franz 定律

對於金屬傳輸線，熱導率與電導率的關係：

```
λ = L₀ · T / ρ(T)
```

其中 L₀ = 2.45 × 10⁻⁸ W·Ω/K² 為 Lorenz 數。

### 熱傳導積分

```
Q = (L₀ · A / L · ρ) · (Tₕ² - Tc²) / 2
```

### 反推長度

```
L = L₀ · A · (Tₕ² - Tc²) / (2 · Q · ρ)
```

### 熱輻射 (Stefan-Boltzmann)

```
Q_rad = ε · σ · A_surface · (Tₕ⁴ - Tc⁴)
```

## 📁 檔案結構

```
.
├── cryo_cable_app.py      # 主應用程式
├── requirements.txt       # Python 依賴
├── Dockerfile            # Docker 建置檔
├── docker-compose.yml    # Docker Compose 配置
├── build.sh              # Docker 建置腳本 (Linux/Mac)
├── build.bat             # Docker 建置腳本 (Windows)
├── launch.sh             # 快速啟動腳本 (Linux/Mac)
├── launch.bat            # 快速啟動腳本 (Windows)
├── build_pyinstaller.sh  # PyInstaller 打包 (Linux/Mac)
└── build_pyinstaller.bat # PyInstaller 打包 (Windows)
```

## ⚙️ 預設參數

| 參數 | 數值 |
|------|------|
| Lorenz 數 L₀ | 2.45 × 10⁻⁸ W·Ω/K² |
| Ag 電阻率 (300K) | 1.6 × 10⁻⁸ Ω·m |
| Ag 電阻率 (低溫) | 1.5 × 10⁻⁸ Ω·m |
| NbTi 電阻率 | 6.5 × 10⁻⁷ Ω·m |
| CuNi 電阻率 | 4.9 × 10⁻⁷ Ω·m |
| Al 發射率 ε | 0.03 |
| Stefan-Boltzmann σ | 5.67 × 10⁻⁸ W/m²/K⁴ |

## ⚠️ 免責聲明

本模擬器基於理想化假設：
- 電阻率在每個溫度段內視為常數
- 不考慮接觸電阻與接頭熱阻
- NbTi 低溫熱負載可能來自銅穩定層
- 實際值可能因 RRR、磁場等因素而異

## 📄 授權

MIT License
