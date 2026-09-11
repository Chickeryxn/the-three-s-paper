# -*- coding: utf-8 -*-
"""Stage the paper repository (github.com/Chickeryxn/the-three-s-paper).

Collects the paper sources AND the tools that generate them, so a collaborator
can clone, edit, rebuild and regenerate every number and figure.

The target repository is PUBLIC, so the raw contest material is deliberately
left out: workspace/problem.txt and workspace/data_raw/ (the original
attachments). Everything derived from them that the pipeline actually reads
(workspace/data_clean/) is included, so the code still runs.

Run: python code/stage_paper_repo.py <target-dir>
"""
from __future__ import annotations

import shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIRS = ["paper", "code", "results", "robustness", "planning", "methods"]
FILES = ["scripts/latex_assembly.py"]
DATA_IN = ["workspace/data_clean"]

SKIP_SUFFIX = (".svg", ".pyc", ".aux", ".log", ".out", ".toc", ".synctex.gz",
               ".fls", ".fdb_latexmk", ".xlsx", ".gitkeep")
SKIP_PARTS = {"__pycache__", ".ipynb_checkpoints", "runs"}


def keep(rel: Path) -> bool:
    if any(p in SKIP_PARTS for p in rel.parts):
        return False                    # per-run console logs, no reproduction value
    return not rel.name.endswith(SKIP_SUFFIX)


def copy_tree(src_root: Path, dst_root: Path, rels):
    n = 0
    for rel in rels:
        src = ROOT / rel
        if not src.is_file():
            continue
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1]).resolve()

    rels = []
    for d in DIRS + DATA_IN:
        base = ROOT / d
        if not base.is_dir():
            print("warn: missing", d)
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file():
                rel = p.relative_to(ROOT)
                if keep(rel):
                    rels.append(rel)
    rels += [Path(f) for f in FILES]

    n = copy_tree(ROOT, out, rels)
    for name in ("README.md", ".gitignore", ".gitattributes", "编译说明.md"):
        src = ROOT / "code/paper_repo_templates" / name
        shutil.copy2(src, out / name)
        n += 1
    print("staged %d files into %s" % (n, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
