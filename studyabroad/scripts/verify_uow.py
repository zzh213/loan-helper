#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""卧龙岗大学 University of Wollongong (UOW) 官方核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分/单项——取自官方课程页静态 HTML
（表格措辞：IELTS Academic 6.5 6.0 6.0 6.0 6.0，首位总分，其后为各单项，取最低）。
均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "uow_verified.csv")
BASE = "https://www.uow.edu.au/study/courses"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "卧龙岗大学 UOW"
QS = 167
TIMELINE = "多为 2/7 月两次入学；分轮次滚动审理，建议尽早递交（以官网为准）"
LASTV = "2026-07"
DUR = "1.5–2 年"
A = dict(a985=70, a211=73, asy=76, asf=78, ahb=66)

# (id, 官方项目名, field, slug)
ITEMS = [
    ("au-uow-cs", "Master of Computer Science", "计算机科学", "master-of-computer-science"),
    ("au-uow-it", "Master of Information Technology", "信息技术", "master-of-information-technology"),
    ("au-uow-ba", "Master of Business Analytics", "商业分析", "master-of-business-analytics"),
    ("au-uow-fintech", "Master of Financial Technology", "金融科技", "master-of-financial-technology"),
    ("au-uow-ib", "Master of International Business", "国际商务", "master-of-international-business"),
    ("au-uow-eng", "Master of Engineering", "工程", "master-of-engineering"),
    ("au-uow-mkt", "Master of Marketing", "市场营销", "master-of-marketing"),
    ("au-uow-acc", "Master of Professional Accounting", "会计", "master-of-professional-accounting"),
]

PAT = re.compile(r"IELTS Academic\s*([0-9]\.[0-9])((?:\s+[0-9]\.[0-9]){1,4})", re.I)


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
        url = f"{BASE}/{slug}/"
        text = clean(fetch(url))
        m = PAT.search(text)
        if not m:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        io = m.group(1)
        subs = [float(x) for x in m.group(2).split()]
        isub = f"{min(subs):.1f}"
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
