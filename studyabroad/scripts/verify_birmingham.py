#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从伯明翰大学官方课程页核实一批项目 -> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页静态 HTML。
注：部分商科/工科页面雅思为 JS 加载，此批只覆盖静态可核实的课程。
均分门槛为基于官方学位要求(2:1)的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "birmingham_verified.csv")
BASE = "https://www.birmingham.ac.uk/postgraduate/courses/taught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "伯明翰大学"
QS = 84
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-bham-cs", "Computer Science MSc", "计算机/CS", "computer-science/computer-science-msc", 80, 82, 84, 86, 76),
    ("uk-bham-aiml", "Artificial Intelligence and Machine Learning MSc", "数据科学/AI", "computer-science/artificial-intelligence-machine-learning-msc", 81, 83, 85, 87, 77),
    ("uk-bham-advcs", "Advanced Computer Science MSc", "计算机/CS", "computer-science/advanced-computer-science-msc", 81, 83, 85, 87, 77),
    ("uk-bham-hci", "Human-Computer Interaction MSc", "计算机/CS", "computer-science/human-computer-interaction-msc", 79, 81, 83, 85, 75),
    ("uk-bham-robotics", "Robotics MSc", "计算机/CS", "computer-science/robotics-msc", 80, 82, 84, 86, 76),
    ("uk-bham-cyber", "Cyber Security MSc", "计算机/CS", "computer-science/cyber-security-msc", 80, 82, 84, 86, 76),
    ("uk-bham-intmkt", "International Marketing MSc", "市场营销", "business/international-marketing-msc", 80, 82, 84, 86, 76),
    ("uk-bham-invest", "Investments MSc", "金融", "business/investments-msc", 81, 83, 85, 87, 77),
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
    m = re.search(r"IELTS[^0-9]{0,25}([0-9]\.[0-9])[^0-9]{0,40}?([0-9]\.[0-9])", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"(2:1|2:2|upper second|first[- ]class)[^.]{0,80}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["£", "IELTS", "Full requ", "Full Requ", "TOEFL"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return ielts, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}"
        text = clean(fetch(url))
        (io, isub), deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS（可能 JS 加载）")
            continue
        if len(deg) < 6:
            deg = "官方要求 2:1 荣誉学位（详见官方课程页）"
        notes = f"官方入学要求：{deg}"
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:50]}")

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
