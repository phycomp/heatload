import gdspy

lib = gdspy.GdsLibrary()
cell = lib.new_cell('COMPENSATED_QUANTUM_STRIPLINE')

W_LINE, W_PAD, L_LINE, L_TAPER, L_PAD = 27.27, 68.50, 10000.0, 300.0, 200.0

fp_core = gdspy.FlexPath(points=[(0, 0)], width=W_PAD, layer=1, datatype=0)
fp_core.segment(by_spacing=(0, L_PAD))
fp_core.segment(by_spacing=(0, L_TAPER), final_width=W_LINE)
fp_core.segment(by_spacing=(0, L_LINE - 2*L_TAPER - 2*L_PAD))
fp_core.segment(by_spacing=(0, L_TAPER), final_width=W_PAD)
fp_core.segment(by_spacing=(0, L_PAD))
cell.add(fp_core)

fp_trench = gdspy.FlexPath(points=[(0, 0)], width=W_PAD*3, layer=2, datatype=0)
fp_trench.segment(by_spacing=(0, L_PAD))
fp_trench.segment(by_spacing=(0, L_TAPER), final_width=W_LINE*3)
fp_trench.segment(by_spacing=(0, L_LINE - 2*L_TAPER - 2*L_PAD))
fp_trench.segment(by_spacing=(0, L_TAPER), final_width=W_PAD*3)
fp_trench.segment(by_spacing=(0, L_PAD))
cell.add(fp_trench)

lib.write_gds('compensated_quantum_stripline.gds')
print("GDSII Layout generated successfully.")