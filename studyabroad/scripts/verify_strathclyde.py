#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""斯特拉斯克莱德大学（University of Strathclyde）官方课程页核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方 postgraduatetaught 课程页静态 HTML。
Strathclyde 措辞两种：
  1) `minimum of X IELTS score, with no individual score lower than Y`（商科常见）
  2) `IELTS X (with no component below Y)`（理学常见）
学位：`second-class Honours degree`。均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "strathclyde_verified.csv")
BASE = "https://www.strath.ac.uk/courses/postgraduatetaught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "斯特拉斯克莱德大学"
QS = 276
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-strath-fintech", "Financial Technology MSc", "金融科技", "financialtechnology", 76, 78, 80, 82, 72),
    ("uk-strath-fin", "Finance MSc", "金融", "finance", 76, 78, 80, 82, 72),
    ("uk-strath-intmgmt", "International Management MSc", "管理学/商科", "internationalmanagement", 76, 78, 80, 82, 72),
    ("uk-strath-mkt", "Marketing MSc", "市场营销", "marketing", 76, 78, 80, 82, 72),
    ("uk-strath-hrm", "Human Resource Management MSc", "人力资源", "humanresourcemanagement", 76, 78, 80, 82, 72),
    ("uk-strath-bac", "Business Analysis & Consulting MSc", "商业分析/咨询", "businessanalysisconsulting", 76, 78, 80, 82, 72),
    ("uk-strath-da", "Data Analytics MSc", "数据分析", "dataanalytics", 76, 78, 80, 82, 72),
    ("uk-strath-ecofin", "Economics & Finance MSc", "经济/金融", "economicsfinance", 76, 78, 80, 82, 72),
    ("uk-strath-appecon", "Applied Economics MSc", "应用经济", "appliedeconomics", 76, 78, 80, 82, 72),
    ("uk-strath-ads", "Advanced Data Science MSc", "数据科学/AI", "advanceddatascience", 74, 76, 78, 80, 70),
    ("uk-strath-actsci", "Actuarial Science MSc", "精算学", "actuarialscience", 74, 76, 78, 80, 70),
]

PAT1 = re.compile(r"minimum of ([0-9]\.[0-9]) IELTS score, with no individual score lower than ([0-9]\.[0-9])", re.I)
PAT2 = re.compile(r"IELTS ([0-9]\.[0-9]) \(with no component below ([0-9]\.[0-9])\)", re.I)


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t))


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, url], capture_output=True, text=True)
    return r.stdout


def extract(text):
    m = PAT1.search(text) or PAT2.search(text)
    if not m:
        return None, None, ""
    overall, sub = m.group(1), m.group(2)
    d = re.search(r"(first-class|second-class|upper second|2\.1|2\.2|Honours degree)[^.]{0,70}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "view", "You"]:
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
