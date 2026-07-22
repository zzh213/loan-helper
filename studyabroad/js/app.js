const CATEGORY_META = {
  保底: { emoji: "🟢", desc: "把握较大，建议作为保底校" },
  匹配: { emoji: "🔵", desc: "背景匹配，重点冲击对象" },
  冲刺: { emoji: "🟡", desc: "有机会但需努力，建议冲刺" },
  超出: { emoji: "⚪", desc: "当前背景差距较大，可作了解" },
};

let DATA = null;
let UNIVERSITIES = [];
let UNI_MAP = {};
let MAJORS = [];
let MAJOR_MAP = {};
let GRAD_FIELDS = [];
let PROGRAM_FIELDS = new Set();
let selectedGradFields = [];
let currentTier = "双非";
let CASES = [];
let POLICIES = [];
let POLICY_CATS = [];
let activePolicyCat = "";

const SHORTLIST_KEY = "studyabroad_shortlist";
const AUTH_KEY = "studyabroad_auth";

/* ============ 通用请求 ============ */
async function loadJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(url + " 加载失败");
  return res.json();
}
function getAuth() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_KEY));
  } catch {
    return null;
  }
}
function authHeaders() {
  const a = getAuth();
  return a ? { Authorization: "Bearer " + a.token } : {};
}
async function api(path, method = "GET", body = null) {
  const opts = { method, headers: { ...authHeaders() } };
  if (body) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "请求失败");
  return data;
}
const isLoggedIn = () => !!getAuth();

/* ============ 轻量埋点（自建，无第三方） ============ */
const TRACK_SID_KEY = "studyabroad_sid";
function trackSession() {
  let s = localStorage.getItem(TRACK_SID_KEY);
  if (!s) {
    s = (Date.now().toString(36) + Math.random().toString(36).slice(2, 8));
    localStorage.setItem(TRACK_SID_KEY, s);
  }
  return s;
}
function track(name, props) {
  try {
    const body = JSON.stringify({
      name,
      props: props == null ? "" : String(props).slice(0, 300),
      path: location.pathname,
      session: trackSession(),
    });
    const url = "/api/track";
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
    } else {
      fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true });
    }
  } catch {}
}

/* ============ GPA 换算 ============ */
function gpaToPercentage(gpa, scale) {
  if (!gpa) return 0;
  const tables = {
    "4.0": [[4.0,95],[3.7,90],[3.5,88],[3.3,85],[3.0,82],[2.7,78],[2.3,75],[2.0,72],[0,65]],
    "4.3": [[4.3,95],[4.0,91],[3.7,88],[3.3,85],[3.0,82],[2.7,78],[2.3,75],[2.0,72],[0,65]],
    "5.0": [[5.0,95],[4.5,90],[4.0,85],[3.5,80],[3.0,75],[2.5,70],[2.0,66],[0,60]],
  };
  const table = tables[scale] || tables["4.0"];
  for (const [g, pct] of table) if (gpa >= g) return pct;
  return table[table.length - 1][1];
}

/* ============ WES iGPA 估算（中国百分制 → 美国 4.0，按 WES 段位换算）============ */
function wesGpa(pct) {
  if (!pct) return null;
  // WES 中国成绩 4-point 换算（公认段位法；WES 实际逐门课按学分加权）
  if (pct >= 85) return { gpa: 4.0, grade: "A" };
  if (pct >= 75) return { gpa: 3.0, grade: "B" };
  if (pct >= 60) return { gpa: 2.0, grade: "C" };
  return { gpa: 0.0, grade: "F（不及格）" };
}

/* ============ 院校层次识别 ============ */
function detectTier(name) {
  name = (name || "").trim();
  return UNI_MAP[name] ? UNI_MAP[name].tier : null;
}

