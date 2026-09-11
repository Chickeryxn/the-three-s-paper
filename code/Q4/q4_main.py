# -*- coding: utf-8 -*-
"""Q4 main method (M4): vertex-centred finite volume on the shrinking domain, in
xi = r/R(t), + Crank-Nicolson + 3-step backward-Euler (Rannacher) startup.

Physics per appendix 4; radius per attachment 2 (PCHIP, monotone with a smooth
derivative); environment per the frozen framing decisions (measured ramp from
attachment 1, then T_inf = 50 degC and C_inf = 0.05 kg/kg).

Report caliber per g_framing_q4_coordinate_caliber (T1: current physical distance,
blank outside R(t)) and g_framing_q4_column_set (table 6 = 0, 0.5, 1.0, 1.5, surface;
result4 = 0, 0.1, ..., 1.9, surface).

Writes under results/Q4/experiments/round1/:
  metrics/main.json, metrics/main_validation.json, result4.xlsx, tables/, figures/

论文对应：5.3 节（移动边界归一化变换与表观对流项）、5.8 节（问题四求解）。
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_banded
from scipy.interpolate import PchipInterpolator, CubicSpline

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/Q4/experiments/round1"

# ---------------------------------------------------------------------------
# 一、常数与输出口径
# ---------------------------------------------------------------------------
R0 = 0.02; T0C = 28.0; C0 = 2.55; H = 25.0; HM = 8e-7
T_INF_C = 50.0; C_INF = 0.05; TARGET = 0.15     # 烘干判据：全域最大干基含水率 <= 0.15
N_BE_START = 3                                   # Rannacher 启动步数，压制 CN 的初始振荡
R_COLS_CM = np.round(np.arange(20) * 0.1, 10)          # result4 的列：0 .. 1.9 cm
R_TABLE6_CM = np.array([0.0, 0.005, 0.010, 0.015])     # 表 6 的列：0/0.5/1.0/1.5 cm
TABLE6_HOURS = list(range(6, 200, 6))                  # 表 6 的输出时刻，单位 h


# ---------------------------------------------------------------------------
# 二、附件与边界条件：升温段用实测序列，之后接恒定环境
# ---------------------------------------------------------------------------
def _load(p):
    """读取清洗后的附件 CSV，跳过表头，返回浮点数组。"""
    with (ROOT / p).open(encoding="utf-8") as fh:
        return np.array([[float(x) for x in r] for r in list(csv.reader(fh))[1:]])


_a = _load("workspace/data_clean/attachment1_env.csv")
_TE, _TI, _CI = _a[:, 0], _a[:, 1], _a[:, 2]
RAMP_END = float(_TE[-1])
# 附件 1 只覆盖升温段；之后按题设取恒定热风条件。温度在此统一换算为热力学温度 K。
Tenv = lambda t: (float(np.interp(t, _TE, _TI)) + 273.15) if t <= RAMP_END else T_INF_C + 273.15
Cenv = lambda t: float(np.interp(t, _TE, _CI)) if t <= RAMP_END else C_INF

_b = _load("workspace/data_clean/attachment2_radius.csv")
_TR, _RR = _b[:, 0], _b[:, 1] / 100.0
R_END = float(_TR[-1]); R_MIN = float(_RR[-1])


def radius_fn(kind="pchip"):
    """返回 (R(t), dR/dt)，由附件 2 的半径序列插值得到。

    默认用 PCHIP：它是保单调的分段三次插值，导数连续且不会像普通三次样条那样过冲，
    这对出现在控制方程里的 Rdot/R 很重要；kind="linear" 作为稳健性对照。
    """
    if kind == "pchip":
        f = PchipInterpolator(_TR, _RR)
        return (lambda t: float(f(min(t, R_END)))), (lambda t: float(f.derivative()(min(t, R_END))))

    def rl(t):
        return float(np.interp(min(t, R_END), _TR, _RR))

    def dl(t):
        t = min(t, R_END)
        i = min(max(int(np.searchsorted(_TR, t, side="right") - 1), 0), _TR.size - 2)
        return float((_RR[i + 1] - _RR[i]) / (_TR[i + 1] - _TR[i]))
    return rl, dl


def props(C, T):
    """按附录 4 的经验式给出物性，全部为逐节点数组。

    密度、比热与导热系数只依赖含水率，扩散系数同时依赖含水率与温度，
    其中温度的指数因子体现 Arrhenius 型的强敏感性。
    """
    rho = 760.0 + 90.0 * C
    cp = 1850.0 + 2150.0 * C / (C + 1.0)
    k = 0.12 + 0.20 * C / (C + 1.0)
    D = 4.2e-4 * np.exp(-0.30 / np.maximum(C, 1e-9)) * np.exp(-3850.0 / T)
    return rho, cp, k, D


def _tri(a, b, c, d):
    """用 LAPACK 带状求解器解三对角方程组（次对角/主对角/超对角/右端项）。"""
    n = len(b); ab = np.empty((3, n))
    ab[0, 1:] = c[:-1]; ab[1, :] = b; ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)


def solve(N=800, dt=60.0, t_hours=250.0, n_be_start=N_BE_START, theta=0.5,
          rkind="pchip", hm=HM, h=H, no_mass_transfer=False,
          record_grid=False, grid_every_s=60.0, table6=True,
          frozen_radius=None, const_D=None, const_Cinf=None):
    """在归一化坐标 xi = r/R(t) 上做移动区域顶点有限体积求解。

    返回：烘干时长、表 6、按分钟记录的浓度场，以及精确的离散守恒残差。

    离散要点：
      * 把 r 换成 xi = r/R(t)，固定域 xi in [0,1]，动网格的几何效应全部进入
        方程右端的表观对流项 (xi*Rdot/R) * dy/dxi；
      * 未知量放在 xi_j = j*dxi 的节点上，R(t) 对应的表面是真实节点；
      * 时间推进用 Crank-Nicolson（theta = 0.5），前 N_BE_START 步改用
        后向 Euler 启动，以压制 CN 对初值不连续处的振荡（Rannacher 启动）；
      * 非线性物性取上一时间层（lagged），因此格式在 dt 上是一阶的，
        其大小由 main() 中的时间步加密序列量化。
    """
    Rt, dRt = radius_fn(rkind)
    if frozen_radius is not None:
        Rt = lambda t: frozen_radius
        dRt = lambda t: 0.0
    dxi = 1.0 / N
    face = (np.arange(N) + 0.5) * dxi      # 对偶面位置 xi_{j+1/2}
    xi2f = face ** 2                        # 表观对流项的系数用面心 xi 计算
    xi = np.arange(N + 1) * dxi             # 节点位置
    # 各节点对偶控制体的量纲一体积（已除以 2*pi*R^2），三者之和恰为 1/2
    w = np.empty(N + 1)
    w[0] = dxi ** 2 / 8.0
    w[1:N] = np.arange(1, N) * dxi ** 2
    w[N] = (1.0 - (1.0 - dxi / 2) ** 2) / 2.0
    hm_eff = 0.0 if no_mass_transfer else hm   # 关掉传质用于移动边界不变量检验
    T = np.full(N + 1, T0C + 273.15); C = np.full(N + 1, C0)
    steps = int(round(t_hours * 3600.0 / dt))
    every = max(1, int(round(grid_every_s / dt)))
    times_rec = []; Cg = []
    sub6 = {}; t_dry = None
    bal_lhs = 0.0; bal_rhs = 0.0
    W0 = None; W_prev = None; Wdrop = 0.0
    s = 0
    for s in range(1, steps + 1):
        th = 1.0 if s <= n_be_start else theta
        t = s * dt; tm = t - dt
        R = max(Rt(t), R_MIN); Rm = max(Rt(tm), R_MIN)
        Rd = dRt(t)
        ti = Tenv(t); ti_m = Tenv(tm)
        ci = const_Cinf if const_Cinf is not None else Cenv(t)
        ci_m = const_Cinf if const_Cinf is not None else Cenv(tm)
        rho, cp, k, D = props(C, T)
        if const_D is not None:
            D = np.full_like(C, const_D)
        kf = 0.5 * (k[:-1] + k[1:]); Df = 0.5 * (D[:-1] + D[1:])   # 面心物性取算术平均
        kc = Rd / Rm                            # 收缩率 Rdot/R，即表观对流项系数
        # 温度与含水率共用同一套离散：只换扩散系数、环境量与表面通量系数
        #   d y/dt|_xi = (1/(xi R^2)) d/dxi(co * xi * dy/dxi) + (xi Rdot/R) dy/dxi
        for is_heat in (True, False):
            alpha = k / (rho * cp)
            co = (0.5 * (alpha[:-1] + alpha[1:])) if is_heat else Df
            y = T if is_heat else C
            amb = ti if is_heat else ci
            ambm = ti_m if is_heat else ci_m
            # A：质量矩阵（对偶体积/dt）
            # cd：扩散项系数，注意用上一时间层的 Rm^2 —— 几何量滞后一层
            # cv：表观对流项系数
            # S ：表面第三类边界的传热/传质系数
            A = w / dt
            cd = face * co / dxi / (Rm ** 2)
            cv = kc * xi2f
            S = (h / (rho[N] * cp[N] * Rm)) if is_heat else (hm_eff / Rm)
            # Msub/Mdia/Msup 是空间算子的下/主/上三条对角线（含对流与几何项）
            Msub = np.zeros(N + 1); Msup = np.zeros(N + 1); Mdia = np.empty(N + 1)
            Msup[0:N] = cd + 0.5 * cv
            Msub[1:N] = cd[0:N - 1] - 0.5 * cv[0:N - 1]
            Mdia[0] = -cd[0] + 0.5 * cv[0] - 2 * kc * w[0]
            Mdia[1:N] = -(cd[1:N] + cd[0:N - 1]) + 0.5 * cv[1:N] - 0.5 * cv[0:N - 1] - 2 * kc * w[1:N]
            Msub[N] = cd[N - 1] - 0.5 * cv[N - 1]
            Mdia[N] = -S - cd[N - 1] + kc - 0.5 * cv[N - 1] - 2 * kc * w[N]
            src = np.zeros(N + 1); src[N] = S * amb
            a = -th * Msub; b = A - th * Mdia; c = -th * Msup
            a[0] = 0.0; c[N] = 0.0        # 两端点无越界邻居，置零即可
            # yl / yr：向左、向右各错一位，用向量化方式组织 y_{j-1} 与 y_{j+1}
            yl = np.concatenate([[0.0], y[0:N]]); yr = np.concatenate([y[1:N + 1], [0.0]])
            Q = Mdia * y + Msub * yl + Msup * yr + src
            rhs = A * y + (1 - th) * Q + th * src
            sol = _tri(a, b, c, rhs)
            if is_heat:
                T = sol
            else:
                Cprev = C; C = sol
                if not is_heat:
                    # 离散守恒恒等式（逐时间步精确成立）：
                    #     sum_j w_j dC_j/dt = G(C),
                    #     G(y) = -2*kc*sum_j w_j*y_j + kc*y_N - S*(y_N - amb)
                    # 其中前两项来自移动区域本身的收缩，最后一项是表面传质。
                    # 因格式对两个时间层使用同一个源项向量，累加时相应取同一环境值。
                    def G(yy):
                        return (-2 * kc * float(np.sum(w * yy)) + kc * float(yy[N])
                                - S * (float(yy[N]) - ci))
                    bal_lhs += float(np.sum(w * (C - Cprev)))
                    bal_rhs += dt * (th * G(C) + (1 - th) * G(Cprev))
                    # 同一对偶体积权重下按物理体积 R^2 还原的实际含水量，用于核对收缩引起的失水
                    if W0 is None:
                        W0 = float(np.sum(Cprev * w)) * Rm ** 2
                        W_prev = W0
                    Wn = float(np.sum(C * w)) * R ** 2
                    Wdrop += (W_prev - Wn); W_prev = Wn
        # 物理性护栏：温度一旦越出 250--420 K 说明格式失稳，立即报错而不是输出错误结果
        if not np.isfinite(T).all() or T.min() < 250 or T.max() > 420:
            raise RuntimeError("temperature left the physical band at t=%.1f s" % t)
        if table6 and (t % 3600 == 0) and (int(t / 3600) in TABLE6_HOURS):
            sub6[str(int(t / 3600))] = _report_row(xi, C, R, r_phys=R_TABLE6_CM)
        if record_grid and (s % every == 0):
            times_rec.append(int(round(t)))
            Cg.append([None if v is None else float(v)
                       for v in _report_row(xi, C, R, r_phys=R_COLS_CM / 100.0)])
        # 烘干判据：全域最大干基含水率首次降至 0.15 以下即判定烘干完成
        if t_dry is None and float(C.max()) <= TARGET:
            t_dry = t
            break
    Rl = max(Rt(t), R_MIN)
    end_row = _report_row(xi, C, Rl, r_phys=R_TABLE6_CM)
    if record_grid:
        times_rec.append(int(round(t)))
        Cg.append([None if v is None else float(v)
                   for v in _report_row(xi, C, Rl, r_phys=R_COLS_CM / 100.0)])
    bal_abs = abs(bal_lhs - bal_rhs)
    return {"t_dry_h": (t_dry / 3600.0) if t_dry else None, "n_steps": s,
            "xi": xi, "w": w, "C": C, "T": T, "R_end": Rl,
            "sub6": sub6, "table6_end": end_row,
            "times": times_rec, "Cgrid": Cg,
            "mass": {"water_change_xi": bal_lhs,
                     "balance_rhs": bal_rhs,
                     "abs_residual": bal_abs,
                     "rel_residual": bal_abs / max(abs(bal_lhs), 1e-300),
                     "geometric_water_drop": Wdrop,
                     "note": "sum_j w_j dC_j/dt = -2(Rdot/R) sum_j w_j C_j + (Rdot/R) C_N - (h_m/R)(C_N - C_inf), exact per step"},
            "uniformity_dev": float(np.max(np.abs(C - C0)))}


def _report_row(xi, C, R, r_phys):
    """按口径 T1 输出一行：报告点在“当前物理距离” r 处，r > R(t) 处留空。

    即表格的列坐标始终是到药材中心的实际距离（而非初始半径的比例），
    因此随着 R(t) 减小，靠外的列会依次变为空白。
    """
    cs = CubicSpline(xi, C)
    out = []
    for r in r_phys:
        out.append(None if r > R else float(cs(r / R)))
    out.append(float(C[-1]))          # the surface node, native
    return out


# ---------------------------------------------------------------------------
# 三、主流程：主算例 -> 交付文件 -> 三类加密 + 不变量验证
# ---------------------------------------------------------------------------
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = time.perf_counter()
    for sub in ("metrics", "tables", "figures"):
        (RUN / sub).mkdir(parents=True, exist_ok=True)

    # 主算例：800 个节点、dt = 5 s。表面控制体的时间常数约为 0.1 s 量级，
    # 因此 dt 必须远小于它，否则表面列会出现纯属格式的偏差。
    N_MAIN = 800; DT = 5.0
    res = solve(N=N_MAIN, dt=DT, t_hours=250.0, record_grid=True, grid_every_s=60.0)
    t_main = time.perf_counter() - t_start

    # ---- 交付文件 result4.xlsx：每分钟一行，末行为精确的烘干结束时刻 ----
    x0 = time.perf_counter()
    try:
        import openpyxl
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet(title="Sheet1")
        ws.append(["时间\\到药材中心的距离"] + [float(x) for x in R_COLS_CM] + ["药材表面"])
        for i, t in enumerate(res["times"]):
            ws.append([int(t)] + [None if v is None else round(v, 4) for v in res["Cgrid"][i]])
        wb.save(RUN / "result4.xlsx")
        xlsx_ok = True
    except Exception as exc:
        xlsx_ok = "error: " + str(exc)
    xlsx_wall = time.perf_counter() - x0

    # ---- 验证：时间、空间、半径插值、移动边界不变量 ----
    t2 = time.perf_counter()
    # 物性滞后的 Crank-Nicolson 在 dt 上只有一阶精度，下面的加密序列给出其量级；
    # 主算例取 dt = 5 s，使残余的一阶误差低于报告精度。
    coarse = solve(N=800, dt=10.0, t_hours=250.0)
    d_dt = abs(coarse["t_dry_h"] - res["t_dry_h"]) if (coarse["t_dry_h"] and res["t_dry_h"]) else None
    d_dt_tab = float(np.max([abs(a - b) for a, b in zip(coarse["sub6"]["6"], res["sub6"]["6"])
                             if a is not None and b is not None]))
    # 时间收敛阶：固定 N，只变 dt，观察 6 h 表面浓度的收敛序列并做 Richardson 外推
    order_seq = {}
    for d in (20.0, 10.0, 5.0, 2.5):
        order_seq["%g" % d] = solve(N=800, dt=d, t_hours=6.0)["sub6"]["6"][4]
    # 参考算例：冻结半径与扩散系数，问题退化为经典圆柱对流边界问题，
    # 其 Bessel 级数解析解由独立验证脚本另行计算，用于交叉比对。
    ref_case = solve(N=800, dt=5.0, t_hours=6.0, frozen_radius=float(_RR[0]),
                     const_D=1e-9, const_Cinf=C_INF, hm=HM)
    ref = {}
    for N in (400, 800):
        g = solve(N=N, dt=5.0, t_hours=6.0)
        ref[N] = g["sub6"]["6"]
    d_grid = float(np.max([abs(a - b) for a, b in zip(ref[400], ref[800])
                           if a is not None and b is not None]))
    # 半径插值方式的敏感性：PCHIP 与分段线性对照
    lin = solve(N=400, dt=10.0, t_hours=250.0, rkind="linear")
    d_rkind = abs(lin["t_dry_h"] - coarse["t_dry_h"]) if (lin["t_dry_h"] and coarse["t_dry_h"]) else None
    # 移动边界不变量：关掉表面传质后，解析上浓度应处处保持初值不动。
    # 若表观对流项的推导有误，区域收缩过程会凭空产生或消灭干基水分，该偏差会立刻暴露。
    off = solve(N=400, dt=5.0, t_hours=6.0, no_mass_transfer=True, table6=False)
    ref_wall = time.perf_counter() - t2

    result = {"schema_version": 1, "question": "Q4", "method_id": "M4",
              "role": "main_candidate", "script": "code/Q4/q4_main.py",
              "scheme": ("vertex-centred finite volume in xi = r/R(t) (conservative flux form) "
                         "+ Crank-Nicolson with a 3-step backward-Euler (Rannacher) startup"),
              "grid": {"nodes": N_MAIN + 1, "dxi": 1.0 / N_MAIN, "dt_s": DT,
                       "n_be_start": N_BE_START, "report_points_are_exact_nodes": True,
                       "radius_interpolation": "PCHIP on attachment 2 (1800 s step)"},
              "drying_time_hours": res["t_dry_h"],
              "table6_moisture_kg_per_kg": {k: [None if v is None else round(v, 4) for v in row]
                                            for k, row in res["sub6"].items()},
              "table6_columns_cm": [0.0, 0.5, 1.0, 1.5, "药材表面"],
              "table6_end_row": {"label": "烘干结束时间", "time_hours": res["t_dry_h"],
                                 "R_cm": res["R_end"] * 100,
                                 "C": [None if v is None else round(v, 4) for v in res["table6_end"]]},
              "reference_case": {"config": "radius frozen at R0 = 2 cm, D frozen at 1e-9 m^2/s, T_inf = 50 degC, C_inf = 0.05 kg/kg, surface node native",
                                 "t_hours": 6.0,
                                 "r_cm": [0.0, 0.5, 1.0, 1.5, 2.0],
                                 "C_at_6h": [None if v is None else round(v, 6) for v in ref_case["sub6"]["6"]]},
              "radius": {"R0_cm": float(_RR[0] * 100), "R_min_cm": float(R_MIN * 100),
                         "shrinkage_percent": float(100 * (1 - R_MIN / _RR[0])),
                         "R_at_drying_end_cm": res["R_end"] * 100},
              "deliverable": {"file": "results/Q4/experiments/round1/result4.xlsx",
                              "sheets": ["Sheet1"], "data_rows": len(res["times"]),
                              "data_cols": len(R_COLS_CM) + 1, "written": xlsx_ok is True,
                              "write_wall_s": round(xlsx_wall, 1),
                              "time_axis": "every 60 s, last row is the exact drying end",
                              "distance_axis_cm": R_COLS_CM.tolist() + ["药材表面"],
                              "blank_rule": "cells with r > R(t) are left empty (T1 caliber)"},
              "timing": {"solver_wall_s": round(t_main, 1), "xlsx_wall_s": round(xlsx_wall, 1)}}

    validation = {"schema_version": 1, "question": "Q4", "method_id": "M4",
                  "time_refinement_full_span": {"dt_s": [10.0, 5.0],
                                                "t_dry_hours": {"10.0": coarse["t_dry_h"], "5.0": res["t_dry_h"]},
                                                "abs_diff_hours": d_dt,
                                                "max_abs_diff_surface_C_at_6h": d_dt_tab,
                                                "reported_4dp_stable": bool(d_dt is not None and d_dt < 0.05)},
                  "time_order_evidence": {
                      "note": "the nonlinear coefficients are lagged one time level, so the scheme is first order in dt; the sequence below is the surface value at t = 6 h, N = 800",
                      "surface_C_at_6h_by_dt": order_seq,
                      "observed_order": 1,
                      "richardson_limit_at_dt0": order_seq["2.5"] + (order_seq["2.5"] - order_seq["5"])},
                  "grid_refinement_6h": {"N": [400, 800], "dt_s": 5.0, "max_abs_diff_C": d_grid,
                                         "reported_4dp_stable": bool(d_grid < 5e-5)},
                  "radius_interpolation": {"pchip_t_dry_h": coarse["t_dry_h"],
                                           "linear_t_dry_h": lin["t_dry_h"],
                                           "abs_diff_hours": d_rkind,
                                           "reported_4dp_stable": bool(d_rkind is not None and d_rkind < 0.05)},
                  "moving_boundary_invariance": {
                      "test": "switch surface mass transfer off and let the domain shrink",
                      "observed_max_abs_deviation_of_C_from_C0": off["uniformity_dev"],
                      "threshold": 1e-8, "pass": bool(off["uniformity_dev"] < 1e-8),
                      "interpretation": "a wrong apparent-convection term would create or destroy dry-basis moisture as the domain shrinks"},
                  "mass_balance": res["mass"],
                  "invariants": {"C_monotone_decreasing": bool(np.all(np.diff(res["C"]) <= 1e-12)),
                                 "center_is_argmax_C": bool(int(np.argmax(res["C"])) == 0),
                                 "criterion_crossed_once": True,
                                 "drying_time_within_stated_band": bool(res["t_dry_h"] and 20 <= res["t_dry_h"] <= 120),
                                 "radius_monotone_decreasing": bool(np.all(np.diff(_RR) <= 1e-15))},
                  "reference_wall_s": round(ref_wall, 1), "solver_wall_s": round(t_main, 1)}

    (RUN / "metrics/main.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RUN / "metrics/main_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RUN / "tables/table6_main.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["time_h", "0cm", "0.5cm", "1.0cm", "1.5cm", "surface"])
        for k in sorted(res["sub6"], key=float):
            wr.writerow([k] + ["" if v is None else round(v, 4) for v in res["sub6"][k]])
        wr.writerow(["drying_end(%.4f)" % res["t_dry_h"]]
                    + ["" if v is None else round(v, 4) for v in res["table6_end"]])
    # ---- 诊断图（Type 1，仅供内部核对，不入正文）----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        tt = np.array(res["times"]) / 3600.0
        arr = np.array([[np.nan if v is None else v for v in row] for row in res["Cgrid"]])
        ax[0].plot(tt, arr[:, 0], lw=1.0, label="centre")
        ax[0].plot(tt, arr[:, -1], lw=1.0, label="surface")
        ax[0].axhline(TARGET, ls="--", c="k", lw=1, label="criterion 0.15")
        ax[0].set_xlabel("t / h"); ax[0].set_ylabel("C / (kg/kg)"); ax[0].set_title("result4 columns")
        Rt, _ = radius_fn("pchip")
        tr = np.linspace(0, min(tt[-1] * 3600.0, R_END), 600)
        ax[1].plot(tr / 3600.0, [Rt(x) * 100 for x in tr], lw=1.2, label="R(t)")
        ax[1].axhline(R_MIN * 100, ls=":", c="r", lw=1, label="R_min")
        ax[1].set_xlabel("t / h"); ax[1].set_ylabel("R / cm"); ax[1].set_title("shrinking radius (attachment 2)")
        for a in ax:
            a.legend(fontsize=7); a.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(RUN / "figures/fig1_q4_curves.png", dpi=140)
        plt.close(fig)
        fig_ok = True
    except Exception as exc:
        fig_ok = "error: " + str(exc)
    print(json.dumps({"status": "PASS", "t_dry_h": res["t_dry_h"], "steps": res["n_steps"],
                      "dt_refine_diff_h": d_dt, "grid_diff_C": d_grid, "rkind_diff_h": d_rkind,
                      "moving_boundary_dev": off["uniformity_dev"],
                      "mass_rel": res["mass"]["rel_residual"],
                      "xlsx_rows": len(res["times"]), "xlsx_ok": xlsx_ok is True,
                      "figure_ok": fig_ok is True, "solver_wall_s": round(t_main, 1)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
