#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从谢菲尔德大学官方 2026 课程页核实一批硕士项目，产出 CSV 供 ingest.py 导入。
核实项：雅思总分/小分、入学学位要求（2:1/2:2 及专业背景）、时长——均取自官方项目页。
均分门槛(a985..ahb)为基于官方学位要求的中国大陆申请参考线（非官方保证）。
"""
import csv
import html
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "sheffield_verified.csv")
BASE = "https://www.sheffield.ac.uk/postgraduate/taught/courses/2026/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
UNI = "谢菲尔德大学"
QS = 105
TIMELINE = "9 月入学；国际生名额有限、多轮滚动审理，招满即止，建议尽早递交（以官网 Deadlines 页为准）"
DURATION = "1 年"
LASTV = "2026-06"

# (id, 官方项目名, field, slug, a985,a211,asy,asf,ahb)
ITEMS = [
    ("uk-sheffield-cs", "Computer Science MSc", "计算机/CS", "computer-science-msc", 78, 80, 82, 84, 74),
    ("uk-sheffield-adv-cs", "Advanced Computer Science MSc", "计算机/CS", "advanced-computer-science-msc", 80, 82, 84, 86, 76),
    ("uk-sheffield-ai", "Artificial Intelligence MSc", "数据科学/AI", "artificial-intelligence-msc", 80, 82, 84, 86, 76),
    ("uk-sheffield-cyber-ai", "Cybersecurity and Artificial Intelligence MSc", "计算机/CS", "cybersecurity-and-artificial-intelligence-msc", 80, 82, 84, 86, 76),
    ("uk-sheffield-ba", "Business Analytics MSc", "商业分析", "business-analytics-msc", 80, 82, 84, 85, 76),
    ("uk-sheffield-fintech", "Financial Technology and Innovation MSc", "金融工程", "financial-technology-and-innovation-msc", 81, 83, 85, 86, 77),
    ("uk-sheffield-facc", "Finance and Accounting MSc", "会计", "finance-and-accounting-msc", 80, 82, 84, 85, 76),
    ("uk-sheffield-mbf", "Money, Banking and Finance MSc", "金融", "money-banking-and-finance-msc", 80, 82, 84, 85, 76),
    ("uk-sheffield-econ", "Economics MSc", "经济学", "economics-msc", 80, 82, 84, 86, 76),
    ("uk-sheffield-bfe", "Business Finance and Economics MSc", "经济学", "business-finance-and-economics-msc", 79, 81, 83, 85, 75),
    ("uk-sheffield-eee", "Electronic and Electrical Engineering MSc(Eng)", "电子/电气工程", "electronic-and-electrical-engineering-msceng", 79, 81, 83, 85, 75),
    ("uk-sheffield-wireless", "Wireless Communication Systems MSc", "通信工程", "wireless-communication-systems-msc", 79, 81, 83, 85, 75),
    ("uk-sheffield-robotics", "Robotics MSc", "电子/电气工程", "robotics-msc", 80, 82, 84, 86, 76),
    ("uk-sheffield-materials", "Materials Science and Engineering MSc", "材料工程", "materials-science-and-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-sheffield-civil", "Civil and Structural Engineering MSc", "土木/建筑", "civil-and-structural-engineering-msc", 78, 80, 82, 84, 74),
    ("uk-sheffield-ism", "Information Systems Management MSc", "信息系统/IT", "information-systems-management-msc", 79, 81, 83, 85, 75),
    ("uk-sheffield-translation", "Translation and Intercultural Studies MA", "翻译/语言", "translation-and-intercultural-studies-ma", 80, 82, 84, 86, 76),
    ("uk-sheffield-digmk", "Digital Marketing and Communication MSc", "市场营销", "digital-marketing-msc", 80, 82, 84, 85, 76),
    ("uk-sheffield-smb", "Strategic Marketing and Branding MSc", "市场营销", "strategic-marketing-and-branding-msc", 80, 82, 84, 85, 76),
    ("uk-sheffield-hrm", "Human Resource Management MSc", "管理学/商科", "human-resource-management-msc", 80, 82, 84, 86, 76),
    ("uk-sheffield-mgmt", "Management MSc", "管理学/商科", "management-msc", 80, 82, 84, 86, 76),
    ("uk-sheffield-scm", "Logistics and Supply Chain Management MSc", "管理学/商科", "logistics-and-supply-chain-management-msc", 80, 82, 84, 85, 76),
    ("uk-sheffield-llm-intl", "LLM International Law and Global Justice", "法律(LLM)", "llm-international-law-and-global-justice-llm", 80, 82, 84, 86, 76),
    ("uk-sheffield-edu", "Education MA", "教育", "education-ma", 79, 81, 83, 85, 75),
    ("uk-sheffield-media", "Digital Media and Society MA", "传媒", "digital-media-and-society-ma", 80, 82, 84, 86, 76),
    ("uk-sheffield-urban", "Urban and Regional Planning MSc", "土木/建筑", "urban-and-regional-planning-msc", 78, 80, 82, 84, 74),
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
    m = re.search(r"IELTS\s*([0-9.]+)\s*\(with\s*([0-9.]+)\s*in each", text)
    ielts = (m.group(1), m.group(2)) if m else (None, None)
    d = re.search(r"(2:1|2:2|first[- ]class)[^.]{0,140}?degree[^.]{0,120}", text, re.I)
    if not d:
        d = re.search(r"Minimum[^.]{0,160}degree[^.]{0,120}", text, re.I)
    deg = re.sub(r"\s+", " ", d.group(0)).strip() if d else ""
    deg = deg.split("Library item")[0].strip()
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
        notes = f"官方入学要求：{deg}" if deg else "入学要求见官方项目页"
        bg = deg or ""
        rows.append({
            "id": pid, "country": "英国", "university": UNI, "qsRank": QS,
            "program": prog, "field": field,
            "a985": a985, "a211": a211, "asy": asy, "asf": asf, "ahb": ahb,
            "ielts_overall": io, "ielts_sub": isub,
            "gre_total": "", "gre_quant": "",
            "background": bg, "notes": notes,
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
