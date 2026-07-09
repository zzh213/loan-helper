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
      updateSoftPreview();
    };
  });
  host.querySelectorAll(".entry-desc").forEach((el) => {
    el.oninput = () => { cfg.store[el.dataset.idx].desc = el.value; };
  });
  host.querySelectorAll(".entry-del").forEach((el) => {
    el.onclick = () => {
      cfg.store.splice(el.dataset.idx, 1);
      renderEntries(kind);
      updateSoftPreview();
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

  // 院校 → 层次识别
  const schoolInput = document.getElementById("school");
  const hint = document.getElementById("school-hint");
  const uniAc = document.getElementById("uni-ac");
  let uniAcIndex = -1;

  function refreshTierHint() {
    const tier = detectTier(schoolInput.value);
    const uni = UNI_MAP[schoolInput.value.trim()];
    if (tier) {
      document.getElementById("tier").value = tier;
      if (uni && uni.partner) {
        hint.innerHTML =
          `✅ 已识别：<strong>${tier}</strong>（${uni.province}）<br>` +
          `<span class="coop-banner">🎓 中外合作大学：申研以合作方【${uni.partner}（${uni.degreeRegion}）】海外学位申请。` +
          `${uni.coopNote || ""}</span>`;
      } else {
        hint.innerHTML = `✅ 已识别：<strong>${tier}</strong>（${uni.province}）`;
      }
      hint.className = "hint ok-hint";
    } else if (schoolInput.value.trim()) {
      hint.innerHTML = "未在列表中找到，请在右侧手动选择院校层次";
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
      uniAc.innerHTML = `<div class="ac-empty">未找到匹配院校，可直接手动选择右侧院校层次</div>`;
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

  // 反馈组件
  const fbModal = document.getElementById("fb-modal");
  const fbTip = document.getElementById("fb-tip");
  const openFb = () => {
    fbModal.hidden = false;
    fbTip.textContent = "";
    track("feedback_open");
  };
  const closeFb = () => { fbModal.hidden = true; };
  document.getElementById("fb-fab").onclick = openFb;
  document.getElementById("fb-close").onclick = closeFb;
  fbModal.addEventListener("click", (e) => { if (e.target === fbModal) closeFb(); });
  document.getElementById("fb-submit").onclick = async () => {
    const msg = document.getElementById("fb-message").value.trim();
    if (!msg) { fbTip.style.color = "#f0729a"; fbTip.textContent = "请填写反馈内容"; return; }
    const btn = document.getElementById("fb-submit");
    btn.disabled = true;
    try {
      await api("/api/feedback", "POST", {
        category: document.getElementById("fb-category").value,
        message: msg,
        contact: document.getElementById("fb-contact").value.trim(),
        path: location.pathname,
        session: trackSession(),
      });
      fbTip.style.color = "";
      fbTip.textContent = "✅ 已收到，感谢你的反馈！";
      document.getElementById("fb-message").value = "";
      document.getElementById("fb-contact").value = "";
      track("feedback_submit", document.getElementById("fb-category").value);
      setTimeout(() => { fbModal.hidden = true; }, 1200);
    } catch (err) {
      fbTip.style.color = "#f0729a";
      fbTip.textContent = "提交失败：" + err.message;
    } finally {
      btn.disabled = false;
    }
  };

  // 简历上传
  document.getElementById("resume-pick").onclick = () =>
    document.getElementById("resume-file").click();
  document.getElementById("resume-file").addEventListener("change", (e) => {
    if (e.target.files[0]) handleResume(e.target.files[0]);
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
