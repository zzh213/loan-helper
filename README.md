---
title: 中小微企业贷款服务小助手
emoji: 💰
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 8000
pinned: false
---

# 中小微企业贷款服务小助手

一个面向中小微企业的网页版贷款服务小助手。用户填写企业实际情况(行业、营收、征信、抵押、纳税、贷款需求等),系统智能匹配贷款产品,综合打分排序,给出**最优方案 + 备选方案**,并附额度/利率/月供估算、推荐理由、注意事项和资质提升建议。

> 📖 **产品经理视角的完整叙事**(定位 / 用户洞察 / 商业模式 / 指标体系 / 数据护城河):见 [docs/产品故事线.md](docs/产品故事线.md)
>
> 🎓 **实习结项答辩材料**:[结项答辩报告](docs/实习结项答辩报告.md)（[Word](docs/实习结项答辩报告.docx)） · [答辩 PPT 大纲 + 逐页口述稿](docs/答辩演示脚本.md)（[Word](docs/答辩演示脚本.docx)）

## 功能特点

- 📋 **企业情况采集**:行业、经营年限、年营业额、注册资本、征信、抵押物、纳税/开票、贷款金额/用途/期限、是否急用
- 🧠 **智能推荐引擎**:产品准入判断 → 额度估算 → 利率匹配(征信越好越接近下限)→ 综合打分排序
- 🛡️ **精细化风控模型**:基于征信、逾期、经营年限、营收规模、负债杠杆、抵押、纳税、行业风险等 8+ 维度计算综合风控评分(0-100)与风险等级(A-E),输出风险因子明细,并反哺额度/利率/通过率
- 🎯 **个性化融资建议**:结合行业、规模、用途、风险画像生成定制化融资规划与服务建议
- 🏛️ **补贴政策匹配**:内置普惠贴息、科技研发、创业担保、稳岗扩岗、技改奖补、税费减免等扶持政策库,按企业情况自动匹配可申报政策与申请要点
- 📄 **一键导出 PDF / Excel**:生成包含企业画像、风控评估、推荐方案、个性化建议、补贴政策的完整方案报告。PDF 适合打印存档(支持中文);Excel 按工作表分类(方案概览/企业画像/推荐方案/风控评估/个性化建议/扶持政策/提升建议),便于二次编辑与数据分析
- 📁 **申请记录管理**:保存匹配结果为申请记录,支持列表查看、详情查看、状态流转(待提交→已提交→审核中→已通过/已拒绝→已放款)、导出 PDF/Excel 与删除,数据持久化到 SQLite
- 🤖 **虚拟金融顾问**:右下角浮动虚拟人,可对话式解答贷款与金融问题(征信、利率、额度、抵押、纳税、补贴、防范诈骗等)。接入通义千问大模型(配置 API Key 后),未配置时自动降级到内置金融知识库,流式输出体验
  - 🎤 **语音输入**:点击麦克风用普通话语音提问(浏览器原生语音识别,Chrome/Edge/Safari 支持)
  - 🔊 **语音朗读**:可开启 TTS 自动朗读顾问回复
  - 🧑‍🚀 **形象库 + 自定义形象**:内置 8 款虚拟人形象供客户自选(🧑‍💼 专业顾问 / 👩‍💼 女顾问 / 🐣 招财吉祥物 / 🤖 智能机器人 / 🐶 西高地小狗 / 🐼 招财熊猫 / 🧧 财神福星 / 🐱 布朗小猫);还可点 ✏️ 自定义专属形象(主色调、眼睛颜色、头型、可多选搭配的配饰——眼镜/墨镜/滑雪镜/头盔/礼帽/围巾/领带/领结/耳机、昵称),选择会被记住;所有形象均带待机呼吸、眨眼、思考、说话(嘴型同步)等状态动画
  - 🕑 **对话记录**:所有对话自动存入数据库,可查看/加载/删除历史会话,支持新建对话
