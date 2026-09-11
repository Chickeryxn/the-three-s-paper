# -*- coding: utf-8 -*-
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "code/Q1")
import numpy as np
from q1_common import R, T0, C0, RHO, CP, K, H, HM, R_REPORT, D_q1, Tinf, Cinf, thomas, report_profile

def run(N=400, dt=0.125, scheme="BE", t_end=1800.0):
    dr = R/N; rf = np.arange(N+1)*dr
    Af = 2*np.pi*rf; V = np.pi*(rf[1:]**2 - rf[:-1]**2)
    rc = (rf[1:]+rf[:-1])/2
    T = np.full(N, T0); C = np.full(N, C0)
    steps = int(round(t_end/dt)); th = 1.0 if scheme == "BE" else 0.5
    snaps = {}; every = max(1, int(round(1.0/dt)))
    Gh = Af[N]/(dr/(2*K) + 1/H)
    # heat tridiagonal (constant)
    aH = np.zeros(N); bH = np.zeros(N); cH = np.zeros(N)
    for i in range(N):
        ait = RHO*CP*V[i]/dt
        if i == 0:
            co = Af[1]*K/dr; bH[i] = ait + th*co; cH[i] = -th*co
        elif i == N-1:
            ci = Af[N-1]*K/dr; bH[i] = ait + th*(ci+Gh); aH[i] = -th*ci
        else:
            ci = Af[i]*K/dr; co = Af[i+1]*K/dr
            bH[i] = ait + th*(ci+co); aH[i] = -th*ci; cH[i] = -th*co
    for s in range(1, steps+1):
        t = s*dt; tm = (s-1)*dt
        tq = t if scheme == "BE" else (t+tm)/2
        ait_h = RHO*CP*V/dt
        # explicit part of heat
        dH = ait_h*T
        for i in range(N):
            if i == 0:
                co = Af[1]*K/dr; dH[i] += (1-th)*co*(T[1]-T[0])
            elif i == N-1:
                ci = Af[N-1]*K/dr; dH[i] += (1-th)*(ci*(T[i-1]-T[i]) + Gh*(Tinf(tm)-T[i]))
            else:
                ci = Af[i]*K/dr; co = Af[i+1]*K/dr
                dH[i] += (1-th)*(ci*(T[i-1]-T[i]) + co*(T[i+1]-T[i]))
        dH[N-1] += th*Gh*Tinf(tq)
        T = thomas(aH, bH, cH, dH)
        # mass with lagged D
        Dv = D_q1(C); Df = 0.5*(Dv[:-1]+Dv[1:])
        G = Af[N]/(dr/(2*Dv[N-1]) + 1/HM)
        ait = V/dt
        aM = np.zeros(N); bM = np.zeros(N); cM = np.zeros(N); dM = np.zeros(N)
        for i in range(N):
            if i == 0:
                co = Af[1]*Df[0]/dr
                bM[i] = ait[i] + th*co; cM[i] = -th*co
                dM[i] = ait[i]*C[i] + (1-th)*co*(C[1]-C[0])
            elif i == N-1:
                ci = Af[N-1]*Df[-1]/dr
                bM[i] = ait[i] + th*(ci+G); aM[i] = -th*ci
                dM[i] = ait[i]*C[i] + (1-th)*(ci*(C[i-1]-C[i]) + G*(Cinf(tm)-C[i])) + th*G*Cinf(tq)
            else:
                ci = Af[i]*Df[i-1]/dr; co = Af[i+1]*Df[i]/dr
                bM[i] = ait[i] + th*(ci+co); aM[i] = -th*ci; cM[i] = -th*co
                dM[i] = ait[i]*C[i] + (1-th)*(ci*(C[i-1]-C[i]) + co*(C[i+1]-C[i]))
        C = thomas(aM, bM, cM, dM)
        if s % every == 0:
            Dl = float(D_q1(np.array([C[-1]]))[0])
            Cs = (C[-1]*(2*Dl/dr) + HM*Cinf(t))/(2*Dl/dr + HM)
            Ts = (T[-1]*(2*K/dr) + H*Tinf(t))/(2*K/dr + H)
            snaps[int(round(t))] = (T.copy(), C.copy(), float(Ts), float(Cs))
    return rc, snaps

dr = R/400; Dv0 = float(D_q1(np.array([C0]))[0])
rf = np.arange(401)*dr; Af = 2*np.pi*rf; V = np.pi*(rf[1:]**2 - rf[:-1]**2)
ci = Af[399]*Dv0/dr; G = Af[400]/(dr/(2*Dv0)+1/HM)
tau = V[399]/(ci+G)
print("表面单元时间常数 tau = %.3f s ; dt=0.5 时 lambda*dt = %.2f" % (tau, 0.5/tau))
print()
res = {}
for dt in (0.5, 0.25, 0.125):
    t0 = time.perf_counter(); rc, sn = run(N=400, dt=dt, scheme="BE"); el = time.perf_counter()-t0
    res[dt] = {t: report_profile(rc, sn[t][1], sn[t][3], R_REPORT) for t in (100, 600, 1800)}
    print("BE dt=%.3f  %.0fs" % (dt, el))
for a, b in ((0.5, 0.25), (0.25, 0.125)):
    for t in (100, 600, 1800):
        d = np.abs(res[a][t]-res[b][t])
        print("  BE %.3f->%.3f t=%4d max=%.2e  %s" % (a, b, t, d.max(), np.array2string(d, precision=2, floatmode="maxprec")))
print()
rescn = {}
for dt in (1.0, 0.5, 0.25):
    t0 = time.perf_counter(); rc, sn = run(N=400, dt=dt, scheme="CN"); el = time.perf_counter()-t0
    rescn[dt] = {t: report_profile(rc, sn[t][1], sn[t][3], R_REPORT) for t in (100, 600, 1800)}
    print("CN dt=%.3f  %.0fs" % (dt, el))
for a, b in ((1.0, 0.5), (0.5, 0.25)):
    for t in (100, 600, 1800):
        d = np.abs(rescn[a][t]-rescn[b][t])
        print("  CN %.3f->%.3f t=%4d max=%.2e  %s" % (a, b, t, d.max(), np.array2string(d, precision=2, floatmode="maxprec")))
print()
print("BE(0.125) vs CN(0.25):")
for t in (100, 600, 1800):
    d = np.abs(res[0.125][t]-rescn[0.25][t])
    print("  t=%4d max=%.2e  %s" % (t, d.max(), np.array2string(d, precision=2, floatmode="maxprec")))
