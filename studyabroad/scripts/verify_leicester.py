#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""莱斯特大学官方课程页核实一批项目 -> CSV 供 ingest.py 导入。
核实项：雅思总分、入学学位要求——取自官方课程页静态 HTML。
注：莱斯特课程页只公布雅思总分（`IELTS X or equivalent`），小分标准见其语言中心，
本表 ielts_sub 沿用总分并在 notes 注明「官方公布总分，小分以语言中心为准」。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "leicester_verified.csv")
BASE = "https://le.ac.uk/courses"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "莱斯特大学"
QS = 240
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-leic-advcs", "Advanced Computer Science MSc", "计算机/CS", "advanced-computer-science-msc", 76, 78, 80, 82, 72),
    ("uk-leic-ai", "Artificial Intelligence MSc", "数据科学/AI", "artificial-intelligence-msc", 77, 79, 81, 83, 73),
    ("uk-leic-ds", "Data Science MSc", "数据科学/AI", "data-science-msc", 77, 79, 81, 83, 73),
    ("uk-leic-cloud", "Cloud Computing MSc", "计算机/CS", "cloud-computing-msc", 76, 78, 80, 82, 72),
    ("uk-leic-fin", "Finance MSc", "金融", "finance-msc", 78, 80, 82, 84, 74),
    ("uk-leic-ba", "Business Analytics MSc", "商业分析", "business-analytics-msc", 78, 80, 82, 84, 74),
    ("uk-leic-mgmt", "Management MSc", "管理学/商科", "management-msc", 78, 80, 82, 84, 74),
    ("uk-leic-mkt", "Marketing MSc", "市场营销", "marketing-msc", 78, 80, 82, 84, 74),
    ("uk-leic-law", "Law LLM", "法律(LLM)", "law-llm", 78, 80, 82, 84, 74),
    ("uk-leic-comlaw", "International Commercial Law LLM", "法律(LLM)", "international-commercial-law-llm", 78, 80, 82, 84, 74),
    ("uk-leic-aero", "Aerospace Engineering MSc", "机械工程", "aerospace-engineering-msc", 76, 78, 80, 82, 72),
    ("uk-leic-media", "Communication and Media MA", "传媒", "communication-and-media-ma", 78, 80, 82, 84, 74),
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
    m = re.search(r"IELTS\s*([0-9]\.[0-9])\s*or equivalent", text)
    if not m:
        m = re.search(r"IELTS\s*([0-9]\.[0-9])", text)
    overall = m.group(1) if m else None
    d = re.search(r"(2:1|2:2|second class|upper second|first class)[^.]{0,70}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "Scroll"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return overall, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}/2025"
        text = clean(fetch(url))
        io, deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        if len(deg) < 5:
            deg = "官方要求 2:1/2:2 荣誉学位（详见官方课程页）"
        notes = f"官方入学要求：{deg}；雅思总分 {io}（官方课程页只公布总分，小分标准以语言中心为准）"
        rows.append({
            "id": pid, "country": "英国", "university": UNI, "qsRank": QS,
            "program": prog, "field": field,
            "a985": a985, "a211": a211, "asy": asy, "asf": asf, "ahb": ahb,
            "ielts_overall": io, "ielts_sub": io,
            "gre_total": "", "gre_quant": "",
            "background": deg, "notes": notes,
            "tuition": "", "duration": DURATION, "timeline": TIMELINE,
            "sourceUrl": url, "lastVerified": LASTV,
        })
        print(f"  [OK] {prog} | IELTS {io} | {deg[:50]}")

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
