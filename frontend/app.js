const form = document.getElementById("loan-form");
const resultEl = document.getElementById("result");
const submitBtn = document.getElementById("submit-btn");

/* ===================== 轻提示 Toast ===================== */
function showToast(message, type = "info") {
  let host = document.getElementById("toast-host");
  if (!host) {
    host = document.createElement("div");
    host.id = "toast-host";
    host.setAttribute("aria-live", "polite");
    document.body.appendChild(host);
  }
  const icons = { info: "ℹ️", success: "✅", error: "⚠️" };
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span class="toast-ico" aria-hidden="true">${icons[type] || icons.info}</span><span>${escapeHtml(message)}</span>`;
  host.appendChild(el);
  requestAnimationFrame(() => el.classList.add("show"));
  setTimeout(() => {
    el.classList.remove("show");
    setTimeout(() => el.remove(), 300);
  }, 3200);
}

/* ===================== 表单校验 ===================== */
function clearFieldError(field) {
  field.classList.remove("invalid");
  const msg = field.parentElement.querySelector(".field-error");
  if (msg) msg.remove();
}

function setFieldError(field, text) {
  field.classList.add("invalid");
  let msg = field.parentElement.querySelector(".field-error");
  if (!msg) {
    msg = document.createElement("small");
    msg.className = "field-error";
    field.parentElement.appendChild(msg);
  }
  msg.textContent = text;
}

function validateForm(profile) {
  const errors = [];
  const fieldOf = (name) => form.querySelector(`[name="${name}"]`);
  form.querySelectorAll(".invalid").forEach((f) => clearFieldError(f));

  if (!(profile.years_in_business >= 0)) {
    setFieldError(fieldOf("years_in_business"), "请填写有效的经营年限");
    errors.push("经营年限");
  }
  if (!(profile.annual_revenue > 0)) {
    setFieldError(fieldOf("annual_revenue"), "年营业额需大于 0");
    errors.push("年营业额");
  }
  if (!(profile.loan_amount > 0)) {
    setFieldError(fieldOf("loan_amount"), "期望贷款金额需大于 0");
    errors.push("期望贷款金额");
  }
  if (!(profile.preferred_term_months > 0)) {
    setFieldError(fieldOf("preferred_term_months"), "期望期限需大于 0");
    errors.push("期望期限");
  }
  // 合理性温馨提示(不阻断)
  if (profile.annual_revenue > 0 && profile.loan_amount > profile.annual_revenue * 3) {
    showToast("提示:期望贷款金额超过年营业额的 3 倍,通过率可能较低", "info");
  }
  return errors;
}

function renderSkeleton() {
  resultEl.classList.remove("hidden");
  resultEl.innerHTML = `
    <div class="skeleton-box">
      <div class="sk-line sk-title"></div>
      <div class="sk-line w80"></div>
      <div class="sk-line w60"></div>
      <div class="sk-cards">
        <div class="sk-card"></div>
        <div class="sk-card"></div>
        <div class="sk-card"></div>
      </div>
    </div>`;
}

function collectProfile() {
  const fd = new FormData(form);
  return {
    company_name: fd.get("company_name") || "",
    industry: effectiveIndustry().industry,
    industry_detail: effectiveIndustry().detail,
    years_in_business: parseFloat(fd.get("years_in_business")) || 0,
    annual_revenue: parseFloat(fd.get("annual_revenue")) || 0,
    registered_capital: parseFloat(fd.get("registered_capital")) || 0,
    employees: parseInt(fd.get("employees")) || 0,
    credit_level: fd.get("credit_level"),
    has_overdue: fd.get("has_overdue") === "on",
    has_collateral: fd.get("has_collateral") === "on",
    collateral_value: parseFloat(fd.get("collateral_value")) || 0,
    has_tax_record: fd.get("has_tax_record") === "on",
    has_invoice: fd.get("has_invoice") === "on",
    loan_amount: parseFloat(fd.get("loan_amount")) || 0,
    loan_purpose: fd.get("loan_purpose"),
    preferred_term_months: parseInt(fd.get("preferred_term_months")) || 12,
    urgent: fd.get("urgent") === "on",
    industry_bonus: Array.from(document.querySelectorAll(".ind-bonus:checked")).map((c) => c.value),
  };
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const profile = collectProfile();

  const errors = validateForm(profile);
  if (errors.length) {
    showToast(`请检查:${errors.join("、")}`, "error");
    const firstInvalid = form.querySelector(".invalid");
    if (firstInvalid) firstInvalid.focus();
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "匹配中...";
  renderSkeleton();

  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!res.ok) throw new Error("请求失败:" + res.status);
    const data = await res.json();
    window.__lastProfile = profile;
    window.__lastMode = "enterprise";
    render(data);
    showToast("已为你匹配最优方案", "success");
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    resultEl.innerHTML = `<div class="empty err-empty">😕 匹配遇到问题:${escapeHtml(err.message)}<br><button id="retry-match" class="export-btn">🔄 重试一次</button><br><small style="color:#8a98a8">多次失败?点右下角💬 智能助手或拨打客户经理热线,我们帮你人工匹配。</small></div>`;
    resultEl.classList.remove("hidden");
    const rb = document.getElementById("retry-match");
    if (rb) rb.addEventListener("click", () => form.requestSubmit());
    showToast("匹配失败,请稍后重试", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "🔍 智能匹配最优方案";
  }
});

const preauditBtn = document.getElementById("preaudit-btn");
const preauditEl = document.getElementById("preaudit-result");
if (preauditBtn) {
  preauditBtn.addEventListener("click", async () => {
    const profile = collectProfile();
    const errors = validateForm(profile);
    if (errors.length) {
      showToast(`请检查:${errors.join("、")}`, "error");
      const fi = form.querySelector(".invalid");
      if (fi) fi.focus();
      return;
    }
    preauditBtn.disabled = true;
    preauditBtn.textContent = "预审中...";
    try {
      const res = await fetch("/api/preaudit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!res.ok) throw new Error("请求失败:" + res.status);
      renderPreaudit(await res.json());
      preauditEl.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      preauditEl.innerHTML = `<div class="empty">预审失败:${escapeHtml(err.message)}</div>`;
      preauditEl.classList.remove("hidden");
    } finally {
      preauditBtn.disabled = false;
      preauditBtn.textContent = "🛡️ 前置预审(提交前先体检)";
    }
  });
}

function renderPreaudit(d) {
  const vClass = { pass: "pa-pass", optimize: "pa-opt", risk: "pa-risk" }[d.verdict] || "pa-opt";
  const ws = (d.weaknesses || []).map((w) => {
    const sev = { high: "高", medium: "中", low: "低" }[w.severity] || "";
    return `<div class="pa-item pa-${w.severity}">
      <div class="pa-item-h"><span class="pa-sev">${sev}</span><b>${escapeHtml(w.title)}</b>
        ${w.minus ? `<span class="pa-minus">-${w.minus}分</span>` : ""}</div>
      <div class="pa-issue">⚠️ ${escapeHtml(w.issue)}</div>
      <div class="pa-fix">✅ 整改建议:${escapeHtml(w.fix)}</div>
    </div>`;
  }).join("");
  preauditEl.innerHTML = `<div class="card pa-card">
    <h3>🛡️ 前置预审报告</h3>
    <div class="pa-top ${vClass}">
      <div class="pa-score"><span>${d.score}</span><small>预审分·${escapeHtml(d.grade)}级</small></div>
      <div class="pa-verdict"><b>${escapeHtml(d.verdict_label)}</b>
        ${d.recoverable ? `<div class="pa-gain">补齐短板后预计可达 <b>${d.target_score}</b> 分(+${d.recoverable})</div>` : "<div class='pa-gain'>资质达标,可直接提交</div>"}</div>
    </div>
    ${ws ? `<div class="pa-list">${ws}</div>` : '<div class="empty">未发现明显短板,资质良好。</div>'}
    <div class="pa-note">📌 建议先按上方整改,再点「智能匹配」提交,可减少征信硬查询、提高通过率。</div>
  </div>`;
  preauditEl.classList.remove("hidden");
}

const hiddenSubBtn = document.getElementById("hidden-sub-btn");
const hiddenSubAddr = document.getElementById("hidden-sub-addr");
const hiddenSubList = document.getElementById("hidden-sub-list");
const hsProv = document.getElementById("hs-prov");
const hsCity = document.getElementById("hs-city");
const hsDist = document.getElementById("hs-dist");
let regionTree = {};
async function initRegions() {
  if (!hsProv) return;
  try {
    regionTree = await (await fetch("/api/regions")).json();
    Object.keys(regionTree).forEach((p) => hsProv.add(new Option(p, p)));
  } catch (e) {}
}
function fillSel(sel, items, ph) {
  sel.innerHTML = `<option value="">${ph}</option>`;
  items.forEach((i) => sel.add(new Option(i, i)));
}
if (hsProv) {
  initRegions();
  hsProv.addEventListener("change", () => {
    const cities = regionTree[hsProv.value] || {};
    fillSel(hsCity, Object.keys(cities), "市");
    fillSel(hsDist, [], "区县/园区");
    syncAddr();
  });
  hsCity.addEventListener("change", () => {
    const dists = (regionTree[hsProv.value] || {})[hsCity.value] || [];
    fillSel(hsDist, dists, "区县/园区");
    syncAddr();
  });
  hsDist.addEventListener("change", syncAddr);
}
function syncAddr() {
  const parts = [hsProv.value, hsCity.value, hsDist.value].filter((v) => v && v !== "其他");
  hiddenSubAddr.value = parts.join("");
}
if (hiddenSubBtn) {
  hiddenSubBtn.addEventListener("click", queryHiddenSubsidies);
  hiddenSubAddr.addEventListener("keydown", (e) => {
    if (e.key === "Enter") queryHiddenSubsidies();
  });
}
const _prBtn = document.getElementById("policy-remind-btn");
function refreshPolicyRemind() {
  if (!_prBtn) return;
  const on = localStorage.getItem("policyRemind") === "on";
  _prBtn.textContent = on ? "✅ 已开启贴息窗口提醒(点击关闭)" : "🔔 开启贴息窗口到期提醒";
  _prBtn.classList.toggle("on", on);
}
if (_prBtn) {
  refreshPolicyRemind();
  _prBtn.addEventListener("click", () => {
    const on = localStorage.getItem("policyRemind") === "on";
    localStorage.setItem("policyRemind", on ? "off" : "on");
    refreshPolicyRemind();
    showToast(on ? "已关闭提醒" : "已开启,窗口期将第一时间通知你", "success");
  });
}
async function queryHiddenSubsidies() {
  const addr = (hiddenSubAddr.value || "").trim();
  if (!addr) {
    showToast("请输入企业所在地址", "error");
    return;
  }
  const industry = currentCanonicalIndustry();
  hiddenSubList.innerHTML = '<div class="empty">解锁中...</div>';
  try {
    const res = await fetch("/api/hidden-subsidies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: addr, industry }),
    });
    const data = await res.json();
    const items = data.items || [];
    window.__hiddenSubsidies = items;
    window.__hiddenAddr = addr;
    if (!items.length) {
      hiddenSubList.innerHTML =
        '<div class="empty">该地址暂未收录隐藏贴息。可试试园区/区县名称,如「张江」「南山」「余杭」「高新区」。</div>';
      return;
    }
    hiddenSubList.innerHTML = items.map(hiddenSubCard).join("");
  } catch (err) {
    hiddenSubList.innerHTML = `<div class="empty">查询失败:${escapeHtml(err.message)}</div>`;
  }
}
function hiddenSubCard(s) {
  return `<div class="hidden-sub-item">
    <div class="hs-top"><b>${escapeHtml(s.name)}</b>
      <span class="hs-tag">独家</span><span class="hs-cat">${escapeHtml(s.category)}</span></div>
    <div class="hs-region">📍 ${escapeHtml(s.region)} · 最高 ${s.amount_max}万 · 贴息 ${s.rate_subsidy}%</div>
    <div class="hs-benefit">💰 ${escapeHtml(s.benefit)}</div>
    <div class="hs-apply">📝 申报:${escapeHtml(s.apply_points)}</div>
  </div>`;
}

/* ===== 材料清单打包 + 填写示例 ===== */
/* ===== 资质成长报告:下月提额建议 ===== */
function showGrowthReport(data) {
  const p = window.__lastProfile || {};
  const r = data.risk || {};
  const items = [];
  if (!p.has_tax_record) items.push({ act: "补齐连续纳税记录", gain: "+8~12 分", why: "纳税B级以上是多数银行隐性加分项" });
  if (!p.has_invoice) items.push({ act: "稳定开票流水≥6个月", gain: "+5~8 分", why: "流水稳定直接提高授信额度" });
  if ((p.years_in_business || 0) < 2) items.push({ act: "经营满2年再申请", gain: "+6 分", why: "跨过2年门槛通过率明显提升" });
  if (p.loan_amount > (p.annual_revenue || 0)) items.push({ act: "降杠杆至年营收以内", gain: "+5~10 分", why: "负债率高是被拒主因" });
  if (p.credit_level !== "excellent") items.push({ act: "6个月内零逾期养征信", gain: "+8 分", why: "征信优秀直降利率" });
  if (!items.length) items.push({ act: "维持资质,关注续贷/提额窗口", gain: "保持A类", why: "资质已优,可冲更低利率产品" });
  const cur = r.score || 80;
  const next = Math.min(98, cur + items.reduce((s, i) => s + 6, 0));
  const li = items.map((i) => `<li><b>${escapeHtml(i.act)}</b> <span class="gr-gain">${i.gain}</span><small>${escapeHtml(i.why)}</small></li>`).join("");
  document.getElementById("modal-content").innerHTML = `<h2>📈 资质成长报告</h2>
    <p class="modal-sub">当前风控 ${cur} 分,坚持优化下月预计可达 <b>${next}</b> 分,额度/利率随之提升。</p>
    <ul class="growth-ul">${li}</ul>
    <p class="modal-sub">📌 把一次性测算变成长期服务,每月对照执行,授信稳步提升。</p>`;
  document.getElementById("detail-modal").classList.remove("hidden");
}

/* ===== 组合贷测算:多产品叠加额度 ===== */
function showCombo(data) {
  const plans = (data.plans || []).slice(0, 3);
  if (plans.length < 2) return showToast("可匹配产品不足,无法组合", "error");
  const a = plans[0], b = plans[1];
  const total = a.estimated_amount + b.estimated_amount;
  const avgRate = ((a.annual_rate_min + a.annual_rate_max + b.annual_rate_min + b.annual_rate_max) / 4).toFixed(1);
  document.getElementById("modal-content").innerHTML = `<h2>➕ 组合贷测算</h2>
    <p class="modal-sub">单产品额度不够时,组合两款可放大授信。需分别审批,先批稳妥再冲额度。</p>
    <table class="modal-table"><tr><th>产品</th><th>额度</th><th>年化</th></tr>
      <tr><td>${escapeHtml(a.product_name)}</td><td>${a.estimated_amount}万</td><td>${a.annual_rate_min}%-${a.annual_rate_max}%</td></tr>
      <tr><td>${escapeHtml(b.product_name)}</td><td>${b.estimated_amount}万</td><td>${b.annual_rate_min}%-${b.annual_rate_max}%</td></tr>
      <tr class="best-row"><td>合计</td><td>${total}万</td><td>≈${avgRate}%</td></tr></table>
    <p class="modal-sub">⚠️ 组合贷会拉高总负债率,建议总额不超过年营收。征信查询集中在2周内完成,减少花征信。</p>`;
  document.getElementById("detail-modal").classList.remove("hidden");
}

/* ===== 方案海报:画到 canvas,可保存/转发 ===== */
function makePoster(data) {
  const p = data.plans && data.plans[0];
  if (!p) return showToast("暂无方案可生成海报", "error");
  const prof = window.__lastProfile || {};
  const risk = data.risk || {};
  const subsidy = data.tiers && data.tiers.find((t) => t.key === "subsidy");
  const W = 720, H = 1240, c = document.createElement("canvas");
  c.width = W; c.height = H;
  const ctx = c.getContext("2d");
  const g = ctx.createLinearGradient(0, 0, W, H);
  g.addColorStop(0, "#8cacd2"); g.addColorStop(0.5, "#9cb6d7"); g.addColorStop(1, "#6d8aa6");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.textAlign = "center";
  ctx.fillStyle = "#fff"; ctx.font = "bold 46px sans-serif"; ctx.fillText("💰 我的融资方案", W / 2, 100);
  ctx.fillStyle = "#fbbf24"; ctx.font = "22px sans-serif"; ctx.fillText("中小微企业贷款服务小助手", W / 2, 144);
  // 公司+行业
  ctx.fillStyle = "#dbe4ee"; ctx.font = "20px sans-serif";
  ctx.fillText(`${(prof.company_name || "企业").slice(0, 12)} · ${prof.industry || "行业"} · 风控 ${risk.score || "-"}/${risk.grade || "-"}级`, W / 2, 186);
  const cy = 226;
  const box = (y, label, val) => {
    ctx.fillStyle = "rgba(255,255,255,.12)"; ctx.fillRect(70, y, W - 140, 108);
    ctx.fillStyle = "#bccadb"; ctx.font = "24px sans-serif"; ctx.textAlign = "left"; ctx.fillText(label, 100, y + 46);
    ctx.fillStyle = "#fff"; ctx.font = "bold 38px sans-serif"; ctx.textAlign = "right"; ctx.fillText(val, W - 100, y + 70);
  };
  box(cy, "推荐产品", p.product_name.slice(0, 8));
  box(cy + 128, "预估额度", p.estimated_amount + " 万");
  box(cy + 256, "年化利率", p.annual_rate_min + "%-" + p.annual_rate_max + "%");
  box(cy + 384, "预估月供", p.monthly_payment_estimate + " 万");
  box(cy + 512, "建议期限", p.suggested_term_months + " 月");
  box(cy + 640, "通过率·放款", p.approval_probability + " · " + p.expected_release_days);
  if (subsidy && subsidy.after_subsidy) {
    ctx.fillStyle = "#fbbf24"; ctx.fillRect(70, cy + 770, W - 140, 64);
    ctx.fillStyle = "#3c6da7"; ctx.font = "bold 22px sans-serif"; ctx.textAlign = "center";
    ctx.fillText("🎁 含贴息更省:" + subsidy.after_subsidy.slice(0, 22), W / 2, cy + 810);
  }
  ctx.textAlign = "center"; ctx.fillStyle = "rgba(219,228,238,.85)"; ctx.font = "18px sans-serif";
  ctx.fillText("📈 方案精准匹配本地银行产品 · 数据仅供参考", W / 2, H - 78);
  ctx.fillText("不发放贷款,最终以银行/担保机构审核为准", W / 2, H - 48);
  const finish = () => c.toBlob((b) => {
    const url = URL.createObjectURL(b);
    document.getElementById("modal-content").innerHTML = `<h2>📱 分享海报</h2><p class="modal-sub">长按/右键保存图片,扫码或转发给伙伴、客户经理。</p><img src="${url}" style="width:100%;border-radius:12px"><a href="${url}" download="融资方案海报.png" class="export-btn" style="display:inline-block;margin-top:10px;text-decoration:none">⬇️ 下载海报</a>`;
    document.getElementById("detail-modal").classList.remove("hidden");
  });
  const qr = new Image();
  qr.onload = () => {
    const qs = 120, qx = W / 2 - qs / 2, qy = H - 240;
    ctx.fillStyle = "#fff"; ctx.fillRect(qx - 8, qy - 8, qs + 16, qs + 16);
    ctx.drawImage(qr, qx, qy, qs, qs);
    ctx.fillStyle = "rgba(219,228,238,.9)"; ctx.font = "16px sans-serif"; ctx.fillText("扫码体验·测你的额度", W / 2, qy + qs + 22);
    finish();
  };
  qr.onerror = finish;
  qr.src = "/api/qr?text=" + encodeURIComponent(location.origin || "http://127.0.0.1:8000/");
}

async function showChecklist() {
  const ind = (window.__lastProfile && window.__lastProfile.industry) || currentCanonicalIndustry();
  let mats = ["营业执照副本", "近12个月对公流水", "近一年纳税证明", "法人身份证", "经营场所租赁合同", "贷款用途说明"];
  let title = "通用材料清单";
  try {
    const t = await (await fetch(`/api/industry-template/${encodeURIComponent(ind)}`)).json();
    if (t && t.materials && t.materials.length) { mats = t.materials; title = (t.emoji || "📋") + " " + t.title + " 材料清单"; }
  } catch (_) {}
  const examples = { "营业执照副本": "彩色扫描/拍照,确保统一社会信用代码清晰", "近12个月对公流水": "银行盖章版,标注大额进出说明", "近一年纳税证明": "税务系统导出PDF,A/B/M级最佳", "法人身份证": "正反面,有效期内", "贷款用途说明": "一句话写明用途+金额,如'采购设备60万'" };
  const items = mats.map((m) => `<li><label><input type="checkbox"> ${escapeHtml(m)}</label>${examples[m] ? `<small>示例:${escapeHtml(examples[m])}</small>` : ""}</li>`).join("");
  document.getElementById("modal-content").innerHTML = `<h2>${escapeHtml(title)}</h2>
    <p class="modal-sub">对照逐项打钩,准备齐全可显著提高通过率。</p>
    <ul class="checklist-ul">${items}</ul>
    <button class="export-btn" onclick="window.print()">🖨️ 打印/另存清单</button>`;
  document.getElementById("detail-modal").classList.remove("hidden");
}

function render(data) {
  window.__lastProfile = window.__lastProfile || null;
  let html = "";

  // 首屏结论卡:三句话直给,详情下方展开
  if (data.plans && data.plans.length) {
    const byAmt = [...data.plans].sort((a, b) => b.estimated_amount - a.estimated_amount)[0];
    const byCost = [...data.plans].sort((a, b) => (a.annual_rate_min + a.annual_rate_max) - (b.annual_rate_min + b.annual_rate_max))[0];
    const bySafe = data.tiers && data.tiers.find((t) => t.key === "steady");
    html += `<div class="verdict-box">
      <h3>✅ 一句话结论</h3>
      <div class="verdict-grid">
        <div class="verdict-card"><span class="vc-tag">额度最高</span><b>${byAmt.estimated_amount} 万</b><small>${escapeHtml(byAmt.product_name)}</small></div>
        <div class="verdict-card"><span class="vc-tag">成本最低</span><b>${byCost.annual_rate_min}%-${byCost.annual_rate_max}%</b><small>${escapeHtml(byCost.product_name)}</small></div>
        <div class="verdict-card"><span class="vc-tag">最稳通过</span><b>${data.plans[0].approval_probability}</b><small>${escapeHtml(bySafe ? bySafe.product_name : data.plans[0].product_name)}</small></div>
      </div>
    </div>`;
  }

  const isPersonal = window.__lastMode === "personal";
  const actionBtns = isPersonal
    ? `<button id="export-pdf-personal" class="export-btn">📄 导出方案 PDF</button>
    <button class="export-btn" onclick="window.print()">🖨️ 打印 / 另存</button>`
    : `<button id="export-pdf" class="export-btn">📄 导出方案 PDF</button>
    <button id="export-excel" class="export-btn excel-btn">📊 导出 Excel</button>
    <button id="export-bank" class="export-btn bank-btn">🏦 银行成品材料 PDF</button>
    <button id="export-bank-docx" class="export-btn bank-btn">📝 银行成品材料 Word</button>
    <button id="export-checklist" class="export-btn">📋 材料清单</button>
    <button id="share-poster" class="export-btn">📱 生成分享海报</button>
    <button id="growth-report" class="export-btn">📈 资质成长报告</button>
    <button id="combo-credit" class="export-btn">➕ 组合贷测算</button>
    <select id="bank-tpl-sel" class="bank-sel" title="选择银行专属申报模板"><option value="">通用模板</option></select>
    <button id="save-application" class="export-btn save-btn">💾 保存为申请记录</button>`;

  html += `<div class="summary-box">
    <h3>📊 匹配结果</h3>
    <p>${escapeHtml(data.summary)}</p>
    <ul class="highlights">
      ${data.profile_highlights.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}
    </ul>
    ${actionBtns}
  </div>`;

  // 风控评估
  if (data.risk) {
    const r = data.risk;
    html += `<div class="risk-box">
      <div class="risk-head">
        <h3>🛡️ 风控评估</h3>
        <div class="risk-score grade-${r.grade}" title="风控等级 A≥85 / B 70-84 / C 55-69 / D<55,综合8维度评分">
          <span class="rs-num">${r.score}</span>
          <span class="rs-grade">等级 ${r.grade} · ${escapeHtml(r.grade_label)}</span>
        </div>
      </div>
      ${
        r.debt_ratio != null
          ? `<p class="risk-meta">负债杠杆(贷款/年营收):约 ${Math.round(r.debt_ratio * 100)}%</p>`
          : ""
      }
      <div class="factors">
        ${r.factors
          .map(
            (f) =>
              `<div class="factor factor-${f.impact}"><b>${escapeHtml(f.name)}</b> ${escapeHtml(
                f.detail
              )}</div>`
          )
          .join("")}
      </div>
    </div>`;
  }

  if (data.plans.length === 0) {
    html += `<div class="plan"><div class="empty">暂无匹配方案,请参考下方建议提升资质。</div></div>`;
  }

  // 政府性融资担保增信方案(抵押不足补满额度)
  if (data.guarantee) {
    const g = data.guarantee;
    html += `<div class="guar-box">
      <h3>🤝 ${escapeHtml(g.title)} <span class="guar-tag">${escapeHtml(g.tagline)}</span></h3>
      <div class="guar-amt"><span>${g.base_amount}万</span> → <b>${g.boosted_amount}万</b> <small>补缺口 +${g.fill_gap}万</small></div>
      <p class="guar-reason">${escapeHtml(g.reason)}</p>
      <div class="guar-steps">${g.steps.map((s, i) => `<span>${i + 1}.${escapeHtml(s)}</span>`).join("")}</div>
      <p class="guar-note">📌 ${escapeHtml(g.note)}</p>
    </div>`;
  }

  // 差异化:三层方案推荐
  if (data.tiers && data.tiers.length) {
    const tierIco = { steady: "🛡️", sprint: "🚀", subsidy: "💰" };
    html += `<div class="tiers-box">
      <h3>🎯 分层智能推荐 · 三套方案任你选</h3>
      <div class="tiers-grid">
        ${data.tiers
          .map(
            (t) => `<div class="tier-card tier-${t.key}">
              <div class="tier-name">${tierIco[t.key] || "★"} ${escapeHtml(t.name)}</div>
              <div class="tier-tag">${escapeHtml(t.tagline)}</div>
              <div class="tier-prod">${escapeHtml(t.product_name)}</div>
              <div class="tier-headline">${escapeHtml(t.headline)}</div>
              <div class="tier-reason">${escapeHtml(t.reason)}</div>
              ${t.after_subsidy ? `<div class="tier-after">💰 ${escapeHtml(t.after_subsidy)}</div>` : ""}
              <div class="tier-risk">⚠ ${escapeHtml(t.risk_note)}</div>
            </div>`
          )
          .join("")}
      </div>
    </div>`;
  }

  // 方案对比表(2 个及以上方案时)
  if (data.plans.length >= 2) {
    const ps = data.plans;
    const row = (label, fn) =>
      `<tr><th>${label}</th>${ps
        .map((p, i) => `<td class="${i === 0 ? "cmp-best" : ""}">${fn(p)}</td>`)
        .join("")}</tr>`;
    html += `<div class="compare-box">
      <h3>📊 方案对比</h3>
      <div class="compare-scroll">
      <table class="compare-table">
        <thead><tr><th>对比项</th>${ps
          .map((p, i) => `<th class="${i === 0 ? "cmp-best" : ""}">${i === 0 ? "⭐ " : ""}${escapeHtml(p.product_name)}</th>`)
          .join("")}</tr></thead>
        <tbody>
          ${row("预估额度", (p) => p.estimated_amount + " 万")}
          ${row("年化利率", (p) => p.annual_rate_min + "%-" + p.annual_rate_max + "%")}
          ${row("建议期限", (p) => p.suggested_term_months + " 月")}
          ${row("预估月供", (p) => p.monthly_payment_estimate + " 万")}
          ${row("预估总利息", (p) => p.total_interest_estimate + " 万")}
          ${row("通过率", (p) => p.approval_probability)}
          ${row("放款时效", (p) => escapeHtml(p.expected_release_days))}
          ${row("是否需抵押", (p) => (p.requires_collateral ? "需要" : "免抵押"))}
          ${row("材料复杂度", (p) => (p.requires_collateral ? "较高(含抵押评估)" : (p.provider_type === "小额贷款公司" ? "简单" : "中等")))}
          ${row("匹配分", (p) => p.score)}
        </tbody>
      </table>
      </div>
    </div>`;
  }

  data.plans.forEach((p, i) => {
    html += `<div class="plan ${i === 0 ? "best" : ""}">
      ${i === 0 ? '<span class="best-badge">⭐ 最优推荐</span>' : ""}
      <div class="plan-head">
        <div>
          <h3>${escapeHtml(p.product_name)}</h3>
          <span class="provider">${escapeHtml(p.provider_type)}</span>
        </div>
        <div class="plan-head-right">
          <button class="fav-btn" data-fav='${encodeURIComponent(JSON.stringify({
            product_name: p.product_name, provider_type: p.provider_type,
            estimated_amount: p.estimated_amount, annual_rate_min: p.annual_rate_min,
            annual_rate_max: p.annual_rate_max, suggested_term_months: p.suggested_term_months,
            monthly_payment_estimate: p.monthly_payment_estimate, total_interest_estimate: p.total_interest_estimate,
            approval_probability: p.approval_probability, expected_release_days: p.expected_release_days,
            requires_collateral: p.requires_collateral, score: p.score,
          }))}' title="收藏对比">☆</button>
          <div class="score-ring" title="匹配分综合考量额度满足度、利率、通过率、放款时效,分数越高越契合你的需求">
            <div class="num">${p.score}</div>
            <div class="lbl">匹配分</div>
          </div>
        </div>
      </div>

      <div class="metrics">
        <div class="metric"><div class="m-label">预估额度</div><div class="m-value">${p.estimated_amount} 万</div></div>
        <div class="metric"><div class="m-label">年化利率</div><div class="m-value">${p.annual_rate_min}%-${p.annual_rate_max}%</div></div>
        <div class="metric"><div class="m-label">建议期限</div><div class="m-value">${p.suggested_term_months} 月</div></div>
        <div class="metric"><div class="m-label">预估月供</div><div class="m-value">${p.monthly_payment_estimate} 万</div></div>
        <div class="metric"><div class="m-label">预估总利息</div><div class="m-value">${p.total_interest_estimate} 万</div></div>
        <div class="metric"><div class="m-label">通过率</div><div class="m-value prob-${p.approval_probability}" title="基于本地审批样本与你的资质综合评估的获批概率,非承诺值">${p.approval_probability}</div></div>
        <div class="metric"><div class="m-label">放款时效</div><div class="m-value" style="font-size:13px">${escapeHtml(p.expected_release_days)}</div></div>
        <div class="metric"><div class="m-label">是否需抵押</div><div class="m-value">${p.requires_collateral ? "需要" : "免抵押"}</div></div>
      </div>

      <div class="reasons">
        <h4>推荐理由</h4>
        <ul>${p.match_reasons.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul>
      </div>

      ${
        p.cautions.length
          ? `<div class="cautions"><h4>注意事项</h4><ul>${p.cautions
              .map((c) => `<li>${escapeHtml(c)}</li>`)
              .join("")}</ul></div>`
          : ""
      }

      ${
        p.hidden_criteria || p.local_approval_rate
          ? `<div class="exclusive">
              <div class="excl-tag">🔒 独家数据</div>
              ${p.local_approval_rate ? `<div class="excl-rate">近三月本地审批通过率 <b>${p.local_approval_rate}%</b></div>` : ""}
              ${p.hidden_criteria ? `<div class="excl-hidden">支行隐性准入:${escapeHtml(p.hidden_criteria)}</div>` : ""}
            </div>`
          : ""
      }
    </div>`;
  });

  // 个性化建议
  if (data.personalized_advice && data.personalized_advice.length) {
    html += `<div class="advice-box">
      <h3>🎯 个性化融资建议</h3>
      <ul>${data.personalized_advice.map((a) => `<li>${escapeHtml(a)}</li>`).join("")}</ul>
    </div>`;
  }

  // 补贴政策
  if (data.subsidies && data.subsidies.length) {
    html += `<div class="subsidy-box">
      <h3>🏛️ 可申报扶持政策(${data.subsidies.length})</h3>
      ${data.subsidies
        .map(
          (s) => `<div class="subsidy">
            <div class="sub-top"><span class="sub-name">${escapeHtml(s.name)}</span>
            <span class="sub-cat">${escapeHtml(s.category)}</span></div>
            <div class="sub-benefit">${escapeHtml(s.benefit)}</div>
            <div class="sub-apply">📌 申请要点:${escapeHtml(s.apply_points)}</div>
            <div class="sub-auth">主管部门:${escapeHtml(s.authority)}</div>
            <div class="sub-meta"><span class="sub-window">🗓️ ${escapeHtml(s.apply_window || "常年可申报")}</span><span class="sub-upd">政策更新于 ${escapeHtml(s.updated || "2026-06")}</span></div>
          </div>`
        )
        .join("")}
    </div>`;
  }

  if (data.improvement_tips.length) {
    html += `<div class="tips-box">
      <h3>提升资质 · 获得更优方案</h3>
      <ul>${data.improvement_tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
    </div>`;
  }

  resultEl.innerHTML = html;
  resultEl.classList.remove("hidden");
  resultEl.scrollIntoView({ behavior: "smooth", block: "start" });

  const exportBtn = document.getElementById("export-pdf");
  if (exportBtn) exportBtn.addEventListener("click", exportPdf);

  const excelBtn = document.getElementById("export-excel");
  if (excelBtn) excelBtn.addEventListener("click", exportExcel);

  const bankBtn = document.getElementById("export-bank");
  if (bankBtn) bankBtn.addEventListener("click", exportBankPackage);

  const bankDocxBtn = document.getElementById("export-bank-docx");
  if (bankDocxBtn) bankDocxBtn.addEventListener("click", exportBankPackageDocx);

  const checklistBtn = document.getElementById("export-checklist");
  if (checklistBtn) checklistBtn.addEventListener("click", showChecklist);

  const posterBtn = document.getElementById("share-poster");
  if (posterBtn) posterBtn.addEventListener("click", () => makePoster(data));

  const growthBtn = document.getElementById("growth-report");
  if (growthBtn) growthBtn.addEventListener("click", () => showGrowthReport(data));

  const comboBtn = document.getElementById("combo-credit");
  if (comboBtn) comboBtn.addEventListener("click", () => showCombo(data));

  const saveBtn = document.getElementById("save-application");
  if (saveBtn) saveBtn.addEventListener("click", saveApplication);

  const pdfPersonalBtn = document.getElementById("export-pdf-personal");
  if (pdfPersonalBtn) pdfPersonalBtn.addEventListener("click", exportPersonalPdf);

  loadBankOptions();
  bindFavButtons();
  refreshFavBar();
}

/* ===================== 产品收藏对比 ===================== */
function getFavs() {
  try { return JSON.parse(localStorage.getItem("favPlans") || "[]"); } catch (e) { return []; }
}
function setFavs(arr) { localStorage.setItem("favPlans", JSON.stringify(arr)); }
function isFav(name) { return getFavs().some((p) => p.product_name === name); }

function toggleFav(plan) {
  const favs = getFavs();
  const idx = favs.findIndex((p) => p.product_name === plan.product_name);
  if (idx >= 0) { favs.splice(idx, 1); showToast("已取消收藏", "info"); }
  else {
    if (favs.length >= 4) return showToast("最多收藏 4 个产品对比", "error");
    favs.push(plan); showToast("已加入收藏对比", "success");
  }
  setFavs(favs);
  bindFavButtons();
  refreshFavBar();
}

function bindFavButtons() {
  document.querySelectorAll(".fav-btn").forEach((b) => {
    const plan = JSON.parse(decodeURIComponent(b.dataset.fav));
    const on = isFav(plan.product_name);
    b.textContent = on ? "★" : "☆";
    b.classList.toggle("on", on);
    b.onclick = () => toggleFav(plan);
  });
}

function refreshFavBar() {
  let bar = document.getElementById("fav-bar");
  const favs = getFavs();
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "fav-bar";
    document.body.appendChild(bar);
  }
  if (!favs.length) { bar.classList.remove("show"); return; }
  bar.classList.add("show");
  bar.innerHTML = `<span class="fav-count">⭐ 已收藏 ${favs.length} 个</span>
    <button id="fav-compare" class="export-btn">查看对比</button>
    <button id="fav-clear" class="ghost-btn">清空</button>`;
  document.getElementById("fav-compare").onclick = showFavCompare;
  document.getElementById("fav-clear").onclick = () => { setFavs([]); bindFavButtons(); refreshFavBar(); };
}

function showFavCompare() {
  const favs = getFavs();
  if (favs.length < 1) return;
  const row = (label, fn) =>
    `<tr><th>${label}</th>${favs.map((p) => `<td>${fn(p)}</td>`).join("")}</tr>`;
  const html = `<h2>⭐ 收藏方案对比</h2><div class="compare-scroll"><table class="compare-table">
    <thead><tr><th>对比项</th>${favs.map((p) => `<th>${escapeHtml(p.product_name)}</th>`).join("")}</tr></thead>
    <tbody>
      ${row("预估额度", (p) => p.estimated_amount + " 万")}
      ${row("年化利率", (p) => p.annual_rate_min + "%-" + p.annual_rate_max + "%")}
      ${row("建议期限", (p) => p.suggested_term_months + " 月")}
      ${row("预估月供", (p) => p.monthly_payment_estimate + " 万")}
      ${row("预估总利息", (p) => p.total_interest_estimate + " 万")}
      ${row("通过率", (p) => p.approval_probability)}
      ${row("放款时效", (p) => escapeHtml(p.expected_release_days))}
      ${row("是否需抵押", (p) => (p.requires_collateral ? "需要" : "免抵押"))}
      ${row("匹配分", (p) => p.score)}
    </tbody></table></div>`;
  document.getElementById("modal-content").innerHTML = html;
  document.getElementById("detail-modal").classList.remove("hidden");
}

async function saveApplication() {
  if (!window.__lastProfile) return;
  const btn = document.getElementById("save-application");
  const old = btn.textContent;
  btn.disabled = true;
  btn.textContent = "保存中...";
  try {
    const res = await fetch("/api/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: window.__lastProfile }),
    });
    if (!res.ok) throw new Error("保存失败:" + res.status);
    btn.textContent = "✅ 已保存";
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = old;
    }, 2000);
  } catch (err) {
    showToast(err.message, "error");
    btn.disabled = false;
    btn.textContent = old;
  }
}

async function exportPdf() {
  await exportReport("/api/export/pdf", "pdf", document.getElementById("export-pdf"));
}

async function exportPersonalPdf() {
  const btn = document.getElementById("export-pdf-personal");
  if (!window.__lastPersonalProfile || !btn) return;
  const old = btn.textContent;
  btn.disabled = true;
  btn.textContent = "生成中...";
  try {
    const res = await fetch("/api/export/pdf-personal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(window.__lastPersonalProfile),
    });
    if (!res.ok) throw new Error("导出失败:" + res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${window.__lastPersonalProfile.name || "个人"}_贷款方案.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = old;
  }
}

async function exportExcel() {
  await exportReport("/api/export/excel", "xlsx", document.getElementById("export-excel"));
}

async function exportBankPackage() {
  const btn = document.getElementById("export-bank");
  const bank = document.getElementById("bank-tpl-sel")?.value || "";
  await exportReport(`/api/export/bank-package${bank ? "?bank=" + encodeURIComponent(bank) : ""}`, "pdf", btn, "_银行成品材料", true);
}

async function exportBankPackageDocx() {
  const btn = document.getElementById("export-bank-docx");
  const bank = document.getElementById("bank-tpl-sel")?.value || "";
  await exportReport(`/api/export/bank-package-docx${bank ? "?bank=" + encodeURIComponent(bank) : ""}`, "docx", btn, "_银行成品材料", true);
}

async function loadBankOptions() {
  const sel = document.getElementById("bank-tpl-sel");
  if (!sel || sel.dataset.loaded) return;
  try {
    const res = await fetch("/api/banks");
    const banks = await res.json();
    banks.forEach((b) => {
      const o = document.createElement("option");
      o.value = b; o.textContent = b + " 模板";
      sel.appendChild(o);
    });
    sel.dataset.loaded = "1";
  } catch (_) {}
}

async function exportReport(endpoint, ext, btn, suffix, withHidden) {
  if (!window.__lastProfile) return;
  const old = btn.textContent;
  btn.disabled = true;
  btn.textContent = "生成中...";
  try {
    const payload = withHidden
      ? { ...window.__lastProfile, hidden_subsidies: window.__hiddenSubsidies || [] }
      : window.__lastProfile;
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("导出失败:" + res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const cn = window.__lastProfile.company_name || "企业";
    a.download = `${cn}${suffix || "_贷款方案"}.${ext}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = old;
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/* ===================== 申请记录 ===================== */
const STATUS_LIST = ["待提交", "已提交", "审核中", "已通过", "已拒绝", "已放款"];

function statusClass(s) {
  return (
    {
      待提交: "st-pending",
      已提交: "st-submitted",
      审核中: "st-reviewing",
      已通过: "st-approved",
      已拒绝: "st-rejected",
      已放款: "st-funded",
    }[s] || "st-pending"
  );
}

document.querySelectorAll(".tab-btn[data-tab]").forEach((btn) => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});

/* ===================== 数据保鲜标注:动态拉取更新日期 ===================== */
(function initDataNote() {
  const el = document.getElementById("data-note");
  if (!el) return;
  fetch("/api/data-info")
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => {
      if (!d) return;
      el.textContent =
        `📌 利率基准参考 LPR(一年期 ${d.lpr_1y}%、五年期以上 ${d.lpr_5y}%,${d.lpr_updated} 起);` +
        `产品与政策依据国家公开信息整理,数据核对于 ${d.lpr_updated},具体以金融机构审批及主管部门最新文件为准。`;
    })
    .catch(() => {});
})();

