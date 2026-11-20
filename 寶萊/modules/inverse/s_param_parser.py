# import os
#base = "/mnt/agents/output/pcb_calc_app"
#os.makedirs(f"{base}/modules/inverse", exist_ok=True)
#open(f"{base}/modules/inverse/__init__.py", "w").close()

# ========== 1. S 參數解析器 (自寫 Touchstone 解析器) ==========

"""
Touchstone S 參數文件解析器 (.s1p / .s2p / .s3p / .s4p)
不依賴 scikit-rf，純自寫解析
支持格式: MA (幅度-角度), DB (dB-角度), RI (實部-虛部)
"""
import numpy as np
from typing import Dict, List, Tuple, Optional


class TouchstoneParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.freq_unit = "GHz"  # Hz, kHz, MHz, GHz
        self.parameter = "S"
        self.format = "MA"      # MA, DB, RI
        self.n_ports = 2
        self.reference_impedance = 50.0
        self._data = None
        self._parse()

    def _parse(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        data_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            if line.startswith("#"):
                self._parse_header(line)
                continue
            if line.startswith("[Version]") or line.startswith("[Number of Ports]"):
                continue
            data_lines.append(line)

        self._parse_data(data_lines)

    def _parse_header(self, header_line: str):
        parts = header_line[1:].strip().split()
        for i, part in enumerate(parts):
            part_lower = part.lower()
            if part_lower in ("hz", "khz", "mhz", "ghz"):
                self.freq_unit = part
            elif part_lower in ("s", "y", "z", "h", "g"):
                self.parameter = part.upper()
            elif part_lower in ("ma", "db", "ri"):
                self.format = part.upper()
            elif part_lower == "r":
                if i + 1 < len(parts):
                    self.reference_impedance = float(parts[i + 1])

    def _parse_data(self, data_lines: List[str]):
        all_values = []
        for line in data_lines:
            vals = [float(x) for x in line.split() if x.strip()]
            all_values.extend(vals)

        # 每行數據: freq, S11, S21, S12, S22 (對于 2-port)
        # 根據格式和端口數確定每行元素數
        n_data_per_port_pair = 2  # 每個 S 參數有 2 個值 (幅度/相位 或 實部/虛部)
        n_s_params = self.n_ports * self.n_ports
        cols_per_row = 1 + n_s_params * n_data_per_port_pair  # freq + S-params

        # 將數據重組爲矩陣
        n_rows = len(all_values) // cols_per_row
        data = np.array(all_values[:n_rows * cols_per_row]).reshape(n_rows, cols_per_row)

        freqs = data[:, 0]
        # 頻率轉換爲 Hz
        unit_mult = {"hz": 1.0, "khz": 1e3, "mhz": 1e6, "ghz": 1e9}
        freqs_hz = freqs * unit_mult.get(self.freq_unit.lower(), 1e9)
        freqs_ghz = freqs_hz / 1e9

        # 解析 S 參數
        s_params = {}
        for i in range(self.n_ports):
            for j in range(self.n_ports):
                idx = i * self.n_ports + j
                col_start = 1 + idx * 2
                val1 = data[:, col_start]
                val2 = data[:, col_start + 1]

                if self.format == "DB":
                    mag = 10 ** (val1 / 20.0)
                    phase_rad = np.deg2rad(val2)
                    s_complex = mag * np.exp(1j * phase_rad)
                elif self.format == "MA":
                    phase_rad = np.deg2rad(val2)
                    s_complex = val1 * np.exp(1j * phase_rad)
                elif self.format == "RI":
                    s_complex = val1 + 1j * val2
                else:
                    s_complex = val1 + 1j * val2

                s_params[f"S{i+1}{j+1}"] = s_complex

        self._data = {
            "freq_hz": freqs_hz,
            "freq_ghz": freqs_ghz,
            "s_params": s_params,
            "z0": self.reference_impedance
        }

    def get_frequencies_ghz(self) -> np.ndarray:
        return self._data["freq_ghz"]

    def get_s_param(self, name: str) -> np.ndarray:
        return self._data["s_params"].get(name, np.array([]))

    def get_s21_db(self) -> np.ndarray:
        s21 = self.get_s_param("S21")
        return 20.0 * np.log10(np.abs(s21) + 1e-15)

    def get_s11_db(self) -> np.ndarray:
        s11 = self.get_s_param("S11")
        return 20.0 * np.log10(np.abs(s11) + 1e-15)

    def get_s21_magnitude(self) -> np.ndarray:
        return np.abs(self.get_s_param("S21"))

    def get_s11_magnitude(self) -> np.ndarray:
        return np.abs(self.get_s_param("S11"))

    def get_data_summary(self) -> dict:
        return {
            "freq_range_ghz": (self._data["freq_ghz"].min(), self._data["freq_ghz"].max()),
            "n_points": len(self._data["freq_ghz"]),
            "format": self.format,
            "z0": self.reference_impedance,
            "s21_min_db": self.get_s21_db().min(),
            "s21_max_db": self.get_s21_db().max(),
            "s11_min_db": self.get_s11_db().min(),
            "s11_max_db": self.get_s11_db().max()
        }

# with open(f"{base}/modules/inverse/s_param_parser.py", "w", encoding="utf-8") as f:
    # f.write(s_param_parser)

# print("✅ s_param_parser.py 已創建")