/* ============ 读取表单 ============ */
function getScoreType() {
  return document.querySelector('input[name="scoreType"]:checked').value;
}
function readAvg() {
  if (getScoreType() === "gpa") {
    const gpa = parseFloat(document.getElementById("gpa").value) || 0;
    return gpaToPercentage(gpa, document.getElementById("gpaScale").value);
  }
  return parseFloat(document.getElementById("avg").value) || 0;
}
/* ============ 经历条目（通用：实习/项目/校园活动/交换） ============ */
const ENTRY_KINDS = {
  internship: {
    store: [], hostId: "internship-list", addId: "add-internship",
    label: "实习", scoreField: "internshipList",
    fields: [
      { key: "company", ph: "公司 / 机构（如 腾讯）" },
      { key: "role", ph: "岗位（如 后端开发实习生）" },
      { key: "period", ph: "时间（如 2025.06-2025.09）" },
    ],
    descPh: "工作内容 / 成果（如：负责订单服务接口开发，QPS 提升 30%）",
    empty: "还没有实习经历，点击「+ 添加实习」填写公司、岗位与内容。",
  },
  project: {
    store: [], hostId: "project-list", addId: "add-project",
    label: "项目", scoreField: "projectList",
    fields: [
      { key: "name", ph: "项目名称（如 校园二手交易平台）" },
      { key: "role", ph: "你的角色（如 全栈 / 队长）" },
      { key: "period", ph: "时间（如 2025.03-2025.06）" },
    ],
    descPh: "项目内容 / 技术栈 / 成果（如：React+Node，日活 500，获院级优秀项目）",
    empty: "还没有项目经历，点击「+ 添加项目」填写课程项目 / 个人作品 / 开源等。",
  },
  activity: {
    store: [], hostId: "activity-list", addId: "add-activity",
    label: "活动", scoreField: "activityList",
    fields: [
      { key: "org", ph: "社团 / 组织（如 学生会 / 志愿者协会）" },
      { key: "role", ph: "职务（如 部长 / 负责人）" },
      { key: "period", ph: "时间（如 2024.09-2025.06）" },
    ],
    descPh: "职责 / 成果（如：组织 300 人迎新活动，统筹 10 人团队）",
    empty: "还没有校园活动，点击「+ 添加活动」填写社团 / 志愿 / 组织经历。",
  },
  exchange: {
    store: [], hostId: "exchange-list", addId: "add-exchange",
    label: "交换", scoreField: "exchangeList",
    fields: [
      { key: "school", ph: "学校 / 项目（如 UC Berkeley 暑校）" },
      { key: "program", ph: "形式（如 交换 / 暑研 / 海外课程）" },
      { key: "period", ph: "时间（如 2025.07-2025.08）" },
    ],
    descPh: "内容 / 收获（如：修读 2 门 CS 课程，GPA 3.9，参与教授课题）",
    empty: "还没有交换 / 海外经历，点击「+ 添加交换」填写交换、暑研、海外课程等。",
  },
  planInternship: {
    store: [], hostId: "plan-internship-list", addId: "plan-add-internship",
    label: "实习", scoreField: "internshipList", noPreview: true,
    fields: [
      { key: "company", ph: "公司 / 机构（如 字节跳动）" },
      { key: "role", ph: "岗位（如 数据分析实习生）" },
      { key: "period", ph: "时间（如 2025.07-2025.09）" },
    ],
    descPh: "工作内容 / 成果（如：搭建用户行为看板，支撑 3 个业务线决策）",
    empty: "还没有实习经历，点击「+ 添加实习」填写公司、岗位与内容。",
  },
  planResearch: {
    store: [], hostId: "plan-research-list", addId: "plan-add-research",
    label: "科研", scoreField: "researchList", noPreview: true,
    fields: [
      { key: "topic", ph: "课题 / 方向（如 图神经网络推荐）" },
      { key: "role", ph: "角色（如 RA / 组员，导师：X 教授）" },
      { key: "period", ph: "时间（如 2025.03-至今）" },
    ],
    descPh: "研究内容 / 产出（如：负责数据预处理与实验，投稿 1 篇会议在审）",
    empty: "还没有科研经历，点击「+ 添加科研」填写课题、角色与内容。",
  },
  planCompetition: {
    store: [], hostId: "plan-competition-list", addId: "plan-add-competition",
    label: "竞赛", scoreField: "competitionList", noPreview: true,
    fields: [
      { key: "name", ph: "赛事名称（如 全国大学生数学建模）" },
      { key: "award", ph: "奖项 / 名次（如 国家一等奖）" },
      { key: "period", ph: "时间（如 2025.09）" },
    ],
    descPh: "项目内容 / 你的贡献（如：负责建模与编程，队伍排名前 1%）",
    empty: "还没有竞赛经历，点击「+ 添加竞赛」填写赛事、奖项与内容。",
  },
  planPaper: {
    store: [], hostId: "plan-paper-list", addId: "plan-add-paper",
    label: "论文", scoreField: "paperList", noPreview: true,
    fields: [
      { key: "title", ph: "论文标题" },
      { key: "venue", ph: "期刊 / 会议及级别（如 SCI 二区 / EI / 在投）" },
      { key: "period", ph: "时间（如 2025.05 录用）" },
    ],
    descPh: "研究内容 / 你的角色（如：第一作者，提出 X 方法，指标提升 12%）",
    empty: "还没有论文，点击「+ 添加论文」填写标题、期刊/会议与内容。",
  },
};
function entryRow(kind, it, idx) {
  const cfg = ENTRY_KINDS[kind];
  const esc = (v) => (v || "").replace(/"/g, "&quot;");
  const inputs = cfg.fields
    .map(
      (f) =>
        `<input class="entry-f" data-kind="${kind}" data-idx="${idx}" data-key="${f.key}" placeholder="${f.ph}" value="${esc(it[f.key])}" />`
    )
    .join("");
  return `
    <div class="entry" data-idx="${idx}">
      <div class="entry-row">
        ${inputs}
        <button type="button" class="entry-del" data-kind="${kind}" data-idx="${idx}" title="删除">✕</button>
      </div>
      <textarea class="entry-desc" data-kind="${kind}" data-idx="${idx}" rows="2" placeholder="${cfg.descPh}">${esc(it.desc)}</textarea>
    </div>`;
}
function renderEntries(kind) {
  const cfg = ENTRY_KINDS[kind];
  const host = document.getElementById(cfg.hostId);
  if (!host) return;
  host.innerHTML = cfg.store.length
    ? cfg.store.map((it, i) => entryRow(kind, it, i)).join("")
    : `<div class="entry-empty">${cfg.empty}</div>`;
  host.querySelectorAll(".entry-f").forEach((el) => {
    el.oninput = () => {
      cfg.store[el.dataset.idx][el.dataset.key] = el.value;
      if (!cfg.noPreview) updateSoftPreview();
    };
  });
  host.querySelectorAll(".entry-desc").forEach((el) => {
    el.oninput = () => { cfg.store[el.dataset.idx].desc = el.value; };
  });
  host.querySelectorAll(".entry-del").forEach((el) => {
    el.onclick = () => {
      cfg.store.splice(el.dataset.idx, 1);
      renderEntries(kind);
      if (!cfg.noPreview) updateSoftPreview();
    };
  });
}
function addEntry(kind, prefill) {
  const cfg = ENTRY_KINDS[kind];
  const blank = {};
  cfg.fields.forEach((f) => (blank[f.key] = ""));
  blank.desc = "";
  cfg.store.push({ ...blank, ...(prefill || {}) });
  renderEntries(kind);
}
function entryFilled(kind) {
  return ENTRY_KINDS[kind].store.filter((x) =>
    Object.values(x).some((v) => (v || "").trim())
  );
}

function readSoft() {
  const num = (id) => parseFloat(document.getElementById(id).value) || 0;
  return {
    internshipList: entryFilled("internship"),
    projectList: entryFilled("project"),
    activityList: entryFilled("activity"),
    exchangeList: entryFilled("exchange"),
    papers: num("papers"),
    paperLevel: document.getElementById("paperLevel").value || null,
    competitions: num("competitions"),
    competitionLevel: document.getElementById("competitionLevel").value || null,
    research: num("research"),
    workYears: num("workYears"),
    certificates: document.getElementById("certificates").value || "",
  };
}
function readProfile() {
  const fields = selectedGradFields.slice();
  const hasCustom = fields.some((f) => !PROGRAM_FIELDS.has(f));
  const primary = fields.length ? fields[0] : "全部";
  const gre = parseInt(document.getElementById("gre").value) || 0;
  const school = (document.getElementById("school").value || "").trim();
  const uni = UNI_MAP[school];
  const coop =
    uni && uni.partner
      ? {
          school,
          partner: uni.partner,
          partnerEn: uni.partnerEn,
          degreeRegion: uni.degreeRegion,
          gradeSystem: uni.gradeSystem,
          englishTaught: uni.englishTaught,
          note: uni.coopNote,
        }
      : null;
  return {
    tier: document.getElementById("tier").value,
    avg: readAvg(),
    field: primary,
    fields: fields,
    rawFields: fields,
    customField: hasCustom,
    undergradMajor: document.getElementById("undergradMajor").value.trim(),
    coop,
    countries: Array.from(
      document.querySelectorAll("#countries input:checked")
    ).map((c) => c.value),
    onlyVerified: !!document.getElementById("onlyVerified")?.checked,
    ielts: {
      overall: parseFloat(document.getElementById("ielts").value) || 0,
      sub: parseFloat(document.getElementById("ieltsSub").value) || 0,
    },
    gre: { total: gre },
    soft: readSoft(),
  };
}
function updateSoftPreview() {
  const s = computeSoftBackground(readSoft());
  const badge = document.getElementById("soft-badge");
  const prev = document.getElementById("soft-preview");
  if (s.boost > 0) {
    badge.textContent = `竞争力 ${s.level} · +${s.boost} 分`;
    badge.className = "soft-badge on";
    prev.innerHTML =
      `🔥 软背景竞争力：<strong>${s.level}</strong>（评分 ${s.score}/100），匹配时等效 <strong>+${s.boost}</strong> 分均分加成。` +
      (s.highlights.length ? `<br>已计入：${s.highlights.join("、")}` : "");
  } else {
    badge.textContent = "";
    badge.className = "soft-badge";
    prev.textContent = "填写实习、论文、竞赛、科研等经历，匹配会给予均分加成（最多等效 +6 分）。";
  }
}

/* ============ 收藏清单 + 申请进度 ============ */
const TRACK_KEY = "studyabroad_track";
const STATUS_LIST = ["待定", "准备中", "已递交", "面试中", "已录取", "已拒绝"];
const STATUS_COLOR = {
  待定: "#9ca3af", 准备中: "#60a5fa", 已递交: "#fbbf24",
  面试中: "#a78bfa", 已录取: "#34d399", 已拒绝: "#f87171",
};
let TRACK = {}; // { id: {status, deadline, note} }

function getLocalShortlist() {
  try {
    return JSON.parse(localStorage.getItem(SHORTLIST_KEY)) || [];
  } catch {
    return [];
  }
}
function saveLocalShortlist(ids) {
  localStorage.setItem(SHORTLIST_KEY, JSON.stringify(ids));
}
function getLocalTrack() {
  try {
    return JSON.parse(localStorage.getItem(TRACK_KEY)) || {};
  } catch {
    return {};
  }
}
function saveLocalTrack() {
  localStorage.setItem(TRACK_KEY, JSON.stringify(TRACK));
}
function trackOf(id) {
  return TRACK[id] || { status: "待定", deadline: "", note: "" };
}
let SHORTLIST_IDS = [];
function isFav(id) {
  return SHORTLIST_IDS.includes(id);
}
async function loadShortlist() {
  if (isLoggedIn()) {
    try {
      const items = await api("/api/shortlist");
      SHORTLIST_IDS = items.map((p) => p.id);
      TRACK = {};
      items.forEach((p) => {
        if (p.track) TRACK[p.id] = p.track;
      });
    } catch {
      SHORTLIST_IDS = getLocalShortlist();
      TRACK = getLocalTrack();
    }
  } else {
    SHORTLIST_IDS = getLocalShortlist();
    TRACK = getLocalTrack();
  }
  renderShortlist();
  refreshFavButtons();
}
async function toggleFav(id) {
  const idx = SHORTLIST_IDS.indexOf(id);
  const adding = idx < 0;
  if (adding) SHORTLIST_IDS.push(id);
  else {
    SHORTLIST_IDS.splice(idx, 1);
    delete TRACK[id];
  }

  if (isLoggedIn()) {
    try {
      if (adding) await api("/api/shortlist", "POST", { program_id: id });
      else await api(`/api/shortlist?program_id=${encodeURIComponent(id)}`, "DELETE");
    } catch (e) {
      /* 出错时退回本地，不阻塞 UI */
    }
  }
  saveLocalShortlist(SHORTLIST_IDS);
  saveLocalTrack();
  renderShortlist();
  refreshFavButtons();
}
async function updateTrack(id, patch) {
  TRACK[id] = { ...trackOf(id), ...patch };
  saveLocalTrack();
  if (isLoggedIn()) {
    try {
      await api("/api/shortlist", "PATCH", { program_id: id, ...patch });
    } catch (e) {
      /* 本地已保存，忽略网络错误 */
    }
  }
}

/* ============ 卡片渲染 ============ */
function programCard(result) {
  const p = result.program;
  const req = p.requirements;
  const fav = isFav(p.id);
  const qs = p.qsRank ? `<span class="qs">QS #${p.qsRank}</span>` : "";

  let gapBlock = "";
  if (result.requiredAvg !== undefined && result.requiredAvg !== null) {
    const gapText =
      result.avgGap >= 0
        ? `<span class="ok">高于参考线 ${result.avgGap} 分</span>`
        : `<span class="warn">低于参考线 ${Math.abs(result.avgGap)} 分</span>`;
    const boost =
      result.softBoost > 0
        ? ` · <span class="boost">软背景 +${result.softBoost} 分</span>`
        : "";
    gapBlock = `<div><strong>你的层次（${currentTier}）参考均分门槛：</strong>${result.requiredAvg} 分 · ${gapText}${boost}</div>`;
  }
  const ielts = req.ielts ? `雅思 ${req.ielts.overall}（小分 ${req.ielts.sub}）` : "雅思 见官网";
  const gre = req.gre ? `GRE ${req.gre.total}+（数学 ${req.gre.quant}+）` : "GRE 不强制";
  const warnings = (result.warnings || []).length
    ? `<ul class="warnings">${result.warnings.map((w) => `<li>⚠️ ${w}</li>`).join("")}</ul>`
    : "";
  const coopNotes = (result.coopNotes || []).length
    ? `<ul class="coop-notes">${result.coopNotes.map((w) => `<li>${w}</li>`).join("")}</ul>`
    : "";

  const needsWes = /美国|加拿大/.test(p.country || "");
  const wesNote = needsWes
    ? `<div class="wes-tag" title="美国/加拿大院校常要求 NACES 学历认证">📄 申该校通常需 <strong>WES</strong>/ECE 等 NACES 学历认证（约 $205，4–8 周，建议尽早办理）</div>`
    : "";

  const prov = p.provenance || {};
  const verifyBadge = prov.verified
    ? `<span class="data-badge verified" title="数据已对照官方项目页核实">✔ 官方核实${prov.lastVerified ? " · " + prov.lastVerified : ""}</span>`
    : `<span class="data-badge estimate" title="基于公开信息与往年经验的参考线，请以官网为准">≈ 参考估算</span>`;
  const verifyHref =
    prov.sourceUrl ||
    prov.searchUrl ||
    "https://www.google.com/search?q=" +
      encodeURIComponent(p.university + " " + p.program + " entry requirements");
  const verifyText = prov.sourceUrl ? "🔗 查看官方项目页" : "🔗 去官网核实最新要求";

  // 学费可信度：官方币种金额直接显示；「约..万元」为估算区间需标注
  let tuitionDisplay;
  const tui = (p.tuition || "").trim();
  if (!tui || /官网/.test(tui)) {
    tuitionDisplay = "学费以官网为准";
  } else if (/万元|约/.test(tui)) {
    tuitionDisplay = `${tui}（估算区间，以官网为准）`;
  } else {
    tuitionDisplay = tui;
  }

  return `
    <div class="program">
      <div class="program-head">
        <div>
          <div class="uni">${p.university}${qs}</div>
          <div class="prog">${p.program} · <span class="field-tag">${p.field}</span></div>
        </div>
        <div class="head-right">
          <div class="country-tag">${p.country}</div>
          <button class="fav-btn ${fav ? "active" : ""}" data-id="${p.id}" title="收藏到选校清单">${fav ? "★" : "☆"}</button>
        </div>
      </div>
      <div class="reqs">
        <div class="badge-row">${verifyBadge}</div>
        ${gapBlock}
        <div><strong>语言：</strong>${ielts}</div>
        <div><strong>标化：</strong>${gre}</div>
        <div><strong>背景要求：</strong>${req.background || "见官网"}</div>
        <div class="meta-row"><span>💰 ${tuitionDisplay}</span><span>⏳ ${p.duration || ""}</span></div>
        <div class="timeline">🗓️ ${p.timeline || "申请时间见官网"}</div>
        ${req.notes ? `<div class="notes">💡 ${req.notes}</div>` : ""}
        ${wesNote}
        ${coopNotes}
        ${warnings}
        <div class="verify"><a href="${verifyHref}" target="_blank" rel="noopener" onclick="track('open_school','${(p.university || '').replace(/'/g, '')} · ${(p.program || '').replace(/'/g, '')}')">${verifyText}</a></div>
      </div>
    </div>`;
}
function refreshFavButtons() {
  document.querySelectorAll(".fav-btn").forEach((btn) => {
    const fav = isFav(btn.dataset.id);
    btn.classList.toggle("active", fav);
    btn.textContent = fav ? "★" : "☆";
  });
}
function bindFavButtons() {
  document.querySelectorAll(".fav-btn").forEach((btn) => {
    btn.onclick = () => toggleFav(btn.dataset.id);
  });
}

/* ============ 匹配结果 ============ */
function render(buckets, profile) {
  currentTier = profile.tier;
  const summaryEl = document.getElementById("summary");
  const resultsEl = document.getElementById("results");
  const total = ["保底", "匹配", "冲刺", "超出"].reduce((s, k) => s + buckets[k].length, 0);

  let note = "";
  if (profile.customField) {
    const customs = (profile.fields || []).filter((f) => !PROGRAM_FIELDS.has(f));
    const known = (profile.fields || []).filter((f) => PROGRAM_FIELDS.has(f));
    if (customs.length) {
      const tail = known.length
        ? `已按已收录方向「${known.join("、")}」展示匹配结果。`
        : `已为你展示全部方向的匹配结果。`;
      note = `<p class="note-line">🔎 自定义方向「${customs.join("、")}」暂无单独收录的项目，${tail}</p>`;
    }
  }
  const soft = computeSoftBackground(profile.soft);
  const softLine =
    soft.boost > 0
      ? `<p class="note-line">💪 软背景竞争力 <strong>${soft.level}</strong>（+${soft.boost} 分均分加成）已计入匹配${
          soft.highlights.length ? "：" + soft.highlights.join("、") : ""
        }。</p>`
      : "";

  summaryEl.classList.remove("hidden");
  const verifiedTotal = ["保底", "匹配", "冲刺", "超出"].reduce(
    (s, k) => s + buckets[k].filter((r) => r.program.provenance && r.program.provenance.verified).length,
    0
  );
  const verifiedLine = total
    ? `<p class="note-line">📑 数据可信度：其中 <strong>${verifiedTotal}</strong> 个项目已对照官方页核实（✔ 官方核实），其余为公开经验参考线（≈ 参考估算），请以官网为准。</p>`
    : "";
  summaryEl.innerHTML = `
    <h2>匹配结果</h2>
    <p>根据 <strong>${profile.tier}</strong> · 均分 <strong>${profile.avg}</strong>${
    profile.ielts.overall ? ` · 雅思 <strong>${profile.ielts.overall}</strong>` : ""
  }，共匹配到 <strong>${total}</strong> 个项目。</p>
    ${note}
    ${softLine}
    ${verifiedLine}
    <div class="counts">
      <span class="c-baodi">🟢 保底 ${buckets.保底.length}</span>
      <span class="c-pipei">🔵 匹配 ${buckets.匹配.length}</span>
      <span class="c-chongci">🟡 冲刺 ${buckets.冲刺.length}</span>
    </div>`;

  resultsEl.innerHTML = ["保底", "匹配", "冲刺", "超出"]
    .filter((cat) => buckets[cat].length > 0)
    .map((cat) => {
      const meta = CATEGORY_META[cat];
      return `<div class="bucket bucket-${cat}">
        <h3>${meta.emoji} ${cat} <span class="bucket-desc">${meta.desc}</span></h3>
        <div class="program-list">${buckets[cat].map(programCard).join("")}</div>
      </div>`;
    })
    .join("");

  if (total === 0) {
    resultsEl.innerHTML = `<div class="empty">没有匹配到项目，试着放宽国家/方向筛选，或检查均分是否填写。</div>`;
  }
  bindFavButtons();
  window.scrollTo({ top: summaryEl.offsetTop - 20, behavior: "smooth" });
}

/* 计算截止日剩余天数 */
function daysUntil(deadline) {
  if (!deadline) return null;
  const d = new Date(deadline + "T23:59:59");
  if (isNaN(d)) return null;
  return Math.ceil((d - new Date()) / 86400000);
}
function deadlineBadge(deadline, status) {
  const days = daysUntil(deadline);
  if (days === null) return "";
  const done = status === "已递交" || status === "已录取" || status === "已拒绝";
  if (done) return `<span class="dl-badge dl-done">截止 ${deadline}</span>`;
  if (days < 0) return `<span class="dl-badge dl-over">已过期 ${-days} 天</span>`;
  if (days <= 14) return `<span class="dl-badge dl-soon">⏰ 还剩 ${days} 天</span>`;
  return `<span class="dl-badge">还剩 ${days} 天</span>`;
}

/* 选校清单 + 申请进度看板 */
function trackCard(p) {
  const t = trackOf(p.id);
  const qs = p.qsRank ? `<span class="qs">QS #${p.qsRank}</span>` : "";
  const opts = STATUS_LIST.map(
    (s) => `<option value="${s}" ${s === t.status ? "selected" : ""}>${s}</option>`
  ).join("");
  return `
    <div class="track-card" style="border-left-color:${STATUS_COLOR[t.status] || "#888"}">
      <div class="track-head">
        <div>
          <div class="uni">${p.university}${qs}</div>
          <div class="prog">${p.program} · <span class="field-tag">${p.field}</span> · ${p.country}</div>
        </div>
        <button class="fav-btn active" data-id="${p.id}" title="从清单移除">★</button>
      </div>
      <div class="track-controls">
        <label>状态
          <select class="trk-status" data-id="${p.id}">${opts}</select>
        </label>
        <label>截止日期
          <input type="date" class="trk-deadline" data-id="${p.id}" value="${t.deadline || ""}" />
        </label>
        ${deadlineBadge(t.deadline, t.status)}
      </div>
      <input class="trk-note" data-id="${p.id}" placeholder="备注（如：文书进度、网申账号、面试时间…）" value="${(t.note || "").replace(/"/g, "&quot;")}" />
    </div>`;
}

function renderProgressSummary() {
  const counts = {};
  STATUS_LIST.forEach((s) => (counts[s] = 0));
  SHORTLIST_IDS.forEach((id) => {
    const s = trackOf(id).status || "待定";
    counts[s] = (counts[s] || 0) + 1;
  });
  const chips = STATUS_LIST.filter((s) => counts[s] > 0)
    .map(
      (s) =>
        `<span class="status-chip" style="background:${STATUS_COLOR[s]}22;color:${STATUS_COLOR[s]};border-color:${STATUS_COLOR[s]}55">${s} ${counts[s]}</span>`
    )
    .join("");
  // 临近截止提醒
  const soon = SHORTLIST_IDS.map((id) => {
    const t = trackOf(id);
    const days = daysUntil(t.deadline);
    return { id, days, t };
  })
    .filter((x) => x.days !== null && x.days >= 0 && x.days <= 14 && x.t.status !== "已递交")
    .sort((a, b) => a.days - b.days);
  const byId = {};
  (DATA?.programs || []).forEach((p) => (byId[p.id] = p));
  const alert = soon.length
    ? `<div class="dl-alert">⏰ 临近截止：${soon
        .map((x) => `${byId[x.id]?.university || ""}（${x.days} 天）`)
        .join("、")}</div>`
    : "";
  return `<div class="status-chips">${chips}</div>${alert}`;
}

function renderShortlist() {
  const section = document.getElementById("shortlist-section");
  const listEl = document.getElementById("shortlist-list");
  document.getElementById("shortlist-count").textContent = SHORTLIST_IDS.length;
  if (!SHORTLIST_IDS.length) {
    section.classList.add("hidden");
    document.getElementById("checklist-section").classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  const byId = {};
  (DATA?.programs || []).forEach((p) => (byId[p.id] = p));

  const summaryHost = document.getElementById("progress-summary");
  if (summaryHost) summaryHost.innerHTML = renderProgressSummary();

  listEl.innerHTML = SHORTLIST_IDS.map((id) => byId[id])
    .filter(Boolean)
    .map((p) => trackCard(p))
    .join("");

  bindFavButtons();
  bindTrackControls();
}

function bindTrackControls() {
  document.querySelectorAll(".trk-status").forEach((el) => {
    el.onchange = async () => {
      await updateTrack(el.dataset.id, { status: el.value });
      renderShortlist();
    };
  });
  document.querySelectorAll(".trk-deadline").forEach((el) => {
    el.onchange = async () => {
      await updateTrack(el.dataset.id, { deadline: el.value });
      renderShortlist();
    };
  });
  document.querySelectorAll(".trk-note").forEach((el) => {
    el.onchange = () => updateTrack(el.dataset.id, { note: el.value });
  });
}

/* ============ 申请时间线 + 文书清单 ============ */
async function renderChecklist() {
  const el = document.getElementById("checklist-section");
  let data;
  try {
    if (isLoggedIn()) data = await api("/api/checklist");
    else data = await api("/api/checklist", "POST", { program_ids: SHORTLIST_IDS });
  } catch (e) {
    el.classList.remove("hidden");
    el.innerHTML = `<div class="empty">清单生成失败：${e.message}</div>`;
    return;
  }

  const docs = data.documents
    .map(
      (d) =>
        `<li><label><input type="checkbox" class="doc-chk" /> ${d.name}${
          d.required ? "" : ' <span class="opt">(按需)</span>'
        }</label></li>`
    )
    .join("");
  const tl = data.timeline
    .map((t) => `<div class="tl-row"><div class="tl-phase">${t.phase}</div><div class="tl-task">${t.task}</div></div>`)
    .join("");
  const notes = (data.countryNotes || [])
    .map((n) => `<li><strong>${n.country}：</strong>${n.tip}</li>`)
    .join("");

  el.classList.remove("hidden");
  el.innerHTML = `
    <h2>📋 申请规划（基于 ${data.programCount} 个收藏项目）</h2>
    <div class="checklist-grid">
      <div class="card sub">
        <h3>📄 文书 / 材料清单</h3>
        <ul class="doc-list">${docs}</ul>
      </div>
      <div class="card sub">
        <h3>🗓️ 申请时间线</h3>
        <div class="timeline-list">${tl}</div>
        ${notes ? `<h4>各地区提示</h4><ul class="country-notes">${notes}</ul>` : ""}
      </div>
    </div>`;
  el.scrollIntoView({ behavior: "smooth" });
}

/* ============ 研究生方向多选管理 ============ */
function renderSelectedFields() {
  const box = document.getElementById("selectedFields");
  if (!box) return;
  if (!selectedGradFields.length) {
    box.innerHTML = `<span class="sf-empty">未选择 = 匹配全部方向</span>`;
  } else {
    box.innerHTML = selectedGradFields
      .map(
        (f) =>
          `<span class="sf-tag${PROGRAM_FIELDS.has(f) ? "" : " custom"}">${f}` +
          `<button type="button" class="sf-x" data-field="${f}" title="移除">×</button></span>`
      )
      .join("");
    box.querySelectorAll(".sf-x").forEach((b) => {
      b.onclick = () => removeGradField(b.dataset.field);
    });
  }
  // 同步推荐区 chip 高亮
  document.querySelectorAll("#recommend .chip").forEach((c) => {
    c.classList.toggle("active", selectedGradFields.includes(c.dataset.field));
  });
}

function addGradField(name) {
  const f = (name || "").trim();
  if (!f || f === "全部") return;
  if (!selectedGradFields.includes(f)) selectedGradFields.push(f);
  renderSelectedFields();
}

function removeGradField(name) {
  selectedGradFields = selectedGradFields.filter((x) => x !== name);
  renderSelectedFields();
}

/* ============ 本科专业 → 推荐研究生方向（含 AI 智能识别） ============ */
function paintRecommendChips(label, fields) {
  const box = document.getElementById("recommend");
  if (!fields || !fields.length) {
    box.innerHTML = "";
    return;
  }
  box.innerHTML =
    `<div class="rec-label">${label}</div>` +
    `<div class="chips">` +
    fields
      .map(
        (f) =>
          `<button type="button" class="chip${
            selectedGradFields.includes(f) ? " active" : ""
          }" data-field="${f}">${f}</button>`
      )
      .join("") +
    `</div>`;
  box.querySelectorAll(".chip").forEach((c) => {
    c.onclick = () => {
      const f = c.dataset.field;
      if (selectedGradFields.includes(f)) removeGradField(f);
      else addGradField(f);
    };
  });
}

let recommendSeq = 0;
function renderRecommend(majorName) {
  const name = (majorName || "").trim();
  const box = document.getElementById("recommend");
  if (!name) {
    box.innerHTML = "";
    return;
  }
  const m = MAJOR_MAP[name];
  if (m) {
    paintRecommendChips(
      `💡 与「${name}」匹配的研究生方向（点击多选，可叠加自定义）：`,
      m.recommendFields
    );
    return;
  }
  // 列表外专业：调用后端 AI 智能识别
  const seq = ++recommendSeq;
  box.innerHTML = `<div class="rec-label">🤖 正在 AI 识别「${name}」的相关研究生方向…</div>`;
  fetch("/api/recommend-fields", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ major: name }),
  })
    .then((r) => r.json())
    .then((d) => {
      if (seq !== recommendSeq) return; // 已有更新的输入，丢弃过期结果
      const label = d.note
        ? `🤖 ${d.note}（点击多选）：`
        : `💡 与「${name}」匹配的研究生方向（点击多选）：`;
      paintRecommendChips(label, d.fields || []);
    })
    .catch(() => {
      if (seq !== recommendSeq) return;
      box.innerHTML = `<div class="rec-label">未能识别该专业，可直接在上方输入研究生方向。</div>`;
    });
}