/* ===================== 个人贷款:身份切换与匹配 ===================== */
(function initPersonalLoan() {
  const switchEl = document.getElementById("identity-switch");
  const entView = document.getElementById("enterprise-view");
  const perView = document.getElementById("personal-view");
  const perForm = document.getElementById("personal-form");
  if (!switchEl || !perForm) return;

  function setIdentity(id) {
    switchEl.querySelectorAll(".id-btn").forEach((b) =>
      b.classList.toggle("active", b.dataset.identity === id)
    );
    const personal = id === "personal";
    if (entView) entView.classList.toggle("hidden", personal);
    if (perView) perView.classList.toggle("hidden", !personal);
    // 切换身份清空上一次结果,避免混淆
    resultEl.classList.add("hidden");
    resultEl.innerHTML = "";
    window.__lastMode = personal ? "personal" : "enterprise";
  }
  switchEl.querySelectorAll(".id-btn").forEach((b) =>
    b.addEventListener("click", () => setIdentity(b.dataset.identity))
  );

  function collectPersonalProfile() {
    const fd = new FormData(perForm);
    const num = (k) => parseFloat(fd.get(k)) || 0;
    const identities = Array.from(perForm.querySelectorAll(".pf-identity:checked")).map((c) => c.value);
    const houseVal = num("house_value");
    const carVal = num("car_value");
    const fundMonthly = num("housing_fund_monthly");
    return {
      name: fd.get("name") || "",
      age: parseInt(fd.get("age")) || 30,
      occupation_type: fd.get("occupation_type"),
      monthly_income: num("monthly_income"),
      income_type: fd.get("income_type") || "salary",
      work_years: num("work_years"),
      has_social_security: fd.get("has_social_security") === "on",
      has_housing_fund: fd.get("has_housing_fund") === "on" || fundMonthly > 0,
      housing_fund_monthly: fundMonthly,
      has_house: fd.get("has_house") === "on" || houseVal > 0,
      house_value: houseVal,
      has_car: fd.get("has_car") === "on" || carVal > 0,
      car_value: carVal,
      has_insurance_policy: fd.get("has_insurance_policy") === "on",
      credit_level: fd.get("credit_level"),
      has_overdue: fd.get("has_overdue") === "on",
      monthly_debt_payment: num("monthly_debt_payment"),
      is_entrepreneur: fd.get("is_entrepreneur") === "on",
      special_identity: identities,
      loan_amount: num("loan_amount"),
      loan_purpose: fd.get("loan_purpose"),
      preferred_term_months: parseInt(fd.get("preferred_term_months")) || 12,
      urgent: fd.get("urgent") === "on",
    };
  }

  function validatePersonal(p) {
    const errs = [];
    if (!p.monthly_income || p.monthly_income <= 0) errs.push("请填写月收入");
    if (!p.loan_amount || p.loan_amount <= 0) errs.push("请填写贷款金额");
    if (!p.preferred_term_months || p.preferred_term_months < 1) errs.push("请填写贷款期限");
    return errs;
  }

  const perBtn = document.getElementById("personal-submit-btn");
  perForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const profile = collectPersonalProfile();
    const errors = validatePersonal(profile);
    if (errors.length) {
      showToast(`请检查:${errors.join("、")}`, "error");
      return;
    }
    perBtn.disabled = true;
    perBtn.textContent = "匹配中...";
    renderSkeleton();
    try {
      const res = await fetch("/api/recommend-personal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!res.ok) throw new Error("请求失败:" + res.status);
      const data = await res.json();
      window.__lastPersonalProfile = profile;
      window.__lastMode = "personal";
      render(data);
      showToast("已为你匹配最优方案", "success");
      resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      resultEl.innerHTML = `<div class="empty err-empty">😕 匹配遇到问题:${escapeHtml(err.message)}<br><button id="retry-personal" class="export-btn">🔄 重试一次</button></div>`;
      resultEl.classList.remove("hidden");
      const rb = document.getElementById("retry-personal");
      if (rb) rb.addEventListener("click", () => perForm.requestSubmit());
      showToast("匹配失败,请稍后重试", "error");
    } finally {
      perBtn.disabled = false;
      perBtn.textContent = "🔍 智能匹配最优方案";
    }
  });

  const fillSample = document.getElementById("fill-sample-personal");
  if (fillSample) {
    fillSample.addEventListener("click", (e) => {
      e.preventDefault();
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
      set("pf-name", "张先生");
      set("pf-occupation", "salaried");
      set("pf-age", 32);
      set("pf-income", 12000);
      set("pf-income-type", "salary");
      set("pf-workyears", 4);
      set("pf-fund", 1500);
      set("pf-house", 0);
      set("pf-car", 0);
      set("pf-credit", "good");
      set("pf-debt", 2000);
      set("pf-amount", 15);
      set("pf-purpose", "decoration");
      set("pf-term", 36);
      const chk = (name, on) => { const el = perForm.querySelector(`input[name="${name}"]`); if (el) el.checked = on; };
      chk("has_social_security", true);
      chk("has_housing_fund", true);
      showToast("已填入示例,直接点匹配试试", "info");
    });
  }
})();

