from numpy import abs, arange, ceil, interp, linspace, log, log10, pi, sqrt
from streamlit import session_state, markdown, columns, metric, caption, pyplot, warning
from matplotlib.pyplot import subplots

def calculate_next(c_m: float, c: float, l_m: float, l: float) -> float: # Crosstalk calculation functions
    """Calculate Near-End Crosstalk (NEXT) coefficient"""
    return 0.25 * (c_m / c + l_m / l)

def calculate_fext(c_m: float, c: float, l_m: float, l: float, v: float, length: float, rise_time: float) -> float:
    """Calculate Far-End Crosstalk (FEXT) coefficient"""
    k_f = (1 / (2 * v)) * (c_m / c - l_m / l)
    return (length / rise_time) * k_f

def calculate_coupling_coefficients(s: float, h: float, w: float, epsilon_r: float) -> Tuple[float, float, float, float]:
    """Calculate mutual capacitance and inductance for coupled striplines"""
    # Simplified model for coupled striplines
    # s: spacing, h: height to ground, w: width, epsilon_r: relative permittivity

    c = (2 * pi * epsilon_r * 8.854e-12) / log(2 * h / (w/2)) # Self capacitance per unit length (approximate)

    c_m = c * (h / (h + s)) * 0.1 # Mutual capacitance (approximate for parallel lines)

    mu_0 = 4 * pi * 1e-7 # Self inductance per unit length
    l = mu_0 * h / w

    l_m = l * (h / (h + s)) * 0.15 # Mutual inductance

    return c, c_m, l, l_m

def linear_to_db(linear: float) -> float:
    """Convert linear scale to dB"""
    return 20 * log10(abs(linear))

def 計算串擾(spacing, ground_plane_dist, line_width, epsilon_r):
  length=session_state['length']
  rise_time=session_state['rise_time']
  c, c_m, l, l_m=calculate_coupling_coefficients(spacing/1000, ground_plane_dist/1000, line_width/1000, epsilon_r) # Calculate coupling coefficients

  c_light = 3e8 # Velocity of propagation
  v = c_light / sqrt(epsilon_r)

  next_coeff = calculate_next(c_m, c, l_m, l) # Calculate NEXT and FEXT
  fext_coeff = calculate_fext(c_m, c, l_m, l, v, length/1000, rise_time/1e12)

  next_db = linear_to_db(next_coeff) # Convert to dB
  fext_db = linear_to_db(fext_coeff) if fext_coeff != 0 else -100

  # Display results
  markdown("### 📈 計算結果")

  res_col1, res_col2, res_col3 = columns(3)

  with res_col1:
      metric("近端串擾 (NEXT)", f"{next_coeff:.4f}", f"{next_db:.1f} dB")
      caption("耦合係數 (線性)")

  with res_col2:
      metric("遠端串擾 (FEXT)", f"{fext_coeff:.4f}", f"{fext_db:.1f} dB")
      caption("耦合係數 (線性)")

  with res_col3:
      total_crosstalk = sqrt(next_coeff**2 + fext_coeff**2)
      metric("總串擾", f"{total_crosstalk:.4f}", f"{linear_to_db(total_crosstalk):.1f} dB")

  # Visualization
  fig, (ax1, ax2) = subplots(1, 2, figsize=(14, 5))

  # Crosstalk vs Spacing
  spacings = linspace(0.1, 5.0, 50)
  next_vals = []
  fext_vals = []

  for s in spacings:
      c_t, c_m_t, l_t, l_m_t = calculate_coupling_coefficients(
          s/1000, ground_plane_dist/1000, line_width/1000, epsilon_r
      )
      next_vals.append(abs(calculate_next(c_m_t, c_t, l_m_t, l_t)))
      fext_vals.append(abs(calculate_fext(c_m_t, c_t, l_m_t, l_t, v, length/1000, rise_time/1e12)))

  ax1.semilogy(spacings, next_vals, 'b-', label='NEXT', linewidth=2)
  ax1.semilogy(spacings, fext_vals, 'r-', label='FEXT', linewidth=2)
  ax1.axvline(x=spacing, color='g', linestyle='--', label=f'Current: {spacing}mm')
  ax1.set_xlabel('Line Spacing (mm)')
  ax1.set_ylabel('Crosstalk Coefficient')
  ax1.set_title('Crosstalk vs Line Spacing')
  ax1.legend()
  ax1.grid(True, alpha=0.3)
  freqs = linspace(0.1, 40, 100) # Frequency response
  next_freq = [next_coeff * (1 + f/10) for f in freqs] # Simplified frequency dependence
  fext_freq = [fext_coeff * (f/6) for f in freqs]

  ax2.plot(freqs, 20*log10(abs(next_freq)), 'b-', label='NEXT', linewidth=2)
  ax2.plot(freqs, 20*log10(abs(fext_freq)), 'r-', label='FEXT', linewidth=2)
  freq = session_state['freq']
  ax2.axvline(x=freq, color='g', linestyle='--', label=f'Current: {freq}GHz')
  ax2.set_xlabel('Frequency (GHz)')
  ax2.set_ylabel('Crosstalk (dB)')
  ax2.set_title('Frequency Response')
  ax2.legend()
  ax2.grid(True, alpha=0.3)

  pyplot(fig)

  # Recommendations
  markdown("### 💡 設計建議")
  if next_db > -40 or fext_db > -40:
      warning("⚠️ 串擾水平較高，建議增加線間距或使用屏蔽結構")
  elif next_db > -60 or fext_db > -60:
      info("ℹ️ 串擾水平中等，適合一般量子計算應用")
  else:
      success("✅ 串擾水平優良，適合高精度量子計算")
