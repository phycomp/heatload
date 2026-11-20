def make_mesh(w: float, d: float, h: float, res: float = 1.0):
    """
    微帶雙線 2-D 截面
    單位 µm；回傳 skfem.Mesh
    """
    with pygmsh.geo.Geometry() as geom:
        rect = geom.add_rectangle([-w/2 - d, 0], w + 2*d, h)
        s1 = geom.add_rectangle([-w/2 - d, h], w, 0.1)   # 導體1
        s2 = geom.add_rectangle([d, h], w, 0.1)          # 導體2
        geom.set_mesh_size_callback(
            lambda dim, tag, x, y, z: res if y < h + 5 else res * 3
        )
        mesh = geom.generate_mesh()
    return Mesh.from_meshio(mesh)   # 轉成 skfem 格式

# ---------- 2. 計算互容 Cm ----------
def extract_Cm(w: float, d: float, h: float, er: float):
    mesh = make_mesh(w, d, h)
    basis = InteriorBasis(mesh, ElementTriP1())

    # 標記導體節點
    dof1 = basis.get_dofs(lambda x: np.isclose(x[1], h) & (x[0] <= -d/2))
    dof2 = basis.get_dofs(lambda x: np.isclose(x[1], h) & (x[0] >=  d/2))

    @bilinear_form
    def cform(u, v, w):
        # εr 在基板內，空氣區=1
        eps = er if w.y[0] < h else 1.0
        return sum(ui * vi for ui, vi in zip(u.grad, v.grad)) * eps

    C = asm(cform, basis)
    # 固定電位 1 V / 0 V → 解 Laplace
    A, b = condense(C, np.zeros(basis.N), I=dof1.all(), D=dof2.all())
    phi = solve(A, b)

    # 能量積分 = 1/2 C V^2 → C = 2*Energy
    energy = phi @ C @ phi
    Cm = energy * 1e12 * 1e-2          # pF / cm
    return Cm

# ---------- 3. 計算互感 Lm ----------
def extract_Lm(w: float, d: float, h: float):
    mesh = make_mesh(w, d, h)
    basis = InteriorBasis(mesh, ElementTriP1())
    dof1 = basis.get_dofs(lambda x: np.isclose(x[1], h) & (x[0] <= -d/2))
    dof2 = basis.get_dofs(lambda x: np.isclose(x[1], h) & (x[0] >=  d/2))

    @bilinear_form
    def lform(u, v, w):
        return sum(ui * vi for ui, vi in zip(u.grad, v.grad))

    L = asm(lform, basis)
    A, b = condense(L, np.zeros(basis.N), I=dof1.all(), D=dof2.all())
    phi = solve(A, b)
    energy = phi @ L @ phi
    Lm = energy * 1e9 * 1e-2             # nH / cm
    return Lm

# ---------- 4. 快速封裝 ----------
def lookup_Cm_Lm(w: float, d: float, h: float, er: float):
    return extract_Cm(w, d, h, er), extract_Lm(w, d, h)

# ---------- 5. 測試 ----------
if __name__ == "__main__":
    w, d, h, er = 400, 100, 200, 3.48      # µm, Rogers4350B
    Cm, Lm = lookup_Cm_Lm(w, d, h, er)
    print(f"Cm = {Cm:.3f} pF/cm,  Lm = {Lm:.3f} nH/cm")
