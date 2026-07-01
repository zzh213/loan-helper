# 真实数据接入（官方核实）

本目录用于把**从学校官方项目页核实**的数据导入项目库，并将对应项目标记为
「官方核实」(✔)，与「参考估算」区分开，逐步提升数据准确度。

## 工作流

1. **打开官方项目页**（如 `https://www.gla.ac.uk/postgraduate/taught/dataanalytics/`），
   抄录：入学要求 / 雅思小分 / 学费 / 时长 / 申请截止时间。
2. **填入 CSV**（`programs_verified.csv` 或新建 `xxx.csv`），一行一个项目。
   - `id`：与库中一致则**更新**该项目；不存在则**新增**。
   - 均分门槛列（a985/a211/asy/asf/ahb）留空则沿用原值/默认。
   - `gre_total` 留空表示该项目不要求 GRE。
   - `sourceUrl` + `lastVerified`(YYYY-MM) 为标记「官方核实」的依据，**必填**。
3. **运行导入**：

   ```bash
   cd studyabroad
   python3 scripts/ingest.py
   ```

   脚本会校验、规范化并合并进 `data/programs.json`，统计新增/更新数与已核实总数。

## CSV 列说明

| 列 | 含义 | 必填 |
|----|------|------|
| id | 项目唯一 ID（如 `uk-glasgow-da`） | ✔ |
| country | 国家/地区 | ✔ |
| university | 学校名 | ✔ |
| qsRank | QS 排名（数字） | |
| program | **真实项目名**（如 `Data Analytics MSc`） | ✔ |
| field | 方向分类（见 meta.fields） | ✔ |
| a985,a211,asy,asf,ahb | 各院校层次建议均分门槛 | |
| ielts_overall, ielts_sub | 雅思总分/小分 | |
| gre_total, gre_quant | GRE 总分/数学（不要求则留空） | |
| background | 背景要求文字 | |
| notes | 备注/提示 | |
| tuition, duration, timeline | 学费/时长/申请时间线 | |
| sourceUrl | 官方项目页 URL | ✔ |
| lastVerified | 核实年月 YYYY-MM | ✔ |

## 进阶：批量/自动化

- 可写脚本用 `web_fetch`/爬虫逐项抓取官方页，产出符合上表的 CSV，再走本管道导入。
- 注意遵守各校 robots/使用条款；分数线类信息以「建议参考线」呈现，最终以官网为准。
