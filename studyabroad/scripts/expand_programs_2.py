#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二批扩充：补全 CS/数据科学/AI、传媒、法律、教育、工科等集群 + 更多学校（含美国）。
分数线为公开经验参考线，非官方保证。按 id/(校,项目) 去重，可重复运行。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "programs.json")
data = json.load(open(PATH, encoding="utf-8"))
programs = data["programs"]
ids = {p["id"] for p in programs}
pairs = {(p["university"], p["program"]) for p in programs}


def req(a985, a211, asy, asf, ahb, io=6.5, isub=6.0, gre=None, bg="", notes=""):
    return {"avgByTier": {"985": a985, "211": a211, "双一流": asy, "双非": asf, "海本/中外合作": ahb},
            "ielts": {"overall": io, "sub": isub}, "gre": gre, "background": bg, "notes": notes}


TUI = {"英国": "约 25–38 万元 / 1年", "中国香港": "约 14–28 万元 / 1年", "新加坡": "约 18–32 万元 / 1–1.5年",
       "澳大利亚": "约 20–35 万元 / 1.5–2年", "美国": "约 35–60 万元 / 1–2年"}
DUR = {"英国": "1 年", "中国香港": "1 年", "新加坡": "1–1.5 年", "澳大利亚": "1.5–2 年", "美国": "1–2 年"}
TL = {"英国": "每年 9–10 月开放，滚动录取先到先得，建议 10–12 月递交",
      "中国香港": "每年 9 月开放，多轮截止，建议首轮（10–12 月）递交",
      "新加坡": "每年 10–11 月开放，建议次年 1–2 月前递交",
      "澳大利亚": "多为两次入学（2 月 / 7 月），常年滚动审理",
      "美国": "每年 9 月开放，截止 12 月–次年 1 月，部分有早申轮次"}