/* ============ 简历 PDF 上传 → AI 提取 → 回填 ============ */
function setVal(id, v) {
  const el = document.getElementById(id);
  if (el && v !== undefined && v !== null && v !== "") el.value = v;
}
function applyExtracted(d) {
  if (d.school) {
    setVal("school", d.school);
    document.getElementById("school").dispatchEvent(new Event("input"));
  }
  if (d.tier) document.getElementById("tier").value = d.tier;
  if (d.undergradMajor) {
    setVal("undergradMajor", d.undergradMajor);
    renderRecommend(d.undergradMajor);
    // 简历识别出的推荐方向自动预选前两个，方便用户直接匹配
    if (Array.isArray(d.recommendFields)) {
      d.recommendFields.slice(0, 2).forEach((f) => addGradField(f));
    }
  }
  if (d.avg) {
    document.querySelector('input[name="scoreType"][value="avg"]').checked = true;
    document.getElementById("avg-field").classList.remove("hidden");
    document.getElementById("gpa-field").classList.add("hidden");
    setVal("avg", d.avg);
  } else if (d.gpa) {
    document.querySelector('input[name="scoreType"][value="gpa"]').checked = true;
    document.getElementById("avg-field").classList.add("hidden");
    document.getElementById("gpa-field").classList.remove("hidden");
    setVal("gpa", d.gpa);
    document.getElementById("gpa").dispatchEvent(new Event("input"));
  }
  if (d.ielts) setVal("ielts", d.ielts);
  if (d.gre) setVal("gre", d.gre);
  // 实习：优先用结构化条目，否则按数量生成占位条目
  if (Array.isArray(d.internshipList) && d.internshipList.length) {
    ENTRY_KINDS.internship.store = d.internshipList.map((x) => ({
      company: x.company || "", role: x.role || "", period: x.period || "", desc: x.desc || "",
    }));
    renderEntries("internship");
  } else if (d.internships) {
    ENTRY_KINDS.internship.store = [];
    for (let i = 0; i < Math.min(d.internships, 5); i++) {
      ENTRY_KINDS.internship.store.push({ company: i === 0 && d.internshipTop ? "（名企，请补充）" : "", role: "", period: "", desc: "" });
    }
    renderEntries("internship");
  }
  // 项目 / 交换（简历若解析到）
  if (Array.isArray(d.projectList) && d.projectList.length) {
    ENTRY_KINDS.project.store = d.projectList.map((x) => ({
      name: x.name || "", role: x.role || "", period: x.period || "", desc: x.desc || "",
    }));
    renderEntries("project");
  }
  if (Array.isArray(d.exchangeList) && d.exchangeList.length) {
    ENTRY_KINDS.exchange.store = d.exchangeList.map((x) => ({
      school: x.school || "", program: x.program || "", period: x.period || "", desc: x.desc || "",
    }));
    renderEntries("exchange");
  }
  setVal("papers", d.papers);
  if (d.paperLevel) document.getElementById("paperLevel").value = d.paperLevel;
  setVal("competitions", d.competitions);
  if (d.competitionLevel) document.getElementById("competitionLevel").value = d.competitionLevel;
  setVal("research", d.research);
  if (d.certificates) setVal("certificates", d.certificates);
  updateSoftPreview();
  if (d.internships || (d.internshipList || []).length || (d.projectList || []).length ||
      (d.exchangeList || []).length || d.papers || d.competitions || d.research || d.certificates) {
    document.getElementById("soft-block").open = true;
  }
}
async function handleResume(file) {
  const box = document.getElementById("resume-result");
  const nameEl = document.getElementById("resume-name");
  nameEl.textContent = file.name;
  box.classList.remove("hidden");
  box.innerHTML = "⏳ 正在解析简历并提取背景…";
  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/extract-resume", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "解析失败");
    applyExtracted(data);
    const labels = {
      school: "院校", undergradMajor: "本科专业", avg: "均分", gpa: "GPA",
      ielts: "雅思", toefl: "托福", gre: "GRE", internships: "实习",
      papers: "论文", competitions: "竞赛", research: "科研",
    };
    const got = (data.extracted || [])
      .map((k) => `<span class="ext-tag">${labels[k] || k}：${data[k]}</span>`)
      .join("");
    box.innerHTML = got
      ? `✅ 已自动识别并回填以下信息（请核对修改）：<div class="ext-tags">${got}</div>`
      : "⚠️ 未能识别到明确字段，请手动填写。可能是扫描件或排版特殊。";
  } catch (e) {
    box.innerHTML = `❌ ${e.message}`;
  }
}

