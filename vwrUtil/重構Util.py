from ast import ClassDef, FunctionDef, NodeVisitor, parse, unparse
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Dict, Tuple


def 掃瞄(root: Path, pattern: str = "**/*.py") -> List[Path]:
    """遞迴掃描符合副檔名的所有檔案"""
    return [p for p in root.rglob(pattern) if p.is_file()]

import ast
from pathlib import Path
from typing import List, Dict

class ConceptExtractor(NodeVisitor):
    def __init__(self):
        self.classes = []
        self.funcs = []
        self.imports = []

    def visit_ClassDef(self, node: ClassDef):
        self.classes.append({
            "name": node.name,
            "bases": [unparse(b) for b in node.bases],
            "methods": [m.name for m in node.body if isinstance(m, FunctionDef)],
            "src": unparse(node)
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        self.funcs.append({
            "name": node.name,
            "args": [a.arg for a in node.args.args],
            "src": unparse(node)
        })
        self.generic_visit(node)

def parse_file(path: Path) -> Dict:
    tree = parse(path.read_text(encoding="utf-8"))
    extractor = ConceptExtractor()
    extractor.visit(tree)
    return {"file": str(path), "classes": extractor.classes, "funcs": extractor.funcs}

from typing import List, Dict
import ast

def merge_classes(class_group: List[Dict]) -> Dict:
    """將相似類別整併為單一通用抽象"""
    # 簡化版：取第一個當基底，其餘方法合併
    base = class_group[0].copy()
    for c in class_group[1:]:
        base["methods"] = list(set(base["methods"]) | set(c["methods"]))
    base["name"] = "Base" + base["name"]  # 重新命名
    return base

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))

def render(template_name: str, ctx: Dict, output: Path):
    tmpl = env.get_template(template_name)
    output.write_text(tmpl.render(**ctx), encoding="utf-8")


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def group_similar(items: List[Dict], threshold: float = 0.8, key: str = "src") -> List[List[Dict]]:
    """將相似度>threshold的項目分群"""
    groups: List[List[Dict]] = []
    for item in items:
        found = False
        for g in groups:
            if similar(item[key], g[0][key]) >= threshold:
                g.append(item)
                found = True
                break
        if not found:
            groups.append([item])
    return groups