function activateTab(tab) {
  closeChatPanel();
  document.querySelectorAll(".tab-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.tab === tab)
  );
  document.getElementById("tab-apply").classList.toggle("hidden", tab !== "apply");
  document.getElementById("tab-subsidy").classList.toggle("hidden", tab !== "subsidy");
  document.getElementById("tab-calc").classList.toggle("hidden", tab !== "calc");
  document.getElementById("tab-records").classList.toggle("hidden", tab !== "records");
  document.getElementById("tab-game").classList.toggle("hidden", tab !== "game");
  if (tab === "records") { loadRecords(); startRecPolling(); } else { stopRecPolling(); }
  if (tab === "game") initGame();
  window.scrollTo({ top: 0, behavior: "smooth" });
}
let _recTimer = null;
function startRecPolling() { stopRecPolling(); _recTimer = setInterval(loadRecords, 20000); }
function stopRecPolling() { if (_recTimer) { clearInterval(_recTimer); _recTimer = null; } }

document.querySelectorAll(".chain-step[data-tab]").forEach((s) => {
  s.addEventListener("click", () => activateTab(s.dataset.tab));
});
const _heroCta = document.getElementById("hero-subsidy-cta");
if (_heroCta) _heroCta.addEventListener("click", () => activateTab("subsidy"));

