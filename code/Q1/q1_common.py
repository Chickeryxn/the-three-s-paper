# -*- coding: utf-8 -*-
"""问题一公共模块：物理常数、附件读取、报告点映射与解析级数参照。

本模块只放与空间离散格式无关的公共工具。主方法（顶点有限体积）、
可用基线（格心有限体积）与独立验证（解析级数）因此保持为三套互不相同的
数值实现——任何一方的离散细节都不写在这里。

论文对应：5.1 节（控制方程与参数取值）、5.4 节（验证设计）。
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np
from scipy.special import j0, j1
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

# ---------------------------------------------------------------------------
# 一、几何、初值与物性常数（论文表 7）
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]      # 仓库根：本文件位于 code/Q1/

R = 0.02          # 药材半径，m
T0 = 28.0         # 初始温度，degC
C0 = 2.55         # 初始干基含水率，kg/kg
RHO, CP, K = 820.0, 2600.0, 0.36    # 密度 kg/m^3、比热 J/(kg*K)、导热系数 W/(m*K)
H, HM = 25.0, 8e-7                  # 表面对流换热系数 W/(m^2*K)、表面对流传质系数 m/s

# ---------------------------------------------------------------------------
# 二、输出目录与报告点：题目要求 7 个时刻 x 5 个径向位置
# ---------------------------------------------------------------------------
ROUND_DIR = ROOT / "results/Q1/experiments/round1"
R_REPORT = np.array([0.0, 0.005, 0.010, 0.015, 0.020])      # m，即 0/0.5/1/1.5/2 cm
T_REPORT = [100, 300, 600, 900, 1200, 1500, 1800]          # s
R_GRID = np.round(np.arange(21) * 0.1, 10)                 # cm，result1.xlsx 的列坐标

def D_q1(C):
    """问题一的水分扩散系数经验式，单位 m^2/s。

    用 maximum 做下限兜底：C -> 0 时指数会溢出，而实际浓度不会为零。
    """
    return 7e-9 * np.exp(-0.89 / np.maximum(C, 1e-9))

# ---------------------------------------------------------------------------
# 三、附件 1 的环境序列：热风温度与含湿量按时间线性插值
# ---------------------------------------------------------------------------
def load_env():
    """读取清洗后的附件 1，返回 (时间 s, 环境温度 degC, 环境含湿量 kg/kg)。"""
    with (ROOT / "workspace/data_clean/attachment1_env.csv").open(encoding="utf-8") as fh:
        rows = list(csv.reader(fh))[1:]
    a = np.array([[float(x) for x in r] for r in rows])
    return a[:, 0], a[:, 1], a[:, 2]

TE, TINF, CINF = load_env()
Tinf = lambda t: float(np.interp(t, TE, TINF))   # 热风温度 T_inf(t)
Cinf = lambda t: float(np.interp(t, TE, CINF))   # 热风含湿量 C_inf(t)

# ---------------------------------------------------------------------------
# 四、通用数值工具
# ---------------------------------------------------------------------------
def thomas(a, b, c, d):
    """追赶法（Thomas 算法）解三对角方程组，供基线 B1 的 Crank--Nicolson 使用。

    形参依次为次对角、主对角、超对角与右端项。这里自建实现而不直接调用库函数，
    是为了让基线在“线性求解器”这一层也保持独立。
    """
    n = len(b); cp = np.zeros(n); dp = np.zeros(n)
    cp[0] = c[0] / b[0]; dp[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = np.zeros(n); x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x

def report_profile(rc, vals, surface, targets):
    """把格心解插值到报告点，供基线 B1 复用。

    格心格式的未知量位于 r = dr/2, 3dr/2, ...，而 r = R 是边界不是格心，
    故在插值节点末尾补上边界值本身，再用三次样条求报告点处的值。
    """
    xs = np.concatenate([rc, [R]]); ys = np.concatenate([vals, [surface]])
    cs = CubicSpline(xs, ys)
    return np.array([float(cs(x)) for x in targets])

# ---------------------------------------------------------------------------
# 五、解析级数参照：圆柱一维、均匀初值、第三类（对流）边界
# ---------------------------------------------------------------------------
def bessel_roots(Bi, nmax=200):
    """求特征方程 lambda*J1(lambda) - Bi*J0(lambda) = 0 的正根。

    先以固定步长扫描变号区间，再用 Brent 法精确求根。
    扫描上界取到 1200，保证 nmax 个根全部落在扫描范围内，不会漏根或重复计数。
    """
    f = lambda lam: lam * j1(lam) - Bi * j0(lam)
    roots = []; lam = 1e-8; step = 0.005; prev = f(lam); lam += step
    while len(roots) < nmax and lam < 1200:
        cur = f(lam)
        if prev * cur < 0:
            roots.append(brentq(f, lam - step, lam))
        prev = cur; lam += step
    return np.array(roots)

def bessel_C(r, t, D, hm, Cinit=C0, Cinfv=0.05, nmax=200):
    """圆柱试样在均匀初值与表面对流传质下的含水率解析解（量纲一过余浓度级数）。

    该解仅当“扩散系数取常数、环境量恒定”时成立，因此只用于参考算例的验证，
    不参与实际工况求解；实际工况下 D 随含水率与温度变化，只能数值求解。
    """
    Bi = hm * R / D
    lam = bessel_roots(Bi, nmax)
    rho = np.atleast_1d(np.asarray(r, float)) / R
    Fo = D * t / R ** 2
    s = np.zeros_like(rho)
    for L in lam:
        s += 2 * Bi / ((L * L + Bi * Bi) * j0(L)) * j0(L * rho) * math.exp(-L * L * Fo)
    return Cinfv + (Cinit - Cinfv) * s

def write_json(path, data):
    """写 UTF-8 JSON，自动创建父目录，并关闭中文转义以便人工核对。"""
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def round4(x):
    """统一截断到 4 位小数，与题目要求的结果有效位数一致。"""
    return float(f"{float(x):.4f}")
