/**
 * 选校匹配算法
 * 输入用户背景，输出按「冲刺 / 匹配 / 保底」分档的项目列表，并标注差距。
 */

const TIER_DEFAULT = "双非";

const TOP_EMPLOYERS = [
  "腾讯", "阿里", "字节", "抖音", "华为", "百度", "美团", "京东", "网易", "小米",
  "蚂蚁", "快手", "拼多多", "携程", "滴滴", "商汤", "旷视", "大疆",
  "google", "microsoft", "amazon", "apple", "meta", "facebook", "ibm", "intel", "nvidia",
  "麦肯锡", "贝恩", "波士顿", "bcg", "普华永道", "德勤", "安永", "毕马威", "四大",
  "高盛", "摩根", "中金", "中信", "招商", "goldman", "morgan",
];
function isTopEmployer(name) {
  const s = (name || "").toLowerCase();
  return TOP_EMPLOYERS.some((e) => s.includes(e.toLowerCase()));
}

/**
 * 计算软实力背景（实习/论文/竞赛/科研/工作经验/证书）的竞争力加成。
 * 兼容两种实习写法：internshipList[{company,role,desc}] 或 internships(数字)+internshipTop。
 * @returns {object} { score:0-100, boost:均分等效加成, level, highlights:[] }
 */
function computeSoftBackground(soft) {
  if (!soft) return { score: 0, boost: 0, level: "未填写", highlights: [] };
  let boost = 0;
  const hl = [];

  // 实习
  const list = Array.isArray(soft.internshipList)
    ? soft.internshipList.filter((x) => x && (x.company || x.role || x.desc))
    : [];
  const internCount = list.length || soft.internships || 0;
  const internTop =
    soft.internshipTop || list.some((x) => isTopEmployer(x.company));
  if (internCount > 0) {
    let v = Math.min(internCount, 3) * 1;
    if (internTop) v += 0.8;
    boost += v;
    hl.push(`${internCount} 段实习${internTop ? "（含名企/大厂）" : ""}`);
  }

  const paperW = { "SCI/EI": 4, 核心: 2.5, 会议: 1.5, 在投: 0.8 }[soft.paperLevel] || 0;
  if ((soft.papers || 0) > 0 && paperW) {
    boost += Math.min(soft.papers, 3) * paperW;
    hl.push(`${soft.papers} 篇${soft.paperLevel}论文`);
  }
  const compW = { "国际/国家级": 2.5, 省级: 1.2, 校级: 0.4 }[soft.competitionLevel] || 0;
  if ((soft.competitions || 0) > 0 && compW) {
    boost += Math.min(soft.competitions, 3) * compW;
    hl.push(`${soft.competitions} 项${soft.competitionLevel}竞赛获奖`);
  }
  if ((soft.research || 0) > 0) {
    boost += Math.min(soft.research, 2) * 1;
    hl.push(`${soft.research} 段科研经历`);
  }
  if ((soft.workYears || 0) > 0) {
    boost += Math.min(soft.workYears, 4) * 0.5;
    hl.push(`${soft.workYears} 年工作经验`);
  }

  // 项目 / 校园活动 / 交换经历（各有上限，权重低于实习/论文）
  const countFilled = (arr) =>
    (Array.isArray(arr) ? arr : []).filter(
      (x) => x && Object.values(x).some((v) => (v || "").toString().trim())
    ).length;
  const projN = countFilled(soft.projectList);
  if (projN > 0) {
    boost += Math.min(projN, 3) * 0.6;
    hl.push(`${projN} 个项目经历`);
  }
  const actN = countFilled(soft.activityList);
  if (actN > 0) {
    boost += Math.min(actN, 2) * 0.4;
    hl.push(`${actN} 项校园活动`);
  }
  const exN = countFilled(soft.exchangeList);
  if (exN > 0) {
    boost += Math.min(exN, 2) * 0.7;
    hl.push(`${exN} 段交换/海外经历`);
  }

  // 证书
  const certs = (soft.certificates || "")
    .split(/[\n;,，；]/)
    .map((c) => c.trim())
    .filter(Boolean);
  if (certs.length) {
    boost += Math.min(certs.length, 3) * 0.5;
    hl.push(`${certs.length} 项证书`);
  }

  boost = Math.min(boost, 6); // 加成上限：最多等效 +6 分均分
  const score = Math.round((boost / 6) * 100);
  const level = score >= 70 ? "强" : score >= 35 ? "中等" : score > 0 ? "一般" : "未填写";
  return { score, boost: Math.round(boost * 10) / 10, level, highlights: hl };
}