// 行业专属风控模板:切换行业即展示授信加分项与材料清单
let _customIndustry = { category: "", detail: "" };

function effectiveIndustry() {
  const sel = document.getElementById("f-industry");
  if (!sel) return { industry: "服务业", detail: "" };
  if (sel.value === "__custom__") {
    const txt = (document.getElementById("f-industry-custom") || {}).value || "";
    return { industry: _customIndustry.category || "", detail: (_customIndustry.detail || txt.trim()) };
  }
  const opt = sel.selectedOptions && sel.selectedOptions[0];
  const detail = (opt && opt.dataset && opt.dataset.detail) || "";
  return { industry: sel.value, detail };
}

function currentCanonicalIndustry() {
  return effectiveIndustry().industry || "";
}

async function loadIndustryTemplate() {
  const box = document.getElementById("industry-template-box");
  const ind = currentCanonicalIndustry();
  if (!box) return;
  if (!ind) { box.innerHTML = ""; return; }
  try {
    const res = await fetch(`/api/industry-template/${encodeURIComponent(ind)}`);
    const t = await res.json();
    if (!t || !t.title) { box.innerHTML = ""; return; }
    const bonus = (t.bonus_items || []).map((x, i) =>
      `<label class="tpl-chk"><input type="checkbox" class="ind-bonus" value="${escapeHtml(x)}"> ${escapeHtml(x)}</label>`
    ).join("");
    const mats = (t.materials || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
    box.innerHTML = `<div class="tpl-card"><div class="tpl-head">${t.emoji || "🏷️"} ${escapeHtml(t.title)}<span class="tpl-badge">行业定制</span></div>
      <div class="tpl-sub">勾选已具备的加分项,命中即提升风控评分与通过率:</div>
      <div class="tpl-bonus">${bonus}</div>
      <div class="tpl-tip">💡 ${escapeHtml(t.tip)}</div>
      <details class="tpl-mat"><summary>建议准备材料</summary><ul>${mats}</ul></details></div>`;
  } catch (_) { box.innerHTML = ""; }
}

// 行业下拉:自定义模式切换 + AI 识别
{
  const _sel = document.getElementById("f-industry");
  const _box = document.getElementById("custom-industry-box");
  const _input = document.getElementById("f-industry-custom");
  const _detectBtn = document.getElementById("ci-detect");
  const _result = document.getElementById("ci-result");

  function showCustom(show) {
    if (_box) _box.classList.toggle("hidden", !show);
  }

  async function detectIndustry() {
    if (!_input || !_result) return;
    const text = (_input.value || "").trim();
    if (!text) { showToast("请先描述你的行业或主营业务", "error"); return; }
    _result.classList.remove("hidden");
    _result.innerHTML = `<span class="ci-loading">🤖 AI 识别中…</span>`;
    if (_detectBtn) { _detectBtn.disabled = true; }
    try {
      const res = await fetch("/api/classify-industry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error("classify failed");
      const d = await res.json();
      _customIndustry = { category: d.category || "", detail: text };
      const tag = d.method === "ai" ? "AI 智能识别" : (d.method === "keyword" ? "智能匹配" : "默认归类");
      _result.innerHTML =
        `<span class="ci-ok">✅ 已归类为【<b>${escapeHtml(d.category)}</b>】</span>` +
        `<span class="ci-tag">${tag}</span>` +
        `<div class="ci-hint">将按此行业为你匹配风控模型、专属模板与补贴政策。识别不准?可换个下拉选项。</div>`;
      loadIndustryTemplate();
    } catch (e) {
      _result.innerHTML = `<span class="ci-err">识别失败,请重试或直接选择上方下拉行业</span>`;
    } finally {
      if (_detectBtn) { _detectBtn.disabled = false; }
    }
  }

  if (_sel) {
    _sel.addEventListener("change", () => {
      const isCustom = _sel.value === "__custom__";
      showCustom(isCustom);
      if (isCustom) {
        if (_input) _input.focus();
        // 若已有识别结果则保留,否则清空模板等待识别
        if (!_customIndustry.category) {
          const box = document.getElementById("industry-template-box");
          if (box) box.innerHTML = "";
        }
      }
      loadIndustryTemplate();
    });
    loadIndustryTemplate();
  }
  if (_detectBtn) _detectBtn.addEventListener("click", detectIndustry);
  if (_input) {
    _input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); detectIndustry(); }
    });
    let _t;
    _input.addEventListener("input", () => {
      _customIndustry = { category: "", detail: (_input.value || "").trim() };
      clearTimeout(_t);
      _t = setTimeout(detectIndustry, 900);
    });
  }
}

document.getElementById("refresh-records").addEventListener("click", loadRecords);
document.getElementById("export-records-pdf").addEventListener("click", () => {
  window.open("/api/applications-summary/pdf", "_blank");
});
const _recFilter = document.getElementById("rec-filter");
if (_recFilter) { let t; _recFilter.addEventListener("input", () => { clearTimeout(t); t = setTimeout(loadRecords, 300); }); }
const _recSpeed = document.getElementById("rec-speed");
if (_recSpeed) {
  fetch("/api/settings/advance-mode").then((r) => r.json()).then((d) => { _recSpeed.value = d.mode || "demo"; }).catch(() => {});
  _recSpeed.addEventListener("change", async () => {
    try {
      await fetch("/api/settings/advance-mode", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: _recSpeed.value }) });
      showToast(_recSpeed.value === "real" ? "已切换真实节奏(按天推进)" : "已切换演示加速(按分钟推进)", "success");
      loadRecords();
    } catch (e) { showToast("切换失败", "error"); }
  });
}
const _fillSample = document.getElementById("fill-sample");
if (_fillSample) _fillSample.addEventListener("click", (e) => {
  e.preventDefault();
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
  set("f-company", "示例·小微制造有限公司"); set("f-industry", "制造业"); set("f-years", "3");
  set("f-revenue", "800"); set("f-employees", "15"); set("f-amount", "200"); set("f-term", "24");
  set("f-credit", "good"); set("f-collateral", "0");
  document.querySelectorAll("input[type=number]").forEach((el) => { if (!el.value) el.value = el.min || 0; });
  showToast("已填入示例,直接点匹配即可体验", "success");
});

// 用户输入时即时清除该字段的报错状态
form.querySelectorAll("input, select").forEach((el) => {
  el.addEventListener("input", () => clearFieldError(el));
});