/* ============ 成绩单截图 OCR：自动算均分 / 绩点 ============ */
let _tesseractPromise = null;
function loadTesseract() {
  if (window.Tesseract) return Promise.resolve(window.Tesseract);
  if (_tesseractPromise) return _tesseractPromise;
  _tesseractPromise = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js";
    s.onload = () => resolve(window.Tesseract);
    s.onerror = () => reject(new Error("OCR 组件加载失败，请检查网络后重试"));
    document.head.appendChild(s);
  });
  return _tesseractPromise;
}

// 中国百分制 → 4.0 绩点（常用院校换算段位）
function china4(pct) {
  if (pct >= 90) return 4.0;
  if (pct >= 85) return 3.7;
  if (pct >= 82) return 3.3;
  if (pct >= 78) return 3.0;
  if (pct >= 75) return 2.7;
  if (pct >= 72) return 2.3;
  if (pct >= 68) return 2.0;
  if (pct >= 64) return 1.5;
  if (pct >= 60) return 1.0;
  return 0.0;
}

// 从 OCR 文本解析各科成绩与学分，计算均分与绩点
function parseTranscript(text) {
  const lines = text.split(/\n+/).map((l) => l.trim()).filter(Boolean);
  const courses = [];
  const NUM = /\d{1,3}(?:\.\d{1,2})?/g;
  for (const ln of lines) {
    // 跳过明显的汇总/表头行，避免把「平均分/总学分」当成科目
    if (/(平均|均分|总学分|绩点|GPA|学期|排名|加权|合计|总分)/i.test(ln) &&
        !/\d{2,3}\s*\d|\d\.\d\s+\d{2}/.test(ln)) continue;
    const nums = (ln.match(NUM) || []).map(Number);
    if (!nums.length) continue;
    // 成绩：40–100（排除年份 19xx/20xx）
    const scoreCands = nums.filter((n) => n >= 40 && n <= 100 && !(n >= 1900 && n <= 2100));
    if (!scoreCands.length) continue;
    const score = Math.max(...scoreCands); // 一行多数字时取较大者为成绩
    // 学分：0.5–10 的较小数字（成绩以外）
    const creditCands = nums.filter((n) => n >= 0.5 && n <= 10 && n !== score);
    const credit = creditCands.length ? creditCands[0] : null;
    courses.push({ score, credit });
  }
  if (courses.length < 3) return { ok: false, count: courses.length };
  const hasCredits = courses.filter((c) => c.credit).length >= Math.ceil(courses.length * 0.6);
  let avg, gpa, wes;
  if (hasCredits) {
    let ws = 0, wc = 0, wg = 0, ww = 0;
    courses.forEach((c) => {
      const cr = c.credit || 1;
      ws += c.score * cr; wc += cr; wg += china4(c.score) * cr;
      ww += (wesGpa(c.score)?.gpa ?? 0) * cr;
    });
    avg = ws / wc; gpa = wg / wc; wes = ww / wc;
  } else {
    avg = courses.reduce((s, c) => s + c.score, 0) / courses.length;
    gpa = courses.reduce((s, c) => s + china4(c.score), 0) / courses.length;
    wes = courses.reduce((s, c) => s + (wesGpa(c.score)?.gpa ?? 0), 0) / courses.length;
  }
  return {
    ok: true, count: courses.length, weighted: hasCredits,
    avg: Math.round(avg * 100) / 100,
    gpa: Math.round(gpa * 100) / 100,
    wes: Math.round(wes * 100) / 100,
    courses,
  };
}

const TS_MAIN = { resultId: "transcript-result", nameId: "transcript-name", target: "main" };
const TS_PLAN = { resultId: "plan-transcript-result", nameId: "plan-transcript-name", target: "plan" };

async function handleTranscript(file, ctx = TS_MAIN) {
  const box = document.getElementById(ctx.resultId);
  const nameEl = document.getElementById(ctx.nameId);
  nameEl.textContent = file.name;
  box.classList.remove("hidden");
  box.innerHTML = "⏳ 正在加载 OCR 组件…";
  let result;
  try {
    const T = await loadTesseract();
    box.innerHTML = "⏳ 正在识别成绩单（首次需下载中文识别包，请稍候）… <span class='ocr-pct'>0%</span>";
    const worker = await T.createWorker("chi_sim+eng", 1, {
      logger: (m) => {
        if (m.status === "recognizing text") {
          const el = box.querySelector(".ocr-pct");
          if (el) el.textContent = Math.round(m.progress * 100) + "%";
        }
      },
    });
    const { data } = await worker.recognize(file);
    await worker.terminate();
    result = parseTranscript(data.text || "");
  } catch (e) {
    box.innerHTML = `❌ ${e.message || "识别失败"}，可改用清晰截图或手动填写均分。`;
    return;
  }
  if (!result.ok) {
    box.innerHTML =
      `⚠️ 只识别到 ${result.count} 门课的成绩，样本太少可能不准。建议换用更清晰、完整的成绩单截图，或手动填写均分。`;
    return;
  }
  renderTranscript(result, ctx);
}

