from numpy import abs, clip, diff, exp, gradient, linspace, mean, random, sin, where
from pandas import DataFrame, read_csv
import matplotlib.pyplot as plt

class SParameterAnalyzer:
    def __init__(self, s_param_data):
        """
        加載S參數數據
        數據格式：頻率(Hz), S11(dB), S21(dB), S12(dB), S22(dB)
        """
        self.df = DataFrame(s_param_data)
        self.issues = []
        self.warnings = []
    
    def analyze_all(self):
        """一鍵執行完整S參數推理分析"""
        print("🔬 啟動S參數智能分析系統...\n")
        
        # 1. S11回波損耗分析（阻抗匹配）
        self._analyze_return_loss()
        
        # 2. S21插入損耗分析（功率損耗）
        self._analyze_insertion_loss()
        
        # 3. 計算實際功率損耗
        self._calculate_power_loss()
        
        # 4. 頻域異常檢測
        self._detect_frequency_anomalies()
        
        return self._generate_engineering_report()
    
    def _analyze_return_loss(self):
        """S11回波損耗智能分析"""
        s11 = self.df['S11']
        
        # **智能規則1：阻抗匹配判定**
        if s11.max() > -10:
            self.issues.append(f"❌ 回波損耗超標：{s11.max():.1f}dB（頻點{self.df.loc[s11.idxmax(), '頻率']/1e6:.1f}MHz），阻抗失配嚴重")
        elif s11.min() < -20:
            self.warnings.append(f"✅ 回波損耗優異：最小{s11.min():.1f}dB，匹配良好")
        
        # **智能規則2：諧振點檢測**
        peaks = self._find_peaks(s11, threshold=-15)
        if len(peaks) > 0:
            for idx in peaks:
                freq = self.df.loc[idx, '頻率']/1e6
                self.issues.append(f"📍 檢測到諧振點：{freq:.1f}MHz (S11={s11.iloc[idx]:.1f}dB)，可能結構共振")
    
    def _analyze_insertion_loss(self):
        """S21插入損耗智能分析"""
        s21 = self.df['S21']
        
        # **智能規則3：功率損耗閾值**
        if s21.min() < -3:
            self.issues.append(f"⚡ 插入損耗過大：{s21.min():.1f}dB @ {self.df.loc[s21.idxmin(), '頻率']/1e6:.1f}MHz，建議更換低損耗材料")
        
        # **智能規則4：頻帶平坦度**
        freq_range = self.df['頻率'].max() - self.df['頻率'].min()
        target_bw = freq_range * 0.8  # 目標頻寬
        flat_region = s21[(s21 > -1) & (s21 < -0.5)]
        
        if len(flat_region) < len(s21) * 0.6:
            self.warnings.append(f"📈 頻率響應不平坦，建議優化材料均勻性或線材結構")
    
    def _calculate_power_loss(self):
        """計算實際功率損耗百分比"""
        # S21(dB)轉換為線性功率比
        linear_s21 = 10 ** (self.df['S21'] / 10)
        power_loss = (1 - linear_s21) * 100
        
        avg_loss = power_loss.mean()
        max_loss = power_loss.max()
        
        self.avg_power_loss = avg_loss
        self.max_power_loss = max_loss
        
        # **智能規則5：功率損耗評估**
        if max_loss > 50:
            self.issues.append(f"🔥 最大功率損耗{max_loss:.1f}%，材料嚴重不合格")
        elif avg_loss > 20:
            self.warnings.append(f"⚠️ 平均功率損耗{avg_loss:.1f}%，建議改用LCP或PTFE材料")
    
    def _detect_frequency_anomalies(self):
        """檢測頻域異常模式"""
        # 計算S21斜率（高頻衰減）
        s21_slope = gradient(self.df['S21'], self.df['頻率'])
        avg_slope = mean(s21_slope)
        
        # **智能規則6：高頻衰減特性**
        if avg_slope < -1e-9:
            self.warnings.append(f"⬇️ 高頻衰減嚴重，可能導體粗糙度過大或介質損耗高")
        
        # **智能規則7：突波檢測**
        spikes = self._find_spikes(self.df['S21'], threshold=1.5)
        if spikes.size:
            self.issues.append(f"〰️ 檢測到突波干擾{len(spikes)}處，可能連接器或測試夾具問題")
    
    def _generate_engineering_report(self):
        """生成工程決策報告"""
        print("="*70)
        print("📊 S參數智能分析報告")
        print("="*70)
        
        # 關鍵指標摘要
        print(f"\n🎯 關鍵指標：")
        print(f"   平均功率損耗: {self.avg_power_loss:.1f}%")
        print(f"   最大回波損耗: {self.df['S11'].max():.1f}dB")
        print(f"   頻率範圍: {self.df['頻率'].min()/1e6:.1f}MHz - {self.df['頻率'].max()/1e6:.1f}MHz")
        
        if self.issues:
            print(f"\n🚨 **必須解決的問題** ({len(self.issues)}項):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.warnings:
            print(f"\n⚠️ **優化建議** ({len(self.warnings)}項):")
            for i, warn in enumerate(self.warnings, 1):
                print(f"   {i}. {warn}")
        
        # **最終材料決策**
        print("\n" + "="*70)
        print("🎯 **系統決策建議**：")
        if len(self.issues) >= 2:
            print("→ **建議：停用此材料批次**，檢查：1)銅線純度 2)介電常數 3)幾何尺寸")
        elif len(self.warnings) >= 2:
            print("→ **建議：限制使用頻段**，可用於<1GHz應用，不建議高速傳輸")
        else:
            print("→ **建議：材料合格**，可用於量產，持續監控高頻性能")
        
        return {
            'issues': self.issues,
            'warnings': self.warnings,
            'avg_power_loss': self.avg_power_loss,
            'data': self.df
        }
    
    def _find_peaks(self, series, threshold):
        """檢測峰值"""
        return series[series > threshold].index
    
    def _find_spikes(self, series, threshold):
        """檢測突波"""
        diff = abs(diff(series))
        return where(diff > threshold)[0]


# ==================== 使用範例 ====================

# 模擬S參數測試數據（USB4電纜，20GHz範圍）
freqs = linspace(0.1e9, 20e9, 200)
s11_data = -25 + 5*sin(freqs/1e9) + random.normal(0, 1, 200)
s21_data = -0.5 - 0.02*freqs/1e9 + 3*exp(-((freqs-15e9)/2e9)**2)  # 15GHz處有損耗尖峰

sample_data = {
    '頻率': freqs,
    'S11': clip(s11_data, -35, -5),
    'S21': clip(s21_data, -15, -0.1),
    'S12': clip(s21_data, -15, -0.1),
    'S22': clip(s11_data, -35, -5)
}

# 執行分析
#analyzer = SParameterAnalyzer(sample_data)
#results = analyzer.analyze_all()

# 可視化建議
print("\n📈 建議繪製S11/S21曲線圖以視覺確認問題點")
### 實際應用：如何接入您的數據

#**方式1：從VNA（矢量網絡分析儀）導入**
# 通常VNA可導出CSV格式：頻率, S11(dB), S21(dB)
#your_data = read_csv('vna_test_data.csv')
#analyzer = SParameterAnalyzer(your_data)
#**方式2：從產線數據庫讀取**
# 假設已有DataFrame: df_sparams
#analyzer = SParameterAnalyzer(df_sparams)
#results = analyzer.analyze_all()