/* ===== 实时侧边预审 + 杠杆预警 ===== */
let _liveTimer = null;
function updateLeverageWarn() {
  const rev = parseFloat(document.getElementById("f-revenue").value) || 0;
  const amt = parseFloat(document.getElementById("f-amount").value) || 0;
  const el = document.getElementById("leverage-warn");
  if (!el) return;
  if (rev > 0 && amt > rev) {
    const half = Math.round(amt / 2);
    el.innerHTML = `⚠️ 申请额超年营收(杠杆 ${Math.round((amt / rev) * 100)}%),通过率偏低。` +
      `<button type="button" class="lev-fix" data-amt="${half}">一键降至 ${half} 万</button>` +
      `<button type="button" class="lev-fix" data-amt="${Math.round(rev)}">降至年营收 ${Math.round(rev)} 万</button>`;
    el.classList.remove("hidden");
    el.querySelectorAll(".lev-fix").forEach((b) => b.addEventListener("click", () => {
      document.getElementById("f-amount").value = b.dataset.amt;
      updateLeverageWarn(); scheduleLiveScore();
    }));
  } else { el.classList.add("hidden"); el.innerHTML = ""; }
}
async function scheduleLiveScore() {
  clearTimeout(_liveTimer);
  _liveTimer = setTimeout(async () => {
    const box = document.getElementById("live-score");
    const profile = collectProfile();
    if (!(profile.annual_revenue > 0)) { box.classList.add("hidden"); return; }
    try {
      const r = await fetch("/api/preaudit", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!r.ok) return;
      const d = await r.json();
      box.classList.remove("hidden");
      const ring = document.getElementById("live-score-num");
      ring.textContent = d.score;
      ring.parentElement.className = "live-score-ring grade-" + (d.grade || "B");
      document.getElementById("live-score-tip").textContent =
        d.recoverable ? `补齐短板后预计可达 ${d.target_score} 分,勾选加分项即时刷新` : "资质达标,可直接提交";
      const cw = getCoupons();
      if ((cw.risk || 0) > 0) document.getElementById("live-score-tip").textContent += `(可用风控加分券 ×${cw.risk})`;
    } catch (_) {}
  }, 450);
}
form.querySelectorAll("input, select").forEach((el) => {
  el.addEventListener("input", () => { updateLeverageWarn(); scheduleLiveScore(); });
  el.addEventListener("change", () => { updateLeverageWarn(); scheduleLiveScore(); });
});
document.addEventListener("change", (e) => {
  if (e.target.classList && e.target.classList.contains("ind-bonus")) scheduleLiveScore();
});
updateLeverageWarn(); scheduleLiveScore();

// 月供试算器(等额本息)
function calcMortgage() {
  const amt = parseFloat(document.getElementById("calc-amount").value) || 0;
  const rate = parseFloat(document.getElementById("calc-rate").value) || 0;
  const term = parseInt(document.getElementById("calc-term").value) || 0;
  const mode = (document.getElementById("calc-mode") || {}).value || "equal";
  const subsidy = parseFloat((document.getElementById("calc-subsidy") || {}).value) || 0;
  const mEl = document.getElementById("calc-monthly");
  const iEl = document.getElementById("calc-interest");
  const tEl = document.getElementById("calc-total");
  const saveWrap = document.querySelector(".calc-save");
  const sEl = document.getElementById("calc-saved");
  const mLbl = mEl.parentElement.querySelector("small");
  if (amt <= 0 || term <= 0) {
    mEl.textContent = iEl.textContent = tEl.textContent = "—";
    return;
  }
  const r = rate / 100 / 12;
  let monthly, total;
  if (mode === "interest_first") {
    monthly = amt * r;
    total = monthly * term + amt;
    mLbl.textContent = "每月付息(末期还本)";
  } else {
    if (r === 0) monthly = amt / term;
    else monthly = (amt * r * Math.pow(1 + r, term)) / (Math.pow(1 + r, term) - 1);
    total = monthly * term;
    mLbl.textContent = "每月还款";
  }
  mEl.textContent = monthly.toFixed(2) + " 万";
  iEl.textContent = (total - amt).toFixed(2) + " 万";
  tEl.textContent = total.toFixed(2) + " 万";
  if (subsidy > 0) {
    const effR = Math.max(0, rate - subsidy) / 100 / 12;
    let tot2;
    if (mode === "interest_first") tot2 = amt * effR * term + amt;
    else if (effR === 0) tot2 = amt;
    else { const m2 = (amt * effR * Math.pow(1 + effR, term)) / (Math.pow(1 + effR, term) - 1); tot2 = m2 * term; }
    sEl.textContent = (total - tot2).toFixed(2) + " 万";
    saveWrap.classList.remove("hidden");
  } else if (saveWrap) saveWrap.classList.add("hidden");
  drawCalcChart(amt, r, mode === "interest_first" ? amt * r : monthly, term);
}

function drawCalcChart(amt, r, monthly, term) {
  const cv = document.getElementById("calc-chart");
  if (!cv) return;
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || cv.parentElement.clientWidth || 600;
  const H = 180;
  cv.width = W * dpr;
  cv.height = H * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, W, H);

  // 逐月剩余本金
  const pts = [amt];
  let bal = amt;
  for (let i = 0; i < term; i++) {
    bal = bal * (1 + r) - monthly;
    pts.push(Math.max(0, bal));
  }
  const dark = document.body.classList.contains("dark");
  const line = dark ? "#60a5fa" : "#8cacd2";
  const grid = dark ? "#2a3a55" : "#e5e7eb";
  const pad = { l: 44, r: 12, t: 12, b: 24 };
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
  const max = pts[0];
  const x = (i) => pad.l + (cw * i) / term;
  const y = (v) => pad.t + ch * (1 - v / max);

  ctx.strokeStyle = grid; ctx.lineWidth = 1; ctx.fillStyle = dark ? "#9ca3af" : "#9ca3af";
  ctx.font = "11px sans-serif";
  for (let g = 0; g <= 4; g++) {
    const gy = pad.t + (ch * g) / 4;
    ctx.beginPath(); ctx.moveTo(pad.l, gy); ctx.lineTo(W - pad.r, gy); ctx.stroke();
    ctx.fillText(Math.round((max * (4 - g)) / 4) + "万", 4, gy + 3);
  }
  const grad = ctx.createLinearGradient(0, pad.t, 0, H);
  grad.addColorStop(0, line + "55"); grad.addColorStop(1, line + "00");
  ctx.beginPath(); ctx.moveTo(x(0), y(pts[0]));
  pts.forEach((v, i) => ctx.lineTo(x(i), y(v)));
  ctx.lineTo(x(term), y(0)); ctx.lineTo(x(0), y(0)); ctx.closePath();
  ctx.fillStyle = grad; ctx.fill();
  ctx.beginPath(); ctx.moveTo(x(0), y(pts[0]));
  pts.forEach((v, i) => ctx.lineTo(x(i), y(v)));
  ctx.strokeStyle = line; ctx.lineWidth = 2.5; ctx.stroke();
}
["calc-amount", "calc-rate", "calc-term", "calc-mode", "calc-subsidy"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("input", calcMortgage);
  if (el) el.addEventListener("change", calcMortgage);
});

/* ===== 征信养护工具箱 ===== */
function creditHealth() {
  const el = document.getElementById("credit-health");
  if (!el) return;
  const od = parseInt(document.getElementById("ct-overdue").value) || 0;
  const q = parseInt(document.getElementById("ct-queries").value) || 0;
  const debt = parseFloat(document.getElementById("ct-debt").value) || 0;
  const rev = parseFloat(document.getElementById("ct-revenue").value) || 0;
  let score = 100;
  score -= Math.min(40, od * 12);
  score -= Math.max(0, q - 4) * 5;
  const ratio = rev > 0 ? debt / rev : 1;
  score -= Math.max(0, ratio - 0.7) * 60;
  score = Math.max(20, Math.round(score));
  const tips = [];
  if (od > 0) tips.push(`存在 ${od} 次逾期:保持后续24个月零逾期,旧记录5年后覆盖,近期申请前先结清欠款。`);
  else tips.push("无逾期,信用基础良好,继续保持。");
  if (q > 4) tips.push(`半年硬查询 ${q} 次偏多,建议停止点击各类"测额度",养1-2个月再集中申请。`);
  else tips.push("查询次数健康,集中2周内完成申请可减少花征信。");
  if (ratio > 0.7) tips.push(`负债率约 ${Math.round(ratio * 100)}%:先息后本/分笔申请或先还部分,降到70%以内更易批。`);
  else tips.push(`负债率约 ${Math.round(ratio * 100)}%,处于安全区间。`);
  const grade = score >= 85 ? "A 优秀" : score >= 70 ? "B 良好" : score >= 55 ? "C 一般" : "D 偏弱";
  const cls = score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : "D";
  el.innerHTML = `<div class="ch-score grade-${cls}"><span>${score}</span><small>征信健康分·${grade}</small></div>
    <ul class="ch-tips">${tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
    <div class="ch-note">📌 按建议养护 1-3 个月,通过率与额度通常明显改善;申请前用「前置预审」复核更稳。</div>`;
}
["ct-overdue", "ct-queries", "ct-debt", "ct-revenue"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("input", creditHealth);
});
creditHealth();
calcMortgage();

// 深色模式切换
const themeToggle = document.getElementById("theme-toggle");
function applyTheme(dark) {
  document.body.classList.toggle("dark", dark);
  if (themeToggle) themeToggle.textContent = dark ? "☀️ 浅色模式" : "🌙 深色模式";
  localStorage.setItem("theme", dark ? "dark" : "light");
  if (typeof calcMortgage === "function") calcMortgage();
}
if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    applyTheme(!document.body.classList.contains("dark"));
  });
}
applyTheme(localStorage.getItem("theme") === "dark");

async function loadRecords() {
  const listEl = document.getElementById("records-list");
  const statsEl = document.getElementById("records-stats");
  listEl.innerHTML = '<div class="empty">加载中...</div>';
  if (statsEl) statsEl.innerHTML = "";
  try {
    const res = await fetch("/api/applications");
    let records = await res.json();
    const kw = (document.getElementById("rec-filter")?.value || "").trim().toLowerCase();
    if (kw) records = records.filter((r) => (r.company_name || "").toLowerCase().includes(kw));
    if (!records.length) {
      if (statsEl) statsEl.innerHTML = "";
      listEl.innerHTML = kw
        ? `<div class="empty">没有匹配「${escapeHtml(kw)}」的记录,换个企业名试试。</div>`
        : '<div class="empty">暂无申请记录。在「智能匹配」中完成匹配后,点击「保存为申请记录」即可。</div>';
      loadDataAssets();
      return;
    }
    if (statsEl) statsEl.innerHTML = renderRecordStats(records);
    listEl.innerHTML = records.map(recordRow).join("");
    bindRecordEvents();
    loadRecordInsights();
    loadDataAssets();
  } catch (err) {
    listEl.innerHTML = `<div class="empty">加载失败:${escapeHtml(err.message)}</div>`;
  }
}

function renderRecordStats(records) {
  const total = records.length;
  const counts = {};
  STATUS_LIST.forEach((s) => (counts[s] = 0));
  let demand = 0;
  let approvedAmt = 0;
  records.forEach((r) => {
    counts[r.status] = (counts[r.status] || 0) + 1;
    demand += Number(r.loan_amount) || 0;
    if (r.status === "已通过" || r.status === "已放款")
      approvedAmt += Number(r.best_amount) || 0;
  });
  const inFlight = counts["已提交"] + counts["审核中"];
  const done = counts["已通过"] + counts["已放款"];
  const closed = done + counts["已拒绝"];
  const approveRate = closed ? Math.round((done / closed) * 100) : 0;
  const avgDemand = total ? Math.round(demand / total) : 0;

  const cards = [
    { label: "申请总数", value: total, sub: `${counts["待提交"]} 待提交` },
    { label: "进行中", value: inFlight, sub: "已提交+审核中" },
    { label: "已获批", value: done, sub: `通过率 ${approveRate}%` },
    { label: "需求合计", value: `${demand}万`, sub: `均额 ${avgDemand}万` },
    { label: "预计获贷", value: `${approvedAmt}万`, sub: "通过/放款额度" },
  ];
  const statCards = cards
    .map(
      (c) => `<div class="rec-stat"><div class="rec-stat-val">${c.value}</div>
        <div class="rec-stat-lbl">${c.label}</div><div class="rec-stat-sub">${c.sub}</div></div>`
    )
    .join("");

  const bars = STATUS_LIST.filter((s) => counts[s] > 0)
    .map((s) => {
      const pct = Math.round((counts[s] / total) * 100);
      return `<div class="rec-bar-row"><span class="rec-bar-tag ${statusClass(
        s
      )}">${s} ${counts[s]}</span><div class="rec-bar"><i style="width:${pct}%"></i></div></div>`;
    })
    .join("");

  let tip = "";
  if (counts["待提交"] > 0) tip = `有 ${counts["待提交"]} 笔待提交,尽快导出银行成品材料提交可加快放款。`;
  else if (counts["审核中"] > 0) tip = `${counts["审核中"]} 笔审核中,建议主动联系支行客户经理跟进。`;
  else if (counts["已拒绝"] > 0) tip = "存在被拒申请,可在「冲刺/稳妥方案」中切换更匹配的产品再申请。";
  else if (done > 0) tip = "恭喜!已有获批方案,后续可关注贴息申报与续贷时机。";

  return `<div class="rec-stats-grid">${statCards}</div>
    <div class="rec-bars">${bars}</div>
    ${tip ? `<div class="rec-tip">💡 ${tip}</div>` : ""}
    <div id="records-insights"></div>`;
}

async function loadDataAssets() {
  const el = document.getElementById("data-assets");
  if (!el) return;
  try {
    const res = await fetch("/api/data-assets");
    const d = await res.json();
    const cards = [
      { v: d.total_samples, l: "累积样本", s: "真实预审/申请" },
      { v: d.approved_samples, l: "放款案例", s: `通过率 ${d.pass_rate}%` },
      { v: `${d.released_amount}万`, l: "撮合放款额", s: "已获批/放款" },
      { v: d.subsidy_cases, l: "贴息落地", s: "补贴匹配案例" },
      { v: d.avg_risk_score, l: "平均风控分", s: "样本均值" },
    ].map((c) => `<div class="rec-stat"><div class="rec-stat-val">${c.v}</div>
      <div class="rec-stat-lbl">${c.l}</div><div class="rec-stat-sub">${c.s}</div></div>`).join("");
    const inds = (d.industries || []).map((i) =>
      `<span class="da-ind">${escapeHtml(i.name)} ${i.count}</span>`).join("");
    const adminView = localStorage.getItem("daView") !== "c";
    const toggle = `<div class="da-toggle"><button data-v="c" class="${adminView ? "" : "on"}">C端用户视图</button><button data-v="admin" class="${adminView ? "on" : ""}">管理员视图</button></div>`;
    const moat = adminView ? `<div class="da-moat">数据壁垒指数 <b>${d.moat_index}</b>/100<div class="da-bar"><i style="width:${d.moat_index}%"></i></div><small>样本越多,匹配越准,壁垒越深,越难被复制。</small></div>
      ${(d.trend && d.trend.length) ? `<div class="da-trend"><div class="da-trend-h">📈 近月样本/放款趋势</div><canvas id="da-trend-cv" height="160"></canvas></div>` : ""}` :
      `<div class="da-cview">仅展示本行业/区域的放款成功率与贴息落地案例。完整壁垒与趋势数据见管理员视图。</div>`;
    el.innerHTML = `<div class="da-head">🔐 独家私有数据集 <span class="da-badge">通用AI无法获取的线下闭环数据</span></div>
      ${toggle}
      <div class="rec-stats-grid">${cards}</div>
      ${inds ? `<div class="da-inds">行业分布:${inds}</div>` : ""}
      ${moat}`;
    el.querySelectorAll(".da-toggle button").forEach((b) => b.addEventListener("click", () => {
      localStorage.setItem("daView", b.dataset.v); loadDataAssets();
    }));
    if (adminView && d.trend && d.trend.length) drawTrend(d.trend);
  } catch (_) { el.innerHTML = ""; }
}

