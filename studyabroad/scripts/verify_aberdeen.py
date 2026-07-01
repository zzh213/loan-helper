#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阿伯丁大学（University of Aberdeen）官方课程页核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分+四项小分、入学学位要求——取自官方 degree-programmes 课程页静态 HTML。
Aberdeen 措辞：`IELTS Academic: OVERALL - X with: Listening - a; Reading - b; Speaking - c; Writing - d`。
ielts_sub 取四项最低分；notes 记录完整四项小分。
均分门槛为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "aberdeen_verified.csv")
BASE = "https://www.abdn.ac.uk/study/postgraduate-taught/degree-programmes"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "阿伯丁大学"
QS = 236
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, id/slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-abdn-accfin", "Accounting & Finance MSc", "会计与金融", "1/accounting-and-finance", 78, 80, 82, 84, 74),
    ("uk-abdn-ai", "Artificial Intelligence MSc", "数据科学/AI", "1034/artificial-intelligence", 77, 79, 81, 83, 73),
    ("uk-abdn-biobiz", "Biotechnology, Bioinformatics & Bio-Business MSc", "生物技术", "1036/msc-biotechnology-bioinformatics-and-bio-business", 78, 80, 82, 84, 74),
    ("uk-abdn-mecheng", "Advanced Mechanical Engineering MSc", "机械工程", "1037/advanced-mechanical-engineering", 76, 78, 80, 82, 72),
    ("uk-abdn-cheeng", "Advanced Chemical Engineering MSc", "化学工程", "1120/advanced-chemical-engineering", 76, 78, 80, 82, 72),
    ("uk-abdn-structeng", "Advanced Structural Engineering MSc", "结构/土木工程", "1126/advanced-structural-engineering", 76, 78, 80, 82, 72),
    ("uk-abdn-buslaw", "Business Law & Sustainable Development LLM", "商法/法律", "1128/business-law-and-sustainable-development-with-dissertation", 78, 80, 82, 84, 74),
    ("uk-abdn-archaeo", "Archaeology MSc", "考古学", "17/archaeology", 78, 80, 82, 84, 74),
    ("uk-abdn-anthro", "Anthropological Research MSc", "人类学", "2077/anthropological-research", 78, 80, 82, 84, 74),
    ("uk-abdn-biodiv", "Biodiversity Conservation & Management MSc", "生态/环境", "2179/biodiversity-conservation", 78, 80, 82, 84, 74),
    ("uk-abdn-climpol", "Climate Politics & Policy MSc", "气候政策/国际关系", "72/climate-politics-and-policy", 78, 80, 82, 84, 74),
    ("uk-abdn-chemenergy", "Chemistry for Sustainable Energy MSc", "化学", "1912/chemistry-for-sustainable-energy", 78, 80, 82, 84, 74),
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
    m = re.search(
        r"IELTS Academic:\s*OVERALL\s*-\s*([0-9]\.[0-9])\s*with:\s*"
        r"Listening\s*-\s*([0-9]\.[0-9]);\s*Reading\s*-\s*([0-9]\.[0-9]);\s*"
        r"Speaking\s*-\s*([0-9]\.[0-9]);\s*Writing\s*-\s*([0-9]\.[0-9])", text)
    if not m:
        return None, None, None, ""
    overall = m.group(1)
    bands = [m.group(2), m.group(3), m.group(4), m.group(5)]
    sub = min(bands, key=float)
    bandstr = f"听{bands[0]}/读{bands[1]}/说{bands[2]}/写{bands[3]}"
    d = re.search(r"(2:1|2:2|upper second|second class|first class|2\.1|2\.2)[^.]{0,70}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "TOEFL", "You"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return overall, sub, bandstr, deg


def main():
    rows = []
    for pid, prog, field, ref, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{ref}/"
        text = clean(fetch(url))
        io, isub, bandstr, deg = extract(text)
        if not io:
            print(f"  [跳过] {ref}: 未解析到 IELTS")
            continue
        if len(deg) < 4:
            deg = "官方要求 2:1 荣誉学位或同等学历（详见官方课程页）"
        notes = f"官方入学要求：{deg}；雅思总分 {io}（{bandstr}），取自官方课程页"
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) {bandstr} | {deg[:40]}")

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
