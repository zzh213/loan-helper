#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""爱丁堡大学补充核实（信息学院 CS）-> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页静态 HTML。
爱丁堡措辞：`IELTS Academic : total X with at least Y in each component`。
注：爱丁堡多数课程页数字码路由无规律、商学院页 JS 加载，此处只覆盖可稳定核实项。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "edinburgh2_verified.csv")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "爱丁堡大学"
QS = 27
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, 完整URL, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-ed-cs", "Computer Science MSc", "计算机/CS",
     "https://study.ed.ac.uk/programmes/postgraduate-taught/110-computer-science",
     82, 84, 86, 88, 78),
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
    m = re.search(r"IELTS Academic\s*:?\s*total ([0-9]\.[0-9]) with at least ([0-9]\.[0-9])", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"(2:1|2:2|upper second|UK 2\.1)[^.]{0,80}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "We do not"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return ielts, deg


def main():
    rows = []
    for pid, prog, field, url, a985, a211, asy, asf, ahb in ITEMS:
        text = clean(fetch(url))
        (io, isub), deg = extract(text)
        if not io:
            print(f"  [跳过] {url}: 未解析到 IELTS")
            continue
        if len(deg) < 5:
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
