#!/usr/bin/env python3
"""硬性規則守門：檢查公開 repo 是否滿足 docs/公開repo_排除決策.md 的 R2/R3/R4/R6/R7/R9。

失敗時以非零 exit 結束，Blocking 任何 commit/push（pre-push hook 與 CI 共用）。
唯讀：不修改任何檔案。
"""

from __future__ import annotations
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CRED_RE = re.compile(
    r"(?i)(password|passwd|pwd|secret|api[ _-]?key|token|private[ _-]?key|"
    r"access[ _-]?key|client[ _-]?secret)\s*[:=]\s*\S{4,}"
)
TOKEN_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{20,}|ghp_[A-Za-z0-9]{30,}|gho_[A-Za-z0-9]{30,}|"
    r"github_pat_[A-Za-z0-9_]{30,}|xox[baprs]-[A-Za-z0-9\-]{10,}|"
    r"AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_\-]{30,}|hf_[A-Za-z0-9]{30,})"
)
BINARY_SUFFIX = {
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".exe",
    ".png",
    ".jpg",
    ".pdf",
    ".zip",
    ".gz",
    ".s4p",
}

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def tracked_files() -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT, stderr=subprocess.DEVNULL
        )
        return [x for x in out.decode().split("\0") if x]
    except Exception:
        return []


def main() -> int:
    os.chdir(ROOT)
    tracked = tracked_files()

    # R9: no gitlinks
    try:
        ls = subprocess.check_output(["git", "ls-files", "-s"], cwd=ROOT).decode()
        gitlinks = [l for l in ls.splitlines() if l.startswith("160000")]
    except Exception:
        gitlinks = []
    check("R9 無巢狀 gitlink", not gitlinks, "、".join(gitlinks[:3]))

    # R2: exact 24 secret-file paths from push-repo preflight (worktree+history union)
    SECRET_FILES = {
        "archive/柔線/pages/0全傳輸線材模擬.py",
        "bk2vwr/0snpvwr.py",
        "bk2vwr/0匯入Bytes.py",
        "bk2vwr/0匯入astbk.py",
        "bk2vwr/async_database.py",
        "bk2vwr/async_databaseII.py",
        "bk2vwr/bk2Util.py",
        "bk2vwr/bkUtil.py",
        "bk2vwr/snpUtil.py",
        "bk2vwr/匯入摸石.py",
        "bk2vwr/匯入皮可.py",
        "bk2vwr/取出表.py",
        "src/量傳線設計/核心/LLM輔助.py",
        "三視圖/柔性/pages/08md2簡報.py",
        "三視圖/柔性/tchwiki/ai模型.py",
        "三視圖/柔性/tchwiki/docker-compose.yml",
        "三視圖/柔性/tchwiki/sync_wiki.py",
        "三視圖/柔性/tchwiki/主程式.py",
        "三視圖/柔性/tchwiki/同步向量.py",
        "三視圖/柔性/量量/.streamlit/secrets.toml",
        "三視圖/柔性/量量/auth.py",
        "柔線/pages/0全傳輸線材模擬.py",
        "柔線/五家傳輸線.md",
        "柔線/金傳輸線材參數.md",
    }
    secret_paths = sorted(set(tracked) & SECRET_FILES)
    check(
        "R2 無機密路徑被追蹤（preflight 精確 24 檔）",
        not secret_paths,
        "、".join(secret_paths[:8]),
    )

    cred_hits: list[str] = []
    for f in tracked:
        p = ROOT / f
        if not p.exists() or p.stat().st_size > 2_000_000:
            continue
        if p.suffix in BINARY_SUFFIX:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if CRED_RE.search(line) or TOKEN_RE.search(line):
                cred_hits.append(f"{f}:{i}")
                break
    check("R3 無憑證樣式（CRED_RE/TOKEN_RE）", not cred_hits, "、".join(cred_hits[:8]))

    # R4: remote URLs must not contain token-like strings / embedded credentials
    bad_remote = []
    try:
        remotes = subprocess.check_output(["git", "remote", "-v"], cwd=ROOT).decode()
        for line in remotes.splitlines():
            if re.search(r"https?://[^/@\s]+@|ghp_[A-Za-z0-9]{20,}|github_pat_", line):
                bad_remote.append(line.strip())
    except Exception:
        pass
    check("R4 remote 無內嵌憑證", not bad_remote, "、".join(bad_remote[:3]))

    # R6/R7: excluded ledger columns + reconciliation (tracked ∪ covered = disk)
    excl = ROOT / "_repo_excluded.tsv"
    covered_rows: list[tuple[str, str, str]] = []
    if excl.exists():
        lines = excl.read_text(encoding="utf-8").splitlines()
        for line in lines[1:]:
            if not line.strip():
                continue
            cells = line.split("\t")
            cells += [""] * (4 - len(cells))
            path, size, reason, backup = cells[:4]
            covered_rows.append((path, reason, backup))
    vague = {
        "",
        "無",
        "沒有",
        "未知",
        "不知道",
        "n/a",
        "na",
        "none",
        "null",
        "?",
        "-",
        "tbd",
        "待確認",
        "x",
    }
    incomplete = [
        p
        for p, r, b in covered_rows
        if r.strip().lower() in vague or b.strip().lower() in vague
    ]
    check("R6 排除清單每列有 reason+backup", not incomplete, "、".join(incomplete[:5]))

    def covered(rel: str) -> bool:
        for p, _, _ in covered_rows:
            if p.endswith("/") and rel.startswith(p.rstrip("/") + "/"):
                return True
            if any(c in p for c in "*?[") and (
                fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(os.path.basename(rel), p)
            ):
                return True
            if rel == p:
                return True
        return False

    disk: list[str] = []
    for cur, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for n in names:
            disk.append(os.path.relpath(os.path.join(cur, n), ROOT))
    orphans = sorted(p for p in disk if p not in set(tracked) and not covered(p))
    check("R7 對帳無第三類孤兒", not orphans, "、".join(orphans[:8]))

    # print
    fails = [n for n, ok, _ in results if not ok]
    print("== check_public_readiness ==")
    for name, ok, detail in results:
        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}"
            + (f" — {detail}" if detail and not ok else "")
        )
    print(
        f"checks={len(results)} fail={len(fails)} tracked={len(tracked)} disk={len(disk)}"
    )
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