function renderTranscript(r, ctx = TS_MAIN) {
  const box = document.getElementById(ctx.resultId);
  const rows = r.courses
    .map(
      (c, i) =>
        `<tr><td>${i + 1}</td><td>${c.score}</td><td>${c.credit ?? "—"}</td><td>${china4(c.score).toFixed(1)}</td><td>${(wesGpa(c.score)?.gpa ?? 0).toFixed(1)}</td></tr>`
    )
    .join("");
  const applyBtns =
    ctx.target === "plan"
      ? `<button type="button" class="btn-primary ts-apply-avg">填入均分 ${r.avg}</button>`
      : `<button type="button" class="btn-primary ts-apply-avg">填入均分 ${r.avg}</button>
         <button type="button" class="btn-secondary ts-apply-gpa">填入 GPA ${r.gpa}</button>`;
  box.innerHTML = `
    <div class="ts-summary">
      ✅ 已识别 <strong>${r.count}</strong> 门课程，${r.weighted ? "按<strong>学分加权</strong>" : "按<strong>简单平均</strong>（未识别到学分）"}算出：
      <div class="ts-nums">
        <span class="ts-num">均分 <strong>${r.avg}</strong></span>
        <span class="ts-num">绩点(4.0) <strong>${r.gpa}</strong></span>
        <span class="ts-num ts-num-wes" title="WES 用逐门课四分段位换算（A=4/B=3/C=2），北美院校常用；此为估算，正式以 WES 官方报告为准">WES iGPA <strong>${r.wes != null ? r.wes.toFixed(2) : "—"}</strong> / 4.0</span>
      </div>
      <div class="ts-actions">
        ${applyBtns}
        <button type="button" class="btn-link ts-toggle-detail">查看识别明细</button>
      </div>
      <p class="ts-tip">⚠️ OCR 识别可能有误差（漏课、串行、学分未识别等），<strong>请务必核对</strong>后再使用；最终以学校官方成绩单为准。<br>💡 <strong>WES iGPA</strong> 按 WES 段位法（85+=A/4.0、75–84=B/3.0、60–74=C/2.0）逐门课加权估算，申美/加常需 WES 认证，正式绩点以官方报告为准。</p>
    </div>
    <div class="ts-detail hidden">
      <table class="ts-table">
        <thead><tr><th>#</th><th>成绩</th><th>学分</th><th>绩点</th><th>WES</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  box.querySelector(".ts-apply-avg").onclick = () => {
    if (ctx.target === "plan") {
      setVal("plan-avg", r.avg);
    } else {
      document.querySelector('input[name="scoreType"][value="avg"]').checked = true;
      document.getElementById("avg-field").classList.remove("hidden");
      document.getElementById("gpa-field").classList.add("hidden");
      setVal("avg", r.avg);
      document.getElementById("avg").dispatchEvent(new Event("input"));
    }
    track("transcript_apply", ctx.target + ":avg");
  };
  const gpaBtn = box.querySelector(".ts-apply-gpa");
  if (gpaBtn) {
    gpaBtn.onclick = () => {
      document.querySelector('input[name="scoreType"][value="gpa"]').checked = true;
      document.getElementById("avg-field").classList.add("hidden");
      document.getElementById("gpa-field").classList.remove("hidden");
      document.getElementById("gpaScale").value = "4.0";
      setVal("gpa", r.gpa);
      document.getElementById("gpa").dispatchEvent(new Event("input"));
      track("transcript_apply", "main:gpa");
    };
  }
  box.querySelector(".ts-toggle-detail").onclick = () => {
    box.querySelector(".ts-detail").classList.toggle("hidden");
  };
  track("transcript_ocr", r.weighted ? "weighted" : "simple");
}

/* ============ 早规划（在读生申研路线图） ============ */
function readPlanProfile() {
  const intern = entryFilled("planInternship");
  const research = entryFilled("planResearch");
  const comps = entryFilled("planCompetition");
  const papers = entryFilled("planPaper");
  return {
    grade: parseInt(document.getElementById("plan-grade").value) || 2,
    school: (document.getElementById("plan-school").value || "").trim(),
    tier: document.getElementById("plan-tier").value,
    avg: parseFloat(document.getElementById("plan-avg").value) || 0,
    field: (document.getElementById("plan-field").value || "").trim(),
    countries: Array.from(
      document.querySelectorAll("#plan-countries input:checked")
    ).map((c) => c.value),
    soft: {
      internships: intern.length,
      research: research.length,
      competitions: comps.length,
      papers: papers.length,
    },
    exp: { internships: intern, research, competitions: comps, papers },
    ielts: parseFloat(document.getElementById("plan-ielts").value) || 0,
  };
}

function median(arr) {
  if (!arr.length) return null;
  const s = arr.slice().sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

// 按 QS 档位聚合目标方向/国家的均分线、雅思、代表校
function planTierBands(p) {
  const useField = p.field && PROGRAM_FIELDS.has(p.field) ? p.field : null;
  const def = [
    { key: "top", label: "🌍 世界顶尖", qs: "QS ≤ 50", min: 0, max: 50 },
    { key: "elite", label: "⭐ 世界名校", qs: "QS 51–100", min: 51, max: 100 },
    { key: "quality", label: "✅ 优质院校", qs: "QS 101–200", min: 101, max: 200 },
    { key: "solid", label: "🛟 稳妥院校", qs: "QS 200+", min: 201, max: 999999 },
  ];
  const bands = def.map((b) => ({ ...b, avgs: [], ielts: [], schools: [] }));
  DATA.programs.forEach((pr) => {
    if (p.countries.length && !p.countries.includes(pr.country)) return;
    if (useField && pr.field !== useField) return;
    const qs = pr.qsRank || 9999;
    const band = bands.find((b) => qs >= b.min && qs <= b.max);
    if (!band) return;
    const req = pr.requirements || {};
    const ra = req.avgByTier && (req.avgByTier[p.tier] ?? req.avgByTier["双非"]);
    const io = req.ielts && req.ielts.overall;
    if (ra) band.avgs.push(ra);
    if (io) band.ielts.push(io);
    band.schools.push({ uni: pr.university, program: pr.program, qs, ra, io });
  });
  return bands
    .filter((b) => b.schools.length)
    .map((b) => {
      // 代表校：按 uni 去重取 QS 最靠前，最多 4 所
      const byUni = {};
      b.schools.forEach((s) => {
        if (!byUni[s.uni] || s.qs < byUni[s.uni].qs) byUni[s.uni] = s;
      });
      const reps = Object.values(byUni).sort((a, b2) => a.qs - b2.qs).slice(0, 4);
      return {
        ...b,
        avgMin: b.avgs.length ? Math.min(...b.avgs) : null,
        avgTypical: median(b.avgs),
        ieltsTypical: median(b.ielts),
        count: b.schools.length,
        reps,
      };
    });
}

// 现状定位：用现有匹配引擎评估当前背景能进哪档
function planCurrentStanding(p) {
  if (!p.avg) return null;
  const mk = (nn) => Array.from({ length: nn }, () => ({ company: "x", role: "x" }));
  const profile = {
    tier: p.tier,
    avg: p.avg,
    fields: p.field && PROGRAM_FIELDS.has(p.field) ? [p.field] : [],
    field: p.field && PROGRAM_FIELDS.has(p.field) ? p.field : "全部",
    countries: p.countries,
    ielts: { overall: p.ielts, sub: p.ielts },
    gre: { total: 0 },
    soft: {
      internshipList: mk(p.soft.internships),
      research: p.soft.research,
      competitions: p.soft.competitions,
      competitionLevel: p.soft.competitions ? "省级" : null,
      papers: p.soft.papers,
      paperLevel: p.soft.papers ? "会议" : null,
    },
  };
  const buckets = matchPrograms(DATA.programs, profile);
  const soft = computeSoftBackground(profile.soft);
  return {
    safe: buckets.保底.length,
    match: buckets.匹配.length,
    reach: buckets.冲刺.length,
    boost: soft.boost,
    softLevel: soft.level,
  };
}

// 生成分年级行动清单
function buildRoadmap(p, bands) {
  const stem = /计算|软件|工程|数据|人工智能|电子|机械|材料|物理|数学|统计|生物|化学|信息|网络|通信/.test(p.field || "");
  // 选一个"跳一跳"的目标档作为 GPA 激励线
  const elite = bands.find((b) => b.key === "elite");
  const quality = bands.find((b) => b.key === "quality");
  const target = elite && elite.avgTypical ? elite : quality;
  const targetLine = target && target.avgTypical
    ? `想冲「${target.label}（${target.qs}）」，你所在层次通常需要均分 <strong>${Math.round(target.avgTypical)}+</strong>`
    : "把加权均分稳在同层次高位（通常越高选择越多）";

  const expStem = "找 1 段科研/课题（进实验室、跟老师做项目），有条件冲学科竞赛（如数模、ACM、挑战杯）";
  const expBiz = "找 1 段对口实习（券商/银行/互联网/四大等），参加商赛/数模，积累可写进 CV 的成果";
  const exp = stem ? expStem : expBiz;

  const Y = {
    1: {
      title: "大一",
      gpa: `打好每门专业基础课，冲高绩点、绝不挂科重修（申研主要看前三年加权）。${targetLine}。`,
      lang: "背单词、过四六级，开始磨雅思听力/阅读语感，不用急着考试。",
      exp: "多探索方向：加入相关社团/兴趣科研组，了解自己想读的研究生方向。",
      plan: "初步了解目标国家/地区和专业的大致要求（本站可查各校雅思/均分线）。",
    },
    2: {
      title: "大二",
      gpa: `重视专业核心课，把加权均分往上提。${targetLine}。低分课尽早补救。`,
      lang: "系统备考雅思，目标先摸到 6.0–6.5；口语写作早练。",
      exp: stem
        ? "尝试进实验室做科研入门、参加学科竞赛，积累第一段硬经历。"
        : "争取第一段实习或商赛经历，建立行业认知。",
      plan: "缩小到 2–3 个目标国家 + 方向，关注对口项目的具体门槛。",
    },
    3: {
      title: "大三",
      gpa: "稳住均分（这是申请看到的最后完整成绩），把弱项课补上去。",
      lang: "务必在大三下之前考出达标雅思（多数英港新要 6.5，名校要 7.0）。",
      exp: `${exp}，追求"有成果、能讲故事"而非数量堆砌。`,
      plan: "大三下：确定选校清单（冲刺/匹配/保底）、动笔写 PS/CV、联系 2 位推荐人。",
    },
    4: {
      title: "大四（申请季）",
      gpa: "保持成绩别松懈，部分项目会看到大四成绩单。",
      lang: "如未达标抓紧刷分/补考，卡在小分的重点突破。",
      exp: "收尾实习/项目，把成果量化写进 CV。",
      plan: "9–12 月网申开放即尽早递交（滚动录取先到先得），跟进面试、准备后续签证。",
    },
  };
  const years = [];
  for (let g = p.grade; g <= 4; g++) years.push(Y[g]);
  return { years, target };
}

// 基于差距的针对性诊断：按优先级给出"现在最该做什么"
function buildDiagnosis(p, bands, standing) {
  const items = [];
  const yearsLeft = Math.max(0, 4 - p.grade); // 还剩几个完整学年可提升
  const stem = /计算|软件|工程|数据|人工智能|电子|机械|材料|物理|数学|统计|生物|化学|信息|网络|通信/.test(p.field || "");

  // 找"跳一跳"目标档（优先名校档，否则优质档）
  const elite = bands.find((b) => b.key === "elite");
  const quality = bands.find((b) => b.key === "quality");
  const top = bands.find((b) => b.key === "top");
  const target = (elite && elite.avgTypical) ? elite : (quality || bands[0]);

  // 1) 均分诊断
  if (p.avg && target && target.avgTypical != null) {
    const need = Math.round(target.avgTypical);
    const gap = Math.round((need - p.avg) * 10) / 10;
    if (gap > 0) {
      // 每年需提升多少（还有 yearsLeft 年，若已大四则本季度末）
      const perYear = yearsLeft > 0 ? Math.ceil((gap / yearsLeft) * 10) / 10 : gap;
      const feasible = gap <= 3 ? "完全够得着" : gap <= 6 ? "有挑战但可行" : "难度较大，需持续发力";
      items.push({
        pri: gap <= 6 ? "high" : "mid",
        icon: "📊",
        title: `把均分从 ${p.avg} 提到 ${need}+（冲「${target.label}」还差 ${gap} 分）`,
        body: yearsLeft > 0
          ? `你还有约 ${yearsLeft} 个完整学年，平均每年提升 <strong>${perYear} 分</strong>即可，${feasible}。重点：抓专业核心课学分权重高的科目、避免任何挂科重修、低分课争取重修刷高。`
          : `已进入申请季，均分基本定型；把剩余课程稳住，同时用雅思/软背景/文书弥补，并把选校重心放在"${quality ? quality.label : "匹配档"}"更稳。`,
      });
    } else {
      items.push({
        pri: "low",
        icon: "✅",
        title: `均分 ${p.avg} 已达「${target.label}」参考线（${need}）`,
        body: `保持住别松懈，继续往更高档冲。${top && top.avgTypical ? `若想够世界顶尖（${top.label}），参考线约 ${Math.round(top.avgTypical)}，可作为拉高目标。` : ""}`,
      });
    }
  } else if (!p.avg) {
    items.push({
      pri: "high",
      icon: "📊",
      title: "先填入/上传你的目前均分",
      body: "均分是申研最核心的硬指标，填了才能算出你离各档还差多少。可直接上传成绩单截图自动计算。",
    });
  }

  // 2) 雅思诊断
  const targetIelts = (target && target.ieltsTypical) || 6.5;
  if (!p.ielts) {
    const when = p.grade <= 2 ? "大二起系统备考，大三下前考出" : p.grade === 3 ? "本学年内尽快考出" : "立刻刷分，别再拖";
    items.push({
      pri: p.grade >= 3 ? "high" : "mid",
      icon: "🗣️",
      title: `雅思还没考——目标档通常要 ${targetIelts}`,
      body: `建议${when}。雅思有效期 2 年，${p.grade <= 2 ? "现在先打基础、刷单词和听读语感，大二下再正式考更划算" : "口语写作是中国学生普遍弱项，尽早开练"}。多数英港新要总分 6.5、名校要 7.0。`,
    });
  } else if (p.ielts < targetIelts) {
    const d = Math.round((targetIelts - p.ielts) * 10) / 10;
    items.push({
      pri: "mid",
      icon: "🗣️",
      title: `雅思 ${p.ielts} → 目标档要 ${targetIelts}（差 ${d}）`,
      body: `还有时间，重点突破薄弱单项（小分卡线最常见）；名校常要求单项不低于 6.0/6.5，别只顾总分。`,
    });
  } else {
    items.push({
      pri: "low",
      icon: "🗣️",
      title: `雅思 ${p.ielts} 已达目标档参考线`,
      body: "达标即可，把精力转向均分和软背景；若冲 7.0 名校可再刷高。",
    });
  }

  // 3) 软背景诊断（结合具体填写内容）
  const ex = p.exp || { internships: [], research: [], competitions: [], papers: [] };
  const totalExp = p.soft.internships + p.soft.research + p.soft.competitions + p.soft.papers;
  const firstText = (arr, keys) => {
    if (!arr || !arr.length) return "";
    const it = arr[0];
    return keys.map((k) => it[k]).filter(Boolean).join(" · ");
  };
  const have = [];
  if (p.soft.internships) have.push(`${p.soft.internships} 段实习（如「${firstText(ex.internships, ["company", "role"])}」）`);
  if (p.soft.research) have.push(`${p.soft.research} 段科研（如「${firstText(ex.research, ["topic", "role"])}」）`);
  if (p.soft.competitions) have.push(`${p.soft.competitions} 项竞赛（如「${firstText(ex.competitions, ["name", "award"])}」）`);
  if (p.soft.papers) have.push(`${p.soft.papers} 篇论文（如「${firstText(ex.papers, ["title", "venue"])}」）`);
  const haveTxt = have.length ? `你已填：${have.join("；")}。` : "";
  const missing = [];
  if (stem) {
    if (!p.soft.research) missing.push("科研/课题（理工申研最看重）");
    if (!p.soft.competitions) missing.push("学科竞赛（数模/ACM/挑战杯）");
    if (!p.soft.internships) missing.push("对口实习");
  } else {
    if (!p.soft.internships) missing.push("对口实习（商科/文社科最看重）");
    if (!p.soft.competitions) missing.push("商赛/数模");
    if (!p.soft.research) missing.push("研究/课题助理");
  }
  const missTxt = missing.length ? `目前还缺：<strong>${missing.join("、")}</strong>。` : "";

  if (standing && standing.boost < 2 && yearsLeft >= 0) {
    items.push({
      pri: p.grade >= 3 ? "high" : "mid",
      icon: "💼",
      title: totalExp === 0 ? "软背景几乎空白——现在是积累的最好时机" : "软背景偏薄，建议尽快补强",
      body: `${haveTxt}${missTxt}` + (stem
        ? `理工科建议主动联系专业课老师进实验室做课题（争取 1–2 段有产出的科研），再叠加学科竞赛，这些能显著提升名校竞争力。`
        : `商科/文社科建议争取券商/银行/互联网/四大/名企实习 1–2 段，追求"有量化成果"；辅以商赛、数模。`),
    });
  } else if (standing && standing.boost >= 3) {
    items.push({
      pri: "low",
      icon: "💼",
      title: `软背景不错（等效 +${standing.boost} 分，${standing.softLevel}）`,
      body: `${haveTxt}继续深耕、把经历做出成果和故事线，文书里能讲清「做了什么、拿到什么结果」比堆数量更重要。${missTxt}`,
    });
  }

  // 4) 时间紧迫度提醒
  if (p.grade <= 2) {
    items.push({
      pri: "low",
      icon: "⏳",
      title: "你的最大优势是时间",
      body: "越早规划越主动：现在把绩点打高、方向探索清楚，到大三大四会非常从容。定期回来更新数据、看目标档变化。",
    });
  } else if (p.grade === 4) {
    items.push({
      pri: "high",
      icon: "⏳",
      title: "已进入申请季，行动要快",
      body: "9–12 月网申陆续开放，滚动录取先到先得——尽早定选校清单、写 PS/CV、联系推荐人并递交，别等 deadline。",
    });
  }

  // 排序：高 > 中 > 低
  const order = { high: 0, mid: 1, low: 2 };
  items.sort((a, b) => order[a.pri] - order[b.pri]);
  return items;
}

function renderPlan() {
  const p = readPlanProfile();
  const box = document.getElementById("plan-result");
  box.classList.remove("hidden");
  if (!DATA || !DATA.programs) {
    box.innerHTML = `<div class="empty">数据未加载，请刷新后重试。</div>`;
    return;
  }
  const bands = planTierBands(p);
  if (!bands.length) {
    box.innerHTML = `<div class="empty">没有匹配到项目，试着不填方向或放宽意向国家再生成。</div>`;
    return;
  }
  const standing = planCurrentStanding(p);
  const { years, target } = buildRoadmap(p, bands);
  const diagnosis = buildDiagnosis(p, bands, standing);

  // 现状定位
  let standingHtml = "";
  if (standing) {
    const total = standing.safe + standing.match + standing.reach;
    const w = wesGpa(p.avg);
    const wesLine = w
      ? `<p class="plan-wes">🇺🇸 若申美/加需 <strong>WES</strong> 认证：按你均分 ${p.avg} 估算 <strong>WES iGPA ≈ ${w.gpa.toFixed(1)} / 4.0（${w.grade}）</strong>。<span class="plan-hint">WES 逐门课按段位换算（85+=A、75–84=B、60–74=C），正式绩点以官方报告为准；用成绩单 OCR 可算更精确的逐课加权值。</span></p>`
      : "";
    standingHtml = `
      <div class="plan-card">
        <h3>📍 现状定位</h3>
        <p>按你目前的 <strong>${p.school ? p.school + " · " : ""}${p.tier} · 均分 ${p.avg}</strong>${p.ielts ? " · 雅思 " + p.ielts : ""}，
        软背景等效 <strong>+${standing.boost}</strong> 分（${standing.softLevel}），在你选的方向/国家里现在大致可以：</p>
        <div class="plan-standing">
          <span class="ps-item ps-safe">保底 ${standing.safe}</span>
          <span class="ps-item ps-match">匹配 ${standing.match}</span>
          <span class="ps-item ps-reach">冲刺 ${standing.reach}</span>
        </div>
        ${wesLine}
        <p class="plan-hint">这是"如果现在就毕业申请"的粗略定位；你还有时间，下面的路线图能帮你往上走。</p>
      </div>`;
  } else {
    standingHtml = `
      <div class="plan-card">
        <h3>📍 现状定位</h3>
        <p class="plan-hint">填入「目前均分」后，这里会显示你现在大致能匹配到的学校档位。</p>
      </div>`;
  }

  // 目标档位表
  const gapTag = (avgMin) => {
    if (!p.avg || avgMin == null) return "";
    const d = Math.round((p.avg - avgMin) * 10) / 10;
    if (d >= 0) return `<span class="gap ok">目前已达线（+${d}）</span>`;
    return `<span class="gap warn">还差约 ${Math.abs(d)} 分</span>`;
  };
  const bandsHtml = bands
    .map((b) => {
      const reps = b.reps
        .map((s) => `<span class="rep-school">${s.uni}${s.qs < 9999 ? `<em>#${s.qs}</em>` : ""}</span>`)
        .join("");
      const avgTxt = b.avgTypical != null
        ? `均分 <strong>${Math.round(b.avgTypical)}</strong> 左右${b.avgMin != null ? `（门槛约 ${Math.round(b.avgMin)}+）` : ""}`
        : "均分线暂无数据";
      const ieltsTxt = b.ieltsTypical != null ? `雅思 <strong>${b.ieltsTypical}</strong>` : "雅思见项目";
      return `
        <div class="band-row">
          <div class="band-head">
            <span class="band-label">${b.label}</span>
            <span class="band-qs">${b.qs} · ${b.count} 个项目</span>
          </div>
          <div class="band-req">🎯 ${avgTxt} · 🗣️ ${ieltsTxt} ${gapTag(b.avgMin)}</div>
          <div class="band-reps">${reps}</div>
        </div>`;
    })
    .join("");

  // 路线图
  const roadmapHtml = years
    .map(
      (y) => `
      <div class="rm-year">
        <div class="rm-year-title">${y.title}</div>
        <ul class="rm-tasks">
          <li><strong>📊 绩点：</strong>${y.gpa}</li>
          <li><strong>🗣️ 语言：</strong>${y.lang}</li>
          <li><strong>💼 经历：</strong>${y.exp}</li>
          <li><strong>🗂️ 选校/文书：</strong>${y.plan}</li>
        </ul>
      </div>`
    )
    .join("");

  // 针对性诊断建议（按优先级）
  const priLabel = { high: "高优先", mid: "建议", low: "锦上添花" };
  const diagHtml = diagnosis
    .map(
      (d) => `
      <div class="diag-item diag-${d.pri}">
        <div class="diag-top">
          <span class="diag-icon">${d.icon}</span>
          <span class="diag-title">${d.title}</span>
          <span class="diag-pri diag-pri-${d.pri}">${priLabel[d.pri]}</span>
        </div>
        <p class="diag-body">${d.body}</p>
      </div>`
    )
    .join("");

  // 已填经历回顾（把具体内容原样呈现，便于核对与文书取材）
  const ex = p.exp || { internships: [], research: [], competitions: [], papers: [] };
  const expGroup = (title, arr, keys) => {
    if (!arr || !arr.length) return "";
    const rows = arr
      .map((it) => {
        const head = keys.map((k) => it[k]).filter(Boolean).join(" · ");
        const desc = (it.desc || "").trim();
        return `<li><strong>${head || "（未填写标题）"}</strong>${desc ? `<br><span class="exp-desc">${desc}</span>` : ""}</li>`;
      })
      .join("");
    return `<div class="exp-group"><div class="exp-group-title">${title}</div><ul class="exp-items">${rows}</ul></div>`;
  };
  const expBody =
    expGroup("💼 实习", ex.internships, ["company", "role", "period"]) +
    expGroup("🔬 科研 / 课题", ex.research, ["topic", "role", "period"]) +
    expGroup("🏆 竞赛", ex.competitions, ["name", "award", "period"]) +
    expGroup("📄 论文", ex.papers, ["title", "venue", "period"]);
  const expHtml = expBody
    ? `<div class="plan-card">
        <h3>🗂️ 你填写的经历</h3>
        <p class="plan-hint">下面是你填的具体内容，规划已据此给出针对性建议；这些也是将来写 PS/CV 的素材。</p>
        ${expBody}
      </div>`
    : "";

  box.innerHTML = `
    ${standingHtml}
    <div class="plan-card">
      <h3>🔑 现在最该做什么（按优先级）</h3>
      <p class="plan-hint">根据你当前均分离目标的差距、雅思与软背景现状，为你排好了先后顺序。</p>
      <div class="diag-list">${diagHtml}</div>
    </div>
    <div class="plan-card">
      <h3>🎯 目标档位：想去哪，均分要保持在多少</h3>
      <p class="plan-hint">下面按学校档位列出你所在层次通常需要的均分线与雅思（数据来自本站项目库；均分为中国大陆申请参考线，非官方保证）。</p>
      <div class="bands">${bandsHtml}</div>
    </div>
    ${expHtml}
    <div class="plan-card">
      <h3>🗓️ 你的行动路线图（${years[0].title} → 毕业申请）</h3>
      <div class="roadmap">${roadmapHtml}</div>
    </div>
    <p class="disclaimer">本规划为基于公开数据与普遍规律的<strong>参考建议</strong>，不构成录取保证。真实录取受名额、竞争、文书、面试、科研实习等多因素影响，请结合各校官方要求综合判断。</p>`;

  track("plan_generate", `${p.grade}年级/${p.tier}/${p.field || "不限"}`);
  box.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ============ AI 文书辅助 ============ */
async function renderSOP() {
  const el = document.getElementById("sop-section");
  el.classList.remove("hidden");
  el.innerHTML = "⏳ 正在根据你的背景与选校生成文书建议…";
  let profile = {};
  try {
    profile = readProfile();
  } catch {}
  let data;
  try {
    data = await api("/api/sop", "POST", { program_ids: SHORTLIST_IDS, profile });
  } catch (e) {
    el.innerHTML = `<div class="empty">生成失败：${e.message}</div>`;
    return;
  }
  const c = data.competitiveness;
  const ps = data.psOutline
    .map(
      (s) =>
        `<div class="sop-sec"><h4>${s.section}</h4><ul>${s.tips
          .map((t) => `<li>${t}</li>`)
          .join("")}</ul></div>`
    )
    .join("");
  const cv = data.cvBullets.map((b) => `<li>${b}</li>`).join("");
  el.innerHTML = `
    <h2>✍️ AI 文书辅助（基于 ${data.programCount} 个选校）</h2>
    <div class="sop-comp" style="border-left-color:${
      c.level === "强" ? "#34d399" : c.level === "中等" ? "#60a5fa" : "#fbbf24"
    }">
      <strong>竞争力评估：${c.level}（${c.score}/100，均分加成 +${c.boost}）</strong>
      <p>${c.comment}</p>
    </div>
    <div class="checklist-grid">
      <div class="card sub"><h3>📝 PS / SOP 结构提纲</h3>${ps}</div>
      <div class="card sub"><h3>📄 CV 撰写建议</h3><ul class="doc-list">${cv}</ul></div>
    </div>
    <p class="disclaimer">${data.disclaimer}</p>`;
  el.scrollIntoView({ behavior: "smooth" });
}

/* ============ 导出 PDF / Excel ============ */
async function exportPlan(kind) {
  if (!SHORTLIST_IDS.length) {
    alert("请先收藏至少一个项目再导出");
    return;
  }
  const items = SHORTLIST_IDS.map((id) => {
    const t = trackOf(id);
    return { program_id: id, status: t.status, deadline: t.deadline, note: t.note };
  });
  const path = kind === "pdf" ? "/api/export/plan.pdf" : "/api/export/shortlist.xlsx";
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items }),
    });
    if (!res.ok) throw new Error("导出失败");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = kind === "pdf" ? "申请规划.pdf" : "选校清单.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert(e.message);
  }
}

/* ============ 账号 UI ============ */
function renderAccount() {
  const el = document.getElementById("account");
  const auth = getAuth();
  if (auth) {
    el.innerHTML = `
      <span class="welcome">👤 ${auth.username}</span>
      <button class="btn-link" id="logout-btn">退出</button>`;
    document.getElementById("logout-btn").onclick = doLogout;
  } else {
    el.innerHTML = `
      <div class="auth-form">
        <input id="auth-user" placeholder="用户名" autocomplete="username" />
        <input id="auth-pwd" type="password" placeholder="密码" autocomplete="current-password" />
        <button class="btn-link" id="login-btn">登录</button>
        <button class="btn-link" id="register-btn">注册</button>
      </div>
      <div class="auth-msg" id="auth-msg"></div>`;
    document.getElementById("login-btn").onclick = () => doAuth("/api/login");
    document.getElementById("register-btn").onclick = () => doAuth("/api/register");
  }
}
async function doAuth(path) {
  const username = document.getElementById("auth-user").value.trim();
  const password = document.getElementById("auth-pwd").value;
  const msg = document.getElementById("auth-msg");
  if (!username || !password) {
    msg.textContent = "请输入用户名和密码";
    return;
  }
  try {
    const data = await api(path, "POST", { username, password });
    localStorage.setItem(AUTH_KEY, JSON.stringify(data));
    // 把本地游客收藏与进度合并到账号
    const local = getLocalShortlist();
    const localTrack = getLocalTrack();
    for (const id of local) {
      try {
        await api("/api/shortlist", "POST", { program_id: id });
        const t = localTrack[id];
        if (t && (t.status !== "待定" || t.deadline || t.note)) {
          await api("/api/shortlist", "PATCH", {
            program_id: id,
            status: t.status,
            deadline: t.deadline || "",
            note: t.note || "",
          });
        }
      } catch {}
    }
    renderAccount();
    await loadShortlist();
  } catch (e) {
    msg.textContent = e.message;
  }
}
async function doLogout() {
  try {
    await api("/api/logout", "POST");
  } catch {}
  localStorage.removeItem(AUTH_KEY);
  renderAccount();
  await loadShortlist();
}

/* ============ 初始化 ============ */
function setupSchoolAutocomplete({ schoolId, hintId, acId, tierId, coop }) {
  const schoolInput = document.getElementById(schoolId);
  const hint = document.getElementById(hintId);
  const uniAc = document.getElementById(acId);
  if (!schoolInput || !hint || !uniAc) return;
  let uniAcIndex = -1;

  function refreshTierHint() {
    const tier = detectTier(schoolInput.value);
    const uni = UNI_MAP[schoolInput.value.trim()];
    if (tier) {
      const tierSel = document.getElementById(tierId);
      if (tierSel) tierSel.value = tier;
      if (coop && uni && uni.partner) {
        hint.innerHTML =
          `✅ 已识别：<strong>${tier}</strong>（${uni.province}）<br>` +
          `<span class="coop-banner">🎓 中外合作大学：申研以合作方【${uni.partner}（${uni.degreeRegion}）】海外学位申请。` +
          `${uni.coopNote || ""}</span>`;
      } else {
        hint.innerHTML = `✅ 已识别：<strong>${tier}</strong>（${uni.province}）`;
      }
      hint.className = "hint ok-hint";
    } else if (schoolInput.value.trim()) {
      hint.innerHTML = "未在列表中找到，请手动选择院校层次";
      hint.className = "hint";
    } else {
      hint.textContent = "选择院校后将自动识别院校层次";
      hint.className = "hint";
    }
  }

  function closeUniAc() {
    uniAc.hidden = true;
    uniAc.innerHTML = "";
    uniAcIndex = -1;
  }

  // 按院校名或省份过滤（如输入「北京」列出所有北京院校）
  function renderUniAc() {
    const q = schoolInput.value.trim().toLowerCase();
    if (!q) { closeUniAc(); return; }
    const matches = UNIVERSITIES.filter((x) => {
      const name = x.name.toLowerCase();
      const prov = (x.province || "").toLowerCase();
      const tier = (x.tier || "").toLowerCase();
      return name.includes(q) || prov.includes(q) || tier.includes(q);
    }).slice(0, 60);

    if (!matches.length) {
      uniAc.innerHTML = `<div class="ac-empty">未找到匹配院校，可直接手动选择院校层次</div>`;
      uniAc.hidden = false;
      uniAcIndex = -1;
      return;
    }
    uniAc.innerHTML = matches
      .map(
        (x) =>
          `<div class="ac-item" data-name="${x.name}">` +
          `<span>${x.name}</span>` +
          `<span class="ac-meta">${x.tier} · ${x.province}</span></div>`
      )
      .join("");
    uniAc.hidden = false;
    uniAcIndex = -1;
    uniAc.querySelectorAll(".ac-item").forEach((el) => {
      el.addEventListener("mousedown", (e) => {
        e.preventDefault();
        schoolInput.value = el.dataset.name;
        closeUniAc();
        refreshTierHint();
      });
    });
  }

  schoolInput.addEventListener("input", () => {
    renderUniAc();
    refreshTierHint();
  });
  schoolInput.addEventListener("focus", renderUniAc);
  schoolInput.addEventListener("blur", () => setTimeout(closeUniAc, 120));
  schoolInput.addEventListener("keydown", (e) => {
    if (uniAc.hidden) return;
    const items = [...uniAc.querySelectorAll(".ac-item")];
    if (!items.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      uniAcIndex += e.key === "ArrowDown" ? 1 : -1;
      if (uniAcIndex < 0) uniAcIndex = items.length - 1;
      if (uniAcIndex >= items.length) uniAcIndex = 0;
      items.forEach((el, i) => el.classList.toggle("active", i === uniAcIndex));
      items[uniAcIndex].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && uniAcIndex >= 0) {
      e.preventDefault();
      schoolInput.value = items[uniAcIndex].dataset.name;
      closeUniAc();
      refreshTierHint();
    } else if (e.key === "Escape") {
      closeUniAc();
    }
  });
}

async function init() {
  renderAccount();

  try {
    DATA = await loadJSON("data/programs.json");
    document.getElementById("disclaimer").textContent = DATA.meta.disclaimer;
    PROGRAM_FIELDS = new Set(DATA.programs.map((p) => p.field));
  } catch (e) {
    document.getElementById("disclaimer").textContent = "数据加载失败：" + e.message;
  }

  // 院校
  try {
    const u = await loadJSON("data/universities.json");
    UNIVERSITIES = u.universities;
    UNIVERSITIES.forEach((x) => { UNI_MAP[x.name] = x; });
  } catch {}

  // 专业 + 研究生方向
  try {
    const mj = await loadJSON("data/majors.json");
    MAJORS = mj.undergradMajors;
    GRAD_FIELDS = mj.meta.gradFields;
    document.getElementById("major-list").innerHTML = MAJORS.map((m) => {
      MAJOR_MAP[m.name] = m;
      return `<option value="${m.name}">${m.category}</option>`;
    }).join("");
    document.getElementById("gradfield-list").innerHTML =
      GRAD_FIELDS.map((f) => `<option value="${f}">研究生方向</option>`).join("");
    document.getElementById("plan-field-list").innerHTML =
      GRAD_FIELDS.map((f) => `<option value="${f}">研究生方向</option>`).join("");
  } catch {}
  renderSelectedFields();

  // 参考案例库
  try {
    const cs = await loadJSON("data/cases.json");
    initCasesView(cs);
  } catch {}

  // 政策知识库
  try {
    const pol = await loadJSON("data/policies.json");
    initPoliciesView(pol);
  } catch {}

  // 顶部导航切换
  document.querySelectorAll(".nav-btn").forEach((b) => {
    b.addEventListener("click", () => switchView(b.dataset.view));
  });

  // 院校 → 层次识别（主匹配页 + 早规划页复用）
  setupSchoolAutocomplete({
    schoolId: "school", hintId: "school-hint", acId: "uni-ac", tierId: "tier", coop: true,
  });
  setupSchoolAutocomplete({
    schoolId: "plan-school", hintId: "plan-school-hint", acId: "plan-uni-ac", tierId: "plan-tier", coop: false,
  });

  // 本科专业 → 推荐研究生方向（列表外专业走 AI 识别，输入防抖）
  let majorTimer = null;
  const undergradInput = document.getElementById("undergradMajor");
  undergradInput.addEventListener("input", (e) => {
    const v = e.target.value.trim();
    clearTimeout(majorTimer);
    // 预设列表里的专业立即出推荐；列表外的延迟 500ms 再请求 AI
    if (MAJOR_MAP[v] || !v) renderRecommend(v);
    else majorTimer = setTimeout(() => renderRecommend(v), 500);
  });

  // 研究生方向多选：输入框回车 / 点「添加」/ 从下拉选择 都加入已选
  const gradInput = document.getElementById("gradField");
  function commitGradInput() {
    const v = gradInput.value.trim();
    if (v) {
      addGradField(v);
      gradInput.value = "";
    }
  }
  document.getElementById("addGradField").addEventListener("click", commitGradInput);
  gradInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      commitGradInput();
    }
  });
  // 从 datalist 选择某项时（input 事件且值恰为完整选项）自动加入
  gradInput.addEventListener("change", () => {
    const v = gradInput.value.trim();
    if (v && (GRAD_FIELDS.includes(v) || PROGRAM_FIELDS.has(v))) {
      addGradField(v);
      gradInput.value = "";
    }
  });

  // 成绩类型切换
  document.querySelectorAll('input[name="scoreType"]').forEach((r) => {
    r.addEventListener("change", () => {
      const isGpa = getScoreType() === "gpa";
      document.getElementById("avg-field").classList.toggle("hidden", isGpa);
      document.getElementById("gpa-field").classList.toggle("hidden", !isGpa);
      updateWesHint();
    });
  });
  function updateGpaHint() {
    const gpa = parseFloat(document.getElementById("gpa").value) || 0;
    const pct = gpaToPercentage(gpa, document.getElementById("gpaScale").value);
    document.getElementById("gpa-converted").textContent = gpa ? `≈ 百分制 ${pct} 分（估算，用于匹配）` : "";
    updateWesHint();
  }
  function updateWesHint() {
    const pct = readAvg();
    const w = wesGpa(pct);
    const el = document.getElementById("wes-est");
    if (!el) return;
    el.textContent = w
      ? `≈ WES iGPA ${w.gpa.toFixed(1)} / 4.0（${w.grade}）· 申美/加常用，逐门课加权后以官方报告为准`
      : "";
  }
  document.getElementById("gpa").addEventListener("input", updateGpaHint);
  document.getElementById("gpaScale").addEventListener("change", updateGpaHint);
  document.getElementById("avg").addEventListener("input", updateWesHint);
  updateWesHint();

  // 提交匹配
  document.getElementById("profile-form").addEventListener("submit", (e) => {
    e.preventDefault();
    if (!DATA) return;
    const profile = readProfile();
    const buckets = matchPrograms(DATA.programs, profile);
    render(buckets, profile);

    // 埋点：执行匹配 + 搜索维度 + 无结果
    const total = ["保底", "匹配", "冲刺", "超出"].reduce((s, k) => s + (buckets[k] ? buckets[k].length : 0), 0);
    track("run_match", `tier=${profile.tier || ""};total=${total}`);
    if (profile.school) track("search", "院校:" + profile.school);
    (profile.countries || []).forEach((c) => track("search", "国家:" + c));
    if (profile.undergradMajor) track("search", "本科专业:" + profile.undergradMajor);
    (profile.fields || []).forEach((f) => track("search", "研究生方向:" + f));
    if (total === 0) {
      track("no_result", `国家:${(profile.countries || []).join("/") || "全部"};方向:${(profile.fields || []).join("/") || "全部"}`);
    }
  });

  document.getElementById("checklist-btn").onclick = renderChecklist;
  document.getElementById("sop-btn").onclick = renderSOP;
  document.getElementById("export-pdf-btn").onclick = () => exportPlan("pdf");
  document.getElementById("export-xlsx-btn").onclick = () => exportPlan("xlsx");

  // 简历上传
  document.getElementById("resume-pick").onclick = () =>
    document.getElementById("resume-file").click();
  document.getElementById("resume-file").addEventListener("change", (e) => {
    if (e.target.files[0]) handleResume(e.target.files[0]);
  });

  // 成绩单截图 OCR
  document.getElementById("transcript-pick").onclick = () =>
    document.getElementById("transcript-file").click();
  document.getElementById("transcript-file").addEventListener("change", (e) => {
    if (e.target.files[0]) handleTranscript(e.target.files[0]);
    e.target.value = "";
  });

  // 早规划：表单提交 + 成绩单 OCR
  document.getElementById("plan-form").addEventListener("submit", (e) => {
    e.preventDefault();
    renderPlan();
  });
  document.getElementById("plan-transcript-pick").onclick = () =>
    document.getElementById("plan-transcript-file").click();
  document.getElementById("plan-transcript-file").addEventListener("change", (e) => {
    if (e.target.files[0]) handleTranscript(e.target.files[0], TS_PLAN);
    e.target.value = "";
  });

  // 经历动态条目（实习/项目/校园活动/交换）
  Object.keys(ENTRY_KINDS).forEach((kind) => {
    const btn = document.getElementById(ENTRY_KINDS[kind].addId);
    if (btn) btn.onclick = () => addEntry(kind);
    renderEntries(kind);
  });

  // 软背景实时预览
  ["papers", "paperLevel", "competitions", "competitionLevel",
   "research", "workYears", "certificates"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", updateSoftPreview);
  });
  updateSoftPreview();

  await loadShortlist();
}

/* ============ 视图切换 ============ */
function switchView(view) {
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  const target = document.getElementById("view-" + view);
  if (target) target.classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === view)
  );
  track("view", view);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ============ 申研参考案例 ============ */
const OUTCOME_META = {
  admit: { cls: "oc-admit", label: "可录取", tip: "匹配/保底区间" },
  reach: { cls: "oc-reach", label: "可冲刺", tip: "有机会但不稳" },
  risky: { cls: "oc-risky", label: "偏高风险", tip: "难度大，需强背景/早申" },
};

function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function caseCard(c) {
  const gpaBits = [];
  if (c.gpa) {
    if (c.gpa.pct) gpaBits.push(`均分 ${c.gpa.pct}`);
    if (c.gpa.scale4) gpaBits.push(`GPA ${c.gpa.scale4}/4.0`);
    if (c.gpa.ukClass) gpaBits.push(`英式 ${c.gpa.ukClass}`);
  }
  const gpaStr = gpaBits.join(" · ") || "均分见画像";
  let langStr = "语言见项目";
  if (c.ielts) {
    if (c.ielts.waiver) langStr = c.ielts.waiver;
    else if (c.ielts.overall) langStr = `雅思 ${c.ielts.overall}${c.ielts.sub ? "（小分 " + c.ielts.sub + "）" : ""}`;
  }
  const greStr = c.gre ? `GRE ${c.gre.total}${c.gre.quant ? "（数学 " + c.gre.quant + "）" : ""}` : "无 GRE";
  const bg = (c.background || []).map((b) => `<span class="bg-chip">${escapeHtml(b)}</span>`).join("");
  const results = (c.results || [])
    .map((r) => {
      const m = OUTCOME_META[r.outcome] || OUTCOME_META.reach;
      return `<li class="case-result">
        <span class="oc ${m.cls}" title="${m.tip}">${m.label}</span>
        <span class="cr-school">${escapeHtml(r.school)}</span>
        <span class="cr-prog">${escapeHtml(r.program)}</span>
        <span class="cr-region">${escapeHtml(r.region || "")}</span>
      </li>`;
    })
    .join("");
  return `
    <div class="case-card">
      <div class="case-head">
        <div class="case-tier">${escapeHtml(c.tier)}</div>
        <div class="case-major">${escapeHtml(c.major)}</div>
      </div>
      <div class="case-stats">
        <span>📊 ${escapeHtml(gpaStr)}</span>
        <span>🗣️ ${escapeHtml(langStr)}</span>
        <span>📝 ${escapeHtml(greStr)}</span>
      </div>
      ${bg ? `<div class="case-bg">${bg}</div>` : ""}
      <ul class="case-results">${results}</ul>
      ${c.takeaway ? `<div class="case-takeaway">💡 ${escapeHtml(c.takeaway)}</div>` : ""}
    </div>`;
}

function renderCases() {
  const tier = document.getElementById("case-tier").value;
  const kw = (document.getElementById("case-major").value || "").trim().toLowerCase();
  const list = CASES.filter((c) => {
    if (tier && c.tier !== tier) return false;
    if (kw) {
      const hay = (c.major + " " + (c.results || []).map((r) => r.program).join(" ")).toLowerCase();
      if (!hay.includes(kw)) return false;
    }
    return true;
  });
  const box = document.getElementById("case-list");
  box.innerHTML = list.length
    ? list.map(caseCard).join("")
    : `<p class="empty">没有匹配的参考画像，试试放宽筛选条件。</p>`;
}

function initCasesView(data) {
  CASES = data.cases || [];
  const legend = document.getElementById("case-legend");
  if (legend) {
    legend.innerHTML = Object.values(OUTCOME_META)
      .map((m) => `<span class="lg-item"><span class="oc ${m.cls}">${m.label}</span> ${m.tip}</span>`)
      .join("");
  }
  document.getElementById("case-disclaimer").textContent = data.meta.disclaimer;
  document.getElementById("case-tier").addEventListener("change", renderCases);
  document.getElementById("case-major").addEventListener("input", renderCases);
  renderCases();
}

/* ============ 政策知识库 ============ */
function policyCard(p) {
  const cat = POLICY_CATS.find((c) => c.id === p.category);
  const catLabel = cat ? `${cat.icon} ${cat.name}` : p.category;
  const regions = (p.regions || []).map((r) => `<span class="pl-region">${escapeHtml(r)}</span>`).join("");
  const points = (p.points || []).map((pt) => `<li>${escapeHtml(pt)}</li>`).join("");
  const tags = (p.tags || []).map((t) => `<span class="pl-tag">#${escapeHtml(t)}</span>`).join("");
  return `
    <details class="policy-item">
      <summary>
        <span class="pl-title">${escapeHtml(p.title)}</span>
        <span class="pl-meta">${catLabel}</span>
      </summary>
      <div class="pl-body">
        <div class="pl-regions">${regions}</div>
        <p class="pl-summary">${escapeHtml(p.summary)}</p>
        <ul class="pl-points">${points}</ul>
        ${p.pitfall ? `<div class="pl-pitfall">⚠️ 常见误区：${escapeHtml(p.pitfall)}</div>` : ""}
        <div class="pl-tags">${tags}</div>
      </div>
    </details>`;
}

