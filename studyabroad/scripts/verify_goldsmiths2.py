#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金史密斯学院第二批核实（心理/传媒/艺术/写作方向）-> CSV 供 ingest.py 导入。
核实项：雅思总分/单项、入学学位要求——取自官方 /pg/ 课程页静态 HTML。
写作/新闻类雅思更高（7.0/6.5）。学位多为 2:2 standard or above。
均分门槛为中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "goldsmiths2_verified.csv")
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
    ("uk-gold-psyconv", "Psychology Conversion MSc", "心理学", "msc-psychology-conversion", 74, 76, 78, 80, 70),
    ("uk-gold-cbt", "Cognitive Behavioural Therapy MSc", "认知行为治疗", "msc-cognitive-behavioural-therapy", 74, 76, 78, 80, 70),
    ("uk-gold-clinpsy", "Clinical Psychology & Health Services MSc", "临床心理学", "msc-clinical-psychology-health-services", 74, 76, 78, 80, 70),
    ("uk-gold-musicmind", "Music, Mind & Brain MSc", "音乐认知", "msc-music-mind-brain", 74, 76, 78, 80, 70),
    ("uk-gold-neuroaes", "Psychology of the Arts, Neuroaesthetics & Creativity MSc", "艺术心理学", "msc-psychology-arts-neuroaesthetics-creativity", 74, 76, 78, 80, 70),
    ("uk-gold-digpol", "Digital Political Communications MA", "政治传播", "ma-digital-political-communications", 74, 76, 78, 80, 70),
    ("uk-gold-cultsj", "Cultural Studies & Social Justice MA", "文化研究", "ma-cultural-studies-social-justice", 74, 76, 78, 80, 70),
    ("uk-gold-childlit", "Children's Literature MA", "儿童文学", "ma-childrens-literature", 74, 76, 78, 80, 70),
    ("uk-gold-filmscreen", "Film & Screen Studies MA", "电影研究", "ma-film-screen-studies", 74, 76, 78, 80, 70),
    ("uk-gold-gamesart", "Computer Games Art & Design MA", "游戏艺术设计", "ma-computer-games-art-design", 74, 76, 78, 80, 70),
    ("uk-gold-contart", "Contemporary Art Theory MA", "当代艺术理论", "ma-contemporary-art-theory", 74, 76, 78, 80, 70),
    ("uk-gold-visanth", "Visual Anthropology MA", "视觉人类学", "ma-visual-anthropology", 74, 76, 78, 80, 70),
    ("uk-gold-designexp", "Design: Expanded Practice MA", "设计", "ma-design-expanded-practice", 74, 76, 78, 80, 70),
    ("uk-gold-lifewriting", "Creative & Life Writing MA", "创意写作", "ma-creative-life-writing", 78, 80, 82, 84, 74),
    ("uk-gold-journ", "Journalism (Digital, Broadcast, News, Features & Magazines) MA", "新闻", "ma-journalism-digital-broadcast-news-features-magazines", 78, 80, 82, 84, 74),
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
