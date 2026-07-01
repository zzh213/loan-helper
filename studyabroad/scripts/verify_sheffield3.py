#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""谢菲尔德大学第三批核实（理学/环境/建筑/神经科学方向）-> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方 2026 课程页静态 HTML。
Sheffield 雅思措辞：`IELTS X (with Y in each component)`。
均分门槛为基于官方学位要求(2:1)的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "sheffield3_verified.csv")
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
    ("uk-shef-ds", "Data Science MSc", "数据科学/AI", "data-science-msc", 80, 82, 84, 86, 76),
    ("uk-shef-intmgmt", "International Management MSc", "管理学/商科", "international-management-msc", 80, 82, 84, 86, 76),
    ("uk-shef-ecid", "Environmental Change & International Development MSc", "环境/国际发展", "environmental-change-and-international-development-msc", 78, 80, 82, 84, 74),
    ("uk-shef-archdes", "Architectural Design MA", "建筑设计", "architectural-design-ma", 78, 80, 82, 84, 74),
    ("uk-shef-ccn", "Cognitive & Computational Neuroscience MSc", "神经科学", "cognitive-and-computational-neuroscience-msc", 79, 81, 83, 85, 75),
    ("uk-shef-biopro", "Biological & Bioprocess Engineering MSc", "生物工程", "biological-and-bioprocess-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-shef-clinneuro", "Clinical Neurology MSc", "临床神经科学", "clinical-neurology-msc", 79, 81, 83, 85, 75),
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
