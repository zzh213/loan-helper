#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格拉斯哥大学第三批核实（工科/传媒/法律/教育/公共政策）-> CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求——取自官方课程页静态 HTML。
Glasgow 法律类雅思为 7.0(6.5)，STEM/商科为 6.5(6.0)，均为官方页真实数据。
均分门槛为基于官方学位要求(2.1)的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "glasgow3_verified.csv")
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
    ("uk-gla-aero", "Aerospace Engineering MSc", "机械工程", "aerospace-engineering", 78, 80, 82, 84, 74),
    ("uk-gla-civil", "Civil Engineering MSc", "土木/建筑", "civil-engineering", 78, 80, 82, 84, 74),
    ("uk-gla-mech", "Mechanical Engineering MSc", "机械工程", "mechanicalengineering", 78, 80, 82, 84, 74),
    ("uk-gla-eee", "Electronics & Electrical Engineering MSc", "电子/电气工程", "electronicselectricalengineering", 78, 80, 82, 84, 74),
    ("uk-gla-cse", "Computer Systems Engineering MSc", "电子/电气工程", "computersystemsengineering", 78, 80, 82, 84, 74),
    ("uk-gla-afm", "Advanced Functional Materials MSc", "材料工程", "advanced-functional-materials", 78, 80, 82, 84, 74),
    ("uk-gla-bioinf", "Bioinformatics MSc", "数据科学/AI", "bioinformatics", 79, 81, 83, 85, 75),
    ("uk-gla-biomedeng", "Biomedical Engineering MSc", "机械工程", "biomedical-engineering", 78, 80, 82, 84, 74),
    ("uk-gla-mcij", "Media, Communications & International Journalism MSc", "传媒", "mediacommunicationsinternationaljournalism", 78, 80, 82, 84, 74),
    ("uk-gla-globcomm", "Global Communications MSc", "传媒", "global-communications", 78, 80, 82, 84, 74),
    ("uk-gla-mediamgmt", "Media Management MSc", "传媒", "mediamanagement", 78, 80, 82, 84, 74),
    ("uk-gla-polcomm", "Political Communication MSc", "传媒", "politicalcommunication", 78, 80, 82, 84, 74),
    ("uk-gla-scicomm", "Science Communications MSc", "传媒", "science-communications", 78, 80, 82, 84, 74),
    ("uk-gla-intlaw", "International Law LLM", "法律(LLM)", "internationallaw", 80, 82, 84, 86, 76),
    ("uk-gla-comlaw", "International Commercial Law LLM", "法律(LLM)", "internationalcommerciallaw", 80, 82, 84, 86, 76),
    ("uk-gla-econlaw", "International Economic Law LLM", "法律(LLM)", "internationaleconomiclaw", 80, 82, 84, 86, 76),
    ("uk-gla-corplaw", "Corporate & Financial Law LLM", "法律(LLM)", "corporate-financial-law", 80, 82, 84, 86, 76),
    ("uk-gla-techlaw", "Technology Law & Regulation LLM", "法律(LLM)", "technology-law-regulation", 80, 82, 84, 86, 76),
    ("uk-gla-edustudy", "Educational Studies MSc", "教育", "educationalstudiesmsc", 78, 80, 82, 84, 74),
    ("uk-gla-edupolicy", "Education, Public Policy & Equity MSc", "教育", "educationpublicpolicyequity", 78, 80, 82, 84, 74),
    ("uk-gla-heta", "Health Economics & Health Technology Assessment MSc", "经济学", "health-economics-health-technology-assessment", 80, 82, 84, 86, 76),
    ("uk-gla-ppm", "Public Policy & Management MSc", "公共政策/管理", "publicpolicymanagement", 78, 80, 82, 84, 74),
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:52]}")

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
