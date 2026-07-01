#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从利物浦大学官方 2026 课程页核实一批项目 -> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "liverpool_verified.csv")
BASE = "https://www.liverpool.ac.uk/courses/2026/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "利物浦大学"
QS = 165
TIMELINE = "9 月入学；国际生滚动审理、招满即止，建议尽早递交（以官网 How to apply 为准）"
DURATION = "1 年"
LASTV = "2026-06"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-liverpool-ds-ai", "Data Science and Artificial Intelligence MSc", "数据科学/AI", "data-science-and-artificial-intelligence-msc", 78, 80, 82, 84, 74),
    ("uk-liverpool-ds-comm", "Data Science and Communication MSc", "数据科学/AI", "data-science-and-communication-msc", 78, 80, 82, 84, 74),
    ("uk-liverpool-cs", "Computer Science MSc", "计算机/CS", "computer-science-msc", 78, 80, 82, 84, 74),
    ("uk-liverpool-acs", "Advanced Computer Science MSc", "计算机/CS", "advanced-computer-science-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-fin", "Finance MSc", "金融", "finance-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-fintech", "Financial Technology MSc", "金融工程", "financial-technology-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-econ", "Economics MSc", "经济学", "economics-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-acc", "Accounting and Finance MSc", "会计", "accounting-and-finance-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-ba", "Business Analytics and Big Data MSc", "商业分析", "business-analytics-and-big-data-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-mkt", "Marketing MSc", "市场营销", "marketing-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-hrm", "Human Resource Management MSc", "管理学/商科", "human-resource-management-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-ib", "International Business MSc", "管理学/商科", "international-business-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-scm", "Operations and Supply Chain Management MSc", "管理学/商科", "operations-and-supply-chain-management-msc", 79, 81, 83, 85, 75),
    ("uk-liverpool-env", "Environmental Sciences MSc", "环境科学", "environmental-sciences-msc", 78, 80, 82, 84, 74),
]


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t))


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, url], capture_output=True, text=True)
    return r.stdout


def extract(text):
    m = re.search(r"IELTS\s*([0-9.]+)\s*overall,?\s*with no component below\s*([0-9.]+)", text)
    if not m:
        m = re.search(r"IELTS\s*([0-9.]+)\s*overall[^0-9]{0,30}?([0-9.]+)", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"(2:1|2:2)\s*honours degree[^.]{0,150}", text, re.I)
    if not d:
        d = re.search(r"(2:1|2:2)[^.]{0,150}degree[^.]{0,80}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    return ielts, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = BASE + slug
        text = clean(fetch(url))
        (io, isub), deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        notes = f"官方入学要求：{deg}" if deg else "入学要求见官方课程页"
        rows.append({
            "id": pid, "country": "英国", "university": UNI, "qsRank": QS,
            "program": prog, "field": field,
            "a985": a985, "a211": a211, "asy": asy, "asf": asf, "ahb": ahb,
            "ielts_overall": io, "ielts_sub": isub,
            "gre_total": "", "gre_quant": "",
            "background": deg, "notes": notes,
            "tuition": "", "duration": DURATION, "timeline": TIMELINE,
            "sourceUrl": url, "lastVerified": LASTV,
        })
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:60]}")

    cols = ["id", "country", "university", "qsRank", "program", "field",
            "a985", "a211", "asy", "asf", "ahb", "ielts_overall", "ielts_sub",
            "gre_total", "gre_quant", "background", "notes", "tuition",
            "duration", "timeline", "sourceUrl", "lastVerified"]
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\n写入 {len(rows)} 行 -> {OUT}")


if __name__ == "__main__":
    main()
