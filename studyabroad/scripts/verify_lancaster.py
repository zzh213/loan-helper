#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从兰卡斯特大学官方硕士课程页核实一批项目 -> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "lancaster_verified.csv")
BASE = "https://www.lancaster.ac.uk/study/postgraduate/postgraduate-courses/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "兰卡斯特大学"
QS = 132
TIMELINE = "9 月/10 月入学；国际生滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-06"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-lancaster-ds", "Data Science MSc", "数据科学/AI", "data-science-msc", 78, 80, 82, 84, 74),
    ("uk-lancaster-cs", "Computer Science MSc", "计算机/CS", "computer-science-msc", 78, 80, 82, 84, 74),
    ("uk-lancaster-acs", "Advanced Computer Science MSc", "计算机/CS", "advanced-computer-science-msc", 79, 81, 83, 85, 75),
    ("uk-lancaster-ai", "Artificial Intelligence MSc", "数据科学/AI", "artificial-intelligence-msc", 79, 81, 83, 85, 75),
    ("uk-lancaster-da", "Data Analytics MSc", "数据科学/AI", "data-analytics-msc", 78, 80, 82, 84, 74),
    ("uk-lancaster-fin", "Finance MSc", "金融", "finance-msc", 80, 82, 84, 85, 76),
    ("uk-lancaster-afm", "Accounting and Financial Management MSc", "会计", "accounting-and-financial-management-msc", 80, 82, 84, 85, 76),
    ("uk-lancaster-mbf", "Money, Banking and Finance MSc", "金融", "money-banking-and-finance-msc", 80, 82, 84, 85, 76),
    ("uk-lancaster-qf", "Quantitative Finance MSc", "金融工程", "quantitative-finance-msc", 81, 83, 85, 86, 77),
    ("uk-lancaster-econ", "Economics MSc", "经济学", "economics-msc", 80, 82, 84, 86, 76),
    ("uk-lancaster-finecon", "Financial Economics MSc", "经济学", "financial-economics-msc", 80, 82, 84, 86, 76),
    ("uk-lancaster-mgmt", "Management MSc", "管理学/商科", "management-msc", 80, 82, 84, 86, 76),
    ("uk-lancaster-mkt", "Marketing MSc", "市场营销", "marketing-msc", 80, 82, 84, 86, 76),
    ("uk-lancaster-hrm", "Human Resource Management MSc", "管理学/商科", "human-resource-management-msc", 80, 82, 84, 86, 76),
    ("uk-lancaster-pm", "Project Management MSc", "管理学/商科", "project-management-msc", 79, 81, 83, 85, 75),
    ("uk-lancaster-ebiz", "E-Business and Innovation MSc", "信息系统/IT", "e-business-and-innovation-msc", 79, 81, 83, 85, 75),
    ("uk-lancaster-scm", "Logistics and Supply Chain Management MSc", "管理学/商科", "logistics-and-supply-chain-management-msc", 79, 81, 83, 85, 75),
    ("uk-lancaster-ee", "Electronic Engineering MSc", "电子/电气工程", "electronic-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-lancaster-comm", "Communications Engineering MSc", "通信工程", "communications-engineering-msc", 78, 80, 82, 84, 74),
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
    m = re.search(r"overall score of at least\s*([0-9.]+),\s*and a min[a-z ]*?([0-9.]+)", text, re.I)
    if not m:
        m = re.search(r"IELTS[^0-9]{0,20}([0-9.]+)[^0-9]{0,30}?([0-9.]+)\s*in", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"(2:1|2:2)\s*(?:\(hons\)\s*)?(?:honours\s*)?degree", text, re.I)
    deg = d.group(0).strip() if d else ""
    deg = re.sub(r"\s+", " ", deg)
    fee = ""
    fm = re.search(r"International students[^£]{0,40}(£[\d,]+)", text)
    if not fm:
        fm = re.search(r"(£3[0-9],\d{3})", text)
    if fm:
        fee = f"国际 {fm.group(1)} / 1年"
    return ielts, deg, fee


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = BASE + slug + "/"
        text = clean(fetch(url))
        (io, isub), deg, fee = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        notes = f"官方入学要求：{deg}（英国 2:1 荣誉学位或国际等效）" if deg else "入学要求见官方课程页"
        rows.append({
            "id": pid, "country": "英国", "university": UNI, "qsRank": QS,
            "program": prog, "field": field,
            "a985": a985, "a211": a211, "asy": asy, "asf": asf, "ahb": ahb,
            "ielts_overall": io, "ielts_sub": isub,
            "gre_total": "", "gre_quant": "",
            "background": f"需 {deg}（国际等效）" if deg else "",
            "notes": notes,
            "tuition": fee, "duration": DURATION, "timeline": TIMELINE,
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
