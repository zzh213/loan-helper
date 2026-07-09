#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贝尔法斯特女王大学 Queen's University Belfast (QUB) 官方核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分/单项——取自官方课程页静态 HTML。
措辞：「IELTS* score of X, with not less than Y in any component」。
均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "qub_verified.csv")
BASE = "https://www.qub.ac.uk/courses/postgraduate-taught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "贝尔法斯特女王大学 QUB"
QS = 202
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
LASTV = "2026-07"
DUR = "1 年"
A = dict(a985=76, a211=79, asy=81, asf=83, ahb=72)

# (id, 官方项目名, field, slug)
ITEMS = [
    ("uk-qub-finance", "Finance MSc", "金融", "finance-msc"),
    ("uk-qub-fintrading", "Finance and Trading MSc", "金融", "finance-trading-msc"),
    ("uk-qub-frm", "Financial Risk Management MSc", "金融风险", "financial-risk-management-msc"),
    ("uk-qub-finanalytics", "Financial Analytics MSc", "金融/数据分析", "financial-analytics-msc"),
    ("uk-qub-accfin", "Accounting, Finance and Analytics MSc", "会计与金融", "accounting-finance-analytics-msc"),
    ("uk-qub-ba", "Business Analytics MSc", "商业分析", "business-analytics-msc"),
    ("uk-qub-ai", "Artificial Intelligence MSc", "人工智能", "artificial-intelligence-msc"),
    ("uk-qub-da", "Data Analytics MSc", "数据分析", "data-analytics-msc"),
    ("uk-qub-dsai", "Data Science and Artificial Intelligence (AI) MSc", "数据科学/AI", "data-science-artificial-intelligence-ai-msc"),
    ("uk-qub-cyber", "Applied Cyber Security MSc", "网络安全", "applied-cyber-security-msc"),
    ("uk-qub-digmkt", "Digital Marketing and Analytics MSc", "数字营销", "digital-marketing-analytics-msc"),
    ("uk-qub-aibiz", "Artificial Intelligence in Business MSc", "商业分析", "ai-business-msc"),
    ("uk-qub-leadership", "Global Leadership MSc", "管理学", "global-leadership-msc"),
    ("uk-qub-digbiz", "Digital Business MSc", "商业信息技术", "digital-business-msc"),
]

PATS = [
    re.compile(r"IELTS[^.]{0,20}score of ([0-9]\.[0-9]),?\s*with not less than ([0-9]\.[0-9]) in any", re.I),
    re.compile(r"IELTS[^.]{0,20}score of ([0-9]\.[0-9])[^.]{0,40}?([0-9]\.[0-9]) in any", re.I),
]


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t)).replace("\xa0", " ")


def fetch(url):
    for _ in range(4):
        r = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "30", url],
                           capture_output=True, text=True)
        if len(r.stdout) > 5000:
            return r.stdout
        time.sleep(3)
    return r.stdout


def extract(text):
    for pat in PATS:
        m = pat.search(text)
        if m:
            return m.group(1), m.group(2)
    return None, None


def main():
    rows = []
    for pid, prog, field, slug in ITEMS:
        url = f"{BASE}/{slug}/"
        text = clean(fetch(url))
        io, isub = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS (len={len(text)})")
            continue
        notes = (f"雅思总分 {io}、单项不低于 {isub}（取自官方课程页）；"
                 f"通常要求英国二等荣誉学位或同等学历，具体以官网为准")
        rows.append({
            "id": pid, "country": "英国", "university": UNI, "qsRank": QS,
            "program": prog, "field": field,
            "a985": A["a985"], "a211": A["a211"], "asy": A["asy"], "asf": A["asf"], "ahb": A["ahb"],
            "ielts_overall": io, "ielts_sub": isub,
            "gre_total": "", "gre_quant": "",
            "background": "英国二等荣誉学位或同等学历（以官网为准）", "notes": notes,
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
