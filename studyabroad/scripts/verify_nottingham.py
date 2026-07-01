#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从诺丁汉大学官方硕士课程页核实一批项目 -> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求（2:1 等）——取自官方课程页。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "nottingham_verified.csv")
BASE = "https://www.nottingham.ac.uk/pgstudy/course/taught/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "诺丁汉大学"
QS = 97
TIMELINE = "多为 9 月入学；国际生滚动审理、招满即止，建议尽早递交（以官网 How to apply 为准）"
DURATION = "1 年"
LASTV = "2026-06"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-nottingham-ds", "Data Science MSc", "数据科学/AI", "data-science-msc", 79, 81, 83, 85, 75),
    ("uk-nottingham-mlsci", "Machine Learning in Science MSc", "数据科学/AI", "machine-learning-in-science-msc", 80, 82, 84, 86, 76),
    ("uk-nottingham-hci", "Human-Computer Interaction MSc", "计算机/CS", "human-computer-interaction-msc", 79, 81, 83, 85, 75),
    ("uk-nottingham-econ", "Economics MSc", "经济学", "economics-msc", 80, 82, 84, 86, 76),
    ("uk-nottingham-ba", "Business Analytics MSc", "商业分析", "business-analytics-msc", 80, 82, 84, 85, 76),
    ("uk-nottingham-banking", "Banking and Finance MSc", "金融", "banking-and-finance-msc", 80, 82, 84, 85, 76),
    ("uk-nottingham-acc", "Accounting and Finance MSc", "会计", "accounting-and-finance-msc", 80, 82, 84, 85, 76),
    ("uk-nottingham-mgmt", "Management MSc", "管理学/商科", "management-msc", 80, 82, 84, 86, 76),
    ("uk-nottingham-bm", "Business and Management MSc", "管理学/商科", "business-and-management-msc", 80, 82, 84, 86, 76),
    ("uk-nottingham-ib", "International Business MSc", "管理学/商科", "international-business-msc", 80, 82, 84, 86, 76),
    ("uk-nottingham-mkt", "Marketing MSc", "市场营销", "marketing-msc", 80, 82, 84, 86, 76),
    ("uk-nottingham-eee", "Electrical and Electronic Engineering MSc", "电子/电气工程", "electrical-and-electronic-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-nottingham-mech", "Mechanical Engineering MSc", "机械工程", "mechanical-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-nottingham-energy", "Sustainable Energy Engineering MSc", "环境科学", "sustainable-energy-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-nottingham-ir", "International Relations MA", "公共政策/管理", "international-relations-ma", 80, 82, 84, 86, 76),
    ("uk-nottingham-security", "International Security and Terrorism MA", "公共政策/管理", "international-security-and-terrorism-ma", 80, 82, 84, 86, 76),
    ("uk-nottingham-devdis", "Developmental Disorders MSc", "心理学", "developmental-disorders-msc", 80, 82, 84, 86, 76),
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
    m = re.search(r"IELTS\s*([0-9.]+)\s*with at least\s*([0-9.]+)\s*in each", text)
    if not m:
        m = re.search(r"IELTS\s*([0-9.]+)\s*\((?:no less than\s*)?([0-9.]+)", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"Undergraduate degree\s*(2:1|2:2)[^.]{0,160}", text, re.I)
    if not d:
        d = re.search(r"(2:1|2:2)\s*\(or international equivalent\)[^.]{0,140}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    deg = deg.replace("Undergraduate degree", "").strip()
    for cut in ["How to apply", "Home /", "IELTS", "English"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return ielts, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = BASE + slug
        text = clean(fetch(url))
        (io, isub), deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:60]}")

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
