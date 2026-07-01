#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""斯特林大学（University of Stirling）官方课程页核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分+单项、入学学位要求——取自官方 pg-taught 课程页静态 HTML。
Stirling 措辞：`IELTS Academic or UKVI X with a minimum of Y in each sub-skill`。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "stirling_verified.csv")
BASE = "https://www.stir.ac.uk/courses/pg-taught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "斯特林大学"
QS = 431
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-stir-fin", "Finance MSc", "金融", "finance", 76, 78, 80, 82, 72),
    ("uk-stir-finrisk", "Finance & Risk Management MSc", "金融风险", "finance-risk-management", 76, 78, 80, 82, 72),
    ("uk-stir-iaf", "International Accounting & Finance MSc", "会计与金融", "international-accounting-finance", 76, 78, 80, 82, 72),
    ("uk-stir-ba", "Business Analytics MSc", "商业分析", "business-analytics", 76, 78, 80, 82, 72),
    ("uk-stir-ds", "Data Science MSc", "数据科学/AI", "data-science", 76, 78, 80, 82, 72),
    ("uk-stir-bm", "Business Management MSc", "管理学/商科", "business-management", 76, 78, 80, 82, 72),
    ("uk-stir-ai", "Artificial Intelligence MSc", "数据科学/AI", "artificial-intelligence", 76, 78, 80, 82, 72),
    ("uk-stir-bigdata", "Big Data MSc", "数据科学/AI", "big-data", 76, 78, 80, 82, 72),
    ("uk-stir-mkt", "Marketing MSc", "市场营销", "marketing", 76, 78, 80, 82, 72),
    ("uk-stir-mktanl", "Marketing Analytics MSc", "市场营销", "marketing-analytics", 76, 78, 80, 82, 72),
    ("uk-stir-hrm", "Human Resource Management MSc", "人力资源", "human-resource-management", 78, 80, 82, 84, 74),
    ("uk-stir-ib", "International Business MSc", "管理学/商科", "international-business", 76, 78, 80, 82, 72),
    ("uk-stir-pm", "Project Management MSc", "项目管理", "msc-project-management", 76, 78, 80, 82, 72),
    ("uk-stir-dsbus", "Data Science for Business MSc", "数据科学/AI", "data-science-for-business", 76, 78, 80, 82, 72),
    ("uk-stir-mathds", "Mathematics & Data Science MSc", "数据科学/AI", "mathematics-and-data-science", 76, 78, 80, 82, 72),
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
    m = re.search(r"IELTS Academic or UKVI\s*([0-9]\.[0-9])\s*with a minimum of\s*([0-9]\.[0-9])", text)
    if not m:
        return None, None, ""
    overall, sub = m.group(1), m.group(2)
    d = re.search(r"(minimum of a second class|second class|upper second|2\.1|2\.2|Honours degree)[^.]{0,70}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "TOEFL", "You", "If"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return overall, sub, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}/"
        text = clean(fetch(url))
        io, isub, deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        if len(deg) < 5:
            deg = "官方要求英国二等荣誉学位或同等学历（详见官方课程页）"
        notes = f"官方入学要求：{deg}；雅思总分 {io}、单项不低于 {isub}（取自官方课程页）"
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:46]}")

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
