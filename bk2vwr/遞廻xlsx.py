import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

class ExcelVisualizer:
    def __init__(self, base_directory):
        self.base_directory = Path(base_directory)
        self.excel_files = []
        self.figures = []
        
    def find_excel_files(self):
        """遞歸查找所有xlsx文件"""
        pattern = "**/*.xlsx"
        self.excel_files = list(self.base_directory.glob(pattern))
        print(f"找到 {len(self.excel_files)} 個Excel文件:")
        for file in self.excel_files:
            print(f"  - {file}")
        return self.excel_files
    
    def read_excel_sheets(self, file_path):
        """讀取Excel文件的所有工作表"""
        try:
            sheets_dict = pd.read_excel(file_path, sheet_name=None)
            return sheets_dict
        except Exception as e:
            print(f"讀取文件 {file_path} 時出錯: {e}")
            return {}
    
    def analyze_sheet_structure(self, sheet_name, df):
        """分析工作表結構并返回相關信息"""
        structure_info = {
            'sheet_name': sheet_name,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'has_numeric': False,
            'numeric_columns': []
        }
        
        # 檢查數值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            structure_info['has_numeric'] = True
            structure_info['numeric_columns'] = list(numeric_cols)
            
        return structure_info
    
    def create_visualizations(self, file_path, sheets_dict):
        """爲Excel文件創建可視化圖表"""
        file_name = file_path.name
        visualizations = []
        
        for sheet_name, df in sheets_dict.items():
            if df.empty:
                continue
                
            # 分析工作表結構
            structure = self.analyze_sheet_structure(sheet_name, df)
            
            # 爲每個工作表創建圖表
            sheet_viz = self.visualize_sheet(file_name, sheet_name, df, structure)
            if sheet_viz:
                visualizations.extend(sheet_viz)
                
        return visualizations
    
    def visualize_sheet(self, file_name, sheet_name, df, structure):
        """爲單個工作表創建可視化"""
        viz_list = []
        
        # 設置樣式
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 1. 數據概覽圖
        fig1 = self.create_data_overview(file_name, sheet_name, df, structure)
        if fig1:
            viz_list.append(('數據概覽', fig1))
        
        # 2. 數值數據可視化
        if structure['has_numeric']:
            # 數值分布圖
            fig2 = self.create_numeric_distribution(file_name, sheet_name, df, structure)
            if fig2:
                viz_list.append(('數值分布', fig2))
            
            # 相關性熱力圖（如果有多個數值列）
            if len(structure['numeric_columns']) > 1:
                fig3 = self.create_correlation_heatmap(file_name, sheet_name, df, structure)
                if fig3:
                    viz_list.append(('相關性熱力圖', fig3))
        
        # 3. 分類數據可視化
        fig4 = self.create_categorical_analysis(file_name, sheet_name, df, structure)
        if fig4:
            viz_list.append(('分類分析', fig4))
            
        return viz_list
    
    def create_data_overview(self, file_name, sheet_name, df, structure):
        """創建數據概覽圖"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{file_name}\n工作表: {sheet_name}\n數據概覽', fontsize=16, fontweight='bold')
        
        # 1. 數據形狀信息
        ax1.axis('off')
        info_text = f"數據形狀: {structure['shape']}\n"
        info_text += f"列數: {structure['shape'][1]}\n"
        info_text += f"行數: {structure['shape'][0]}\n"
        info_text += f"數值列: {len(structure['numeric_columns'])}"
        ax1.text(0.1, 0.9, info_text, transform=ax1.transAxes, fontsize=12, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 2. 缺失值分析
        missing_data = df.isnull().sum()
        if missing_data.sum() > 0:
            missing_data = missing_data[missing_data > 0]
            ax2.bar(missing_data.index, missing_data.values)
            ax2.set_title('缺失值統計')
            ax2.tick_params(axis='x', rotation=45)
        else:
            ax2.axis('off')
            ax2.text(0.5, 0.5, '無缺失值', transform=ax2.transAxes, 
                    ha='center', va='center', fontsize=14)
        
        # 3. 數據類型分布
        dtypes_count = df.dtypes.value_counts()
        ax3.pie(dtypes_count.values, labels=dtypes_count.index, autopct='%1.1f%%')
        ax3.set_title('數據類型分布')
        
        # 4. 前5行數據預覽
        ax4.axis('off')
        if len(df) > 0:
            preview_text = "前5行數據:\n" + str(df.head().to_string())
            ax4.text(0.1, 0.9, preview_text, transform=ax4.transAxes, fontsize=8, 
                    verticalalignment='top', family='monospace')
        
        plt.tight_layout()
        return fig
    
    def create_numeric_distribution(self, file_name, sheet_name, df, structure):
        """創建數值數據分布圖"""
        numeric_cols = structure['numeric_columns']
        if not numeric_cols:
            return None
            
        n_cols = min(4, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
        fig.suptitle(f'{file_name}\n工作表: {sheet_name}\n數值分布分析', fontsize=16, fontweight='bold')
        
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        elif n_cols == 1:
            axes = [[ax] for ax in axes]
        
        for i, col in enumerate(numeric_cols):
            row_idx = i // n_cols
            col_idx = i % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            else:
                ax = axes[row_idx][col_idx]
            
            # 直方圖
            df[col].hist(ax=ax, bins=20, alpha=0.7, edgecolor='black')
            ax.set_title(f'{col} 分布')
            ax.set_xlabel(col)
            ax.set_ylabel('頻數')
            
            # 添加統計信息
            stats_text = f'均值: {df[col].mean():.2f}\n標準差: {df[col].std():.2f}'
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 隱藏多余的子圖
        for i in range(len(numeric_cols), n_rows * n_cols):
            row_idx = i // n_cols
            col_idx = i % n_cols
            if n_rows == 1:
                axes[col_idx].axis('off')
            else:
                axes[row_idx][col_idx].axis('off')
        
        plt.tight_layout()
        return fig
    
    def create_correlation_heatmap(self, file_name, sheet_name, df, structure):
        """創建相關性熱力圖"""
        numeric_cols = structure['numeric_columns']
        if len(numeric_cols) < 2:
            return None
            
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 計算相關性矩陣
        corr_matrix = df[numeric_cols].corr()
        
        # 創建熱力圖
        im = ax.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        
        # 設置刻度標簽
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
        ax.set_yticklabels(numeric_cols)
        
        # 添加數值標注
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                              ha="center", va="center", color="black", fontweight='bold')
        
        ax.set_title(f'{file_name}\n工作表: {sheet_name}\n數值列相關性熱力圖', fontsize=14, fontweight='bold')
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        
        return fig
    
    def create_categorical_analysis(self, file_name, sheet_name, df, structure):
        """創建分類數據分析圖"""
        # 選擇分類列（非數值且唯一值數量較少的列）
        categorical_cols = []
        for col in df.columns:
            if col not in structure['numeric_columns']:
                unique_count = df[col].nunique()
                if 1 < unique_count <= 10:  # 唯一值數量在2-10之間
                    categorical_cols.append(col)
        
        if not categorical_cols:
            return None
            
        n_cols = min(3, len(categorical_cols))
        n_rows = (len(categorical_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        fig.suptitle(f'{file_name}\n工作表: {sheet_name}\n分類數據分析', fontsize=16, fontweight='bold')
        
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        elif n_cols == 1:
            axes = [[ax] for ax in axes]
        
        for i, col in enumerate(categorical_cols):
            row_idx = i // n_cols
            col_idx = i % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            else:
                ax = axes[row_idx][col_idx]
            
            # 計算頻數
            value_counts = df[col].value_counts()
            
            # 創建條形圖
            bars = ax.bar(range(len(value_counts)), value_counts.values, color=sns.color_palette("husl", len(value_counts)))
            ax.set_title(f'{col} 分布')
            ax.set_xlabel(col)
            ax.set_ylabel('計數')
            
            # 設置x軸標簽
            ax.set_xticks(range(len(value_counts)))
            ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
            
            # 在柱子上添加數值
            for j, (bar, count) in enumerate(zip(bars, value_counts.values)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom')
        
        # 隱藏多余的子圖
        for i in range(len(categorical_cols), n_rows * n_cols):
            row_idx = i // n_cols
            col_idx = i % n_cols
            if n_rows == 1:
                axes[col_idx].axis('off')
            else:
                axes[row_idx][col_idx].axis('off')
        
        plt.tight_layout()
        return fig
    
    def generate_all_visualizations(self):
        """生成所有可視化圖表"""
        if not self.excel_files:
            self.find_excel_files()
            
        all_visualizations = []
        
        for file_path in self.excel_files:
            print(f"\n處理文件: {file_path}")
            
            # 讀取所有工作表
            sheets_dict = self.read_excel_sheets(file_path)
            
            if sheets_dict:
                # 爲每個文件創建可視化
                file_viz = self.create_visualizations(file_path, sheets_dict)
                all_visualizations.append({
                    'file_name': file_path.name,
                    'file_path': file_path,
                    'visualizations': file_viz
                })
                
                print(f"  爲 {file_path.name} 創建了 {len(file_viz)} 個圖表")
            else:
                print(f"  無法讀取 {file_path.name} 或文件爲空")
        
        return all_visualizations
    
    def save_visualizations(self, output_dir='excel_visualizations'):
        """保存所有可視化圖表到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        visualizations = self.generate_all_visualizations()
        
        for file_viz in visualizations:
            file_name = file_viz['file_name']
            file_stem = Path(file_name).stem
            
            for viz_type, fig in file_viz['visualizations']:
                # 清理文件名
                safe_viz_type = "".join(c for c in viz_type if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_file = output_path / f"{file_stem}_{safe_viz_type}.png"
                
                fig.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
                print(f"保存圖表: {output_file}")
                
                plt.close(fig)  # 關閉圖形釋放內存
        
        print(f"\n所有圖表已保存到: {output_path.absolute()}")

def main():
    # 設置中文字體
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 指定要掃描的目錄
    base_directory = input("請輸入要掃描的目錄路徑 (默認爲當前目錄): ").strip()
    if not base_directory:
        base_directory = "."
    
    # 創建可視化器
    visualizer = ExcelVisualizer(base_directory)
    
    # 查找Excel文件
    excel_files = visualizer.find_excel_files()
    
    if not excel_files:
        print("在指定目錄中未找到任何Excel文件")
        return
    
    # 生成并保存可視化圖表
    print("\n開始生成可視化圖表...")
    visualizer.save_visualizations()
    
    print("\n任務完成!")

if __name__ == "__main__":
    main()
