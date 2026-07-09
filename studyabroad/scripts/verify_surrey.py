#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""萨里大学 University of Surrey 官方核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分/单项——取自官方课程页静态 HTML。
措辞有多个变体：
  「IELTS Academic: X overall with Y in writing and Z in each other component」
  「IELTS Academic: X overall and Y in each other element」
  「IELTS Academic: X overall with/including Y in each element/category」
均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "surrey_verified.csv")
BASE = "https://www.surrey.ac.uk/postgraduate"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "萨里大学 Surrey"
QS = 305
TIMELINE = "9/10 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
LASTV = "2026-07"
DUR = "1 年"
A = dict(a985=74, a211=77, asy=79, asf=82, ahb=70)

# (id, 官方项目名, field, slug)
ITEMS = [
    ("uk-surrey-ai", "Artificial Intelligence MSc", "人工智能", "artificial-intelligence-msc"),
    ("uk-surrey-ds", "Data Science MSc", "数据科学", "data-science-msc"),
    ("uk-surrey-ba", "Business Analytics MSc", "商业分析", "business-analytics-msc"),
    ("uk-surrey-cyber", "Cyber Security MSc", "网络安全", "cyber-security-msc"),
    ("uk-surrey-cvml", "Computer Vision, Robotics & Machine Learning MSc", "计算机视觉与机器学习", "computer-vision-robotics-and-machine-learning-msc"),
    ("uk-surrey-econ", "Economics MSc", "经济学", "economics-msc"),
    ("uk-surrey-ibm", "International Business Management MSc", "国际商务管理", "international-business-management-msc"),
    ("uk-surrey-hrm", "Human Resources Management MSc", "人力资源管理", "human-resources-management-msc"),
    ("uk-surrey-accfin", "Accounting & Finance MSc", "会计与金融", "accounting-and-finance-msc"),
    ("uk-surrey-bankfin", "Banking & Finance MSc", "银行与金融", "banking-and-finance-msc"),
    ("uk-surrey-econfin", "Economics & Finance MSc", "经济与金融", "economics-and-finance-msc"),
    ("uk-surrey-eim", "Entrepreneurship & Innovation Management MSc", "创业与创新管理", "entrepreneurship-innovation-management-msc"),
    ("uk-surrey-aiconv", "Artificial Intelligence (Conversion) MSc", "人工智能转换", "artificial-intelligence-conversion-msc"),
    ("uk-surrey-dsconv", "Data Science (Conversion) MSc", "数据科学转换", "data-science-conversion-msc"),
    ("uk-surrey-eee", "Electronic Engineering MSc", "电子工程", "electronic-engineering-msc"),
]

PATS = [
    re.compile(r"IELTS Academic:?\s*([0-9]\.[0-9]) overall with ([0-9]\.[0-9]) in writing", re.I),
    re.compile(r"IELTS Academic:?\s*([0-9]\.[0-9]) overall (?:with|and|including)?\s*([0-9]\.[0-9])", re.I),
]


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t)).replace("\xa0", " ")


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "25", url],
                       capture_output=True, text=True)
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
        url = f"{BASE}/{slug}"
        text = clean(fetch(url))
        io, isub = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
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
