# -*- coding: utf-8 -*-
"""Build the submission-level robustness reports (robustness/Qx/qx_robustness_report.md)
from the lean summary JSONs. Every number is read from its source; nothing is typed by hand."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def val(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def fmt(v):
    if isinstance(v, float):
        return "%.4g" % v
    return str(v)


def build(q):
    ql = q.lower()
    s = J("robustness/%s/%s_robustness_summary.json" % (q, ql))
    pkg = J("results/%s/reports/frozen_numbers.json" % q)
    claims = {c["claim_id"]: (c["value"], c["unit"], c["source_file"], c["source_locator"])
              for c in pkg["claims"]}
    L = []
    A = L.append
    A("# %s 稳健性报告（submission 口径）" % q)
    A("")
    A("> 由 `robustness/%s/%s_robustness_summary.json` 生成；该 summary 即 lean 口径的稳健性证据。" % (q, ql))
    A("> 生成脚本：`code/robustness_report.py`。所有数值均从源文件读取，未手写。")
    A("")
    A("## 1. 范围与口径")
    A("")
    A("- 提供者角色：`robustness-checker`；消费方：G4 稳定性判定、论文的局限段。")
    A("- 检验目标：本题的承重假设与已确认口径，而非通用清单。")
    A("- 判读口径：**单项扰动下的可观测后果**，不是统计显著性检验。")
    A("")
    A("## 2. 基准状态")
    A("")
    b = s.get("baseline", {})
    if b:
        A("| 项 | 值 |")
        A("|---|---|")
        for k, v in b.items():
            A("| %s | %s |" % (k, fmt(v)))
        A("")
    A("## 3. 逐项检验")
    A("")
    A("| 检验 | 判定 | 观测量 |")
    A("|---|---|---|")
    for name, chk in s["checks"].items():
        subs = [(k, v) for k, v in chk.items() if isinstance(v, dict) and "observed" in v] if isinstance(chk, dict) else []
        if subs:
            for sub, d in subs:
                A("| `%s/%s` | %s | %s |" % (name, sub, d.get("status"), fmt(d.get("observed"))[:160]))
        else:
            A("| `%s` | %s | %s |" % (name, chk.get("status"), fmt(chk.get("observed"))[:160]))
    A("")
    A("整体状态：**%s**；总耗时 %s s。" % (s.get("overall_status"), fmt(s.get("elapsed_s"))))
    A("")
    A("## 4. 与冻结声明的对应")
    A("")
    A("本报告支撑的论文数值声明（来源 `results/%s/reports/frozen_numbers.json`）：" % q)
    A("")
    A("| claim_id | 值 | 单位 | 源 |")
    A("|---|---|---|---|")
    for cid, (v, u, f, loc) in claims.items():
        A("| `%s` | %s | %s | `%s`%s |" % (cid, fmt(v), u, f, loc))
    A("")
    A("## 5. 局限")
    A("")
    for x in s.get("limitations", []):
        A("- %s" % x)
    A("")
    A("## 6. 回退触发状态")
    A("")
    ft = s.get("fallback_trigger_relevance", {})
    A("- fallback_id：`%s`" % ft.get("fallback_id"))
    A("- 触发条件：%s" % ft.get("trigger"))
    A("- 本轮是否观测到：**%s**" % ft.get("observed"))
    A("- 证据：`%s`" % ft.get("evidence"))
    A("")
    out = ROOT / ("robustness/%s/%s_robustness_report.md" % (q, ql))
    out.write_text(chr(10).join(L) + chr(10), encoding="utf-8")
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for q in ("Q1", "Q2", "Q3", "Q4"):
        p = build(q)
        print("wrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