function renderPolicies() {
  const kw = (document.getElementById("policy-search").value || "").trim().toLowerCase();
  const list = POLICIES.filter((p) => {
    if (activePolicyCat && p.category !== activePolicyCat) return false;
    if (kw) {
      const hay = (p.title + " " + p.summary + " " + (p.points || []).join(" ") +
        " " + (p.pitfall || "") + " " + (p.tags || []).join(" ")).toLowerCase();
      if (!hay.includes(kw)) return false;
    }
    return true;
  });
  const box = document.getElementById("policy-list");
  box.innerHTML = list.length
    ? list.map(policyCard).join("")
    : `<p class="empty">没有匹配的政策条目，换个关键词试试。</p>`;
}

function renderPolicyCats() {
  const box = document.getElementById("policy-cats");
  const all = `<button type="button" class="pcat ${activePolicyCat === "" ? "active" : ""}" data-cat="">全部</button>`;
  box.innerHTML = all + POLICY_CATS.map((c) =>
    `<button type="button" class="pcat ${activePolicyCat === c.id ? "active" : ""}" data-cat="${c.id}">${c.icon} ${escapeHtml(c.name)}</button>`
  ).join("");
  box.querySelectorAll(".pcat").forEach((b) => {
    b.addEventListener("click", () => {
      activePolicyCat = b.dataset.cat;
      renderPolicyCats();
      renderPolicies();
    });
  });
}

function initPoliciesView(data) {
  POLICIES = data.policies || [];
  POLICY_CATS = data.categories || [];
  document.getElementById("policy-disclaimer").textContent = data.meta.disclaimer;
  renderPolicyCats();
  document.getElementById("policy-search").addEventListener("input", renderPolicies);
  renderPolicies();
}

init();
track("page_view");