function drawTrend(trend) {
  const cv = document.getElementById("da-trend-cv");
  if (!cv) return;
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || cv.parentElement.clientWidth || 600;
  const H = 160;
  cv.width = W * dpr; cv.height = H * dpr;
  const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr); ctx.clearRect(0, 0, W, H);
  const dark = document.body.classList.contains("dark");
  const pad = { l: 32, r: 12, t: 16, b: 26 };
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
  const maxV = Math.max(1, ...trend.map((t) => t.samples));
  const n = trend.length;
  const bw = cw / n * 0.5;
  trend.forEach((t, i) => {
    const x = pad.l + (cw * (i + 0.5)) / n;
    const hs = ch * (t.samples / maxV), ha = ch * (t.approved / maxV);
    ctx.fillStyle = dark ? "#3a2f6b" : "#ddd4f7";
    ctx.fillRect(x - bw / 2, pad.t + ch - hs, bw, hs);
    ctx.fillStyle = "#6d28d9";
    ctx.fillRect(x - bw / 2, pad.t + ch - ha, bw, ha);
    ctx.fillStyle = dark ? "#aaa" : "#888"; ctx.font = "10px sans-serif"; ctx.textAlign = "center";
    ctx.fillText(t.month.slice(5), x, H - 8);
    ctx.fillText(t.samples, x, pad.t + ch - hs - 4);
  });
}

async function loadRecordInsights() {
  const el = document.getElementById("records-insights");
  if (!el) return;
  try {
    const res = await fetch("/api/applications-insights");
    const data = await res.json();
    if (!data.reasons || !data.reasons.length) { el.innerHTML = ""; return; }
    const items = data.reasons
      .map((r) => `<li><b>${escapeHtml(r.reason)}</b> · ${r.count}次<br><span>${escapeHtml(r.tip)}</span></li>`)
      .join("");
    el.innerHTML = `<div class="rec-insights"><div class="rec-insights-h">📈 迭代优化建议(共 ${data.rejected_total} 笔被拒,越用越准)</div><ul>${items}</ul></div>`;
  } catch (_) { el.innerHTML = ""; }
}

function recProgress(status) {
  if (status === "已拒绝") {
    return `<div class="rec-progress rejected"><span>资质预审</span><span>材料导出</span><span>银行收件</span><span class="cur">审批未通过</span></div>`;
  }
  const steps = ["资质预审", "材料导出", "银行收件", "审批中", "放款"];
  const map = { "待提交": 1, "已提交": 2, "审核中": 3, "已通过": 4, "已放款": 5 };
  const cur = map[status] || 1;
  return `<div class="rec-progress">` + steps.map((s, i) => {
    const n = i + 1;
    const cls = n < cur ? "done" : n === cur ? "cur" : "";
    return `<span class="${cls}">${s}</span>`;
  }).join("") + `</div>`;
}

function recordRow(r) {
  const options = STATUS_LIST.map(
    (s) => `<option value="${s}" ${s === r.status ? "selected" : ""}>${s}</option>`
  ).join("");
  return `<div class="record" data-id="${r.id}">
    <div class="rec-main">
      <div class="rec-title">
        <span class="rec-name">${escapeHtml(r.company_name)}</span>
        <span class="rec-grade grade-${r.risk_grade}">风控 ${r.risk_score}·${escapeHtml(r.risk_grade)}</span>
      </div>
      <div class="rec-meta">${escapeHtml(r.industry)} · 需求 ${r.loan_amount} 万 · 推荐【${escapeHtml(
    r.best_product
  )}】${r.best_amount} 万 · ${escapeHtml(r.created_at)}</div>
      ${r.status === "已拒绝" && r.reject_reason ? `<div class="rec-reject">❌ 被拒原因:${escapeHtml(r.reject_reason)}</div>` : ""}
      ${recProgress(r.status)}
    </div>
    <div class="rec-actions">
      <span class="rec-status ${statusClass(r.status)}">${escapeHtml(r.status)}</span>
      <select class="rec-status-select" data-id="${r.id}">${options}</select>
      <button class="rec-btn rec-view" data-id="${r.id}">查看</button>
      <button class="rec-btn rec-pdf" data-id="${r.id}">PDF</button>
      <button class="rec-btn rec-excel" data-id="${r.id}">Excel</button>
      <button class="rec-btn rec-del" data-id="${r.id}">删除</button>
    </div>
  </div>`;
}

function bindRecordEvents() {
  document.querySelectorAll(".rec-status-select").forEach((sel) => {
    sel.addEventListener("change", async () => {
      let reject_reason = "";
      if (sel.value === "已拒绝") {
        const reasons = ["征信逾期", "抵押物不足", "经营年限短", "流水不足", "负债率高", "资料不全", "其他"];
        reject_reason = prompt("请选择/填写被拒原因(用于优化下次匹配):\n" + reasons.join("、"), "征信逾期") || "";
      }
      await fetch(`/api/applications/${sel.dataset.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: sel.value, reject_reason }),
      });
      loadRecords();
    });
  });
  document.querySelectorAll(".rec-del").forEach((b) => {
    b.addEventListener("click", async () => {
      if (!confirm("确定删除这条申请记录?")) return;
      await fetch(`/api/applications/${b.dataset.id}`, { method: "DELETE" });
      loadRecords();
    });
  });
  document.querySelectorAll(".rec-pdf").forEach((b) => {
    b.addEventListener("click", () => downloadRecordFile(b.dataset.id, "pdf"));
  });
  document.querySelectorAll(".rec-excel").forEach((b) => {
    b.addEventListener("click", () => downloadRecordFile(b.dataset.id, "excel"));
  });
  document.querySelectorAll(".rec-view").forEach((b) => {
    b.addEventListener("click", () => viewRecord(b.dataset.id));
  });
}

async function downloadRecordFile(id, type) {
  const ext = type === "excel" ? "xlsx" : "pdf";
  const res = await fetch(`/api/applications/${id}/${type}`, { method: "POST" });
  if (!res.ok) return showToast("生成失败,请稍后重试", "error");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `贷款方案.${ext}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function viewRecord(id) {
  const res = await fetch(`/api/applications/${id}`);
  if (!res.ok) return showToast("加载失败,请稍后重试", "error");
  const rec = await res.json();
  const p = rec.profile;
  const creditCn = { excellent: "优秀", good: "良好", fair: "一般", poor: "较差" };
  const purposeCn = {
    working_capital: "流动资金周转",
    equipment: "设备采购",
    expansion: "扩大经营",
    inventory: "备货采购",
    rd: "研发投入",
    other: "其他",
  };
  let html = `<h2>${escapeHtml(rec.company_name)} · 申请详情</h2>
    <p class="modal-sub">状态:${escapeHtml(rec.status)} · 创建于 ${escapeHtml(rec.created_at)}</p>
    <h3 class="modal-h3">企业信息</h3>
    <div class="modal-grid">
      <div><b>行业</b>${escapeHtml(p.industry_detail ? `${p.industry_detail}(${p.industry})` : p.industry)}</div>
      <div><b>经营年限</b>${p.years_in_business} 年</div>
      <div><b>年营业额</b>${p.annual_revenue} 万元</div>
      <div><b>注册资本</b>${p.registered_capital} 万元</div>
      <div><b>征信</b>${creditCn[p.credit_level] || p.credit_level}</div>
      <div><b>贷款用途</b>${purposeCn[p.loan_purpose] || p.loan_purpose}</div>
      <div><b>贷款需求</b>${p.loan_amount} 万元</div>
      <div><b>期望期限</b>${p.preferred_term_months} 个月</div>
    </div>`;
  const plans = rec.result.plans || [];
  html += `<h3 class="modal-h3">推荐方案(${plans.length})</h3>`;
  if (plans.length) {
    html += `<table class="modal-table"><tr><th>产品</th><th>额度(万)</th><th>年化利率</th><th>期限</th><th>月供(万)</th><th>匹配分</th></tr>`;
    plans.forEach((pl, i) => {
      html += `<tr class="${i === 0 ? "best-row" : ""}"><td>${i === 0 ? "⭐ " : ""}${escapeHtml(
        pl.product_name
      )}</td><td>${pl.estimated_amount}</td><td>${pl.annual_rate_min}%-${pl.annual_rate_max}%</td><td>${
        pl.suggested_term_months
      }月</td><td>${pl.monthly_payment_estimate}</td><td>${pl.score}</td></tr>`;
    });
    html += `</table>`;
  } else {
    html += `<p class="empty">暂无匹配方案</p>`;
  }
  document.getElementById("modal-content").innerHTML = html;
  document.getElementById("detail-modal").classList.remove("hidden");
}

document.getElementById("modal-close").addEventListener("click", closeModal);
document.querySelector(".modal-backdrop").addEventListener("click", closeModal);
function closeModal() {
  document.getElementById("detail-modal").classList.add("hidden");
}

/* ===== 线下客户经理预约(入库) ===== */
async function fetchBookings() {
  try { return (await (await fetch("/api/leads")).json()).filter((l) => l.kind === "预约"); } catch (e) { return []; }
}
async function openManagerBooking() {
  const today = new Date().toISOString().slice(0, 10);
  const list = await fetchBookings();
  const rows = list.length ? list.map((b) => `<li>📅 ${escapeHtml(b.created_at.slice(5))} · ${escapeHtml(b.bank)} · ${escapeHtml(b.slot)} · ${escapeHtml(b.phone)} <span class="bk-st">${escapeHtml(b.status)}</span></li>`).join("") : '<li class="empty">暂无预约</li>';
  const p = window.__lastProfile || {};
  document.getElementById("modal-content").innerHTML = `<h2>🤝 预约线下客户经理</h2>
    <p class="modal-sub">平台内直接预约,经理可提前查看你的预审报告,提高签约率。</p>
    <div class="bk-grid">
      <label>意向银行<select id="bk-bank"><option>工商银行</option><option>建设银行</option><option>招商银行</option><option>北京银行</option><option>不限,帮我推荐</option></select></label>
      <label>时间段<select id="bk-slot"><option>上午 9:00-12:00</option><option>下午 14:00-17:00</option><option>晚间 18:00-20:00</option></select></label>
      <label>联系电话<input type="tel" id="bk-phone" placeholder="手机号" maxlength="11"></label>
      <label>融资需求(万)<input type="number" id="bk-amt" value="${p.loan_amount || 100}"></label>
    </div>
    <button id="bk-submit" class="export-btn save-btn">确认预约</button>
    <h3 class="modal-h3">我的预约</h3><ul class="bk-list">${rows}</ul>`;
  document.getElementById("detail-modal").classList.remove("hidden");
  document.getElementById("bk-submit").addEventListener("click", async () => {
    const phone = document.getElementById("bk-phone").value.trim();
    if (!/^1\d{10}$/.test(phone)) return showToast("请填写正确的11位手机号", "error");
    const btn = document.getElementById("bk-submit");
    btn.disabled = true; btn.textContent = "提交中...";
    try {
      await fetch("/api/leads", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: "预约", company_name: p.company_name || "", phone, industry: p.industry || "",
          loan_amount: parseFloat(document.getElementById("bk-amt").value) || 0,
          bank: document.getElementById("bk-bank").value, slot: document.getElementById("bk-slot").value }) });
      showToast("预约成功,客户经理将在1个工作日内回访", "success");
      openManagerBooking();
    } catch (e) { showToast("提交失败,请稍后重试", "error"); btn.disabled = false; btn.textContent = "确认预约"; }
  });
}
const _cm = document.getElementById("chain-manager");
if (_cm) _cm.addEventListener("click", openManagerBooking);

/* ===================== 虚拟金融顾问 ===================== */
const chatLauncher = document.getElementById("chat-launcher");
const chatWindow = document.getElementById("chat-window");
const chatClose = document.getElementById("chat-close");
const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatQuick = document.getElementById("chat-quick");
const chatModeEl = document.getElementById("chat-mode");
const avatarStage = document.getElementById("avatar-stage");
const avatarRender = document.getElementById("avatar-render");
const avatarPicker = document.getElementById("avatar-picker");
const chatAvatarEl = document.querySelector(".chat-avatar");
const launcherFaceEl = document.querySelector("#chat-launcher .avatar-face");
const chatNameEl = document.querySelector(".chat-name");
const customPanel = document.getElementById("avatar-custom-panel");
const chatMic = document.getElementById("chat-mic");
const chatTts = document.getElementById("chat-tts");
const chatHistoryBtn = document.getElementById("chat-history-btn");
const chatNewBtn = document.getElementById("chat-new-btn");
const chatHistoryPanel = document.getElementById("chat-history-panel");

let chatHistory = [];
let chatInited = false;
let chatBusy = false;
let chatSessionId = "";
let ttsEnabled = false;

const QUICK_QUESTIONS = [
  "征信不好能贷款吗?",
  "普通人怎么开始理财投资?",
  "有哪些普惠补贴政策?",
  "什么是通货膨胀?",
  "怎么提高工作效率?",
  "推荐几个减压的小方法",
];

function setAvatarState(state) {
  if (avatarStage) avatarStage.dataset.state = state;
}

/* ===================== 形象库 + 自定义 ===================== */
const Lib = window.AvatarLib;
let currentAvatar = "robot"; // preset id 或 "custom"
let customConfig = Object.assign({}, Lib.defaultCustom);

function loadAvatarPrefs() {
  try {
    const sel = localStorage.getItem("avatarSel");
    if (sel) currentAvatar = sel;
    const cfg = localStorage.getItem("avatarCustom");
    if (cfg) customConfig = Object.assign({}, Lib.defaultCustom, JSON.parse(cfg));
    // 兼容旧版单选配饰
    if (!Array.isArray(customConfig.accessories)) {
      customConfig.accessories =
        customConfig.accessory && customConfig.accessory !== "none" ? [customConfig.accessory] : [];
    }
    delete customConfig.accessory;
  } catch (e) {}
}

function avatarEmoji(id) {
  if (id === "custom") return "🎨";
  const p = Lib.getById(id);
  return p ? p.emoji : "🤖";
}

function renderAvatar() {
  if (currentAvatar === "custom") {
    avatarRender.innerHTML = Lib.buildCustom(customConfig, "stage");
  } else {
    const p = Lib.getById(currentAvatar) || Lib.presets[0];
    avatarRender.innerHTML = p.svg;
  }
  // 同步顶部图标与浮动入口
  const emo = avatarEmoji(currentAvatar);
  if (chatAvatarEl) chatAvatarEl.textContent = emo;
  if (launcherFaceEl) launcherFaceEl.textContent = emo;
  // 名称
  let name = "小微贷管家";
  if (currentAvatar === "custom" && customConfig.name) name = customConfig.name;
  if (chatNameEl) chatNameEl.textContent = name;
  // 高亮选中按钮
  if (avatarPicker) {
    avatarPicker.querySelectorAll("button").forEach((b) => {
      b.classList.toggle("active", b.dataset.id === currentAvatar);
    });
  }
}

function selectAvatar(id) {
  currentAvatar = id;
  try {
    localStorage.setItem("avatarSel", id);
  } catch (e) {}
  renderAvatar();
}

function buildPicker() {
  if (!avatarPicker) return;
  let html = "";
  Lib.presets.forEach((p) => {
    html += '<button data-id="' + p.id + '" title="' + p.name + '">' + p.emoji + "</button>";
  });
  html += '<button data-id="custom" title="我的自定义形象">🎨</button>';
  html += '<button class="acp-trigger" data-action="customize" title="自定义形象">✏️</button>';
  avatarPicker.innerHTML = html;
  avatarPicker.querySelectorAll("button").forEach((b) => {
    b.addEventListener("click", () => {
      if (b.dataset.action === "customize") {
        openCustomPanel();
      } else {
        selectAvatar(b.dataset.id);
      }
    });
  });
}

/* -------- 自定义面板 -------- */
const acpPreview = document.getElementById("acp-preview");
const acpPrimary = document.getElementById("acp-primary");
const acpEye = document.getElementById("acp-eye");
const acpHead = document.getElementById("acp-head");
const acpAcc = document.getElementById("acp-acc");
const acpName = document.getElementById("acp-name");
let draftConfig = {};

function swatchHtml(colors, current) {
  return colors
    .map(
      (c) =>
        '<span class="sw' + (c === current ? " active" : "") + '" data-val="' + c + '" style="background:' + c + '"></span>'
    )
    .join("");
}
function optHtml(opts, current) {
  return opts
    .map(
      (o) =>
        '<span class="opt' + (o.id === current ? " active" : "") + '" data-val="' + o.id + '">' + o.name + "</span>"
    )
    .join("");
}
function multiOptHtml(opts, selected) {
  return opts
    .map(
      (o) =>
        '<span class="opt' + (selected.indexOf(o.id) !== -1 ? " active" : "") + '" data-val="' + o.id + '">' + o.name + "</span>"
    )
    .join("");
}

function getDraftAccessories() {
  if (Array.isArray(draftConfig.accessories)) return draftConfig.accessories;
  draftConfig.accessories = draftConfig.accessory && draftConfig.accessory !== "none" ? [draftConfig.accessory] : [];
  return draftConfig.accessories;
}

function renderCustomControls() {
  const o = Lib.customOptions;
  acpPrimary.innerHTML = swatchHtml(o.primary, draftConfig.primary);
  acpEye.innerHTML = swatchHtml(o.eye, draftConfig.eye);
  acpHead.innerHTML = optHtml(o.head, draftConfig.head);
  acpAcc.innerHTML = multiOptHtml(o.accessory, getDraftAccessories());
  acpName.value = draftConfig.name || "";
  acpPreview.innerHTML = Lib.buildCustom(draftConfig, "prev");
}

function bindCustomControls() {
  function pick(container, key) {
    container.addEventListener("click", (e) => {
      const t = e.target.closest("[data-val]");
      if (!t) return;
      draftConfig[key] = t.dataset.val;
      renderCustomControls();
    });
  }
  pick(acpPrimary, "primary");
  pick(acpEye, "eye");
  pick(acpHead, "head");
  // 配饰多选:点击切换
  acpAcc.addEventListener("click", (e) => {
    const t = e.target.closest("[data-val]");
    if (!t) return;
    const list = getDraftAccessories();
    const id = t.dataset.val;
    const i = list.indexOf(id);
    if (i === -1) list.push(id);
    else list.splice(i, 1);
    renderCustomControls();
  });
  acpName.addEventListener("input", () => {
    draftConfig.name = acpName.value;
  });
  document.getElementById("acp-close").addEventListener("click", closeCustomPanel);
  document.getElementById("acp-save").addEventListener("click", saveCustom);
}

function openCustomPanel() {
  draftConfig = JSON.parse(JSON.stringify(Object.assign({}, Lib.defaultCustom, customConfig)));
  getDraftAccessories();
  renderCustomControls();
  customPanel.classList.remove("hidden");
}
function closeCustomPanel() {
  customPanel.classList.add("hidden");
}
function saveCustom() {
  customConfig = JSON.parse(JSON.stringify(draftConfig));
  delete customConfig.accessory;
  if (!customConfig.name) customConfig.name = "我的顾问";
  try {
    localStorage.setItem("avatarCustom", JSON.stringify(customConfig));
  } catch (e) {}
  closeCustomPanel();
  selectAvatar("custom");
}

// 初始化形象库
loadAvatarPrefs();
buildPicker();
bindCustomControls();
renderAvatar();

chatLauncher.addEventListener("click", openChat);
const navChatBtn = document.getElementById("nav-chat-btn");
if (navChatBtn) navChatBtn.addEventListener("click", openChat);
function closeChatPanel() {
  if (chatWindow.classList.contains("hidden")) return;
  chatWindow.classList.add("hidden");
  chatLauncher.classList.remove("hidden");
  if (navChatBtn) navChatBtn.classList.remove("active");
  stopSpeak();
}
chatClose.addEventListener("click", closeChatPanel);
chatSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.isComposing) sendChat();
});
chatNewBtn.addEventListener("click", startNewChat);
chatHistoryBtn.addEventListener("click", toggleHistory);
chatTts.addEventListener("click", toggleTts);
chatMic.addEventListener("click", toggleMic);

