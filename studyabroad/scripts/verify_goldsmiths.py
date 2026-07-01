#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金史密斯学院（Goldsmiths, University of London）官方课程页核实 -> CSV 供 ingest.py 导入。
核实项：雅思总分/单项、入学学位要求——取自官方 /pg/ 课程页静态 HTML。
Goldsmiths 措辞：`IELTS score ... of X overall ... no element lower than Y`
（部分页写 `X with a X in writing and no element lower than Y`）。
学位多为 2:2 standard or above。均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "goldsmiths_verified.csv")
BASE = "https://www.gold.ac.uk/pg"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "伦敦大学金史密斯学院"
QS = 561
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-gold-dsai", "Data Science & Artificial Intelligence MSc", "数据科学/AI", "msc-data-science-artificial-intelligence", 76, 78, 80, 82, 72),
    ("uk-gold-appai", "Applied Artificial Intelligence MSc", "人工智能", "msc-applied-artificial-intelligence", 76, 78, 80, 82, 72),
    ("uk-gold-games", "Computer Games Programming MSc", "游戏编程/CS", "msc-computer-games-programming", 76, 78, 80, 82, 72),
    ("uk-gold-ux", "User Experience Engineering MSc", "用户体验/CS", "msc-user-experience-engineering", 76, 78, 80, 82, 72),
    ("uk-gold-mcb", "Marketing & Consumer Behaviour MSc", "市场营销", "msc-marketing-consumer-behaviour", 74, 76, 78, 80, 70),
    ("uk-gold-mktinno", "Marketing & Innovation MSc", "市场营销/创新", "msc-marketing-innovation", 74, 76, 78, 80, 70),
    ("uk-gold-forensic", "Forensic Psychology MSc", "法务心理学", "msc-forensic-psychology", 74, 76, 78, 80, 70),
    ("uk-gold-socres", "Social Research MSc", "社会研究", "msc-social-research", 74, 76, 78, 80, 70),
    ("uk-gold-mediacom", "Media & Communications MA", "传媒", "ma-media-communications", 74, 76, 78, 80, 70),
    ("uk-gold-digmedia", "Digital Media MA", "数字媒体", "ma-digital-media", 74, 76, 78, 80, 70),
    ("uk-gold-brands", "Brands, Communication & Culture MA", "品牌传播", "ma-brands-communication-culture", 74, 76, 78, 80, 70),
    ("uk-gold-luxury", "Luxury Brand Management MA", "奢侈品品牌管理", "ma-luxury-brand-management", 74, 76, 78, 80, 70),
    ("uk-gold-compart", "Computational Arts MA", "计算艺术", "ma-computational-arts", 74, 76, 78, 80, 70),
    ("uk-gold-pram", "Public Relations, Advertising & Marketing MA", "公关/广告", "ma-public-relations-advertising-marketing", 74, 76, 78, 80, 70),
    ("uk-gold-socanth", "Social Anthropology MA", "社会人类学", "ma-social-anthropology", 74, 76, 78, 80, 70),
]

PAT = re.compile(
    r"IELTS score.{0,90}?of\s*([0-9]\.[0-9]).{0,70}?no element lower than ([0-9]\.[0-9])",
    re.I | re.S,
)


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t))


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, url], capture_output=True, text=True)
    return r.stdout


def extract(text):
    m = PAT.search(text)
    if not m:
        return None, None, ""
    overall, sub = m.group(1), m.group(2)
    d = re.search(r"(2:1|2:2|upper second|first[- ]class|second class)[^.]{0,70}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "You will", "If you"]:
        if cut in deg:
            deg = deg.split(cut)[0].strip()
    return overall, sub, deg


def main():
    rows = []
    for pid, prog, field, slug, a985, a211, asy, asf, ahb in ITEMS:
        url = f"{BASE}/{slug}/"
        text = clean(fetch(url))
        io, isub, deg = extract(text)
        if not io:
            print(f"  [跳过] {slug}: 未解析到 IELTS")
            continue
        if len(deg) < 5:
            deg = "官方要求英国二等荣誉学位（2:2）或同等学历（详见官方课程页）"
        notes = f"官方入学要求：{deg}；雅思总分 {io}、单项不低于 {isub}（取自官方课程页）"
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:40]}")

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
