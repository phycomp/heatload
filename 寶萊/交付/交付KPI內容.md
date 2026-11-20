```
專案：PCB 傳輸線逆工程——物理推導（DOC-002 之後續）
│
├─ Q1 交付物 = D（A→B→C）
│   逆工程定義：DOC-002 之外，開發可解析式/漸進式推導
│   ├─ a. Mantaro 截面
│   └─ b. Polar 幾何疊構
│
├─ Q2 截面範圍 = C（最大範圍）
│   ├─ 傳輸線級（9 項）：
│   │   Microstrip / Stripline / CPW
│   │   Diff Microstrip / Diff Stripline
│   │   Embedded Microstrip / Asymmetric Stripline
│   │   Broadside Coupled Stripline
│   │   ＋ 各截面之 From-Z₀ 逆解版
│   └─ 元件級（≥4 項）：
│       Coax / Parallel Wire / Plane Impedance / Pad Capacitance
│
├─ Q3 疊構範圍 = C（全部）
│   ├─ Rigid：4L/6L/8L/10L（foil build / core build / RF build）
│   ├─ HDI：10L 3 press cycle / 10L 4 press cycle
│   └─ Flex-Rigid：4L~10L 剛撓結合＋stiffener
│       → 含剛撓交界阻抗不連續漸進模型（Mantaro 無此領域，價值最高）
│
├─ Q4 逆解方法學 = B（分級推導深度）
│   ├─ 🟢🟡（Microstrip/Stripline/Coax/...）→ 解析反函數
│   ├─ 🟠（Asymmetric/Broadside）→ 級數反轉/漸進反演＋誤差界
│   └─ 🔴（Diff Stripline/Flex-Rigid 交界）→ 牛頓迭代
│       ＋收斂域證明＋初始值選取法
│
├─ Q5 驗證基準 = B（分級容差）
│   ├─ Mantaro 有的截面 → 對 Mantaro，±1%（公式同源）
│   ├─ Mantaro 沒有的（CPW 逆解/Flex-Rigid）→ 文獻值＋極限解析驗證，±5%
│   └─ 每點三步驗證：反解 → 正算代回 → 第三方比對，全過才算通過
│
└─ Q6 介面定案
    ├─ DOC-003 結構 = c 混合式
    │   Part I 反演方法論（反函數/級數反轉/牛頓收斂理論）
    │   Part II 各截面應用章（與 DOC-002 體例對齊）
    │   Part III 疊構映射（Polar 模板 → 截面公式選擇規則）
    └─ Python API = 丙 兩層式
        核心層 solve(section, stackup, target, method, tol)
        便利層 Stackup.from_polar_template() → assign(layer, target_z0)
```
