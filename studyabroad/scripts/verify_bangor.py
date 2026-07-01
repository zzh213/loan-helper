#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""班戈大学（Bangor University）官方课程页核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分+单项——取自官方课程页静态 HTML（`IELTS: X (with no element below Y)`）。
学位要求为 JS 加载、静态页拿不到，background/notes 注明「以官方页为准」，保持诚实。
班戈商学院以银行与金融方向著称；均分门槛为基于常见二等荣誉学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "bangor_verified.csv")
BASE = "https://www.bangor.ac.uk/courses/postgraduate"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "班戈大学"
QS = 601
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-bangor-bf", "Banking & Finance MSc", "银行与金融", "banking-and-finance-msc", 76, 78, 80, 82, 72),
    ("uk-bangor-accfin", "Accounting & Finance MSc", "会计与金融", "accounting-and-finance-msc", 76, 78, 80, 82, 72),
    ("uk-bangor-fin", "Finance MSc", "金融", "finance-msc", 76, 78, 80, 82, 72),
    ("uk-bangor-mgmtfin", "Management & Finance MSc", "管理与金融", "management-and-finance-msc", 76, 78, 80, 82, 72),
    ("uk-bangor-accbank", "Accounting & Banking MSc", "会计与银行", "accounting-and-banking-msc", 76, 78, 80, 82, 72),
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
    m = re.search(r"IELTS:\s*([0-9]\.[0-9])\s*\(with no element below\s*([0-9]\.[0-9])\)", text)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def main():
    rows = []
    deg = "官方要求二等荣誉学位或同等学历（学位细则以官方课程页为准）"
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}"
        text = clean(fetch(url))
        io, isub = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        notes = f"雅思总分 {io}、单项不低于 {isub}（取自官方课程页，官方核实）；学位要求以官方课程页为准"
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