/**
 * 计算某个项目对用户的匹配结果
 * @param {object} program 项目数据
 * @param {object} profile 用户背景 { tier, avg, ielts:{overall,sub}, gre:{total,quant}, field, soft }
 * @returns {object|null} 匹配明细；若专业完全不符或差距过大则可能返回 category="超出"
 */
function evaluateProgram(program, profile) {
  const req = program.requirements;
  const tier = profile.tier || TIER_DEFAULT;

  const requiredAvg =
    (req.avgByTier && (req.avgByTier[tier] ?? req.avgByTier[TIER_DEFAULT])) || 80;

  const soft = profile._soft || computeSoftBackground(profile.soft);
  const avgGap = (profile.avg ?? 0) - requiredAvg; // 正数=高于门槛
  const effGap = avgGap + soft.boost; // 软背景加成后的有效差距

  // 语言成绩判断
  const ieltsReq = req.ielts || { overall: 6.5, sub: 6.0 };
  const userOverall = profile.ielts?.overall ?? 0;
  const userSub = profile.ielts?.sub ?? userOverall;
  const ieltsOverallOk = userOverall >= ieltsReq.overall;
  const ieltsSubOk = userSub >= ieltsReq.sub;
  const ieltsProvided = userOverall > 0;
  const ieltsOk = !ieltsProvided || (ieltsOverallOk && ieltsSubOk);

  // GRE：仅当项目要求且用户提供时参与判断（不提供不直接淘汰，但会提示）
  // gre 可能是结构化 {total} 要求，或自由文本（如 "GRE 建议"）。
  // 仅结构化数值要求才做硬性比较，文本型只作提示。
  const greRaw = req.gre || null;
  const greReq = greRaw && typeof greRaw === "object" ? greRaw : null;
  const greNote = typeof greRaw === "string" ? greRaw : null;
  const userGre = profile.gre?.total ?? 0;
  const greProvided = userGre > 0;
  const greOk = !greReq || !greProvided || userGre >= greReq.total;

  // 分档逻辑（用软背景加成后的有效差距）
  let category;
  if (effGap >= 3) category = "保底";
  else if (effGap >= 0) category = "匹配";
  else if (effGap >= -3) category = "冲刺";
  else category = "超出"; // 差距过大

  // 语言不达标会下调档位
  const warnings = [];
  const coop = profile.coop || null;
  const langWaivable = !!(coop && coop.englishTaught); // 全英文授课海外学位通常可豁免语言
  if (ieltsProvided && !ieltsOk) {
    warnings.push(
      `雅思未达标：需总分 ${ieltsReq.overall}/小分 ${ieltsReq.sub}，你当前 ${userOverall}/${userSub}` +
        (langWaivable ? "（你的全英文授课海外学位通常可申请豁免，如适用则不受影响）" : "")
    );
    if (!langWaivable) {
      if (category === "保底") category = "匹配";
      else if (category === "匹配") category = "冲刺";
    }
  }
  if (greReq && !greProvided) {
    warnings.push(`该项目通常需要 GRE（建议总分 ${greReq.total}+），你未填写`);
  }
  if (greReq && greProvided && !greOk) {
    warnings.push(`GRE 偏低：建议总分 ${greReq.total}+，你当前 ${userGre}`);
    if (category === "保底") category = "匹配";
    else if (category === "匹配") category = "冲刺";
  }
  if (greNote && !greProvided) {
    warnings.push(`GRE：${greNote}（未填写，建议确认目标项目要求）`);
  }

  // 中外合作大学：申研以合作方海外学位申请，需客观提示学位 / 语言豁免 / 成绩体系
  const coopNotes = [];
  if (coop) {
    coopNotes.push(
      `🎓 本科为中外合作大学，申研以合作方【${coop.partner}（${coop.degreeRegion}）】的海外学位申请`
    );
    if (coop.englishTaught) {
      if (!ieltsProvided) {
        coopNotes.push(
          `全英文授课海外学位，多数 ${coop.degreeRegion}/英港新院校可申请雅思/托福豁免，请向目标院校确认`
        );
      } else {
        coopNotes.push(`全英文授课海外学位，多数院校可申请语言豁免，请向目标院校确认是否仍需提交雅思`);
      }
    }
    if (coop.gradeSystem === "UK") {
      coopNotes.push(
        `成绩按英国荣誉学位评估：一等(First)≥70、二等一(2:1)60–69、二等二(2:2)50–59；英港新院校常按学位等级（而非国内百分制）评估`
      );
    } else if (coop.gradeSystem === "US") {
      coopNotes.push(`成绩按美国 4.0 GPA 体系评估，部分项目仍要求 GRE/GMAT，请按 4.0 制填写均分`);
    } else if (coop.gradeSystem === "HK") {
      coopNotes.push(`成绩按香港院校体系（GPA/荣誉等级）评估，全英文授课背景申港/英/新常可豁免语言`);
    }
  }

  return {
    program,
    category,
    requiredAvg,
    avgGap: Math.round(avgGap * 10) / 10,
    softBoost: soft.boost,
    softLevel: soft.level,
    ieltsReq,
    ieltsOk,
    greReq,
    warnings,
    coopNotes,
  };
}

