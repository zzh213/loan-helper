#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""悉尼科技大学 UTS 官方核实（研究生课程）-> CSV 供 ingest.py 导入。
核实项：雅思总分/写作单项——取自官方课程页静态 HTML
（措辞：IELTS Academic: overall X, writing Y）。
均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "uts_verified.csv")
BASE = "https://www.uts.edu.au/study/find-a-course"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "悉尼科技大学 UTS"
QS = 88
TIMELINE = "多为 3/8 月两次入学；分轮次滚动审理，建议尽早递交（以官网为准）"
LASTV = "2026-07"
DUR = "1.5–2 年"
A = dict(a985=73, a211=76, asy=78, asf=81, ahb=69)

# (id, 官方项目名, field, slug)
ITEMS = [
    ("au-uts-it", "Master of Information Technology", "信息技术", "master-information-technology"),
    ("au-uts-dsi", "Master of Data Science & Innovation", "数据科学", "master-data-science-and-innovation"),
    ("au-uts-ba", "Master of Business Analytics", "商业分析", "master-business-analytics"),
    ("au-uts-peng", "Master of Professional Engineering", "工程", "master-professional-engineering"),
    ("au-uts-fin", "Master of Finance", "金融", "master-finance"),
    ("au-uts-eng", "Master of Engineering", "工程", "master-engineering"),
    ("au-uts-scm", "Master of Strategic Supply Chain Management", "供应链管理", "master-strategic-supply-chain-management"),
    ("au-uts-mgmt", "Master of Management", "管理学", "master-management"),
    ("au-uts-mkt", "Master of Marketing", "市场营销", "master-marketing"),
]

PAT = re.compile(
    r"IELTS Academic:\s*overall\s*([0-9]\.[0-9]),\s*writing\s*([0-9]\.[0-9])",
    re.I,
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
        notes = (f"雅思总分 {io}、写作不低于 {isub}（取自官方课程页）；"
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
        print(f"  [OK] {prog} | IELTS {io}(写作{isub})")

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
