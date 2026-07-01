#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格拉斯哥大学官方课程页核实（第五批：理学/心理/环境/生物工程/传媒）-> CSV。
核实项：雅思总分+小分、入学学位要求——取自官方 postgraduate/taught 课程页静态 HTML。
Glasgow 措辞：`X overall with ... no subtest less than Y`；学位 `2.1 Hons ...`。
均分门槛为基于官方 2:1 学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "glasgow5_verified.csv")
BASE = "https://www.gla.ac.uk/postgraduate/taught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "格拉斯哥大学"
QS = 76
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-gla-biotech", "Biotechnology MSc", "生物技术", "biotechnology", 78, 80, 82, 84, 74),
    ("uk-gla-biotechmgmt", "Biotechnology & Management MSc", "生物技术", "biotechnology-management", 78, 80, 82, 84, 74),
    ("uk-gla-afm2", "Advanced Functional Materials MSc", "材料科学", "advanced-functional-materials", 78, 80, 82, 84, 74),
    ("uk-gla-chem", "Chemistry MSc", "化学", "chemistry", 78, 80, 82, 84, 74),
    ("uk-gla-astro", "Astrophysics MSc", "天体物理", "astrophysics", 78, 80, 82, 84, 74),
    ("uk-gla-behsci", "Behavioural Science MSc", "心理/行为科学", "behavioural-science", 79, 81, 83, 85, 75),
    ("uk-gla-appneuro", "Applied Neuropsychology MSc", "心理/神经科学", "applied-neuropsychology", 78, 80, 82, 84, 74),
    ("uk-gla-crim", "Criminology & Criminal Justice MSc", "犯罪学/法律", "criminology-criminal-justice", 78, 80, 82, 84, 74),
    ("uk-gla-cw", "Creative Writing MLitt", "创意写作", "creativewritingmlitt", 78, 80, 82, 84, 74),
    ("uk-gla-dsee", "Data Science for Ecology & Epidemiology MSc", "数据科学/AI", "data-science-for-ecology-epidemiology", 79, 81, 83, 85, 75),
    ("uk-gla-ecolem", "Ecology & Environmental Monitoring MSc", "生态/环境", "ecology-environmental-monitoring", 78, 80, 82, 84, 74),
    ("uk-gla-fineng2", "Financial Engineering MSc", "金融工程", "financial-engineering", 79, 81, 83, 85, 75),
    ("uk-gla-filmtv", "Film & Television Studies MSc", "传媒/影视", "filmtelevisionstudies", 78, 80, 82, 84, 74),
    ("uk-gla-digsoc", "Digital Society MSc", "数字社会/传媒", "digitalsociety", 78, 80, 82, 84, 74),
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
    m = re.search(r"([0-9]\.[0-9])\s*overall.*?no\s*(?:sub[- ]?test|component|band)\s*(?:score\s*)?less than\s*([0-9]\.[0-9])", text, re.I)
    overall = sub = None
    if m:
        overall, sub = m.group(1), m.group(2)
    d = re.search(r"2\.1\s*Hons[^.]{0,70}", text)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "International", "You"]:
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
            deg = "官方要求 2:1 荣誉学位（详见官方课程页）"
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:48]}")

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
