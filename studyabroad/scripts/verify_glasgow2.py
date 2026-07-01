#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从格拉斯哥大学官方课程页核实新一批项目 -> CSV 供 ingest.py 导入。
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
OUT = os.path.join(ROOT, "data", "sources", "glasgow2_verified.csv")
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
    ("uk-gla-ba", "Business Analytics MSc", "商业分析", "business-analytics", 80, 82, 84, 86, 76),
    ("uk-gla-cfb", "Corporate Finance & Banking MSc", "金融", "corporate-finance-banking", 81, 83, 85, 87, 77),
    ("uk-gla-daef", "Data Analytics for Economics & Finance MSc", "数据科学/AI", "dataanalyticsforeconomicsfinance", 80, 82, 84, 86, 76),
    ("uk-gla-frm", "Financial Risk Management MSc", "金融工程", "financialriskmanagement", 81, 83, 85, 87, 77),
    ("uk-gla-finmgmt", "Finance & Management MSc", "金融", "financemanagement", 81, 83, 85, 87, 77),
    ("uk-gla-ifa", "International Financial Analysis MSc", "金融", "internationalfinancialanalysis", 81, 83, 85, 87, 77),
    ("uk-gla-ibf", "Investment Banking & Finance MSc", "金融", "investmentbankingfinance", 82, 84, 86, 88, 78),
    ("uk-gla-hci", "Human Computer Interaction MSc", "计算机/CS", "human-computer-interaction", 79, 81, 83, 85, 75),
    ("uk-gla-robai", "Robotics & AI MSc", "数据科学/AI", "roboticsai", 80, 82, 84, 86, 76),
    ("uk-gla-advstat", "Advanced Statistics MSc", "数据科学/AI", "advanced-statistics", 80, 82, 84, 86, 76),
    ("uk-gla-geods", "Geospatial & Data Science Modelling MSc", "数据科学/AI", "geospatial-data-science-modelling", 79, 81, 83, 85, 75),
    ("uk-gla-urban", "Urban Analytics MSc", "数据科学/AI", "urbananalytics", 79, 81, 83, 85, 75),
    ("uk-gla-ism", "International Strategic Marketing MSc", "市场营销", "internationalstrategicmarketing", 80, 82, 84, 86, 76),
    ("uk-gla-mwm", "Management with Marketing MSc", "市场营销", "management-with-marketing", 80, 82, 84, 86, 76),
    ("uk-gla-wmpe", "Wealth Management & Private Equity MSc", "金融", "wealth-management-private-equity", 81, 83, 85, 87, 77),
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
    # 清理正则偶发的嵌套残缺（如 "in 2:1 Hons ..."）
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:55]}")

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
