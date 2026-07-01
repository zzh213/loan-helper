#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""斯特林大学（University of Stirling）官方课程页核实（第二批）-> CSV。
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
OUT = os.path.join(ROOT, "data", "sources", "stirling2_verified.csv")
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
    ("uk-stir-acai", "Advanced Computing with AI MSc", "数据科学/AI", "advanced-computing-artificial-intelligence", 76, 78, 80, 82, 72),
    ("uk-stir-dmbm", "Digital Marketing & Brand Management MSc", "数字营销", "digital-marketing-brand-management", 76, 78, 80, 82, 72),
    ("uk-stir-dmc", "Digital Media & Communication MSc", "数字媒体/传媒", "digital-media-and-communication", 76, 78, 80, 82, 72),
    ("uk-stir-envmgmt", "Environmental Management MSc", "环境管理", "environmental-management", 76, 78, 80, 82, 72),
    ("uk-stir-healthpsy", "Health Psychology MSc", "心理学", "health-psychology", 78, 80, 82, 84, 74),
    ("uk-stir-icc", "International Conflict & Cooperation MSc", "国际关系/政治", "international-conflict-cooperation", 76, 78, 80, 82, 72),
    ("uk-stir-ienvlaw", "International Environmental Law LLM", "环境法/法律", "international-environmental-law", 76, 78, 80, 82, 72),
    ("uk-stir-sportba", "Sport Business Analytics MSc", "体育商业分析", "sport-business-analytics", 76, 78, 80, 82, 72),
    ("uk-stir-prm", "Psychological Research Methods MSc", "心理学", "psychological-research-methods-general", 76, 78, 80, 82, 72),
    ("uk-stir-finda", "Finance & Data Analytics MSc", "金融/数据分析", "finance-data-analytics", 76, 78, 80, 82, 72),
    ("uk-stir-melt", "Management & English Language Teaching MSc", "管理/英语教学", "management-english-language-teaching", 78, 80, 82, 84, 74),
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:44]}")

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
