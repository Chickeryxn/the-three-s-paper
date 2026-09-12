# -*- coding: utf-8 -*-
"""Emit the required result tables as LaTeX fragments straight from the metrics.

No table value is typed by hand: every cell is read from the round metric file that
the run snapshot pins.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/tables"


def J(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def cell(v):
    return "--" if v is None else ("%.4f" % float(v))


def wide(label, cols, rows, caption, note, lab):
    L = ["\\begin{table}[H]", "  \\centering", "  \\caption{%s}" % caption,
         "  \\label{%s}" % lab, "  \\small",
         "  \\begin{tabular}{l" + "c" * len(cols) + "}", "    \\toprule",
         "    " + " & ".join([label] + cols) + " \\\\", "    \\midrule"]
    for r in rows:
        L.append("    " + " & ".join(r) + " \\\\")
    L += ["    \\bottomrule", "  \\end{tabular}"]
    if note:
        L.append("  \\par\\smallskip\\footnotesize " + note)
    L.append("\\end{table}")
    return chr(10).join(L) + chr(10)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    written = []

    # ---- Q1: table 1 (temperature) and table 2 (moisture) ----
    d1 = J("results/Q1/experiments/round1/metrics/main.json")
    cols = ["$r=0$", "$0.5$~cm", "$1.0$~cm", "$1.5$~cm", "$2.0$~cm"]
    for key, name, cap in (("table1_temperature_C", "table1_q1_temperature",
                            "预热平衡阶段的温度分布（$^\\circ$C）"),
                           ("table2_moisture_kg_per_kg", "table2_q1_moisture",
                            "预热平衡阶段的干基水分浓度（kg/kg）")):
        t = d1[key]
        rows = [[str(int(float(k))) ] + [cell(v) for v in t[k]] for k in sorted(t, key=float)]
        (OUT / (name + ".tex")).write_text(
            wide("时间/s", cols, rows, cap, "", "tab:" + name), encoding="utf-8")
        written.append(name)

    # ---- Q2: table 3 (temperature) and table 4 (moisture) ----
    d2 = J("results/Q2/experiments/round1/metrics/main.json")
    for key, name, cap in (("table3_temperature_C", "table3_q2_temperature",
                            "$3$~h 内的温度分布（$^\\circ$C）"),
                           ("table4_moisture_kg_per_kg", "table4_q2_moisture",
                            "$3$~h 内的干基水分浓度（kg/kg）")):
        t = d2[key]
        rows = [["%.1f" % float(k)] + [cell(v) for v in t[k]] for k in sorted(t, key=float)]
        (OUT / (name + ".tex")).write_text(
            wide("时间/h", cols, rows, cap, "", "tab:" + name), encoding="utf-8")
        written.append(name)

    # ---- Q3: table 5 ----
    d3 = J("results/Q3/experiments/round1/metrics/main.json")
    cols3 = ["$r=0$", "$0.5$~cm", "$1.0$~cm", "$1.5$~cm", "$2.0$~cm（表面）"]
    t5 = d3["table5_moisture_kg_per_kg"]
    rows = [[k] + [cell(v) for v in t5[k]] for k in sorted(t5, key=float)]
    # 与表 6（问题四）保持一致：末行不写“烘干结束时间”，在时间列直接给出确切烘干时长并整行加粗
    rows.append([r"\textbf{%.4f}" % float(d3["drying_time_hours"])]
                + [r"\textbf{%s}" % cell(v) for v in d3["table5_end_row"]["C"]])
    (OUT / "table5_q3.tex").write_text(
        wide("时间/h", cols3, rows, "烘干过程中每隔 $6$~h 的干基水分浓度（kg/kg）", "", "tab:table5_q3"),
        encoding="utf-8")
    written.append("table5_q3")

    # ---- Q4: table 6 ----
    d4 = J("results/Q4/experiments/round1/metrics/main.json")
    cols4 = ["$r=0$", "$0.5$~cm", "$1.0$~cm", "$1.5$~cm", "药材表面"]
    t6 = d4["table6_moisture_kg_per_kg"]
    rows = [[k] + [cell(v) for v in t6[k]] for k in sorted(t6, key=float)]
    # 末行不再写“烘干结束时间”这类文字，而是在时间列直接给出确切烘干时长，并整行加粗，
    # 读者可以据此直接读表取值；数值仍取自 metrics，不手写。
    rows.append([r"\textbf{%.4f}" % float(d4["drying_time_hours"])]
                + [r"\textbf{%s}" % cell(v) for v in d4["table6_end_row"]["C"]])
    (OUT / "table6_q4.tex").write_text(
        wide("时间/h", cols4, rows,
             "考虑尺寸变化时烘干过程的干基水分浓度（kg/kg）",
             "“--”表示该时刻 $r>R(t)$，该位置在药材之外。", "tab:table6_q4"),
        encoding="utf-8")
    written.append("table6_q4")

    for n in written:
        print("wrote paper/tables/%s.tex" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
