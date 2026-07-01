#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""普利茅斯大学（University of Plymouth）官方课程页核实 -> CSV。
核实项：雅思总分+单项，取自官方 courses/postgraduate 课程页静态 HTML。
Plymouth 措辞不统一，主要形如 `IELTS ... 6.5 ... minimum of 5.5`。
学位要求静态页仅笼统措辞（如 a relevant honours degree），如实标注。
均分门槛为基于官方要求推算的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "plymouth_verified.csv")
BASE = "https://www.plymouth.ac.uk/courses/postgraduate"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "普利茅斯大学"
QS = 651
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-plym-fin", "Finance MSc", "金融", "msc-finance", 74, 76, 78, 80, 70),
    ("uk-plym-dsba", "Data Science & Business Analytics MSc", "数据科学/商业分析", "msc-data-science-and-business-analytics", 74, 76, 78, 80, 70),
    ("uk-plym-cyber", "Cyber Security MSc", "网络安全", "msc-cyber-security", 74, 76, 78, 80, 70),
    ("uk-plym-ai", "Artificial Intelligence MSc", "人工智能", "msc-artificial-intelligence", 74, 76, 78, 80, 70),
    ("uk-plym-robotics", "Robotics MSc", "机器人", "msc-robotics", 74, 76, 78, 80, 70),
    ("uk-plym-civil", "Civil Engineering MSc", "土木工程", "msc-civil-engineering", 74, 76, 78, 80, 70),
    ("uk-plym-envcon", "Environmental Consultancy MSc", "环境咨询", "msc-environmental-consultancy", 74, 76, 78, 80, 70),
    ("uk-plym-marine", "Marine Conservation MSc", "海洋保护", "msc-marine-conservation", 74, 76, 78, 80, 70),
    ("uk-plym-tourism", "Tourism & Hospitality Management MSc", "旅游/酒店管理", "msc-tourism-and-hospitality-management", 74, 76, 78, 80, 70),
    ("uk-plym-sustenv", "Sustainable Environmental Management MSc", "可持续环境管理", "msc-sustainable-environmental-management", 74, 76, 78, 80, 70),
]


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t))


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, url], capture_output=True, text=True)
    return r.stdout


PAT = re.compile(r"IELTS[^<]{0,120}?([0-9]\.[0-9])[^<]{0,60}?minimum of\s*([0-9]\.[0-9])", re.I)
PAT2 = re.compile(r"IELTS[^<]{0,40}?([0-9]\.[0-9])[^<]{0,40}?scores? of\s*([0-9]\.[0-9])", re.I)


def extract(text):
    m = PAT.search(text) or PAT2.search(text)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}"
        text = clean(fetch(url))
        io, isub = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        deg = "官方要求相关专业荣誉学位或同等学历（详见官方课程页）"
        notes = f"雅思总分 {io}、单项不低于 {isub}（取自官方课程页）；入学学位要求见官方页面"
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
        print(f"  [OK] {prog} | IELTS {io}({isub})")

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
