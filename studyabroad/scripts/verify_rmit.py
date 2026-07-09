#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""皇家墨尔本理工大学 RMIT 官方核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分/单项——取自官方课程页静态 HTML
（措辞：IELTS (Academic): minimum overall band of X (with no individual band below Y)）。
均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "rmit_verified.csv")
BASE = ("https://www.rmit.edu.au/study-with-us/levels-of-study/"
        "postgraduate-study/masters-by-coursework")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "皇家墨尔本理工大学 RMIT"
QS = 140
TIMELINE = "多为 2/7 月两次入学；分轮次滚动审理，建议尽早递交（以官网为准）"
LASTV = "2026-07"
DUR = "1.5–2 年"
A = dict(a985=71, a211=74, asy=77, asf=79, ahb=67)

# (id, 官方项目名, field, slug)
ITEMS = [
    ("au-rmit-it", "Master of Information Technology", "信息技术", "master-of-information-technology-mc208"),
    ("au-rmit-ds", "Master of Data Science", "数据科学", "master-of-data-science-mc267"),
    ("au-rmit-ai", "Master of Artificial Intelligence", "人工智能", "master-of-artificial-intelligence-mc271"),
    ("au-rmit-analytics", "Master of Analytics", "数据分析", "master-of-analytics-mc242"),
    ("au-rmit-baai", "Master of Business Analytics & AI Strategy", "商业分析", "master-of-business-analytics-and-ai-strategy-mc274"),
    ("au-rmit-com", "Master of Commerce", "商科", "master-of-commerce-mc288"),
    ("au-rmit-bit", "Master of Business Information Technology", "商业信息技术", "master-of-business-information-technology-mc200"),
    ("au-rmit-cyber", "Master of Cyber Security", "网络安全", "master-of-cyber-security-mc159"),
    ("au-rmit-engmgmt", "Master of Engineering Management", "工程管理", "master-of-engineering-management-mc226"),
]

PAT = re.compile(
    r"IELTS \(Academic\): minimum overall band of ([0-9]\.[0-9]).{0,45}?below ([0-9]\.[0-9])",
    re.I | re.S,
)


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t))


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "25", url],
                       capture_output=True, text=True)
    return r.stdout


def main():
    rows = []
    for pid, prog, field, slug in ITEMS:
        url = f"{BASE}/{slug}"
        text = clean(fetch(url))
        m = PAT.search(text)
        if not m:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        io, isub = m.group(1), m.group(2)
        notes = (f"雅思总分 {io}、单项不低于 {isub}（取自官方课程页）；"
                 f"通常要求本科相关背景，具体入学要求以官网为准")
        rows.append({
            "id": pid, "country": "澳大利亚", "university": UNI, "qsRank": QS,
            "program": prog, "field": field,
            "a985": A["a985"], "a211": A["a211"], "asy": A["asy"], "asf": A["asf"], "ahb": A["ahb"],
            "ielts_overall": io, "ielts_sub": isub,
            "gre_total": "", "gre_quant": "",
            "background": "本科相关专业背景（以官网为准）", "notes": notes,
            "tuition": "", "duration": DUR, "timeline": TIMELINE,
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
