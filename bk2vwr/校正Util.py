from numpy import frombuffer, linspace, zeros
from skrf import Network
from pathlib import Path
from io import BytesIO

CAL_SET_OFFSET = 0x400      # 固定偏移（官方文件）
POINTS_OFFSET  = 0x1A       # 頻率點數位置
FREQ_START     = 0x24       # 起始頻率 (Hz)
FREQ_STOP      = 0x30       # 終止頻率 (Hz)

def 校正網絡(chx_path: Path) -> Network:
    buf = chx_path.read_bytes()
    n_pts = int.from_bytes(buf[POINTS_OFFSET:POINTS_OFFSET+4], 'little')
    f_start = int.from_bytes(buf[FREQ_START:FREQ_START+8], 'little')
    f_stop  = int.from_bytes(buf[FREQ_STOP:FREQ_STOP+8], 'little')
    freqs = linspace(f_start, f_stop, n_pts)

    # 每點 8 byte × 4 S-param (S11RE, S11IM, S21RE, S21IM)
    cal_data = frombuffer(
        buf[CAL_SET_OFFSET:CAL_SET_OFFSET + n_pts*32],
        dtype='<f8'
    ).reshape(n_pts, 4)          # RI 順序

    # 組成 2×2 複數矩陣 [n_freq, n_out, n_in]
    s = zeros((n_pts, 2, 2), dtype=complex)
    s[:, 0, 0] = cal_data[:, 0] + 1j*cal_data[:, 1]   # S11
    s[:, 1, 0] = cal_data[:, 2] + 1j*cal_data[:, 3]   # S21
    # 假設互易 & 無反射，其餘補 0/1
    s[:, 0, 1] = 0
    s[:, 1, 1] = 1

    return Network(frequency=freqs, s=s, name=chx_path.stem)