async function openChat() {
  chatWindow.classList.remove("hidden");
  chatLauncher.classList.add("hidden");
  if (navChatBtn) {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    navChatBtn.classList.add("active");
  }
  chatInput.focus();
  setAvatarState("idle");
  if (chatInited) return;
  chatInited = true;

  // 检测当前对话后端
  try {
    const res = await fetch("/api/chat/status");
    const s = await res.json();
    const labels = {
      azure: "Azure OpenAI · 在线",
      ollama: "本地大模型 · 在线",
      dashscope: "通义千问 · 在线",
      fallback: "智能助手",
    };
    chatModeEl.textContent = labels[s.provider] || (s.llm_enabled ? "在线" : "智能助手");
    azureTtsEnabled = !!s.azure_tts;
  } catch (e) {}

  addMessage(
    "assistant",
    "您好!我是您的智能助手「小微贷管家」🤝\n经济金融是我的强项,日常生活、学习工作、健康旅行、闲聊解闷也都欢迎随便问~ 想融资的话,也可以到'智能匹配'页填写企业情况获取专属方案。"
  );
  renderQuick();
}

function startNewChat() {
  stopSpeak();
  chatHistory = [];
  chatSessionId = "";
  chatMessages.innerHTML = "";
  chatHistoryPanel.classList.add("hidden");
  addMessage(
    "assistant",
    "已开启新的对话 🆕 有什么贷款或金融问题尽管问我吧!"
  );
  renderQuick();
  setAvatarState("idle");
}

