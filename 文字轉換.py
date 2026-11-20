#!/usr/bin/env python3
"""純文字 -> Markdown -> pptx/pdf 轉換器。"""
import argparse, os, subprocess, sys

def 文字轉md(text, title=None):
    lines = text.splitlines()
    out = []
    if title:
        out.append(f"# {title}\n")
    # heuristic: first non-empty line as title if no title
    idx = 0
    if not title:
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        if idx < len(lines):
            out.append(f"# {lines[idx].strip()}\n")
            idx += 1
    # process rest
    para = []
    for line in lines[idx:]:
        s = line.strip()
        if not s:
            if para:
                out.append(" ".join(para) + "\n")
                para = []
            continue
        if s.startswith(("- ", "* ", "• ")):
            if para:
                out.append(" ".join(para) + "\n")
                para = []
            out.append(f"- {s.lstrip('-*• ').strip()}\n")
            continue
        # heading heuristic: short line, no punctuation, title case-ish
        if len(s) < 40 and not s.endswith((".", "。", ",", "，")) and s == s.strip():
            # only treat as heading if not already in para
            if para:
                out.append(" ".join(para) + "\n")
                para = []
            out.append(f"## {s}\n")
            continue
        para.append(s)
    if para:
        out.append(" ".join(para) + "\n")
    return "".join(out)

def 轉換(input_path, title=None, out_dir=None):
    with open(input_path, encoding="utf-8") as f:
        text = f.read()
    md = 文字轉md(text, title=title)
    base = os.path.splitext(os.path.basename(input_path))[0]
    if out_dir is None:
        out_dir = os.path.dirname(os.path.abspath(input_path))
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, base + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    pptx_path = os.path.join(out_dir, base + ".pptx")
    pdf_path = os.path.join(out_dir, base + ".pdf")
    # pptx via pandoc
    subprocess.run(["pandoc", md_path, "-o", pptx_path], check=True)
    # pdf via libreoffice (CJK support)
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", md_path, "--outdir", out_dir], check=True)
    return md_path, pptx_path, pdf_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="輸入純文字檔 (.txt)")
    ap.add_argument("--title", default=None, help="文件標題")
    ap.add_argument("--out-dir", default=None, help="輸出目錄")
    args = ap.parse_args()
    md, pptx, pdf = 轉換(args.input, title=args.title, out_dir=args.out_dir)
    print("已輸出:")
    print("  MD  :", md)
    print("  PPTX:", pptx)
    print("  PDF :", pdf)

if __name__ == "__main__":
    main()
