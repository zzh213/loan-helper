#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""谢菲尔德大学第二批核实（补工科/AI/法律传媒/管理方向）-> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方 2026 课程页静态 HTML。
Sheffield 雅思措辞：`IELTS X (with Y in each component)`；新闻类更高(7.5/7)。
均分门槛为基于官方学位要求(2:1)的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "sheffield2_verified.csv")
BASE = "https://www.sheffield.ac.uk/postgraduate/taught/courses/2026"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "谢菲尔德大学"
QS = 105
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-shef-civil", "Civil Engineering MSc", "土木/建筑", "civil-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-shef-aero", "Aerospace Engineering MSc", "机械工程", "aerospace-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-shef-mat", "Materials Science and Engineering MSc", "材料工程", "materials-science-and-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-shef-advmech", "Advanced Mechanical Engineering MSc", "机械工程", "advanced-mechanical-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-shef-cyberai", "Cybersecurity and Artificial Intelligence MSc", "计算机/CS", "cybersecurity-and-artificial-intelligence-msc", 80, 82, 84, 86, 76),
    ("uk-shef-ai", "Artificial Intelligence MSc", "数据科学/AI", "artificial-intelligence-msc", 81, 83, 85, 87, 77),
    ("uk-shef-robotics", "Robotics MSc", "计算机/CS", "robotics-msc", 80, 82, 84, 86, 76),
    ("uk-shef-mbf", "Money, Banking and Finance MSc", "金融", "money-banking-and-finance-msc", 81, 83, 85, 87, 77),
    ("uk-shef-mgmt", "Management MSc", "管理学/商科", "management-msc", 80, 82, 84, 86, 76),
    ("uk-shef-im", "Information Management MSc", "信息系统/IT", "information-management-msc", 79, 81, 83, 85, 75),
    ("uk-shef-journ", "Journalism MA", "传媒", "journalism-ma", 80, 82, 84, 86, 76),
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
    m = re.search(r"IELTS ([0-9]\.[0-9]) \(with ([0-9]\.?[0-9]?) in each", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    if ielts[1] and "." not in ielts[1]:
        ielts = (ielts[0], ielts[1] + ".0")
    d = re.search(r"(2:1|2:2|upper second|first[- ]class)[^.]{0,80}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "University equivalent", "Library item"]:
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
            deg = "2:1 荣誉学位（详见官方课程页）"
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