NEW = [
    # ============ 计算机 / 数据科学 / AI（英国补强）============
    ("uk-ic-cs", "英国", "帝国理工学院", 2, "Computing (MSc)", "计算机/CS",
     req(84, 86, 88, 89, 79, 6.5, 6.0, None, "需 CS/数理背景", "帝国 Computing 极卷，偏好科研/竞赛")),
    ("uk-ic-ml", "英国", "帝国理工学院", 2, "Machine Learning & Data Science MSc", "数据科学/AI",
     req(84, 86, 88, 89, 79, 6.5, 6.0, None, "需强编程 + 数理背景", "")),
    ("uk-ic-ai", "英国", "帝国理工学院", 2, "Artificial Intelligence MSc", "数据科学/AI",
     req(84, 86, 88, 89, 79, 6.5, 6.0, None, "需 CS/数理背景", "")),
    ("uk-ucl-ds", "英国", "伦敦大学学院 UCL", 9, "Data Science & Machine Learning MSc", "数据科学/AI",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需编程 + 数理背景", "")),
    ("uk-ucl-ai", "英国", "伦敦大学学院 UCL", 9, "Machine Learning MSc", "数据科学/AI",
     req(84, 86, 88, 89, 79, 6.5, 6.0, None, "需强数理 + 编程背景", "UCL ML 顶尖，竞争激烈")),
    ("uk-ed-ai", "英国", "爱丁堡大学", 27, "Artificial Intelligence MSc", "数据科学/AI",
     req(81, 84, 85, 87, 77, 6.5, 6.0, None, "需 CS/数理背景", "爱丁堡 AI 老牌强校")),
    ("uk-ed-ds", "英国", "爱丁堡大学", 27, "Data Science MSc", "数据科学/AI",
     req(81, 84, 85, 87, 77, 6.5, 6.0, None, "需编程 + 数理基础", "")),
    ("uk-man-cs", "英国", "曼彻斯特大学", 34, "Computer Science MSc", "计算机/CS",
     req(81, 84, 85, 87, 77, 6.5, 6.0, None, "需 CS 背景", "")),
    ("uk-man-ds", "英国", "曼彻斯特大学", 34, "Data Science MSc", "数据科学/AI",
     req(81, 84, 85, 87, 77, 6.5, 6.0, None, "需编程 + 数理基础", "")),
    ("uk-kcl-ai", "英国", "伦敦国王学院 KCL", 40, "Artificial Intelligence MSc", "数据科学/AI",
     req(81, 84, 85, 87, 77, 6.5, 6.0, None, "需 CS/数理背景", "")),
    ("uk-bristol-cs", "英国", "布里斯托大学", 54, "Computer Science (Conversion) MSc", "计算机/CS",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "转专业友好", "可接受非 CS 背景转码")),
    ("uk-glasgow-cs", "英国", "格拉斯哥大学", 76, "Computing Science MSc", "计算机/CS",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "需相关背景", "")),
    ("uk-southampton-ai", "英国", "南安普顿大学", 80, "Artificial Intelligence MSc", "数据科学/AI",
     req(77, 80, 82, 84, 73, 6.5, 6.0, None, "需 CS/数理背景", "")),

    # ============ 计算机 / 数据科学 / AI（美国）============
    ("us-cmu-mscs", "美国", "卡内基梅隆大学 CMU", 52, "Master of Computer Science", "计算机/CS",
     req(86, 88, 89, 91, 81, 7.0, 6.5, {"total": 325, "quant": 167}, "需 CS 背景 + 科研/项目", "CMU CS 顶级，竞争极激烈")),
    ("us-cmu-msml", "美国", "卡内基梅隆大学 CMU", 52, "Master of Science in Machine Learning", "数据科学/AI",
     req(87, 89, 90, 92, 82, 7.0, 6.5, {"total": 327, "quant": 168}, "需强数理 + 编程 + 科研", "")),
    ("us-columbia-cs", "美国", "哥伦比亚大学", 34, "Computer Science MS", "计算机/CS",
     req(84, 86, 88, 89, 79, 7.0, 6.5, {"total": 320, "quant": 165}, "需 CS 背景", "")),
    ("us-cornell-cs", "美国", "康奈尔大学", 16, "Computer Science MEng", "计算机/CS",
     req(84, 86, 88, 89, 79, 7.0, 6.5, {"total": 320, "quant": 165}, "需 CS 背景", "")),
    ("us-cornell-ds", "美国", "康奈尔大学", 16, "Applied Statistics / Data Science MPS", "数据科学/AI",
     req(83, 85, 87, 88, 78, 7.0, 6.5, {"total": 318, "quant": 165}, "需数理 + 编程背景", "")),
    ("us-uiuc-cs", "美国", "伊利诺伊大学香槟分校 UIUC", 64, "Computer Science MCS", "计算机/CS",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需 CS 背景", "UIUC CS 强校，MCS 偏授课")),
    ("us-usc-cs", "美国", "南加州大学 USC", 121, "Computer Science MS", "计算机/CS",
     req(82, 84, 86, 88, 78, 7.0, 6.5, {"total": 315, "quant": 162}, "需 CS 背景", "")),
    ("us-nyu-cs", "美国", "纽约大学 NYU", 38, "Computer Science MS", "计算机/CS",
     req(83, 85, 87, 88, 78, 7.0, 6.5, {"total": 318, "quant": 164}, "需 CS 背景", "")),
    ("us-umich-ds", "美国", "密歇根大学安娜堡分校", 44, "Data Science MS", "数据科学/AI",
     req(84, 86, 88, 89, 79, 7.0, 6.5, {"total": 320, "quant": 165}, "需数理 + 编程背景", "")),

    # ============ 计算机 / 数据科学（港新澳补强）============
    ("hk-cuhk-ai", "中国香港", "香港中文大学 CUHK", 36, "Artificial Intelligence MSc", "数据科学/AI",
     req(81, 84, 86, 88, 77, 6.5, 6.0, None, "需 CS/数理背景", "")),
    ("hk-hkust-ai", "中国香港", "香港科技大学 HKUST", 47, "Artificial Intelligence MSc", "数据科学/AI",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需 CS/数理背景", "")),
    ("hk-cityu-ds", "中国香港", "香港城市大学 CityU", 62, "Data Science MSc", "数据科学/AI",
     req(77, 80, 82, 85, 73, 6.5, 6.0, None, "需数理 + 编程基础", "")),
    ("sg-ntu-ai", "新加坡", "南洋理工大学 NTU", 15, "Artificial Intelligence MSc", "数据科学/AI",
     req(82, 85, 87, 88, 78, 6.5, 6.0, None, "需 CS/数理背景", "")),
    ("sg-nus-ds", "新加坡", "新加坡国立大学 NUS", 8, "Data Science & Machine Learning MSc", "数据科学/AI",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需编程 + 数理背景", "")),
    ("au-unimelb-ds", "澳大利亚", "墨尔本大学", 13, "Master of Data Science", "数据科学/AI",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需数理 + 编程基础", "")),

    # ============ 传媒 / 新闻 ============
    ("uk-lse-media", "英国", "伦敦政治经济学院 LSE", 50, "Media & Communications MSc", "传媒",
     req(82, 84, 86, 88, 78, 7.0, 6.5, None, "传媒/社科背景", "LSE 传媒，看重写作与社科基础")),
    ("uk-leeds-media", "英国", "利兹大学", 82, "Communication & Media MA", "传媒",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "传媒/文科背景", "利兹传媒老牌强")),
    ("uk-cardiff-journ", "英国", "卡迪夫大学", 165, "International Journalism MA", "传媒",
     req(76, 79, 81, 84, 72, 7.0, 6.5, None, "新闻/传媒背景", "卡迪夫新闻学院顶尖")),
    ("uk-westminster-media", "英国", "威斯敏斯特大学", 600, "Media & Communications MA", "传媒",
     req(72, 75, 78, 81, 68, 6.5, 6.0, None, "传媒/文科背景", "")),
    ("hk-hku-journ", "中国香港", "香港大学 HKU", 17, "Journalism MJ", "传媒",
     req(80, 83, 85, 87, 76, 7.0, 6.5, None, "新闻/传媒背景", "港大新闻 MJ 实务导向")),
    ("hk-cuhk-comm", "中国香港", "香港中文大学 CUHK", 36, "Communication MA / Global Communication", "传媒",
     req(79, 82, 84, 86, 75, 6.5, 6.0, None, "传媒/社科背景", "")),

    # ============ 法律 LLM ============
    ("uk-ucl-llm", "英国", "伦敦大学学院 UCL", 9, "Master of Laws LLM", "法律(LLM)",
     req(82, 85, 86, 88, 78, 7.0, 6.5, None, "需法律本科（LLB）", "UCL LLM，雅思小分写作要求高")),
    ("uk-kcl-llm", "英国", "伦敦国王学院 KCL", 40, "Master of Laws LLM", "法律(LLM)",
     req(81, 84, 85, 87, 77, 7.5, 6.5, None, "需法律本科", "KCL 法学院强，语言要求高")),
    ("uk-edinburgh-llm", "英国", "爱丁堡大学", 27, "Master of Laws LLM", "法律(LLM)",
     req(80, 83, 85, 87, 76, 7.0, 6.5, None, "需法律本科", "")),
    ("hk-cuhk-llm", "中国香港", "香港中文大学 CUHK", 36, "Master of Laws LLM", "法律(LLM)",
     req(79, 82, 84, 86, 75, 7.0, 6.5, None, "需法律本科", "")),
    ("sg-nus-llm", "新加坡", "新加坡国立大学 NUS", 8, "Master of Laws LLM", "法律(LLM)",
     req(83, 85, 87, 88, 78, 7.0, 6.5, None, "需法律本科 + 排名靠前", "NUS 法学院亚洲顶尖")),

    # ============ 教育 ============
    ("uk-ucl-edu", "英国", "伦敦大学学院 UCL", 9, "Education MA (IOE)", "教育",
     req(80, 83, 85, 87, 76, 7.0, 6.5, None, "教育/文科背景", "UCL IOE 教育学全球第一")),
    ("uk-ucl-tesol", "英国", "伦敦大学学院 UCL", 9, "TESOL MA", "教育",
     req(80, 83, 85, 87, 76, 7.0, 6.5, None, "英语/教育背景", "对英语能力要求高")),
    ("uk-edinburgh-tesol", "英国", "爱丁堡大学", 27, "TESOL MSc", "教育",
     req(78, 81, 83, 85, 74, 7.0, 6.5, None, "英语/教育背景", "")),
    ("hk-hku-edu", "中国香港", "香港大学 HKU", 17, "Master of Education", "教育",
     req(79, 82, 84, 86, 75, 7.0, 6.0, None, "教育/相关背景", "")),
    ("hk-cuhk-tesol", "中国香港", "香港中文大学 CUHK", 36, "English (Applied Linguistics) MA / TESOL", "教育",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "英语/语言背景", "")),

    # ============ 工科：EE / 机械 / 土木 ============
    ("uk-ic-eee", "英国", "帝国理工学院", 2, "Electrical & Electronic Engineering MSc", "电子/电气工程",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需 EE 背景", "")),
    ("uk-ic-me", "英国", "帝国理工学院", 2, "Mechanical Engineering MSc", "机械工程",
     req(83, 85, 87, 88, 78, 6.5, 6.0, None, "需机械/工科背景", "")),
    ("uk-ucl-civil", "英国", "伦敦大学学院 UCL", 9, "Civil Engineering MSc", "土木/建筑",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需土木/工科背景", "")),
    ("uk-manchester-me", "英国", "曼彻斯特大学", 34, "Mechanical Engineering MSc", "机械工程",
     req(79, 82, 84, 86, 75, 6.5, 6.0, None, "需机械/工科背景", "")),
    ("hk-hkust-eee", "中国香港", "香港科技大学 HKUST", 47, "Electronic Engineering MSc", "电子/电气工程",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "需 EE 背景", "")),
    ("sg-nus-eee", "新加坡", "新加坡国立大学 NUS", 8, "Electrical Engineering MSc", "电子/电气工程",
     req(81, 84, 86, 88, 77, 6.5, 6.0, None, "需 EE 背景", "")),
    ("au-unsw-civil", "澳大利亚", "新南威尔士大学 UNSW", 19, "Master of Engineering (Civil)", "土木/建筑",
     req(76, 79, 81, 84, 72, 6.5, 6.0, None, "需土木/工科背景", "")),

    # ============ 心理 / 市场营销 / 管理（补强）============
    ("uk-ucl-psych", "英国", "伦敦大学学院 UCL", 9, "Cognitive & Decision Sciences MSc", "心理学",
     req(81, 84, 85, 87, 77, 7.0, 6.5, None, "心理/认知/社科背景", "")),
    ("hk-cuhk-psych", "中国香港", "香港中文大学 CUHK", 36, "Psychology MSc", "心理学",
     req(80, 83, 85, 87, 76, 6.5, 6.0, None, "心理学背景", "")),
    ("uk-leeds-marketing", "英国", "利兹大学", 82, "Marketing MSc", "市场营销",
     req(78, 81, 83, 85, 74, 6.5, 6.0, None, "商科/传媒背景", "")),
    ("uk-warwick-mktg", "英国", "华威大学", 67, "Marketing & Strategy MSc", "市场营销",
     req(81, 83, 85, 87, 77, 7.0, 6.5, None, "商科背景", "WBS 市场营销")),
    ("sg-nus-mgmt", "新加坡", "新加坡国立大学 NUS", 8, "Management MSc", "管理学/商科",
     req(82, 84, 86, 88, 78, 6.5, 6.0, None, "商科/社科背景", "")),
]


def build(country, qs, uni, program, field, requirements):
    return {"country": country, "university": uni, "qsRank": qs, "program": program,
            "field": field, "degree": "硕士", "requirements": requirements,
            "tuition": TUI.get(country, "学费见官网"), "duration": DUR.get(country, ""),
            "timeline": TL.get(country, "申请时间见官网")}


added = skipped = 0
for pid, country, uni, qs, program, field, requirements in NEW:
    if pid in ids or (uni, program) in pairs:
        skipped += 1
        continue
    entry = {"id": pid}
    entry.update(build(country, qs, uni, program, field, requirements))
    programs.append(entry)
    ids.add(pid)
    pairs.add((uni, program))
    added += 1

data["meta"]["count"] = len(programs)
json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"新增 {added} 个，跳过 {skipped} 个，现共 {len(programs)} 个项目")