function renderQuick() {
  chatQuick.innerHTML = QUICK_QUESTIONS.map(
    (q) => `<button class="quick-q">${escapeHtml(q)}</button>`
  ).join("");
  chatQuick.querySelectorAll(".quick-q").forEach((b) => {
    b.addEventListener("click", () => {
      chatInput.value = b.textContent;
      sendChat();
    });
  });
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `chat-msg ${role}`;
  div.innerHTML = `<div class="bubble">${formatText(text)}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div.querySelector(".bubble");
}

function formatText(text) {
  return escapeHtml(text).replace(/\n/g, "<br>");
}

async function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg || chatBusy) return;
  chatBusy = true;
  chatInput.value = "";
  chatQuick.innerHTML = "";
  chatHistoryPanel.classList.add("hidden");
  stopSpeak();
  addMessage("user", msg);

  const bubble = addMessage("assistant", "");
  bubble.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
  setAvatarState("thinking");

  let full = "";
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, history: chatHistory, session_id: chatSessionId }),
    });
    if (!res.ok || !res.body) throw new Error("请求失败");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();
      for (const line of lines) {
        const t = line.trim();
        if (!t.startsWith("data:")) continue;
        const data = t.slice(5).trim();
        if (data === "[DONE]") continue;
        try {
          const obj = JSON.parse(data);
          if (obj.session_id) {
            chatSessionId = obj.session_id;
          }
          if (obj.delta) {
            full += obj.delta;
            bubble.innerHTML = formatText(full);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
        } catch (e) {}
      }
    }
  } catch (err) {
    full = "抱歉,暂时无法回答,请稍后再试。";
    bubble.innerHTML = formatText(full);
  }

  if (!full) {
    full = "抱歉,我没有理解,请换个说法试试。";
    bubble.innerHTML = formatText(full);
  }

  chatHistory.push({ role: "user", content: msg });
  chatHistory.push({ role: "assistant", content: full });
  chatBusy = false;

  if (ttsEnabled) {
    speak(full);
  } else {
    setAvatarState("idle");
  }
}

/* ===================== 语音输入(Web Speech API) ===================== */
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let recording = false;

if (SpeechRec) {
  recognition = new SpeechRec();
  recognition.lang = "zh-CN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.addEventListener("result", (e) => {
    const text = e.results[0][0].transcript;
    chatInput.value = text;
  });
  recognition.addEventListener("end", () => {
    recording = false;
    chatMic.classList.remove("recording");
    if (chatInput.value.trim()) sendChat();
  });
  recognition.addEventListener("error", () => {
    recording = false;
    chatMic.classList.remove("recording");
  });
} else {
  chatMic.style.display = "none";
}

function toggleMic() {
  if (!recognition) return;
  if (recording) {
    recognition.stop();
    return;
  }
  stopSpeak();
  try {
    recording = true;
    chatMic.classList.add("recording");
    chatInput.value = "";
    recognition.start();
  } catch (e) {
    recording = false;
    chatMic.classList.remove("recording");
  }
}

/* ===================== 语音朗读(TTS) ===================== */
const synth = window.speechSynthesis;
let azureTtsEnabled = false;
let azureAudio = null;
if (!synth) {
  // 即便浏览器无内置 TTS,Azure 仍可用,故不强制隐藏按钮
}

function toggleTts() {
  ttsEnabled = !ttsEnabled;
  chatTts.classList.toggle("off", !ttsEnabled);
  chatTts.title = ttsEnabled ? "朗读回复:开" : "朗读回复:关";
  if (!ttsEnabled) stopSpeak();
}
// 默认关闭朗读
chatTts.classList.add("off");

function speak(text) {
  if (!text) {
    setAvatarState("idle");
    return;
  }
  stopSpeak();
  if (azureTtsEnabled) {
    speakAzure(text);
    return;
  }
  speakBrowser(text);
}

async function speakAzure(text) {
  try {
    setAvatarState("speaking");
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error("tts unavailable");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    azureAudio = new Audio(url);
    azureAudio.addEventListener("ended", () => {
      setAvatarState("idle");
      URL.revokeObjectURL(url);
    });
    azureAudio.addEventListener("error", () => setAvatarState("idle"));
    await azureAudio.play();
  } catch (e) {
    speakBrowser(text);
  }
}

function speakBrowser(text) {
  if (!synth) {
    setAvatarState("idle");
    return;
  }
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "zh-CN";
  utter.rate = 1.0;
  utter.pitch = 1.05;
  utter.addEventListener("start", () => setAvatarState("speaking"));
  utter.addEventListener("end", () => setAvatarState("idle"));
  utter.addEventListener("error", () => setAvatarState("idle"));
  synth.speak(utter);
}

function stopSpeak() {
  if (synth && synth.speaking) synth.cancel();
  if (azureAudio) {
    azureAudio.pause();
    azureAudio = null;
  }
  if (avatarStage && avatarStage.dataset.state === "speaking") setAvatarState("idle");
}

/* ===================== 历史会话 ===================== */
async function toggleHistory() {
  if (!chatHistoryPanel.classList.contains("hidden")) {
    chatHistoryPanel.classList.add("hidden");
    return;
  }
  chatHistoryPanel.innerHTML = '<div class="history-empty">加载中...</div>';
  chatHistoryPanel.classList.remove("hidden");
  try {
    const res = await fetch("/api/chat/sessions");
    const sessions = await res.json();
    renderHistory(sessions);
  } catch (e) {
    chatHistoryPanel.innerHTML = '<div class="history-empty">加载失败</div>';
  }
}

function renderHistory(sessions) {
  if (!sessions || !sessions.length) {
    chatHistoryPanel.innerHTML =
      '<h4>历史会话</h4><div class="history-empty">暂无历史会话</div>';
    return;
  }
  const items = sessions
    .map(
      (s) => `
      <div class="history-item" data-id="${s.session_id}">
        <div>
          <div class="hi-preview">${escapeHtml(s.preview || "(无内容)")}</div>
          <div class="hi-meta">${s.message_count} 条消息 · ${formatChatTime(s.last_at)}</div>
        </div>
        <button class="hi-del" data-id="${s.session_id}" title="删除">🗑</button>
      </div>`
    )
    .join("");
  chatHistoryPanel.innerHTML = "<h4>历史会话</h4>" + items;
  chatHistoryPanel.querySelectorAll(".history-item").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (e.target.classList.contains("hi-del")) return;
      loadSession(el.dataset.id);
    });
  });
  chatHistoryPanel.querySelectorAll(".hi-del").forEach((b) => {
    b.addEventListener("click", async (e) => {
      e.stopPropagation();
      await fetch(`/api/chat/history/${b.dataset.id}`, { method: "DELETE" });
      if (b.dataset.id === chatSessionId) startNewChat();
      const res = await fetch("/api/chat/sessions");
      renderHistory(await res.json());
      chatHistoryPanel.classList.remove("hidden");
    });
  });
}

async function loadSession(sessionId) {
  stopSpeak();
  try {
    const res = await fetch(`/api/chat/history/${sessionId}`);
    const msgs = await res.json();
    chatMessages.innerHTML = "";
    chatHistory = [];
    chatSessionId = sessionId;
    msgs.forEach((m) => {
      addMessage(m.role, m.content);
      chatHistory.push({ role: m.role, content: m.content });
    });
    chatQuick.innerHTML = "";
    chatHistoryPanel.classList.add("hidden");
    setAvatarState("idle");
  } catch (e) {}
}

function formatChatTime(s) {
  if (!s) return "";
  return String(s).replace("T", " ").slice(0, 16);
}

/* ============================ 金融知识闯关游戏 ============================ */
const QUIZ = {
  playerId: null,
  questions: [],
  index: 0,
  streak: 0,
  answered: false,
  roundCorrect: 0,
  roundCoins: 0,
  inited: false,
};

function quizPlayerId() {
  let id = localStorage.getItem("quizPlayerId");
  if (!id) {
    id = "p" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
    localStorage.setItem("quizPlayerId", id);
  }
  return id;
}

/* ===== 闯关奖励券:学习激励直接转化为风控/贴息权益 ===== */
function getCoupons() {
  try { return JSON.parse(localStorage.getItem("coupons") || '{"risk":0,"subsidy":0,"riskHits":0}'); }
  catch (e) { return { risk: 0, subsidy: 0, riskHits: 0 }; }
}
function awardCoupon(type) {
  const c = getCoupons();
  if (type === "risk") {
    c.riskHits = (c.riskHits || 0) + 1;
    if (c.riskHits % 3 === 0) { c.risk = (c.risk || 0) + 1; localStorage.setItem("coupons", JSON.stringify(c)); return true; }
    localStorage.setItem("coupons", JSON.stringify(c)); return false;
  }
  c.subsidy = (c.subsidy || 0) + 1; localStorage.setItem("coupons", JSON.stringify(c)); return true;
}
function renderCouponWallet() {
  const c = getCoupons();
  return `<div class="coupon-wallet">🎟️ 我的权益券:<b>风控加分券 ×${c.risk || 0}</b> · <b>贴息优先申报券 ×${c.subsidy || 0}</b>
    <small>答对3题得风控加分券,全对一组得贴息优先券,可在匹配/申报时抵用</small></div>`;
}

async function initGame() {
  QUIZ.playerId = quizPlayerId();
  if (!QUIZ.inited) {
    bindGameEvents();
    QUIZ.inited = true;
  }
  await Promise.all([loadGameProgress(), loadGameLevels(), loadGameCourses(), loadLeaderboard()]);
}

function bindGameEvents() {
  document.getElementById("game-start-mixed").addEventListener("click", () => startRound(0));
  document.getElementById("game-next").addEventListener("click", nextQuestion);
  document.getElementById("game-quit").addEventListener("click", quitRound);
  document.getElementById("game-again").addEventListener("click", () => {
    document.getElementById("game-result-card").classList.add("hidden");
    document.getElementById("game-start-card").classList.remove("hidden");
  });
  document.getElementById("game-set-name").addEventListener("click", setQuizNickname);
}

async function loadGameProgress() {
  try {
    const res = await fetch(`/api/quiz/progress/${QUIZ.playerId}`);
    const p = await res.json();
    renderProgress(p);
  } catch (e) {
    /* ignore */
  }
}

function renderProgress(p) {
  document.getElementById("game-emoji").textContent = p.emoji || "🌱";
  document.getElementById("game-title").textContent = p.title || "金融小白";
  document.getElementById("game-level").textContent = p.level || 1;
  document.getElementById("game-coins").textContent = p.coins || 0;
  document.getElementById("game-answered").textContent = p.total_answered || 0;
  document.getElementById("game-correct").textContent = p.total_correct || 0;
  document.getElementById("game-accuracy").textContent = (p.accuracy || 0) + "%";
  document.getElementById("game-streak").textContent = p.best_streak || 0;
  const fill = document.getElementById("game-progress-fill");
  fill.style.width = (p.progress || 0) + "%";
  const txt = document.getElementById("game-progress-text");
  if (p.is_max) {
    txt.textContent = "🎖 已达最高等级,金融大师就是你!";
  } else {
    txt.textContent = `距离「${p.next_title}」还差 ${p.coins_to_next} 金币`;
  }
}

async function loadGameLevels() {
  const wrap = document.getElementById("game-levels");
  try {
    const res = await fetch("/api/quiz/levels");
    const levels = await res.json();
    wrap.innerHTML = levels
      .map(
        (l) => `
      <button class="game-level-card" data-level="${l.level}">
        <span class="glc-emoji">${l.emoji}</span>
        <span class="glc-title">${escapeHtml(l.title)}</span>
        <span class="glc-meta">Lv.${l.level} · ${l.question_count}题</span>
      </button>`
      )
      .join("");
    wrap.querySelectorAll(".game-level-card").forEach((b) => {
      b.addEventListener("click", () => startRound(Number(b.dataset.level)));
    });
  } catch (e) {
    wrap.innerHTML = '<div class="empty">关卡加载失败</div>';
  }
}

async function loadGameCourses() {
  const wrap = document.getElementById("game-courses");
  if (!wrap) return;
  try {
    const res = await fetch("/api/quiz/courses");
    const courses = await res.json();
    wrap.innerHTML = courses
      .map(
        (c) => `
      <button class="game-level-card" data-course="${c.key}">
        <span class="glc-emoji">${c.emoji}</span>
        <span class="glc-title">${escapeHtml(c.title)}</span>
        <span class="glc-meta">${escapeHtml(c.desc)} · ${c.question_count}题</span>
      </button>`
      )
      .join("");
    wrap.querySelectorAll(".game-level-card").forEach((b) => {
      b.addEventListener("click", () => startRound(0, b.dataset.course));
    });
  } catch (e) {
    wrap.innerHTML = '<div class="empty">课程加载失败</div>';
  }
}

async function startRound(level, course) {
  try {
    const cq = course ? `&course=${encodeURIComponent(course)}` : "";
    const res = await fetch(`/api/quiz/questions?level=${level}&count=5${cq}`);
    const qs = await res.json();
    if (!qs.length) return;
    QUIZ.questions = qs;
    QUIZ.index = 0;
    QUIZ.streak = 0;
    QUIZ.roundCorrect = 0;
    QUIZ.roundCoins = 0;
    document.getElementById("game-start-card").classList.add("hidden");
    document.getElementById("game-result-card").classList.add("hidden");
    document.getElementById("game-play-card").classList.remove("hidden");
    renderQuestion();
  } catch (e) {
    /* ignore */
  }
}

function renderQuestion() {
  const q = QUIZ.questions[QUIZ.index];
  QUIZ.answered = false;
  document.getElementById("game-q-progress").textContent = `第 ${QUIZ.index + 1} / ${QUIZ.questions.length} 题`;
  document.getElementById("game-streak-pill").textContent = `🔥 连胜 ${QUIZ.streak}`;
  document.getElementById("game-q-type").textContent = q.type === "truefalse" ? "判断题" : "单选题";
  document.getElementById("game-q-text").textContent = q.question;
  const opts = document.getElementById("game-options");
  opts.innerHTML = q.options
    .map(
      (o, i) =>
        `<button class="game-opt" data-i="${i}"><span class="opt-key">${String.fromCharCode(65 + i)}</span><span>${escapeHtml(o)}</span></button>`
    )
    .join("");
  opts.querySelectorAll(".game-opt").forEach((b) => {
    b.addEventListener("click", () => submitAnswer(Number(b.dataset.i), b));
  });
  const fb = document.getElementById("game-feedback");
  fb.className = "game-feedback hidden";
  fb.innerHTML = "";
  document.getElementById("game-next").classList.add("hidden");
}

async function submitAnswer(choice, btn) {
  if (QUIZ.answered) return;
  QUIZ.answered = true;
  const q = QUIZ.questions[QUIZ.index];
  const opts = document.getElementById("game-options");
  opts.querySelectorAll(".game-opt").forEach((b) => (b.disabled = true));
  try {
    const res = await fetch("/api/quiz/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        player_id: QUIZ.playerId,
        question_id: q.id,
        choice,
        streak: QUIZ.streak,
      }),
    });
    const data = await res.json();
    opts.querySelectorAll(".game-opt").forEach((b) => {
      const i = Number(b.dataset.i);
      if (i === data.correct_index) b.classList.add("correct");
      else if (i === choice) b.classList.add("wrong");
    });
    QUIZ.streak = data.streak;
    const fb = document.getElementById("game-feedback");
    const knowledgeBlock = data.knowledge
      ? `<div class="game-knowledge">${escapeHtml(data.knowledge)}</div>`
      : "";
    if (data.correct) {
      QUIZ.roundCorrect += 1;
      QUIZ.roundCoins += data.coins;
      const bonus = data.streak >= 3 ? ` 🔥连胜${data.streak}!` : "";
      const cp = awardCoupon("risk");
      fb.className = "game-feedback ok";
      fb.innerHTML = `<strong>✅ 答对了!+${data.coins} 🪙${bonus}</strong><p>${escapeHtml(data.explanation)}</p>${cp ? `<div class="coupon-pop">🎟️ 获得「风控加分券」+1</div>` : ""}${knowledgeBlock}`;
    } else {
      fb.className = "game-feedback bad";
      fb.innerHTML = `<strong>❌ 答错了</strong><p>${escapeHtml(data.explanation)}</p>${knowledgeBlock}`;
    }
    renderProgress(data.progress);
    document.getElementById("game-streak-pill").textContent = `🔥 连胜 ${QUIZ.streak}`;
    const nextBtn = document.getElementById("game-next");
    nextBtn.textContent = QUIZ.index + 1 >= QUIZ.questions.length ? "查看结算 →" : "下一题 →";
    nextBtn.classList.remove("hidden");
  } catch (e) {
    QUIZ.answered = false;
    opts.querySelectorAll(".game-opt").forEach((b) => (b.disabled = false));
  }
}

function nextQuestion() {
  QUIZ.index += 1;
  if (QUIZ.index >= QUIZ.questions.length) {
    showRoundResult();
  } else {
    renderQuestion();
  }
}

function showRoundResult() {
  document.getElementById("game-play-card").classList.add("hidden");
  const card = document.getElementById("game-result-card");
  card.classList.remove("hidden");
  const total = QUIZ.questions.length;
  const perfect = QUIZ.roundCorrect === total;
  if (perfect) awardCoupon("subsidy");
  document.getElementById("game-result-title").textContent = perfect
    ? "🏆 全部答对,太棒了!"
    : "🎉 本轮闯关完成!";
  document.getElementById("game-result-body").innerHTML = `
    <div class="game-result-stats">
      <div><span>${QUIZ.roundCorrect}/${total}</span><small>答对</small></div>
      <div><span>+${QUIZ.roundCoins}</span><small>本轮金币 🪙</small></div>
      <div><span>${Math.round((QUIZ.roundCorrect / total) * 100)}%</span><small>正确率</small></div>
    </div>
    ${renderCouponWallet()}`;
  loadLeaderboard();
}

function quitRound() {
  document.getElementById("game-play-card").classList.add("hidden");
  document.getElementById("game-start-card").classList.remove("hidden");
}

async function loadLeaderboard() {
  const wrap = document.getElementById("game-leaderboard");
  try {
    const res = await fetch("/api/quiz/leaderboard?limit=10");
    const board = await res.json();
    if (!board.length) {
      wrap.innerHTML = `<div class="lb-empty">
        <div class="lb-empty-ico">🏆</div>
        <div class="lb-empty-title">排行榜虚位以待</div>
        <div class="lb-empty-sub">还没有上榜玩家,完成一组答题即可登顶第一名!</div>
      </div>`;
      return;
    }
    const medals = { 1: "🥇", 2: "🥈", 3: "🥉" };
    wrap.innerHTML = board
      .map(
        (r) => `
      <div class="lb-row ${r.nickname && QUIZ.playerId ? "" : ""}">
        <span class="lb-rank">${medals[r.rank] || r.rank}</span>
        <span class="lb-name">${r.emoji} ${escapeHtml(r.nickname)}</span>
        <span class="lb-title">${escapeHtml(r.title)}</span>
        <span class="lb-coins">${r.coins} 🪙</span>
      </div>`
      )
      .join("");
  } catch (e) {
    wrap.innerHTML = '<div class="empty">排行榜加载失败</div>';
  }
}

async function setQuizNickname() {
  const name = prompt("给自己起个昵称吧(最多20字):");
  if (!name) return;
  try {
    await fetch("/api/quiz/nickname", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_id: QUIZ.playerId, nickname: name }),
    });
    loadLeaderboard();
  } catch (e) {
    /* ignore */
  }
}
