#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格拉斯哥大学第四批核实（管理/环境/城规/统计/教育/HR方向）-> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页静态 HTML。
Glasgow 雅思措辞：`X overall with ... no subtest less than Y`；学位 `2.1 Hons ...`。
均分门槛为基于官方学位要求(2.1)的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "glasgow4_verified.csv")
BASE = "https://www.gla.ac.uk/postgraduate/taught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "格拉斯哥大学"
QS = 78
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-gla-mst", "Management & Sustainable Tourism MSc", "管理学/商科", "managementsustainabletourism", 79, 81, 83, 85, 75),
    ("uk-gla-mwe", "Management & Enterprise MSc", "管理学/商科", "managementwithenterprise", 79, 81, 83, 85, 75),
    ("uk-gla-mhr", "Management with Human Resources MSc", "管理学/商科", "managementwithhumanresources", 79, 81, 83, 85, 75),
    ("uk-gla-ihrm", "International HRM & Development MSc", "管理学/商科", "internationalhumanresourcemanagementdevelopment", 79, 81, 83, 85, 75),
    ("uk-gla-hsm", "Health Service Management MSc", "公共政策/管理", "healthservicemanagement", 78, 80, 82, 84, 74),
    ("uk-gla-cityplan", "City Planning MSc", "土木/建筑", "city-planning", 78, 80, 82, 84, 74),
    ("uk-gla-realestate", "Real Estate MSc", "土木/建筑", "realestate", 78, 80, 82, 84, 74),
    ("uk-gla-stats", "Statistics MSc", "数据科学/AI", "statistics", 80, 82, 84, 86, 76),
    ("uk-gla-quantum", "Quantum Technology MSc", "电子/电气工程", "quantumtechnology", 79, 81, 83, 85, 75),
    ("uk-gla-erm", "Environmental Risk Management MSc", "环境科学", "environmentalriskmanagement", 78, 80, 82, 84, 74),
    ("uk-gla-susenergy", "Sustainable Energy MSc", "环境科学", "sustainableenergy", 78, 80, 82, 84, 74),
    ("uk-gla-museum", "Museum Studies MSc", "设计/艺术", "museumstudies", 78, 80, 82, 84, 74),
    ("uk-gla-tesol", "TESOL MSc", "翻译/语言", "tesolmsc", 79, 81, 83, 85, 75),
    ("uk-gla-appl", "Applied Linguistics MSc", "翻译/语言", "applied-linguistics", 79, 81, 83, 85, 75),
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
    m = re.search(r"([0-9]\.[0-9]) overall with.*?no subtest less than ([0-9]\.[0-9])", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"2\.1 Hons[^.]{0,80}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    deg = re.sub(r"\s+in 2:1 Hons.*$", "", deg, flags=re.I).strip()
    return ielts, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}/"
        text = clean(fetch(url))
        (io, isub), deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        if len(deg) < 8:
            deg = "2.1 荣誉学位（或非英国等效）——详见官方课程页"
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