- 🎮 **金融知识闯关游戏**:5 个难度关卡(金融小白→入门学徒→理财能手→投资达人→金融大师)、共 50 道判断题与单选题题库,涵盖贷款常识、利率换算、财务指标、风控、反诈防骗、政策红利等;答对得金币、连续答对有连胜提示,**答错(或答对)后均会弹出「📚 知识科普」延伸讲解**,寓教于乐;金币累计自动升级解锁称号,实时显示等级进度/正确率/最佳连胜,并有金币排行榜(可设置昵称),进度持久化到 SQLite
- 💡 **资质提升建议**:针对薄弱项给出可执行的优化建议
- 🏦 **多类型产品库**:普惠信用贷、互联网流水贷、银税互动贷、抵押经营贷、设备分期、小贷应急贷

## 技术栈

- 后端:Python + FastAPI + uvicorn
- 前端:HTML + CSS + 原生 JavaScript(单页)
- 数据:内置贷款产品库(`backend/products.py`,可替换为数据库或对接真实银行 API)

## 目录结构

```
zihan/
├── backend/
│   ├── main.py          # FastAPI 应用入口 + API + 静态页面托管
│   ├── models.py        # 请求/响应数据模型(Pydantic)
│   ├── products.py      # 贷款产品库
│   ├── recommender.py   # 推荐 / 打分引擎
│   ├── risk.py          # 精细化风控模型
│   ├── subsidies.py     # 补贴政策库与匹配
│   ├── pdf_export.py    # PDF 方案报告生成(reportlab)
│   ├── excel_export.py  # Excel 方案报告生成(openpyxl)
│   ├── storage.py       # 申请记录 + 闯关游戏进度持久化(SQLite)
│   ├── quiz.py          # 金融知识闯关题库与等级体系
│   └── chatbot.py       # 虚拟金融顾问(通义千问 + 内置知识库降级)
├── frontend/
│   ├── index.html       # 页面
│   ├── style.css        # 样式
│   ├── avatars.js       # 虚拟人形象库(8 款预设 + 自定义生成器)
│   └── app.js           # 交互逻辑
├── requirements.txt
└── README.md
```

## 快速开始

1. 安装依赖:

   ```bash
   pip3 install -r requirements.txt
   ```

2. 启动服务:

   ```bash
   cd backend
   python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. 浏览器打开:<http://127.0.0.1:8000/>

或一键启动:`./start.sh`

## 部署(Docker)

项目已内置 `Dockerfile`,可容器化部署:

```bash
# 构建镜像
docker build -t weidaiguanjia .

# 运行(挂载数据库以持久化申请记录)
docker run -d -p 8000:8000 \
  -v $(pwd)/backend/applications.db:/app/backend/applications.db \
  --name weidaiguanjia weidaiguanjia
```

访问 <http://localhost:8000/>。如需接入大模型,通过 `-e DASHSCOPE_API_KEY=sk-xxx` 注入环境变量即可。

## 虚拟金融顾问(可选接入大模型)

虚拟人「小微贷管家」默认使用**内置金融知识库**回答,开箱即用。如需更智能的对话,可接入通义千问大模型:

```bash
export DASHSCOPE_API_KEY="你的通义千问API Key"   # 阿里云 DashScope
export QWEN_MODEL="qwen-plus"                     # 可选,默认 qwen-plus
cd backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

- API Key 通过环境变量读取,**不写入代码**,更安全。
- 未配置 Key 或调用失败时,自动降级到内置知识库,不影响使用。
- DashScope 申请地址:<https://dashscope.console.aliyun.com/>

## API 说明

### `POST /api/recommend`

