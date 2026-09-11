# -*- coding: utf-8 -*-
"""Assemble a self-contained, transmittable package of the paper.

Keeps the repository-relative layout (paper/ + code/) because paper/main.tex
inputs paper/sections/** and paper/tables/** and lstinputlisting-s code/Q*/**:
moving those files would break the compile.

Excluded on purpose:
  paper/figures/*.svg      40 MB of SVG; LaTeX uses the PDF versions
  workspace/code/**        one-off migration scripts, not part of the method
  **/__pycache__           build artefacts

Run: python code/make_paper_package.py
"""
from __future__ import annotations

import shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
NAME = "2026国赛A题_药材烘干_论文包"
HEAVY = "results/Q2/experiments/round1/result2.xlsx"     # 27.5 MB deliverable

INCLUDE_DIRS = ["paper", "code", "scripts", "results", "robustness", "planning", "workspace"]
SCRIPTS_KEEP = {"latex_assembly.py"}       # the rest of scripts/ is unrelated to the paper
SKIP_PARTS = {"__pycache__", ".ipynb_checkpoints"}
SKIP_SUFFIX = (".pyc", ".svg", ".gitkeep")


def wanted(rel: Path) -> bool:
    parts = rel.parts
    if parts[0] == "workspace" and len(parts) > 1 and parts[1] == "code":
        return False                        # ad-hoc migration scripts
    if parts[0] == "scripts" and rel.name not in SCRIPTS_KEEP:
        return False
    if any(p in SKIP_PARTS for p in parts[:-1]):
        return False
    return not rel.name.endswith(SKIP_SUFFIX)


def collect():
    files = []
    for d in INCLUDE_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file():
                rel = p.relative_to(ROOT)
                if wanted(rel):
                    files.append(rel)
    return files


def zip_tree(stage: Path, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(stage.parent).as_posix())
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    readme = (ROOT / "code/package_readme.md").read_text(encoding="utf-8")
    build_ps1 = chr(10).join([
        "$ErrorActionPreference = 'Stop'",
        "foreach ($i in 1..2) {",
        "  xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex",
        "}",
        "Write-Output 'done -> paper/main.pdf'", ""])
    build_sh = chr(10).join([
        "#!/bin/sh", "set -e",
        "xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex",
        "xelatex -interaction=nonstopmode -output-directory=paper paper/main.tex",
        "echo 'done -> paper/main.pdf'", ""])

    if DIST.exists():
        shutil.rmtree(DIST)
    files = collect()
    print("collected %d files" % len(files))
    for heavy in (True, False):
        suffix = "" if heavy else "_轻量版"
        stage = DIST / (NAME + suffix)
        for rel in files:
            if not heavy and rel.as_posix() == HEAVY:
                continue
            dst = stage / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
        (stage / "编译说明.md").write_text(
            readme.replace("{HEAVY}", "包含" if heavy else "不含"), encoding="utf-8")
        (stage / "build.ps1").write_text(build_ps1, encoding="utf-8")
        (stage / "build.sh").write_text(build_sh, encoding="utf-8", newline=chr(10))
        out = zip_tree(stage, DIST / (NAME + suffix + ".zip"))
        mb = out.stat().st_size / 1048576
        print("wrote %-52s %.1f MB" % (out.relative_to(ROOT).as_posix(), mb))
        shutil.rmtree(stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
