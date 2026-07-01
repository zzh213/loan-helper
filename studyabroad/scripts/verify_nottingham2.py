#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诺丁汉大学第二批核实（补工科/CS/翻译/金融数学方向）-> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页静态 HTML。
诺丁汉雅思措辞：`IELTS X with at least Y in each element`；工科真实为 6.0(5.5)，
翻译类 7.0(6.5)，均取自官方页真实数据。
均分门槛为基于官方学位要求(2:1)的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "nottingham2_verified.csv")
BASE = "https://www.nottingham.ac.uk/pgstudy/course/taught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "诺丁汉大学"
QS = 97
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-nott-accfin", "Accounting and Finance MSc", "会计", "accounting-and-finance-msc", 80, 82, 84, 86, 76),
    ("uk-nott-civil", "Advanced Civil Engineering MSc", "土木/建筑", "advanced-civil-engineering-msc", 76, 78, 80, 82, 72),
    ("uk-nott-mat", "Advanced Materials MSc", "材料工程", "advanced-materials-msc", 76, 78, 80, 82, 72),
    ("uk-nott-chem", "Advanced Chemical Engineering MSc", "材料工程", "advanced-chemical-engineering-msc", 76, 78, 80, 82, 72),
    ("uk-nott-csai", "Computer Science (Artificial Intelligence) MSc", "数据科学/AI", "computer-science-artificial-intelligence", 80, 82, 84, 86, 76),
    ("uk-nott-transl", "Applied Translation Studies MA", "翻译/语言", "applied-translation-studies-ma", 79, 81, 83, 85, 75),
    ("uk-nott-fcm", "Financial and Computational Mathematics MSc", "金融工程", "financial-and-computational-mathematics-msc", 80, 82, 84, 86, 76),
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
    m = re.search(r"IELTS ([0-9]\.[0-9]) with at least ([0-9]\.[0-9]) in (?:each|any)", text)
    if not m:
        m = re.search(r"IELTS ([0-9]\.[0-9]) \(no less than ([0-9]\.[0-9])", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    # 学位：取 2:1 后面到常见导航噪声词之前
    d = re.search(r"(2:1|2:2|upper second)[^.]{0,90}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["How to apply", "Postgraduate funding", "Make an", "IELTS", "English"]:
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
            print(f"  [跳过] {slug}: 未解析到 IELTS（通用页/JS）")
            continue
        if len(deg) < 5:
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:45]}")

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
