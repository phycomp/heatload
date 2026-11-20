## 4. `backend/main.py`（FastAPI 後端）

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import transmission_lines as T
import matching as M
import nlu as N

app = FastAPI(title="Impedance Intelligence Platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


class ParseReq(BaseModel):
    text: str
    use_llm: bool = False


class DesignReq(BaseModel):
    z0: float = 50.0
    h: float = 1.6          # mm
    t: float = 0.035        # mm (35 um = 1 oz)
    er: float = 4.2
    s: float = 0.2          # mm, gap for cpwg / diffpair
    method: str = "ipc"     # ipc | hammerstad


class WidthReq(BaseModel):
    w: float
    h: float = 1.6
    t: float = 0.035
    er: float = 4.2
    s: float = 0.2
    method: str = "ipc"


class LMatchReq(BaseModel):
    zl_re: float
    zl_im: float = 0.0
    z0: float = 50.0
    f_ghz: float | None = None


class StubReq(LMatchReq):
    kind: str = "single"        # single | double
    stub_type: str = "short"    # short | open
    d0_over_lambda: float = 0.125


class PiTReq(BaseModel):
    rs: float = 50.0
    rl: float = 100.0
    f_ghz: float | None = None
    q1: float | None = None     # pi network
    x2: float | None = None     # t network
    lowpass: bool = True


def _f(f_ghz):
    return f_ghz * 1e9 if f_ghz else None


@app.post("/api/parse")
def parse(req: ParseReq):
    return N.parse_smart(req.text) if req.use_llm else N.parse(req.text)


@app.post("/api/design/microstrip")
def design_ms(req: DesignReq):
    return T.design_microstrip(req.z0, req.h, req.t, req.er, req.method)


@app.post("/api/width/microstrip")
def width_ms(req: WidthReq):
    return T.microstrip_from_width(req.w, req.h, req.t, req.er, req.method)


@app.post("/api/design/stripline")
def design_sl(req: DesignReq):
    return T.design_stripline(req.z0, req.h, req.t, req.er)


@app.post("/api/design/cpwg")
def design_cpwg(req: DesignReq):
    return T.design_cpwg(req.z0, req.s, req.h, req.er)


@app.post("/api/design/diffpair")
def design_dp(req: DesignReq):
    w = T.microstrip_w_from_z0_ipc(req.z0 / 2, req.h, req.t, req.er)
    s = T.diffpair_s_from_zdiff(req.z0, w, req.h, req.t, req.er)
    return {"w_mm": w, "s_mm": s,
            "zdiff": T.diffpair_zdiff(w, s, req.h, req.t, req.er)}


@app.post("/api/match/l")
def match_l(req: LMatchReq):
    return M.l_match(complex(req.zl_re, req.zl_im), req.z0, f=_f(req.f_ghz))


@app.post("/api/match/stub")
def match_stub(req: StubReq):
    zl = complex(req.zl_re, req.zl_im)
    kinds = (req.stub_type,)
    if req.kind == "double":
        return M.double_stub(zl, req.z0, f=_f(req.f_ghz),
                             d0_over_lambda=req.d0_over_lambda,
                             stub_types=kinds)
    return M.single_stub(zl, req.z0, f=_f(req.f_ghz), stub_types=kinds)


@app.post("/api/match/pi")
def match_pi(req: PiTReq):
    return M.pi_match(req.rs, req.rl, f=_f(req.f_ghz),
                      q1=req.q1, lowpass=req.lowpass)


@app.post("/api/match/t")
def match_t(req: PiTReq):
    return M.t_match(req.rs, req.rl, f=_f(req.f_ghz), x2=req.x2)
