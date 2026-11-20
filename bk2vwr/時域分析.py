from matplotlib.pyplot import cm, figure, savefig, show, subplot, tight_layout
from numpy import abs, arange, gradient, isnan, linspace, max, mean, min, std, where
from pandas import DataFrame, ExcelFile, ExcelWriter, read_excel
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import signal
import warnings
warnings.filterwarnings('ignore')

class TDRAnalyzer:
    def __init__(self, 資框=None):  #excel_file, 
        """初始化TDR分析器"""
        #self.file = excel_file
        self.資框 = 資框
        self.impedance_data = {}
        self.anomalies = []
        self.issues = []
        
    def load_data(self):
        """加載Excel數據"""
        try:
            # 讀取Excel文件
            excel_data = ExcelFile(self.file)
            
            # 尋找TDR數據工作表
            for sheet_name in excel_data.sheet_names:
                if 'TDR' in sheet_name.upper() or 'DATA' in sheet_name.upper():
                    self.data = read_excel(self.file, sheet_name=sheet_name)
                    break
            
            if self.data is None:
                # 如果沒有找到特定工作表，嘗試讀取第一個工作表
                self.data = read_excel(self.file, sheet_name=0)
                
            print(f"✅ 成功加載數據：{len(self.data)} 行 × {len(self.data.columns)} 列")
            return True
            
        except Exception as e:
            print(f"❌ 數據加載失敗：{str(e)}")
            return False
    
    def identify_columns(self):
        """智能識別TDR列"""
        impedance_cols = []
        time_cols = []
        
        for col in self.資框.columns:
            print([col])
            col_lower = str(col).lower()
            
            # 識別阻抗列
            if any(keyword in col_lower for keyword in 
                   ['impedance', '阻抗', 'ohm', 'tdd', 'tdr data']):
                impedance_cols.append(col)
                
            # 識別時間列
            elif any(keyword in col_lower for keyword in 
                    ['time', '時間', 'ns', 'second']):
                time_cols.append(col)
        
        return impedance_cols, time_cols
    
    def analyze_impedance_profile(self, time_col, impedance_col):
        """分析單個阻抗曲線"""
        time = self.資框[time_col].values
        impedance = self.資框[impedance_col].values
        
        # 去除NaN值
        mask = ~isnan(time) & ~isnan(impedance)
        time = time[mask]
        impedance = impedance[mask]
        
        # 基本統計
        stats = {
            'mean_z': mean(impedance),
            'std_z': std(impedance),
            'min_z': min(impedance),
            'max_z': max(impedance),
            'time_range': [min(time), max(time)]
        }
        
        # 尋找異常點
        anomalies = self.detect_anomalies(time, impedance, impedance_col)
        
        return {
            'time': time,
            'impedance': impedance,
            'stats': stats,
            'anomalies': anomalies
        }
    
    def detect_anomalies(self, time, impedance, channel_name):
        """智能檢測阻抗異常"""
        anomalies = []
        
        # 1. 基於標準差的異常檢測
        mean_z = mean(impedance)
        std_z = std(impedance)
        threshold = 2 * std_z
        
        # 尋找超出2σ的點
        anomaly_indices = where(abs(impedance - mean_z) > threshold)[0]
        
        for idx in anomaly_indices:
            anomalies.append({
                'type': '阻抗突變',
                'time': time[idx],
                'impedance': impedance[idx],
                'deviation': impedance[idx] - mean_z,
                'severity': 'high' if abs(impedance[idx] - mean_z) > 3*std_z else 'medium'
            })
        
        # 2. 尋找阻抗不連續點（導數變化）
        dz_dt = gradient(impedance, time)
        dz_dt_threshold = std(dz_dt) * 3
        
        discontinuity_indices = where(abs(dz_dt) > dz_dt_threshold)[0]
        
        for idx in discontinuity_indices:
            if idx not in anomaly_indices:  # 避免重複
                anomalies.append({
                    'type': '阻抗不連續',
                    'time': time[idx],
                    'impedance': impedance[idx],
                    'slope': dz_dt[idx],
                    'severity': 'high' if abs(dz_dt[idx]) > 5*dz_dt_threshold else 'medium'
                })
        
        # 3. 尋找反射峰值
        peaks, properties = signal.find_peaks(impedance, 
                                              height=mean_z + threshold,
                                              distance=10)
        
        for peak_idx in peaks:
            anomalies.append({
                'type': '反射峰值',
                'time': time[peak_idx],
                'impedance': impedance[peak_idx],
                'peak_height': impedance[peak_idx] - mean_z,
                'severity': 'high' if impedance[peak_idx] > mean_z + 3*std_z else 'medium'
            })
        
        return anomalies
    
    def calculate_reflection_coefficient(self, impedance_profile):
        """計算反射係數"""
        z_mean = impedance_profile['stats']['mean_z']
        z0 = 50  # 假設特性阻抗為50Ω
        
        # 反射係數 Γ = (Z - Z0) / (Z + Z0)
        reflection_coeff = (impedance_profile['impedance'] - z0) / \
                          (impedance_profile['impedance'] + z0)
        
        return reflection_coeff
    
    def generate_visualization(self, save_path=None):
        """生成完整視覺化報告"""
        #if self.data is None:
        #    print("❌ 請先加載數據")
        #    return
        
        impedance_cols, time_cols = self.identify_columns()
        
        print([impedance_cols, time_cols])
        if not impedance_cols or not time_cols:
            print("❌ 無法識別TDR數據列")
            return
        
        # 創建子圖
        fig = plt.figure(figsize=(20, 15))
        
        # 1. 阻抗曲線總覽
        ax1 = plt.subplot(2, 3, 1)
        colors = plt.cm.tab10(linspace(0, 1, len(impedance_cols)))
        
        for i, (imp_col, color) in enumerate(zip(impedance_cols, colors)):
            time_col = time_cols[0] if time_cols else self.data.columns[0]
            profile = self.analyze_impedance_profile(time_col, imp_col)
            
            ax1.plot(profile['time'], profile['impedance'], 
                    color=color, label=imp_col, linewidth=2)
            
            # 標記異常點
            for anomaly in profile['anomalies']:
                if anomaly['severity'] == 'high':
                    ax1.scatter(anomaly['time'], anomaly['impedance'], 
                              color='red', s=100, marker='o', zorder=5)
                elif anomaly['severity'] == 'medium':
                    ax1.scatter(anomaly['time'], anomaly['impedance'], 
                              color='orange', s=60, marker='^', zorder=5)
        
        ax1.set_xlabel('Time (ns)', fontsize=12)
        ax1.set_ylabel('Impedance (Ω)', fontsize=12)
        ax1.set_title('TDR Impedance Profiles with Anomalies', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 2. 反射係數分析
        ax2 = plt.subplot(2, 3, 2)
        for i, (imp_col, color) in enumerate(zip(impedance_cols, colors)):
            time_col = time_cols[0] if time_cols else self.data.columns[0]
            profile = self.analyze_impedance_profile(time_col, imp_col)
            reflection_coeff = self.calculate_reflection_coefficient(profile)
            
            ax2.plot(profile['time'], reflection_coeff, 
                    color=color, label=f'{imp_col} - Γ', linewidth=2)
        
        ax2.set_xlabel('Time (ns)', fontsize=12)
        ax2.set_ylabel('Reflection Coefficient (Γ)', fontsize=12)
        ax2.set_title('Reflection Coefficient Analysis', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # 3. 阻抗分佈直方圖
        ax3 = plt.subplot(2, 3, 3)
        all_impedances = []
        for imp_col in impedance_cols[:4]:  # 只取前4個通道避免圖表過於擁擠
            impedance = self.data[imp_col].dropna().values
            all_impedances.extend(impedance)
            
            ax3.hist(impedance, bins=50, alpha=0.6, label=imp_col, density=True)
        
        ax3.set_xlabel('Impedance (Ω)', fontsize=12)
        ax3.set_ylabel('Density', fontsize=12)
        ax3.set_title('Impedance Distribution', fontsize=14, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 異常點統計
        ax4 = plt.subplot(2, 3, 4)
        anomaly_summary = {}
        for imp_col in impedance_cols:
            time_col = time_cols[0] if time_cols else self.data.columns[0]
            profile = self.analyze_impedance_profile(time_col, imp_col)
            
            high_anomalies = sum(1 for a in profile['anomalies'] if a['severity'] == 'high')
            medium_anomalies = sum(1 for a in profile['anomalies'] if a['severity'] == 'medium')
            
            anomaly_summary[imp_col] = {'High': high_anomalies, 'Medium': medium_anomalies}
        
        channels = list(anomaly_summary.keys())
        high_counts = [anomaly_summary[ch]['High'] for ch in channels]
        medium_counts = [anomaly_summary[ch]['Medium'] for ch in channels]
        
        x = arange(len(channels))
        width = 0.35
        
        ax4.bar(x - width/2, high_counts, width, label='High Severity', color='red', alpha=0.7)
        ax4.bar(x + width/2, medium_counts, width, label='Medium Severity', color='orange', alpha=0.7)
        
        ax4.set_xlabel('Channel', fontsize=12)
        ax4.set_ylabel('Number of Anomalies', fontsize=12)
        ax4.set_title('Anomaly Detection Summary', fontsize=14, fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels([ch.replace('CH', '') for ch in channels], rotation=45)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 5. 阻抗變化率分析
        ax5 = plt.subplot(2, 3, 5)
        for i, (imp_col, color) in enumerate(zip(impedance_cols, colors)):
            time_col = time_cols[0] if time_cols else self.data.columns[0]
            profile = self.analyze_impedance_profile(time_col, imp_col)
            
            # 計算阻抗變化率
            dz_dt = gradient(profile['impedance'], profile['time'])
            
            ax5.plot(profile['time'], dz_dt, color=color, label=imp_col, linewidth=1.5)
        
        ax5.set_xlabel('Time (ns)', fontsize=12)
        ax5.set_ylabel('dZ/dt (Ω/ns)', fontsize=12)
        ax5.set_title('Impedance Change Rate', fontsize=14, fontweight='bold')
        ax5.grid(True, alpha=0.3)
        ax5.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # 6. 綜合報告表格
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        # 生成報告文本
        report_text = "📊 TDR ANALYSIS REPORT\n"
        report_text += "="*50 + "\n\n"
        
        for imp_col in impedance_cols[:3]:  # 顯示前3個通道
            time_col = time_cols[0] if time_cols else self.data.columns[0]
            profile = self.analyze_impedance_profile(time_col, imp_col)
            
            report_text += f"🔍 {imp_col}:\n"
            report_text += f"   Mean Z: {profile['stats']['mean_z']:.1f}Ω\n"
            report_text += f"   Range: {profile['stats']['min_z']:.1f} - {profile['stats']['max_z']:.1f}Ω\n"
            report_text += f"   Anomalies: {len(profile['anomalies'])} detected\n"
            
            if profile['anomalies']:
                high_sev = sum(1 for a in profile['anomalies'] if a['severity'] == 'high')
                report_text += f"   ⚠️  High Severity: {high_sev}\n"
            report_text += "\n"
        
        ax6.text(0.05, 0.95, report_text, transform=ax6.transAxes, 
                fontsize=11, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        
        #if save_path:
        #    plt.savefig(save_path, dpi=300, bbox_inches='tight')
        #    print(f"💾 圖表已保存至: {save_path}")
        
        return fig
        plt.show()
    
    def generate_excel_report(self, output_file):
        """生成Excel分析報告"""
        if self.data is None:
            print("❌ 請先加載數據")
            return
        
        impedance_cols, time_cols = self.identify_columns()
        
        # 創建工作簿
        with ExcelWriter(output_file, engine='openpyxl') as writer:
            # 1. 匯總報告
            summary_data = []
            
            for imp_col in impedance_cols:
                time_col = time_cols[0] if time_cols else self.data.columns[0]
                profile = self.analyze_impedance_profile(time_col, imp_col)
                
                summary_data.append({
                    'Channel': imp_col,
                    'Mean_Impedance_Ohm': round(profile['stats']['mean_z'], 2),
                    'Std_Impedance_Ohm': round(profile['stats']['std_z'], 2),
                    'Min_Impedance_Ohm': round(profile['stats']['min_z'], 2),
                    'Max_Impedance_Ohm': round(profile['stats']['max_z'], 2),
                    'Total_Anomalies': len(profile['anomalies']),
                    'High_Severity': sum(1 for a in profile['anomalies'] if a['severity'] == 'high'),
                    'Medium_Severity': sum(1 for a in profile['anomalies'] if a['severity'] == 'medium'),
                    'Time_Range_ns': f"{profile['stats']['time_range'][0]:.2f} - {profile['stats']['time_range'][1]:.2f}"
                })
            
            summary_df = DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary_Report', index=False)
            
            # 2. 詳細異常點報告
            anomaly_data = []
            
            for imp_col in impedance_cols:
                time_col = time_cols[0] if time_cols else self.data.columns[0]
                profile = self.analyze_impedance_profile(time_col, imp_col)
                
                for anomaly in profile['anomalies']:
                    anomaly_data.append({
                        'Channel': imp_col,
                        'Anomaly_Type': anomaly['type'],
                        'Time_ns': round(anomaly['time'], 3),
                        'Impedance_Ohm': round(anomaly['impedance'], 2),
                        'Severity': anomaly['severity'],
                        'Deviation_Ohm': round(anomaly.get('deviation', 0), 2),
                        'Slope_Ohm_per_ns': round(anomaly.get('slope', 0), 3)
                    })
            
            if anomaly_data:
                anomaly_df = DataFrame(anomaly_data)
                anomaly_df.to_excel(writer, sheet_name='Anomaly_Details', index=False)
            
            # 3. 原始數據（清理後）
            clean_data = self.data.copy()
            clean_data.to_excel(writer, sheet_name='Clean_Data', index=False)
            
        print(f"📊 Excel報告已生成: {output_file}")