请求体(JSON):

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| industry | string | 所属行业 |
| years_in_business | number | 经营年限(年) |
| annual_revenue | number | 年营业额(万元) |
| registered_capital | number | 注册资本(万元) |
| employees | int | 员工人数 |
| credit_level | string | 征信:excellent/good/fair/poor |
| has_overdue | bool | 当前是否逾期 |
| has_collateral | bool | 是否有抵押物 |
| collateral_value | number | 抵押物估值(万元) |
| has_tax_record | bool | 是否有连续纳税记录 |
| has_invoice | bool | 是否有稳定开票流水 |
| loan_amount | number | 期望贷款金额(万元) |
| loan_purpose | string | working_capital/equipment/expansion/inventory/rd/other |
| preferred_term_months | int | 期望期限(月) |
| urgent | bool | 是否急需放款 |

响应体:匹配总结、企业画像要点、提升建议、推荐方案列表(含匹配分、额度、利率、月供等)。

### `GET /api/health`

健康检查,返回 `{"status": "ok"}`。

### `POST /api/export/pdf`

请求体同 `/api/recommend`,返回 PDF 文件(`application/pdf`),内容为完整的贷款方案报告。

### `POST /api/export/excel`

请求体同 `/api/recommend`,返回 Excel 文件(`.xlsx`),按工作表分类展示完整方案。

### 申请记录

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/applications` | 保存申请记录(请求体 `{"profile": {...}}`,自动跑推荐并存档) |
| GET | `/api/applications` | 获取全部申请记录列表 |
| GET | `/api/applications/{id}` | 获取单条记录详情(含企业信息与方案结果) |
| PATCH | `/api/applications/{id}/status` | 更新状态(`{"status": "审核中"}`) |
| POST | `/api/applications/{id}/pdf` | 根据记录生成 PDF |
| POST | `/api/applications/{id}/excel` | 根据记录生成 Excel |
| DELETE | `/api/applications/{id}` | 删除记录 |

申请状态:`待提交 / 已提交 / 审核中 / 已通过 / 已拒绝 / 已放款`。数据存储于 `backend/applications.db`(SQLite,自动创建)。

### 虚拟金融顾问

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/chat/status` | 返回是否已接入大模型(`{"llm_enabled": bool}`) |
| POST | `/api/chat` | 对话接口,请求体 `{"message": "...", "history": [...], "session_id": "..."}`,SSE 流式返回(首帧返回 `session_id`),对话自动存入数据库 |
| GET | `/api/chat/sessions` | 返回所有历史会话摘要列表 |
| GET | `/api/chat/history/{session_id}` | 返回指定会话的全部消息 |
| DELETE | `/api/chat/history/{session_id}` | 删除指定会话 |

### 金融知识闯关游戏

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/quiz/levels` | 返回 5 个关卡及题量 |
| GET | `/api/quiz/questions?level=&count=` | 抽取题目(不含答案,`level=0` 为跨关卡混合) |
| GET | `/api/quiz/progress/{player_id}` | 获取玩家金币/等级/正确率/连胜进度 |
| POST | `/api/quiz/answer` | 提交答案(服务端校验),请求体 `{"player_id","question_id","choice","streak"}`,返回对错/解析/知识科普(`knowledge`)/奖励金币/最新进度 |
| POST | `/api/quiz/nickname` | 设置玩家昵称(用于排行榜) |
| GET | `/api/quiz/leaderboard?limit=` | 金币排行榜 |

等级体系:🌱 金融小白(0) → 📘 入门学徒(60) → 💡 理财能手(160) → 🚀 投资达人(320) → 👑 金融大师(560),括号为累计金币门槛。玩家以浏览器本地生成的 `player_id` 标识,进度存储于 `backend/applications.db` 的 `quiz_players` 表。

## 免责声明

本工具提供的额度、利率、月供均为基于公开规则的**估算**,仅供参考,实际以金融机构审批结果为准。

## 扩展方向

- 将 `products.py` 中的产品库替换为数据库或对接真实银行/助贷平台 API
- 增加用户账号体系与申请记录留存
- 引入更精细的风控评分模型(如行业风险系数、负债率、流水真实性校验)
