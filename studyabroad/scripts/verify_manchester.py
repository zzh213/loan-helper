#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从曼彻斯特大学官方 2026 课程页核实一批 STEM 项目 -> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页静态 HTML。
注：曼大商学院(Alliance MBS)项目雅思为 JS 加载，无法静态核实，此处只覆盖理工科。
均分门槛为基于官方学位要求(2:1≈60%)的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "manchester_verified.csv")
BASE = "https://www.manchester.ac.uk/study/masters/courses/list"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "曼彻斯特大学"
QS = 34
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, 课程码/slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-man-advmat", "Advanced Engineering Materials MSc", "材料工程", "04169/msc-advanced-engineering-materials", 78, 80, 82, 84, 74),
    ("uk-man-eps", "Electrical Power Systems Engineering MSc", "电子/电气工程", "07875/msc-electrical-power-systems-engineering", 78, 80, 82, 84, 74),
    ("uk-man-adveps", "Advanced Electrical Power Systems Engineering MSc", "电子/电气工程", "09718/msc-advanced-electrical-power-systems-engineering", 78, 80, 82, 84, 74),
    ("uk-man-csp", "Communications and Signal Processing MSc", "通信工程", "12034/msc-communications-and-signal-processing", 78, 80, 82, 84, 74),
    ("uk-man-cspext", "Communications and Signal Processing (Extended Research) MSc", "通信工程", "12727/msc-communications-and-signal-processing-with-extended-research", 78, 80, 82, 84, 74),
    ("uk-man-nano", "Nanomaterials MSc", "材料工程", "11998/msc-nanomaterials", 78, 80, 82, 84, 74),
    ("uk-man-polymer", "Polymer Materials Science and Engineering MSc", "材料工程", "04380/msc-polymer-materials-science-and-engineering", 78, 80, 82, 84, 74),
    ("uk-man-biomat", "Biomaterials MSc", "材料工程", "08839/msc-biomaterials", 78, 80, 82, 84, 74),
    ("uk-man-hds", "Health Data Science MSc", "数据科学/AI", "10076/msc-health-data-science", 80, 82, 84, 86, 76),
    ("uk-man-mathfin", "Mathematical Finance MSc", "金融工程", "02250/msc-mathematical-finance", 82, 84, 86, 88, 78),
    ("uk-man-dsmath", "Data Science (Mathematics) MSc", "数据科学/AI", "11428/msc-data-science-mathematics", 80, 82, 84, 86, 76),
    ("uk-man-dscs", "Data Science (Computer Science) MSc", "数据科学/AI", "11552/msc-data-science-computer-science-data-informatics", 80, 82, 84, 86, 76),
    ("uk-man-dssocial", "Data Science (Social Analytics) MSc", "数据科学/AI", "11424/msc-data-science-social-analytics", 79, 81, 83, 85, 75),
    ("uk-man-dsurban", "Data Science (Urban Analytics) MSc", "数据科学/AI", "11425/msc-data-science-urban-analytics", 79, 81, 83, 85, 75),
    ("uk-man-dsbiz", "Data Science (Business and Management) MSc", "数据科学/AI", "11426/msc-data-science-business-and-management", 80, 82, 84, 86, 76),
    ("uk-man-dsenv", "Data Science (Earth and Environmental Analytics) MSc", "数据科学/AI", "18096/msc-data-science-earth-and-environmental-analytics", 79, 81, 83, 85, 75),
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
    m = re.search(r"IELTS[:\s]{0,3}(?:at least\s*)?([0-9]\.[0-9])[^0-9]{0,45}?([0-9]\.[0-9])", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"(Upper Second class honours degree \(2:1[^.]{0,60}|Bachelor[^.]{0,110})", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["£", "IELTS", "TOFEL", "TOEFL"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return ielts, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}/"
        text = clean(fetch(url))
        (io, isub), deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS（可能 JS 加载）")
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
