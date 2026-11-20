import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

def test_import_core():
    import 量傳線設計.核心 as c
    assert c is not None

def test_三視圖_layout():
    from 量傳線設計.核心.三視圖 import LayoutCalculator
    L = LayoutCalculator(通道數=8)
    assert L.通道數 == 8

def test_規格產生器():
    from 量傳線設計.核心.規格產生器 import 產生規格書
    佈局, 試算表 = 產生規格書()
    assert 試算表 is not None

def test_低溫超導():
    from 量傳線設計.核心.低溫超導 import 模擬NbTi串擾
    r = 模擬NbTi串擾()
    assert "Z0" in r

def test_熱負載():
    from 量傳線設計.核心.熱負載 import 熱負載曲線, 回推溫區長度
    r = 熱負載曲線()
    assert len(r["T"]) > 0
    L = 回推溫區長度()
    assert L > 0

def test_傳輸線規格():
    from 量傳線設計.核心.傳輸線規格 import 全部規格
    s = 全部規格()
    assert set(s.keys()) == {"CF3", "FPC", "Uleam1"}

def test_其它():
    from 量傳線設計.核心.其它 import calculate_microstrip_width, 波導截止頻率
    W = calculate_microstrip_width(50, 4.4, 1.6)
    assert W > 0
    fc = 波導截止頻率(0.02286, 0.01016)
    assert fc > 0

def test_HJ串擾_import():
    import matplotlib.pyplot as plt
    from 量傳線設計.核心.HJ串擾 import HJ模型, 優化
    HJ模型()
    fig = plt.gcf()
    assert fig is not None

def test_熱負載回推():
    from 量傳線設計.核心.熱負載回推 import 回推模型比較, 溫度分布
    models, lengths = 回推模型比較()
    assert len(models) == len(lengths)
    x, T = 溫度分布(20.0, 10.0, 350.0)
    assert len(x) == 100

def test_三視圖進階():
    from 量傳線設計.核心.三視圖進階 import StriplineGeometry, LabelPlacementDetector
    geo = StriplineGeometry(w=0.035, t=0.002, h=0.129, s=2.0, L=200.0, n_channels=8)
    det = LabelPlacementDetector(10.0, 1.0, 8)
    assert det is not None

def test_低溫超導_Bloch():
    from 量傳線設計.核心.低溫超導 import BlochGruneisen電阻率
    rho = BlochGruneisen電阻率(10, rho0=1e-8, theta_D=300)
    assert rho >= 0

def test_NbTi_Z0_range():
    from 量傳線設計.核心.低溫超導 import 模擬NbTi串擾
    r = 模擬NbTi串擾()
    assert 40 < r["Z0"] < 200

def test_微帶線寬_numeric():
    from 量傳線設計.核心.其它 import calculate_microstrip_width
    W = calculate_microstrip_width(50, 4.4, 1.6)
    assert 2.0 < W < 4.0

def test_回推長度_numeric():
    from 量傳線設計.核心.熱負載 import 回推溫區長度
    L = 回推溫區長度(熱導率=0.1, 截面積=1e-6, 溫差=50.0, 熱負載_W=1e-6)
    assert L > 0 and L < 10

def test_閉環_eval():
    from 量傳線設計.核心.閉環量傳線 import evaluate_stripline
    z0, qi, alpha, beta = evaluate_stripline(15.0, 0.0, 7e9, 0.1)
    assert z0 > 0
    assert qi > 0

def test_多層結構_import():
    from 量傳線設計.核心.多層結構 import StriplineGeometry, 立體透視
    import matplotlib.pyplot as plt
    geo = StriplineGeometry(w=0.3, t=5, h=0.15, s=2.0, L=400, n_channels=8)
    fig = 立體透視(geo, 2.0, 400, 8)
    assert fig is not None

def test_智慧佈局_import():
    from 量傳線設計.核心.智慧佈局 import StriplineGeometry, draw_optimized_front_view
    import matplotlib.pyplot as plt
    geo = StriplineGeometry(w=0.3, t=5, h=0.15, s=2.0, L=400, n_channels=8)
    fig = draw_optimized_front_view(geo, 2.0, True, 150.0, 2.0, 8)
    assert fig is not None

def test_標註偵測():
    from 量傳線設計.核心.三視圖進階 import StriplineGeometry, draw_smart_side_view
    import matplotlib.pyplot as plt
    geo = StriplineGeometry(w=0.035, t=0.002, h=0.129, s=2.0, L=200.0, n_channels=8)
    fig = draw_smart_side_view(geo, 2.0, 200.0, False, 0.2, 0.5, 8)
    assert fig is not None

def test_智慧佈局_export():
    from 量傳線設計.核心.智慧佈局 import StriplineGeometry, export_optimized_xlsx
    geo = StriplineGeometry(w=0.3, t=5, h=0.15, s=2.0, L=400, n_channels=8)
    data = export_optimized_xlsx(geo, 2.0, 400.0, True, 150.0, 2.0, 8, 0.3, 0.15, 0.005)
    assert data is not None and len(data) > 0

def test_FLAX_geometry():
    from 量傳線設計.核心.熱負載FLAX import compute_geometry, compute_heat_load
    geo = compute_geometry(0.127, 0.279, 0.0254, 3.56, 10)
    assert geo['n_traces'] == 10
    res = compute_heat_load(geo, 0.1, 1.0, 30.48, 0.08, 1.5, 0.007, 2.0)
    assert res['Q_total_nW'] > 0

def test_Raicu_static():
    from 量傳線設計.核心.熱負載Raicu import DEFAULT_STAGES, calc_static_heat_single
    sp = DEFAULT_STAGES["4K"]
    res = calc_static_heat_single(sp, "4K")
    assert res["total"] > 0

def test_Raicu_total():
    from 量傳線設計.核心.熱負載Raicu import DEFAULT_STAGES, calc_total_heat
    tot = calc_total_heat(DEFAULT_STAGES, 100)
    assert tot is not None
    assert tot["total"]["MXC"]["total"] > 0

def test_Raicu_integrate():
    from 量傳線設計.核心.熱負載Raicu import integrate_k
    val = integrate_k(4.0, 10.0, "outer")
    assert val > 0

def test_Raicu_total_boundary():
    from 量傳線設計.核心.熱負載Raicu import DEFAULT_STAGES, calc_total_heat
    tot = calc_total_heat(DEFAULT_STAGES, 100, multiplex=6)
    assert tot is not None
    assert tot["processor"]["qubits"] == 100

