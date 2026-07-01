#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从巴斯大学官方 2026 课程页核实一批项目 -> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "bath_verified.csv")
BASE = "https://www.bath.ac.uk/courses/postgraduate-2026/taught-postgraduate-courses/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "巴斯大学"
QS = 150
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-06"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-bath-cs", "Computer Science MSc", "计算机/CS", "msc-computer-science", 80, 82, 84, 86, 76),
    ("uk-bath-ai", "Artificial Intelligence MSc", "数据科学/AI", "msc-artificial-intelligence", 81, 83, 85, 87, 77),
    ("uk-bath-ds", "Data Science MSc", "数据科学/AI", "msc-data-science", 81, 83, 85, 87, 77),
    ("uk-bath-fin", "Finance MSc", "金融", "msc-finance", 82, 84, 86, 87, 78),
    ("uk-bath-accfin", "Accounting and Finance MSc", "会计", "msc-accounting-and-finance", 82, 84, 86, 87, 78),
    ("uk-bath-finbank", "Finance with Banking MSc", "金融", "msc-finance-with-banking", 82, 84, 86, 87, 78),
    ("uk-bath-finrisk", "Finance with Risk Management MSc", "金融工程", "msc-finance-with-risk-management", 82, 84, 86, 87, 78),
    ("uk-bath-mgmt", "Management MSc", "管理学/商科", "msc-management", 82, 84, 86, 87, 78),
    ("uk-bath-mkt", "Marketing MSc", "市场营销", "msc-marketing", 81, 83, 85, 86, 77),
    ("uk-bath-im", "International Management MSc", "管理学/商科", "msc-international-management", 82, 84, 86, 87, 78),
    ("uk-bath-ba", "Business Analytics MSc", "商业分析", "msc-business-analytics", 82, 84, 86, 87, 78),
    ("uk-bath-entre", "Entrepreneurship and Management MSc", "管理学/商科", "msc-entrepreneurship-and-management", 80, 82, 84, 86, 76),
    ("uk-bath-itm", "Innovation and Technology Management MSc", "管理学/商科", "msc-innovation-and-technology-management", 80, 82, 84, 86, 76),
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
    m = re.search(r"IELTS:?\s*([0-9.]+)\s*overall with no less than\s*([0-9.]+)", text, re.I)
    if not m:
        m = re.search(r"score of at least\s*([0-9.]+)\s*overall\s*\.\s*Your scores[^0-9]*?at least\s*([0-9.]+)", text, re.I)
    if not m:
        m = re.search(r"IELTS[^0-9]{0,15}([0-9.]+)[^0-9]{0,25}?([0-9.]+)\s*in", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"(2:2 to 2:1|2:1|2:2|first[- ]class)[^.]{0,120}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["£", "English", "IELTS"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return ielts, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = BASE + slug + "/"
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
