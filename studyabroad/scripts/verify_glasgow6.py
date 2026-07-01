#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格拉斯哥大学官方课程页核实（第六批：经济/社科/人文）-> CSV。
核实项：雅思总分+小分、入学学位要求——取自官方 postgraduate/taught 课程页静态 HTML。
Glasgow 措辞：`X overall with ... no subtest less than Y`；学位 `2.1 Hons ...`。
均分门槛为基于官方 2:1 学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "glasgow6_verified.csv")
BASE = "https://www.gla.ac.uk/postgraduate/taught"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "格拉斯哥大学"
QS = 76
TIMELINE = "9 月入学；分轮次滚动审理、招满即止，建议尽早递交（以官网为准）"
DURATION = "1 年"
LASTV = "2026-07"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-gla-econ", "Economics MSc", "经济学", "economics-msc", 79, 81, 83, 85, 75),
    ("uk-gla-finecon2", "Financial Economics MSc", "金融经济", "financialeconomics", 79, 81, 83, 85, 75),
    ("uk-gla-hrip", "Human Rights & International Politics MSc", "国际关系/政治", "humanrightsinternationalpolitics", 78, 80, 82, 84, 74),
    ("uk-gla-arthist", "History of Art MSc", "艺术史", "art-history", 78, 80, 82, 84, 74),
    ("uk-gla-archaeo", "Archaeology MSc", "考古学", "archaeology", 78, 80, 82, 84, 74),
    ("uk-gla-classics", "Classics MSc", "古典学", "classics", 78, 80, 82, 84, 74),
    ("uk-gla-engling", "English Language & Linguistics MSc", "语言学", "englishlanguagelinguistics", 78, 80, 82, 84, 74),
    ("uk-gla-filmmaking", "Filmmaking & Media Arts MSc", "影视制作", "filmmaking", 78, 80, 82, 84, 74),
    ("uk-gla-childlit", "Children's Literature, Media & Culture MSc", "文学/传媒", "childrens-literature-media-culture", 78, 80, 82, 84, 74),
    ("uk-gla-dighum", "Digital Humanities MSc", "数字人文", "digital-humanities", 78, 80, 82, 84, 74),
    ("uk-gla-cicp", "Creative Industries & Cultural Policy MSc", "文化产业/政策", "creative-industries-cultural-policy", 78, 80, 82, 84, 74),
    ("uk-gla-ecc", "Environment, Culture & Communication MSc", "环境传播", "environmentculturecommunication", 78, 80, 82, 84, 74),
    ("uk-gla-complit", "Comparative Literature MSc", "比较文学", "comparativeliterature", 78, 80, 82, 84, 74),
    ("uk-gla-socio", "Sociology MSc", "社会学", "sociology", 78, 80, 82, 84, 74),
    ("uk-gla-humgeo", "Human Geography MSc", "人文地理", "human-geography", 78, 80, 82, 84, 74),
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
    m = re.search(r"([0-9]\.[0-9])\s*overall.*?no\s*(?:sub[- ]?test|component|band)\s*(?:score\s*)?less than\s*([0-9]\.[0-9])", text, re.I)
    overall = sub = None
    if m:
        overall, sub = m.group(1), m.group(2)
    d = re.search(r"2\.1\s*Hons[^.]{0,70}", text)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    for cut in ["IELTS", "English", "International", "You"]:
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
            deg = "官方要求 2:1 荣誉学位（详见官方课程页）"
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
        print(f"  [OK] {prog} | IELTS {io}({isub}) | {deg[:48]}")

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