/**
 * 主匹配函数
 * @returns {object} { 冲刺:[], 匹配:[], 保底:[], 超出:[] }
 */
function matchPrograms(allPrograms, profile) {
  const buckets = { 冲刺: [], 匹配: [], 保底: [], 超出: [] };
  profile._soft = computeSoftBackground(profile.soft); // 预计算一次复用
  const KNOWN_FIELDS = new Set(allPrograms.map((p) => p.field));

  allPrograms.forEach((program) => {
    // 国家筛选
    if (profile.countries && profile.countries.length > 0) {
      if (!profile.countries.includes(program.country)) return;
    }
    // 专业筛选：支持多选（取并集）。仅保留库内真实存在的方向参与硬过滤，
    // 自定义/未知方向不参与过滤（视为不限制），避免误杀。
    const wanted =
      profile.fields && profile.fields.length
        ? profile.fields
        : profile.field && profile.field !== "全部"
        ? [profile.field]
        : [];
    const fieldFilter = wanted.filter((f) => f && f !== "全部" && KNOWN_FIELDS.has(f));
    if (fieldFilter.length && !fieldFilter.includes(program.field)) {
      return;
    }
    // 只看官方核实
    if (profile.onlyVerified && !(program.provenance && program.provenance.verified)) {
      return;
    }

    const result = evaluateProgram(program, profile);
    buckets[result.category].push(result);
  });

  // 每档内排序：保底/匹配按 QS 排名升序（越好越靠前）；冲刺按差距从小到大
  const qs = (r) => r.program.qsRank || 9999;
  buckets.保底.sort((a, b) => qs(a) - qs(b));
  buckets.匹配.sort((a, b) => qs(a) - qs(b));
  buckets.冲刺.sort((a, b) => b.avgGap - a.avgGap);
  buckets.超出.sort((a, b) => b.avgGap - a.avgGap);

  return buckets;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { matchPrograms, evaluateProgram, computeSoftBackground };
}
