from math import sqrt as mthSqrt
# 柔性線函式庫/驗證/電氣計算.py
"""電氣特性計算 - 精確版 (含 Skew)"""

# ... (原有程式碼保持不變) ...


def 計算Skew(佈局, 頻率GHz=10, 長度mm=150):
    """
    計算通道間 Skew (相位不匹配)
    
    公式: Skew = Δtpd × L
    其中 Δtpd 為通道間傳播延遲差異
    
    參數:
        佈局: 佈局計算器實例
        頻率GHz: 頻率 (GHz)
        長度mm: 線長度 (mm)
    
    回傳:
        Skew (ps)
    """
    # 基礎傳播延遲
    εr = 3.3
    c = 3e8
    tpd = mthSqrt(εr) / c * 1e12  # ps/m
    
    # 通道間介電常數變異 (PI: ±0.1)
    Δεr = 0.1
    
    # 傳播延遲變異
    Δtpd = (mthSqrt(εr + Δεr) - mthSqrt(εr)) / c * 1e12  # ps/m
    
    # 總 Skew
    Skew = Δtpd * (長度mm / 1000)
    
    return {
        '公式': 'Skew = Δt_pd × L = (√(εᵣ+Δεᵣ) - √εᵣ)/c₀ × L',
        '參數': {
            'εᵣ': εr,
            'Δεᵣ': Δεr,
            'L': f'{長度mm} mm',
        },
        '計算結果': f'{Skew:.2f} ps',
        '物理意義': 'Skew 來自介電常數的製程變異，影響多通道同步性。',
        '設計建議': '降低 Skew：嚴格控制介電層厚度均勻性、選用低 Δεᵣ 材料。'
    }


def 計算Clearance(佈局, 規格類型):
    """
    計算間隙規格 (Clearance)
    
    參數:
        佈局: 佈局計算器實例
    
    回傳:
        dict: 間隙規格
    """
    if 規格類型 == 'FPC':
        # FPC 專屬間隙
        return {
            'Ground space': 100,
            'D1 (訊號單側間距)': 171,
            '線邊緣空白': 100,
            '層間隙 (H1)': 62.5,
            '層間隙 (H2)': 50.2,
            'PTH 直徑': 15, #'10~20'
        }
    else:
        # GSG 間隙
        return {
            '線邊緣空白': 佈局.邊緣間距 * 1000,
            '層間隙': sum(層['厚度um'] for 層 in 佈局.規格層 if '介電' in 層['名稱']) / 2,
            'PTH 直徑': 'N/A',
        }
