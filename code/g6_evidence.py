# -*- coding: utf-8 -*-
"""Collect the mechanical evidence for the G6 audit layer."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QS = ("Q1", "Q2", "Q3", "Q4")


def _json(text):
    dec = json.JSONDecoder()
    i = text.find("{")
    if i < 0:
        return {}
    return dec.raw_decode(text[i:])[0]


def run(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True,
                       encoding="utf-8", cwd=ROOT)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def J(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def exists(rel):
    return (ROOT / rel).is_file()


def _macro_number(body):
    """Recover the numeric value printed by a frozen-number macro.

    scripts/latex_assembly.py emits either a plain literal or, for very small or
    very large magnitudes, a scientific form. The unit travels inside the macro
    body after a thin space ("2.55\\,kg/kg"), so the LEADING number is parsed and
    any unit suffix is ignored. Returns None when the body is absent or not numeric.
    """
    if body is None:
        return None
    s = body.replace("$", "")
    # the printed form is $6.18\times10^{-7}$, i.e. the exponent is a superscript
    m = re.match(r"\s*(-?[0-9.]+)\\times10\^\{(-?[0-9]+)\}", s)
    if m:
        return float(m.group(1)) * 10.0 ** int(m.group(2))
    m = re.match(r"\s*(-?[0-9.]+)", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


NEED = {
    "final_method_explanation": "methods/{q}/{ql}_final_method_explanation.md",
    "python_review": "code/{q}/reviews/{ql}_python_review.json",
    "final_result_analysis": "results/{q}/reports/{ql}_final_result_analysis.md",
    "robustness_report": "robustness/{q}/{ql}_robustness_report.md",
    "solution_package": "results/{q}/reports/{ql}_solution_package_for_writer.md",
    "frozen_numbers": "results/{q}/reports/frozen_numbers.json",
    "paper_section": "paper/sections/05_model_and_solution.tex",
}
GLOBAL = {
    "symbol_table": "planning/symbol_table.md",
    "assumptions": "planning/assumptions.json",
    "references": "paper/refs.bib",
    "consistency_audit": "paper/audits/cross_media_consistency_audit.md",
    "completeness_audit": "paper/audits/completeness_audit.md",
    "ai_use_disclosure": "paper/ai_use_disclosure.md",
    "paper_pdf": "paper/main.pdf",
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    (ROOT / "paper/audits").mkdir(parents=True, exist_ok=True)
    (ROOT / "scratch").mkdir(exist_ok=True)
    ev = {}
    rc, out = run("scripts/latex_assembly.py", ".", "--check-only",
                  "--template", "paper/main_template.tex", "--strict")
    ev["assembly_returncode"] = rc
    ev["assembly"] = _json(out)
    ev["figure_audit"] = _json(run("scripts/figure_render_audit.py", ".")[1])
    ev["freshness"] = _json(run("scripts/check_frozen_freshness.py", ".")[1])
    ev["lineage"] = {q: _json(run("scripts/validate_artifacts.py", ".",
                                  "planning/manifests/%s.json" % q)[1]) for q in QS}
    ev["decisions"] = {q: ("PASS" if run("scripts/validate_decisions.py", ".",
                                        "methods/%s/%s_decisions.jsonl" % (q, q.lower()))[0] == 0
                           else "FAIL") for q in QS}
    mt = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    # \newcommand{\name}{...} with BALANCED braces: a body such as
    # $6.18\times10^{-7}$ contains '}', which a [^}]* pattern truncates.
    macros = {}
    for m in re.finditer(r"newcommand\{\\([A-Za-z]+)\}", mt):
        i = m.end()
        if i >= len(mt) or mt[i] != "{":
            continue
        depth, j = 0, i
        while j < len(mt):
            if mt[j] == "{":
                depth += 1
            elif mt[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        macros[m.group(1)] = mt[i + 1:j]
    sys.path.insert(0, str(ROOT / "scripts"))
    import latex_assembly as la
    frozen = {}
    for q in QS:
        for c in J("results/%s/reports/frozen_numbers.json" % q)["claims"]:
            frozen[c["claim_id"]] = c
    ev["macro_mismatches"] = []
    for cid, c in frozen.items():
        name = la.sanitize_macro_name(cid)
        body = macros.get(name)
        want = c["value"]
        if isinstance(want, bool) or not isinstance(want, (int, float)):
            # non-numeric claim: fall back to a literal prefix match
            if body is None or not body.startswith(str(want)):
                ev["macro_mismatches"].append({"claim_id": cid, "macro": name,
                                               "expected": str(want), "found": body})
            continue
        got = _macro_number(body)
        if got is None or abs(got - float(want)) > max(1e-12, 1e-9 * abs(float(want))):
            ev["macro_mismatches"].append({"claim_id": cid, "macro": name,
                                           "expected": want, "found": body,
                                           "parsed": got})
    missing = []
    texts = [p.read_text(encoding="utf-8") for p in sorted((ROOT / "paper/sections").glob("*.tex"))]
    texts.append(mt)
    for s in texts:
        for m in re.finditer(r"input\{([^}]+)\}", s):
            if not exists(m.group(1)):
                missing.append(m.group(1))
        for m in re.finditer(r"includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", s):
            if not exists("paper/figures/" + m.group(1)):
                missing.append("paper/figures/" + m.group(1))
    ev["missing_referenced_files"] = missing
    log = ROOT / "paper/main.log"
    if log.is_file():
        txt = log.read_text(encoding="utf-8", errors="replace")
        ev["latex_errors"] = len(re.findall(r"^! ", txt, re.M))
        ev["latex_overfull"] = len(re.findall(r"Overfull .hbox", txt))
        mp = re.search(r"Output written on .*\((\d+) pages\)", txt)
        ev["latex_pages"] = int(mp.group(1)) if mp else None
    ev["pdf_bytes"] = (ROOT / "paper/main.pdf").stat().st_size if exists("paper/main.pdf") else 0
    ev["completeness"] = {q: {k: ("PRESENT" if exists(v.format(q=q, ql=q.lower())) else "MISSING")
                              for k, v in NEED.items()} for q in QS}
    ev["global"] = {k: ("PRESENT" if exists(v) else "MISSING") for k, v in GLOBAL.items()}
    (ROOT / "scratch/g6_evidence.json").write_text(
        json.dumps(ev, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    print(json.dumps({k: ev[k] for k in ("assembly_returncode", "macro_mismatches",
                                         "missing_referenced_files", "latex_errors",
                                         "latex_overfull", "latex_pages", "decisions")},
                     ensure_ascii=False))
    print("figures:", ev["figure_audit"].get("status"), "| freshness:", ev["freshness"].get("status"))
    print("completeness:", json.dumps(ev["completeness"], ensure_ascii=False))
    print("global:", json.dumps(ev["global"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
