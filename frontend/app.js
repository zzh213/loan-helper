const form = document.getElementById("loan-form");
const resultEl = document.getElementById("result");
const submitBtn = document.getElementById("submit-btn");

/* ===================== 产品埋点 ===================== */
function _visitorId() {
  let id = localStorage.getItem("vid");
  if (!id) {
    id = "v" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    localStorage.setItem("vid", id);
  }
  return id;
}
function track(name, props) {
  try {
    const body = JSON.stringify({
      sid: _visitorId(),
      name,
      props: props || null,
      page: location.pathname,
    });
    if (navigator.sendBeacon) {
      navigator.sendBeacon("/api/track", new Blob([body], { type: "application/json" }));
    } else {
      fetch("/api/track", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => {});
    }
  } catch (e) { /* 埋点失败不影响业务 */ }
}
// 首次与表单交互时上报一次「开始填表」
let _formStarted = false;
if (form) {
  form.addEventListener("focusin", () => {
    if (!_formStarted) { _formStarted = true; track("form_start"); }
  }, { once: false });
}
// 页面访问
track("page_view");

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

/* ===================== 站内消息中心 ===================== */
const MSG_KEY = "inbox_msgs";
function _loadMsgs() {
  try { return JSON.parse(localStorage.getItem(MSG_KEY) || "[]"); } catch (e) { return []; }
}
function _saveMsgs(list) {
  try { localStorage.setItem(MSG_KEY, JSON.stringify(list.slice(0, 50))); } catch (e) {}
}
function pushMsg(title, body, type = "info") {
  const list = _loadMsgs();
  // 简单去重:同标题同正文 10 分钟内不重复推送
  const now = Date.now();
  if (list.some((m) => m.title === title && m.body === body && now - m.ts < 600000)) return;
  list.unshift({ id: "m" + now.toString(36) + Math.random().toString(36).slice(2, 5), title, body, type, ts: now, read: false });
  _saveMsgs(list);
  renderMsgCenter();
}
function _timeAgo(ts) {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return "刚刚";
  if (s < 3600) return Math.floor(s / 60) + " 分钟前";
  if (s < 86400) return Math.floor(s / 3600) + " 小时前";
  return Math.floor(s / 86400) + " 天前";
}
function renderMsgCenter() {
  const badge = document.getElementById("msg-badge");
  const listEl = document.getElementById("msg-list");
  const list = _loadMsgs();
  const unread = list.filter((m) => !m.read).length;
  if (badge) {
    badge.textContent = unread > 99 ? "99+" : String(unread);
    badge.classList.toggle("hidden", unread === 0);
  }
  if (!listEl) return;
  if (!list.length) {
    listEl.innerHTML = '<div class="msg-empty">暂无消息。完成匹配、保存记录或开启提醒后,节点通知会出现在这里。</div>';
    return;
  }
  const icons = { info: "ℹ️", success: "✅", remind: "🔔", progress: "📶" };
  listEl.innerHTML = list.map((m) => `
    <div class="msg-item ${m.read ? "" : "unread"}" data-id="${m.id}">
      <div class="msg-ico">${icons[m.type] || "ℹ️"}</div>
      <div class="msg-main">
        <div class="msg-title">${escapeHtml(m.title)}</div>
        <div class="msg-body">${escapeHtml(m.body)}</div>
        <div class="msg-time">${_timeAgo(m.ts)}</div>
      </div>
    </div>`).join("");
}
(function initMsgCenter() {
  const bell = document.getElementById("msg-bell");
  const panel = document.getElementById("msg-panel");
  if (!bell || !panel) return;
  bell.addEventListener("click", () => {
    const show = panel.classList.contains("hidden");
    panel.classList.toggle("hidden", !show);
    if (show) { track("msg_center"); renderMsgCenter(); }
  });
  document.getElementById("msg-close")?.addEventListener("click", () => panel.classList.add("hidden"));
  document.getElementById("msg-read-all")?.addEventListener("click", () => {
    const list = _loadMsgs().map((m) => ({ ...m, read: true }));
    _saveMsgs(list); renderMsgCenter();
  });
  document.getElementById("msg-clear")?.addEventListener("click", () => {
    _saveMsgs([]); renderMsgCenter();
  });
  document.getElementById("msg-list")?.addEventListener("click", (e) => {
    const item = e.target.closest(".msg-item");
    if (!item) return;
    const list = _loadMsgs().map((m) => m.id === item.dataset.id ? { ...m, read: true } : m);
    _saveMsgs(list); renderMsgCenter();
  });
  document.addEventListener("click", (e) => {
    if (!panel.contains(e.target) && !bell.contains(e.target)) panel.classList.add("hidden");
  });
  // 首次访问推送欢迎消息
  if (!localStorage.getItem("msg_welcomed")) {
    localStorage.setItem("msg_welcomed", "1");
    pushMsg("👋 欢迎使用小微贷管家", "完成智能匹配后可保存申请记录,状态推进与政策窗口提醒都会在这里通知你。", "info");
  }
  renderMsgCenter();
  fetchRetentionNotices();
})();

// 拉取运营留存推送(LPR 变动 / 政策更新 / 免费诊断活动),按 id 去重进消息中心
async function fetchRetentionNotices() {
  try {
    const res = await fetch("/api/retention-notices");
    if (!res.ok) return;
    const data = await res.json();
    const seen = JSON.parse(localStorage.getItem("retention_seen") || "[]");
    const notices = data.notices || [];
    let changed = false;
    notices.forEach((n) => {
      if (seen.includes(n.id)) return;
      pushMsg(n.title, n.body, n.type === "remind" ? "remind" : "info");
      seen.push(n.id);
      changed = true;
    });
    if (changed) localStorage.setItem("retention_seen", JSON.stringify(seen.slice(-50)));
  } catch (e) {}
}

/* ===================== 账号体系(手机号登录 + 个人中心) ===================== */
const AUTH_KEY = "auth_token";
let _account = null;
function authToken() { return localStorage.getItem(AUTH_KEY) || ""; }
function authHeaders(extra) {
  const h = extra || {};
  const t = authToken();
  if (t) h["X-Auth-Token"] = t;
  return h;
}
function updateAccountBtn() {
  const txt = document.getElementById("account-btn-txt");
  if (!txt) return;
  txt.textContent = _account ? (_account.phone_masked || "个人中心") : "登录 / 注册";
}
async function refreshAccount() {
  if (!authToken()) { _account = null; updateAccountBtn(); return; }
  try {
    const res = await fetch("/api/auth/me", { headers: authHeaders() });
    if (res.ok) { _account = await res.json(); }
    else { localStorage.removeItem(AUTH_KEY); _account = null; }
  } catch (e) { _account = null; }
  updateAccountBtn();
}
function openLoginModal() { document.getElementById("login-modal")?.classList.remove("hidden"); }
function closeLoginModal() { document.getElementById("login-modal")?.classList.add("hidden"); }
function openProfileModal() {
  renderPersonalCenter();
  document.getElementById("profile-modal")?.classList.remove("hidden");
}
function closeProfileModal() { document.getElementById("profile-modal")?.classList.add("hidden"); }

(function initAccount() {
  const accBtn = document.getElementById("account-btn");
  if (!accBtn) return;
  accBtn.addEventListener("click", () => {
    if (_account) openProfileModal(); else openLoginModal();
  });
  document.getElementById("login-close")?.addEventListener("click", closeLoginModal);
  document.getElementById("profile-close")?.addEventListener("click", closeProfileModal);

  const sendBtn = document.getElementById("login-send-otp");
  let _cooldown = 0, _timer = null;
  sendBtn?.addEventListener("click", async () => {
    const phone = (document.getElementById("login-phone").value || "").trim();
    if (!/^1[3-9]\d{9}$/.test(phone)) { showToast("请输入有效的 11 位手机号", "error"); return; }
    try {
      const res = await fetch("/api/auth/request-otp", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone }),
      });
      const data = await res.json();
      if (!data.ok) { showToast(data.error || "获取失败", "error"); return; }
      const tip = document.getElementById("login-demo-tip");
      if (tip) { tip.textContent = `📱 演示验证码:${data.demo_code}(自动填入,5 分钟内有效)`; tip.classList.remove("hidden"); }
      const otpEl = document.getElementById("login-otp");
      if (otpEl) otpEl.value = data.demo_code;
      _cooldown = 60;
      sendBtn.disabled = true;
      _timer = setInterval(() => {
        _cooldown--;
        sendBtn.textContent = _cooldown > 0 ? `${_cooldown}s 后重发` : "获取验证码";
        if (_cooldown <= 0) { clearInterval(_timer); sendBtn.disabled = false; }
      }, 1000);
    } catch (e) { showToast("网络异常,请重试", "error"); }
  });

  document.getElementById("login-submit")?.addEventListener("click", async () => {
    const phone = (document.getElementById("login-phone").value || "").trim();
    const code = (document.getElementById("login-otp").value || "").trim();
    if (!/^1[3-9]\d{9}$/.test(phone)) { showToast("请输入有效的手机号", "error"); return; }
    if (!/^\d{6}$/.test(code)) { showToast("请输入 6 位验证码", "error"); return; }
    try {
      const res = await fetch("/api/auth/verify-otp", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, code }),
      });
      const data = await res.json();
      if (!res.ok) { showToast(data.detail || "登录失败", "error"); return; }
      localStorage.setItem(AUTH_KEY, data.token);
      _account = data.account;
      updateAccountBtn();
      closeLoginModal();
      track("account_login");
      showToast("登录成功", "success");
      pushMsg("👤 登录成功", "企业信息将云端保存,下次匹配可一键回填。", "success");
      if (_account.profile) offerAutofill();
    } catch (e) { showToast("网络异常,请重试", "error"); }
  });

  document.getElementById("logout-btn")?.addEventListener("click", async () => {
    try { await fetch("/api/auth/logout", { method: "POST", headers: authHeaders() }); } catch (e) {}
    localStorage.removeItem(AUTH_KEY);
    _account = null;
    updateAccountBtn();
    closeProfileModal();
    showToast("已退出登录", "info");
  });

  document.getElementById("role-add-btn")?.addEventListener("click", saveRoleFromForm);
  document.getElementById("pc-goto-records")?.addEventListener("click", () => {
    closeProfileModal();
    document.querySelector('.tab-btn[data-tab="records"]')?.click();
  });

  refreshAccount();
})();

function offerAutofill() {
  if (!_account || !_account.profile || !form) return;
  const p = _account.profile;
  const set = (id, v) => { const el = document.getElementById(id); if (el != null && v != null && v !== "") el.value = v; };
  set("f-company", p.company_name);
  set("f-industry", p.industry);
  set("f-years", p.years_in_business);
  set("f-revenue", p.annual_revenue);
  set("f-capital", p.registered_capital);
  set("f-employees", p.employees);
  set("f-credit", p.credit_level);
  set("f-collateral", p.collateral_value);
  set("f-amount", p.loan_amount);
  set("f-purpose", p.loan_purpose);
  set("f-term", p.preferred_term_months);
  const chk = (name, on) => { const el = form.querySelector(`input[name="${name}"]`); if (el) el.checked = !!on; };
  chk("has_collateral", p.has_collateral);
  chk("has_tax_record", p.has_tax_record);
  chk("has_invoice", p.has_invoice);
  chk("has_overdue", p.has_overdue);
  chk("urgent", p.urgent);
  showToast("已回填你上次保存的企业信息", "success");
}

async function saveProfileToCloud(profile) {
  if (!authToken()) return;
  try {
    const res = await fetch("/api/auth/profile", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ profile }),
    });
    if (res.ok) { const d = await res.json(); if (d.account) _account = d.account; }
  } catch (e) {}
}

function renderPersonalCenter() {
  if (!_account) return;
  document.getElementById("pc-phone").textContent = _account.phone_masked || "";
  document.getElementById("pc-since").textContent = _account.created_at ? `注册于 ${_account.created_at.slice(0, 10)}` : "";
  const pf = document.getElementById("pc-profile");
  if (pf) {
    const p = _account.profile;
    if (!p) {
      pf.innerHTML = '<div class="pc-empty">还没有保存企业信息。完成一次智能匹配后会自动云端保存。</div>';
    } else {
      const rows = [
        ["企业名称", p.company_name || "—"],
        ["所属行业", p.industry || "—"],
        ["经营年限", (p.years_in_business ?? "—") + " 年"],
        ["年营业额", (p.annual_revenue ?? "—") + " 万"],
        ["员工人数", (p.employees ?? "—") + " 人"],
        ["拟贷金额", (p.loan_amount ?? "—") + " 万"],
      ];
      pf.innerHTML = `<div class="pc-grid">${rows.map(([k, v]) => `<div class="pc-cell"><small>${k}</small><b>${escapeHtml(String(v))}</b></div>`).join("")}</div>
        <button id="pc-autofill" class="export-btn">↩️ 回填到智能匹配表单</button>`;
      document.getElementById("pc-autofill")?.addEventListener("click", () => {
        closeProfileModal();
        document.querySelector('.tab-btn[data-tab="apply"]')?.click();
        offerAutofill();
      });
    }
  }
  renderRoles();
}

function renderRoles() {
  const box = document.getElementById("pc-roles");
  if (!box) return;
  const roles = (_account && _account.roles) || [];
  if (!roles.length) {
    box.innerHTML = '<div class="pc-empty">尚未添加企业成员。</div>';
    return;
  }
  box.innerHTML = roles.map((r, i) => `
    <div class="pc-role-item">
      <span class="pc-role-tag">${escapeHtml(r.role)}</span>
      <b>${escapeHtml(r.name || "未填写")}</b>
      <span class="pc-role-phone">${escapeHtml(r.phone || "")}</span>
      <button class="pc-role-del" data-idx="${i}" type="button">删除</button>
    </div>`).join("");
  box.querySelectorAll(".pc-role-del").forEach((b) => b.addEventListener("click", async () => {
    const idx = parseInt(b.dataset.idx);
    const roles2 = ((_account && _account.roles) || []).filter((_, i) => i !== idx);
    await saveRoles(roles2);
  }));
}

async function saveRoleFromForm() {
  const name = (document.getElementById("role-name").value || "").trim();
  const role = document.getElementById("role-type").value;
  const phone = (document.getElementById("role-phone").value || "").trim();
  if (!name) { showToast("请填写成员姓名", "error"); return; }
  const roles = ((_account && _account.roles) || []).concat([{ name, role, phone }]);
  await saveRoles(roles);
  document.getElementById("role-name").value = "";
  document.getElementById("role-phone").value = "";
}

async function saveRoles(roles) {
  try {
    const res = await fetch("/api/auth/roles", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ roles }),
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.detail || "保存失败", "error"); return; }
    if (data.account) _account = data.account;
    renderRoles();
    showToast("已更新企业成员", "success");
  } catch (e) { showToast("网络异常,请重试", "error"); }
}



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
  if (submitBtn.classList.contains("btn-loading")) return;
  const consentEl = document.getElementById("consent-enterprise");
  if (consentEl && !consentEl.checked) {
    if (form.__stepper) form.__stepper.gotoEl(consentEl);
    showToast("请先阅读并勾选同意《服务协议》与《隐私政策》", "error");
    consentEl.focus();
    return;
  }
  const profile = collectProfile();

  const errors = validateForm(profile);
  if (errors.length) {
    showToast(`请检查:${errors.join("、")}`, "error");
    const firstInvalid = form.querySelector(".invalid");
    if (firstInvalid) {
      if (form.__stepper) form.__stepper.gotoEl(firstInvalid);
      firstInvalid.focus();
    }
    return;
  }

  setBtnLoading(submitBtn, true, "匹配中…");
  renderSkeleton();
  track("recommend_submit", { industry: profile.industry, amount: profile.loan_amount });

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
    clearDraft();
    track((data.plans && data.plans.length) ? "recommend_success" : "recommend_empty",
      { plans: (data.plans || []).length });
    if (data.plans && data.plans.length) {
      pushMsg("✅ 方案匹配完成", `已为「${(profile.company_name || "你的企业")}」匹配 ${data.plans.length} 套方案,可导出 PDF 或保存为申请记录。`, "success");
    }
    saveProfileToCloud(profile);
    showToast("已为你匹配最优方案", "success");
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    resultEl.innerHTML = `<div class="empty err-empty">😕 匹配遇到问题:${escapeHtml(err.message)}<br><button id="retry-match" class="export-btn">🔄 重试一次</button><br><small style="color:#8a98a8">多次失败?点右下角💬 智能助手或拨打客户经理热线,我们帮你人工匹配。</small></div>`;
    resultEl.classList.remove("hidden");
    const rb = document.getElementById("retry-match");
    if (rb) rb.addEventListener("click", () => form.requestSubmit());
    showToast("匹配失败,请稍后重试", "error");
  } finally {
    setBtnLoading(submitBtn, false);
  }
});

/* ===================== 表单草稿自动保存 ===================== */
const DRAFT_KEY = "loanFormDraft";
function _draftFields() {
  if (!form) return [];
  return Array.from(form.querySelectorAll("input[name], select[name]"));
}
function saveDraft() {
  if (!form) return;
  const data = {};
  _draftFields().forEach((el) => {
    if (el.type === "checkbox") data[el.name] = el.checked;
    else if (el.type === "radio") { if (el.checked) data[el.name] = el.value; }
    else data[el.name] = el.value;
  });
  data.__ts = Date.now();
  try { localStorage.setItem(DRAFT_KEY, JSON.stringify(data)); } catch (e) {}
}
function clearDraft() {
  try { localStorage.removeItem(DRAFT_KEY); } catch (e) {}
  const bar = document.getElementById("draft-restore-bar");
  if (bar) bar.remove();
}
function applyDraft(data) {
  _draftFields().forEach((el) => {
    if (!(el.name in data)) return;
    if (el.type === "checkbox") el.checked = !!data[el.name];
    else if (el.type === "radio") el.checked = el.value === data[el.name];
    else el.value = data[el.name];
    el.dispatchEvent(new Event("change", { bubbles: true }));
  });
}
function initDraft() {
  if (!form) return;
  let raw = null;
  try { raw = localStorage.getItem(DRAFT_KEY); } catch (e) {}
  if (raw) {
    try {
      const data = JSON.parse(raw);
      const mins = Math.max(1, Math.round((Date.now() - (data.__ts || 0)) / 60000));
      const when = mins < 60 ? `${mins} 分钟前` : `${Math.round(mins / 60)} 小时前`;
      const bar = document.createElement("div");
      bar.id = "draft-restore-bar";
      bar.className = "draft-restore-bar";
      bar.innerHTML = `📝 检测到你 ${when} 填写的草稿,是否继续?<span class="dr-btns"><button type="button" id="draft-restore">恢复填写</button><button type="button" id="draft-discard">重新填写</button></span>`;
      form.parentElement.insertBefore(bar, form);
      document.getElementById("draft-restore").addEventListener("click", () => {
        applyDraft(data);
        bar.remove();
        showToast("已恢复上次填写内容", "success");
      });
      document.getElementById("draft-discard").addEventListener("click", async () => {
        const ok = await showConfirm({
          title: "重新填写",
          message: "确定清除已保存的草稿、重新填写吗?此操作不可撤销。",
          okText: "清除并重填",
          danger: true,
        });
        if (ok) { clearDraft(); bar.remove(); }
      });
    } catch (e) {}
  }
  let t = null;
  form.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(saveDraft, 600);
  });
  form.addEventListener("change", saveDraft);
}
initDraft();

/* ===================== 字段说明弹窗(点击问号) ===================== */
(function () {
  function closePop() {
    const p = document.getElementById("hint-pop");
    if (p) p.remove();
    document.removeEventListener("click", onDocClick, true);
  }
  function onDocClick(e) {
    if (!e.target.closest("#hint-pop") && !e.target.classList.contains("hint")) closePop();
  }
  document.addEventListener("click", (e) => {
    const hint = e.target.classList && e.target.classList.contains("hint") ? e.target : null;
    if (!hint) return;
    e.preventDefault();
    e.stopPropagation();
    const text = hint.getAttribute("title") || hint.getAttribute("data-tip");
    if (!text) return;
    closePop();
    const pop = document.createElement("div");
    pop.id = "hint-pop";
    pop.className = "hint-pop";
    pop.innerHTML = `<span class="hint-pop-txt">${escapeHtml(text)}</span><button type="button" class="hint-pop-close" aria-label="关闭">✕</button>`;
    document.body.appendChild(pop);
    const r = hint.getBoundingClientRect();
    const top = r.bottom + window.scrollY + 8;
    let left = r.left + window.scrollX - 10;
    pop.style.top = top + "px";
    pop.style.left = Math.max(10, Math.min(left, window.innerWidth - pop.offsetWidth - 10)) + "px";
    pop.querySelector(".hint-pop-close").addEventListener("click", closePop);
    setTimeout(() => document.addEventListener("click", onDocClick, true), 0);
  });
})();

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
    setBtnLoading(preauditBtn, true, "预审中…");
    track("preaudit");
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
      setBtnLoading(preauditBtn, false);
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
    if (!on) pushMsg("🔔 已开启贴息窗口提醒", "有明确申报窗口期的政策将在消息中心为你标记提示,记得及时申报。", "remind");
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
  track("hidden_subsidy");
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

/* ===== 政策补贴库(可筛选浏览 + 申报指南下载) ===== */
const plProv = document.getElementById("pl-prov");
const plIndustry = document.getElementById("pl-industry");
const plScale = document.getElementById("pl-scale");
const plSearchBtn = document.getElementById("pl-search");
const policyLibList = document.getElementById("policy-lib-list");
function initPolicyLibProv() {
  if (!plProv) return;
  const fill = () => {
    if (!regionTree || !Object.keys(regionTree).length) return;
    Object.keys(regionTree).forEach((p) => plProv.add(new Option(p, p)));
  };
  if (regionTree && Object.keys(regionTree).length) fill();
  else setTimeout(fill, 800);
}
function windowStatus(win) {
  const w = win || "";
  if (/常年|滚动|受理/.test(w)) return { cls: "open", label: "🟢 常年可申报" };
  if (/月|季|年|前|内|期/.test(w)) return { cls: "soon", label: "🟡 有窗口期,注意时间" };
  return { cls: "open", label: "🟢 可申报" };
}
function policyLibCard(p) {
  const remindOn = localStorage.getItem("policyRemind") === "on";
  const ws = windowStatus(p.apply_window);
  const winClass = ws.cls === "soon" && remindOn ? "pl-window remind" : "pl-window";
  return `<div class="policy-lib-item">
    <div class="pl-top"><b>${escapeHtml(p.name)}</b>
      <span class="pl-cat">${escapeHtml(p.category)}</span></div>
    <div class="pl-meta">🏛️ ${escapeHtml(p.authority)} · 适用:${escapeHtml((p.industries || []).join("/"))} · ${escapeHtml((p.scale || []).join("/"))}</div>
    <div class="pl-benefit">💰 ${escapeHtml(p.benefit)}</div>
    <div class="pl-apply">📝 ${escapeHtml(p.apply_points)}</div>
    <div class="${winClass}"><span class="pl-win-status ${ws.cls}">${ws.label}</span>
      <span class="pl-win-txt">🗓️ 申报窗口:${escapeHtml(p.apply_window)}</span></div>
    <div class="pl-actions">
      <a class="pl-guide-btn" href="/api/policy-guide/${encodeURIComponent(p.id)}" download onclick="track('policy_guide')">📥 下载申报指南</a>
    </div>
  </div>`;
}
async function loadPolicyLib() {
  if (!policyLibList) return;
  const params = new URLSearchParams();
  if (plProv && plProv.value) params.set("region", plProv.value);
  if (plIndustry && plIndustry.value) params.set("industry", plIndustry.value);
  if (plScale && plScale.value) params.set("scale", plScale.value);
  policyLibList.innerHTML = '<div class="empty">加载中...</div>';
  track("policy_filter");
  try {
    const items = await (await fetch("/api/policies?" + params.toString())).json();
    if (!items.length) {
      policyLibList.innerHTML = '<div class="empty">未匹配到政策,试试放宽筛选条件。</div>';
      return;
    }
    const remindOn = localStorage.getItem("policyRemind") === "on";
    const soon = items.filter((p) => windowStatus(p.apply_window).cls === "soon").length;
    const tip = remindOn && soon
      ? `<div class="pl-remind-tip">🔔 已开启窗口提醒:${soon} 项政策有明确申报窗口期,请留意时间。</div>`
      : "";
    policyLibList.innerHTML = tip + items.map(policyLibCard).join("");
  } catch (err) {
    policyLibList.innerHTML = `<div class="empty">加载失败:${escapeHtml(err.message)}</div>`;
  }
}
if (plSearchBtn) {
  initPolicyLibProv();
  plSearchBtn.addEventListener("click", loadPolicyLib);
  let _plLoaded = false;
  const tabSubsidyBtn = document.querySelector('.tab-btn[data-tab="subsidy"]');
  if (tabSubsidyBtn) {
    tabSubsidyBtn.addEventListener("click", () => {
      if (!_plLoaded) { _plLoaded = true; loadPolicyLib(); }
    });
  }
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

function planCard(p, i) {
  return `<div class="plan ${i === 0 ? "best" : ""}">
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
    ? `<div class="action-bar">
      <button id="export-pdf-personal" class="export-btn">📄 导出方案 PDF</button>
      <button class="export-btn" onclick="window.print()">🖨️ 打印 / 另存</button>
    </div>`
    : `<div class="action-bar">
      <button id="export-pdf" class="export-btn">📄 导出方案 PDF(自查版)</button>
      <button id="export-checklist" class="export-btn">📋 材料清单</button>
      <button id="save-application" class="export-btn save-btn">💾 保存为申请记录</button>
      <button id="toggle-tools" class="export-btn more-tools-btn" aria-expanded="false">➕ 更多功能</button>
    </div>
    <div id="more-tools" class="more-tools hidden">
      <button id="export-pdf-bank" class="export-btn">📄 银行提交版 PDF(完整信息)</button>
      <button id="export-excel" class="export-btn excel-btn">📊 导出 Excel</button>
      <button id="export-bank" class="export-btn bank-btn">🏦 银行成品材料 PDF</button>
      <button id="export-bank-docx" class="export-btn bank-btn">📝 银行成品材料 Word</button>
      <button id="share-poster" class="export-btn">📱 生成分享海报</button>
      <button id="growth-report" class="export-btn">📈 资质成长报告</button>
      <button id="combo-credit" class="export-btn">➕ 组合贷测算</button>
      <select id="bank-tpl-sel" class="bank-sel" title="选择银行专属申报模板"><option value="">通用模板</option></select>
    </div>`;

  html += `<div class="summary-box">
    <h3>📊 匹配结果</h3>
    <p>${escapeHtml(data.summary)}</p>
    <ul class="highlights">
      ${data.profile_highlights.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}
    </ul>
    ${actionBtns}
  </div>`;

  // 可视化融资分析报告(图表 + 对比卡片 + 前端导出 PDF)
  html += renderVizSection(data);

  // 大白话解读:用通俗语言给看不懂专业术语的用户讲清楚
  if (data.plain_language) {
    const pl = data.plain_language;
    const paras = (pl.paragraphs || []).map((t) => `<p>${escapeHtml(t)}</p>`).join("");
    const steps = (pl.next_steps || []).length
      ? `<div class="pl-steps"><b>👉 接下来您可以这么做:</b><ol>${pl.next_steps
          .map((s) => `<li>${escapeHtml(s)}</li>`)
          .join("")}</ol></div>`
      : "";
    const glossary = (pl.glossary || []).length
      ? `<div class="pl-glossary">
          <button id="toggle-glossary" class="pl-gloss-btn" aria-expanded="false">📖 名词小课堂 · 点我看专业词啥意思</button>
          <div id="pl-glossary-body" class="pl-gloss-body hidden">
            ${pl.glossary
              .map(
                (g) =>
                  `<div class="gloss-item"><span class="gloss-term">${escapeHtml(g.term)}</span><span class="gloss-plain">${escapeHtml(g.plain)}</span></div>`
              )
              .join("")}
          </div>
        </div>`
      : "";
    html += `<div class="plain-box">
      <h3>${escapeHtml(pl.title || "说人话版解读")}</h3>
      <p class="pl-intro">${escapeHtml(pl.intro || "")}</p>
      <div class="pl-body">${paras}</div>
      ${steps}
      ${glossary}
    </div>`;
  }

  // ===== 精简版:先只展示「最优推荐」,其余详情收进「查看更多」 =====
  let moreHtml = "";

  if (data.plans.length) {
    html += planCard(data.plans[0], 0);
  } else {
    html += `<div class="plan"><div class="empty">暂无匹配方案,请参考下方建议提升资质。</div></div>`;
  }

  // ---- 以下为详细内容,默认折叠 ----

  // 风控评估:标准化 8 维评分卡
  if (data.risk) {
    const r = data.risk;
    const dimIcon = { credit: "🧾", revenue: "💰", years: "📅", tax: "🏛️", collateral: "🏠", orders: "📈", debt: "⚖️", industry: "🏭" };
    const scorecard = (r.scorecard && r.scorecard.length) ? r.scorecard : null;
    moreHtml += `<div class="risk-box">
      <div class="risk-head">
        <h3>🛡️ 风控评估 · 8维评分卡</h3>
        <div class="risk-score grade-${r.grade}" title="风控等级 A≥85 / B 70-84 / C 55-69 / D 40-54 / E<40,综合8维度评分">
          <span class="rs-num">${r.score}</span>
          <span class="rs-grade">等级 ${r.grade} · ${escapeHtml(r.grade_label)}</span>
        </div>
      </div>
      ${r.debt_ratio != null ? `<p class="risk-meta">负债杠杆(贷款/年营收):约 ${Math.round(r.debt_ratio * 100)}%${r.bonus_add ? ` · 行业增信 +${r.bonus_add} 分` : ""}</p>` : ""}`;

    if (scorecard) {
      moreHtml += `<div class="scorecard">
        ${scorecard.map((d) => {
          const pct = d.max ? Math.round((d.score / d.max) * 100) : 0;
          return `<div class="sc-dim sc-${d.level}">
            <div class="sc-dim-head">
              <span class="sc-ico">${dimIcon[d.key] || "•"}</span>
              <b class="sc-name">${escapeHtml(d.name)}</b>
              <span class="sc-pts">${d.score}<small>/${d.max}</small></span>
            </div>
            <div class="sc-bar"><div class="sc-bar-fill sc-fill-${d.level}" style="width:${pct}%"></div></div>
            <div class="sc-reason">${escapeHtml(d.reason)}</div>
            ${d.advice ? `<div class="sc-advice">💡 ${escapeHtml(d.advice)}</div>` : ""}
          </div>`;
        }).join("")}
      </div>`;

      if (r.weak_points && r.weak_points.length) {
        moreHtml += `<div class="weak-points">
          <div class="wp-title">🔎 为什么通过率被拉低?(失分最多的 ${r.weak_points.length} 项)</div>
          ${r.weak_points.map((w) => `<div class="wp-item">
            <div class="wp-head"><b>${escapeHtml(w.name)}</b><span class="wp-lost">失分 ${w.lost}</span></div>
            <div class="wp-reason">${escapeHtml(w.reason)}</div>
            <div class="wp-advice">✅ ${escapeHtml(w.advice)}</div>
          </div>`).join("")}
        </div>`;
      }
    } else {
      moreHtml += `<div class="factors">
        ${r.factors.map((f) => `<div class="factor factor-${f.impact}"><b>${escapeHtml(f.name)}</b> ${escapeHtml(f.detail)}</div>`).join("")}
      </div>`;
    }
    moreHtml += `</div>`;
  }

  // 反欺诈 / 异常拦截提示
  if (data.risk_alerts && data.risk_alerts.length) {
    const lvIco = { high: "🚫", mid: "⚠️", info: "ℹ️" };
    const lvLabel = { high: "高风险信号", mid: "存疑待佐证", info: "温馨提示" };
    moreHtml += `<div class="risk-alerts">
      <h3>🛑 合规与反欺诈提示</h3>
      <p class="ra-sub">以下为系统自动识别的数据异常信号,仅作提示,帮助你在进件前修正,避免因资料不实被直接拒件。</p>
      ${data.risk_alerts.map((a) => `<div class="ra-item ra-${a.level}">
        <div class="ra-head">${lvIco[a.level] || "•"} <b>${escapeHtml(a.title)}</b><span class="ra-tag">${lvLabel[a.level] || ""}</span></div>
        <div class="ra-detail">${escapeHtml(a.detail)}</div>
        <div class="ra-suggest">✅ ${escapeHtml(a.suggestion)}</div>
      </div>`).join("")}
    </div>`;
  }

  // 分层匹配策略
  if (data.match_strategy) {
    const ms = data.match_strategy;
    moreHtml += `<div class="match-strategy">
      <h3>🎯 分层匹配策略</h3>
      <div class="ms-seg"><span class="ms-seg-tag">${escapeHtml(ms.segment)}</span><span class="ms-focus">主推:${escapeHtml(ms.focus_label)}</span></div>
      <p class="ms-reason">${escapeHtml(ms.reason)}</p>
      <div class="ms-products">
        ${ms.focus_products.map((p) => `<span class="ms-prod ${p.matched ? "matched" : "locked"}">${p.matched ? "✅" : "🔒"} ${escapeHtml(p.product_name)}</span>`).join("")}
      </div>
      ${ms.tips && ms.tips.length ? `<ul class="ms-tips">${ms.tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>` : ""}
    </div>`;
  }


  // 政府性融资担保增信方案(抵押不足补满额度)
  if (data.guarantee) {
    const g = data.guarantee;
    moreHtml += `<div class="guar-box">
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
    moreHtml += `<div class="tiers-box">
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
    moreHtml += `<div class="compare-box">
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

  // 其余备选方案(第 2 个起)
  if (data.plans.length > 1) {
    moreHtml += `<div class="more-plans-head">📋 其他备选方案(${data.plans.length - 1})</div>`;
    data.plans.slice(1).forEach((p, idx) => {
      moreHtml += planCard(p, idx + 1);
    });
  }

  // 个性化建议
  if (data.personalized_advice && data.personalized_advice.length) {
    moreHtml += `<div class="advice-box">
      <h3>🎯 个性化融资建议</h3>
      <ul>${data.personalized_advice.map((a) => `<li>${escapeHtml(a)}</li>`).join("")}</ul>
    </div>`;
  }

  // 补贴政策
  if (data.subsidies && data.subsidies.length) {
    moreHtml += `<div class="subsidy-box">
      <h3>🏛️ 可申报扶持政策(${data.subsidies.length})</h3>
      ${data.subsidies
        .map(
          (s, si) => `<div class="subsidy">
            <div class="sub-top"><span class="sub-name">${escapeHtml(s.name)}</span>
            <span class="sub-cat">${escapeHtml(s.category)}</span></div>
            <div class="sub-benefit">${escapeHtml(s.benefit)}</div>
            <div class="sub-apply">📌 申请要点:${escapeHtml(s.apply_points)}</div>
            <div class="sub-auth">主管部门:${escapeHtml(s.authority)}</div>
            <div class="sub-meta"><span class="sub-window">🗓️ ${escapeHtml(s.apply_window || "常年可申报")}</span><span class="sub-upd">政策更新于 ${escapeHtml(s.updated || "2026-06")}</span></div>
            <button type="button" class="sub-flow-btn" data-si="${si}" aria-expanded="false">📋 查看申报流程与材料 ▾</button>
            <div class="sub-flow hidden" id="sub-flow-${si}">${subsidyApplyFlow(s)}</div>
          </div>`
        )
        .join("")}
      <p class="sub-flow-note">💡 以上申报流程为通用指引,具体材料与窗口以主管部门最新公告为准;可在「智能助手」中追问某项政策的详细办理方式。</p>
    </div>`;
  }

  if (data.improvement_tips.length) {
    moreHtml += `<div class="tips-box">
      <h3>提升资质 · 获得更优方案</h3>
      <ul>${data.improvement_tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
    </div>`;
  }

  // 折叠详情:一键展开/收起
  if (moreHtml) {
    html += `<div class="more-toggle-wrap">
      <button id="toggle-more" class="more-toggle-btn" aria-expanded="false">
        <span class="mt-txt">查看完整方案详情</span><span class="mt-ico">▾</span>
      </button>
      <p class="more-hint">含风控评估、三套方案对比、补贴政策、提升建议等</p>
    </div>
    <div id="result-more" class="result-more hidden">${moreHtml}</div>`;
  }

  resultEl.innerHTML = html;
  resultEl.classList.remove("hidden");
  renderCommerceCTA(data);
  window.__lastVizData = data;
  drawVizCharts(data);
  const vizPdfBtn = document.getElementById("viz-export-pdf");
  if (vizPdfBtn) vizPdfBtn.addEventListener("click", () => { track("export_viz_pdf"); exportVizPdf(); });
  resultEl.scrollIntoView({ behavior: "smooth", block: "start" });

  const exportBtn = document.getElementById("export-pdf");
  if (exportBtn) exportBtn.addEventListener("click", () => { track("export_pdf"); exportPdf("self"); });

  const exportBankPdfBtn = document.getElementById("export-pdf-bank");
  if (exportBankPdfBtn) exportBankPdfBtn.addEventListener("click", () => { track("export_pdf_bank"); exportPdf("bank"); });

  const excelBtn = document.getElementById("export-excel");
  if (excelBtn) excelBtn.addEventListener("click", () => { track("export_excel"); exportExcel(); });

  const bankBtn = document.getElementById("export-bank");
  if (bankBtn) bankBtn.addEventListener("click", () => { track("export_bank"); exportBankPackage(); });

  const bankDocxBtn = document.getElementById("export-bank-docx");
  if (bankDocxBtn) bankDocxBtn.addEventListener("click", () => { track("export_bank"); exportBankPackageDocx(); });

  const checklistBtn = document.getElementById("export-checklist");
  if (checklistBtn) checklistBtn.addEventListener("click", showChecklist);

  const posterBtn = document.getElementById("share-poster");
  if (posterBtn) posterBtn.addEventListener("click", () => { track("share_poster"); makePoster(data); });

  const growthBtn = document.getElementById("growth-report");
  if (growthBtn) growthBtn.addEventListener("click", () => { track("growth_report"); showGrowthReport(data); });

  const comboBtn = document.getElementById("combo-credit");
  if (comboBtn) comboBtn.addEventListener("click", () => { track("combo_credit"); showCombo(data); });

  const saveBtn = document.getElementById("save-application");
  if (saveBtn) saveBtn.addEventListener("click", saveApplication);

  const pdfPersonalBtn = document.getElementById("export-pdf-personal");
  if (pdfPersonalBtn) pdfPersonalBtn.addEventListener("click", () => { track("export_pdf"); exportPersonalPdf(); });

  loadBankOptions();
  bindFavButtons();
  refreshFavBar();

  const toggleToolsBtn = document.getElementById("toggle-tools");
  if (toggleToolsBtn) {
    toggleToolsBtn.addEventListener("click", () => {
      const tools = document.getElementById("more-tools");
      if (!tools) return;
      const open = tools.classList.toggle("hidden") === false;
      toggleToolsBtn.setAttribute("aria-expanded", open ? "true" : "false");
      toggleToolsBtn.classList.toggle("open", open);
      toggleToolsBtn.textContent = open ? "➖ 收起功能" : "➕ 更多功能";
      if (open) track("more_tools");
    });
  }

  const toggleGlossaryBtn = document.getElementById("toggle-glossary");
  if (toggleGlossaryBtn) {
    toggleGlossaryBtn.addEventListener("click", () => {
      const body = document.getElementById("pl-glossary-body");
      if (!body) return;
      const open = body.classList.toggle("hidden") === false;
      toggleGlossaryBtn.setAttribute("aria-expanded", open ? "true" : "false");
      toggleGlossaryBtn.classList.toggle("open", open);
      if (open) track("view_glossary");
    });
  }

  const toggleMoreBtn = document.getElementById("toggle-more");
  if (toggleMoreBtn) {
    toggleMoreBtn.addEventListener("click", () => {
      const more = document.getElementById("result-more");
      if (!more) return;
      const open = more.classList.toggle("hidden") === false;
      toggleMoreBtn.setAttribute("aria-expanded", open ? "true" : "false");
      toggleMoreBtn.classList.toggle("open", open);
      toggleMoreBtn.querySelector(".mt-txt").textContent = open ? "收起方案详情" : "查看完整方案详情";
      if (open) { track("view_more"); more.scrollIntoView({ behavior: "smooth", block: "nearest" }); }
    });
  }

  document.querySelectorAll(".sub-flow-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panel = document.getElementById("sub-flow-" + btn.dataset.si);
      if (!panel) return;
      const open = panel.classList.toggle("hidden") === false;
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.textContent = open ? "📋 收起申报流程与材料 ▴" : "📋 查看申报流程与材料 ▾";
      if (open) track("subsidy_flow");
    });
  });
}

/* ===================== 可视化融资分析报告 ===================== */
function shortName(s) {
  s = String(s || "");
  return s.length > 6 ? s.slice(0, 6) + "…" : s;
}

// 估算补贴/贴息减免金额(万):有可申报补贴时,按约 2 个百分点贴息折算利息节省
function estSubsidySaving(plan, data) {
  if (!plan || !data || !data.subsidies || !data.subsidies.length) return 0;
  const avg = ((Number(plan.annual_rate_min) || 0) + (Number(plan.annual_rate_max) || 0)) / 2;
  const ti = Number(plan.total_interest_estimate) || 0;
  if (avg <= 0 || ti <= 0) return 0;
  const cut = Math.min(2, avg * 0.4);
  return Math.round(ti * (cut / avg) * 100) / 100;
}

function renderVizSection(data) {
  if (!data.plans || !data.plans.length) return "";
  const isPersonal = window.__lastMode === "personal";
  const name =
    (window.__lastProfile && window.__lastProfile.company_name) ||
    (window.__lastPersonalProfile && window.__lastPersonalProfile.name) ||
    (isPersonal ? "个人客户" : "贵企业");
  const today = new Date().toLocaleDateString("zh-CN");
  const cards = data.plans
    .slice(0, 3)
    .map((p, i) => {
      const tag = p.requires_collateral ? "抵押贷" : "信用贷";
      const label = i === 0 ? "方案A · 首推" : i === 1 ? "方案B" : "方案C";
      return `<div class="viz-card ${i === 0 ? "viz-best" : ""}">
        <div class="vzc-head"><span class="vzc-label">${label}</span><span class="vzc-tag">${tag}</span></div>
        <div class="vzc-name">${escapeHtml(p.product_name)}</div>
        <div class="vzc-metrics">
          <div class="vzc-m"><small>可贷额度</small><b>${p.estimated_amount} 万</b></div>
          <div class="vzc-m"><small>年化利率</small><b>${p.annual_rate_min}%-${p.annual_rate_max}%</b></div>
          <div class="vzc-m"><small>预估月供</small><b>${p.monthly_payment_estimate} 万</b></div>
          <div class="vzc-m"><small>预估总利息</small><b>${p.total_interest_estimate} 万</b></div>
          <div class="vzc-m"><small>通过率</small><b>${escapeHtml(p.approval_probability)}</b></div>
          <div class="vzc-m"><small>建议期限</small><b>${p.suggested_term_months} 月</b></div>
        </div>
      </div>`;
    })
    .join("");
  return `<div id="viz-report" class="viz-report">
    <div class="viz-rep-head">
      <div class="vrh-brand">📊 融资可视化分析报告</div>
      <div class="vrh-meta">对象：${escapeHtml(name)}　|　生成日期：${today}</div>
    </div>
    <div class="viz-charts">
      <div class="viz-chart-box">
        <div class="viz-chart-title">首推方案成本构成</div>
        <canvas id="viz-donut" height="200"></canvas>
        <div class="viz-legend" id="viz-donut-legend"></div>
      </div>
      <div class="viz-chart-box">
        <div class="viz-chart-title">各方案总利息对比（万）</div>
        <canvas id="viz-bar-interest" height="200"></canvas>
      </div>
      <div class="viz-chart-box">
        <div class="viz-chart-title">各方案月供对比（万）</div>
        <canvas id="viz-bar-monthly" height="200"></canvas>
      </div>
    </div>
    <div class="viz-cards-title">🧾 多方案横向对比</div>
    <div class="viz-cards">${cards}</div>
    <div class="viz-rep-foot">本报告基于您填写的信息与本地银行产品测算生成，利率、额度、补贴金额均为估算值，以持牌金融机构及主管部门最终审批为准，仅供参考。本平台为融资信息匹配服务，不直接放贷。</div>
  </div>
  <div class="viz-actions">
    <button id="viz-export-pdf" class="export-btn viz-pdf-btn">📄 一键导出可视化报告 PDF</button>
    <span class="viz-pdf-note">纯前端生成，不上传服务器，敏感信息不留存</span>
  </div>`;
}

function drawVizCharts(data) {
  if (!data || !data.plans || !data.plans.length) return;
  const dark = document.body.classList.contains("dark");
  const best = data.plans[0];
  const principal = Number(best.estimated_amount) || 0;
  const interest = Number(best.total_interest_estimate) || 0;
  const save = estSubsidySaving(best, data);
  const netInterest = Math.max(0, interest - save);
  const segs = [
    { label: "本金", value: principal, color: "#4a7fd6" },
    { label: "净利息", value: netInterest, color: "#e0794b" },
  ];
  if (save > 0) segs.push({ label: "补贴减免", value: save, color: "#f6b73c" });
  drawDonut(document.getElementById("viz-donut"), segs, "viz-donut-legend", dark);
  const plans = data.plans.slice(0, 4);
  drawBars(
    document.getElementById("viz-bar-interest"),
    plans.map((p, i) => ({
      label: shortName(p.product_name),
      value: Number(p.total_interest_estimate) || 0,
      color: i === 0 ? "#e0794b" : "#eab08f",
    })),
    dark
  );
  drawBars(
    document.getElementById("viz-bar-monthly"),
    plans.map((p, i) => ({
      label: shortName(p.product_name),
      value: Number(p.monthly_payment_estimate) || 0,
      color: i === 0 ? "#4a7fd6" : "#9db8dd",
    })),
    dark
  );
}

function drawDonut(cv, segs, legendId, dark) {
  if (!cv) return;
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || cv.parentElement.clientWidth || 280;
  const H = 200;
  cv.width = W * dpr;
  cv.height = H * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, W, H);
  const total = segs.reduce((s, x) => s + Math.max(0, x.value), 0) || 1;
  const cx = W / 2,
    cy = H / 2,
    R = Math.min(W, H) / 2 - 8,
    r = R * 0.58;
  let a = -Math.PI / 2;
  segs.forEach((s) => {
    const ang = (Math.max(0, s.value) / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, R, a, a + ang);
    ctx.closePath();
    ctx.fillStyle = s.color;
    ctx.fill();
    a += ang;
  });
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = dark ? "#111a2b" : "#fff";
  ctx.fill();
  ctx.textAlign = "center";
  ctx.fillStyle = dark ? "#e5edf7" : "#2b3648";
  ctx.font = "bold 15px sans-serif";
  ctx.fillText(total.toFixed(1), cx, cy - 1);
  ctx.font = "11px sans-serif";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText("合计(万)", cx, cy + 15);
  const lg = legendId && document.getElementById(legendId);
  if (lg) {
    lg.innerHTML = segs
      .map(
        (s) =>
          `<span class="vz-lg"><i style="background:${s.color}"></i>${s.label} ${s.value.toFixed(1)}万 (${Math.round(
            (s.value / total) * 100
          )}%)</span>`
      )
      .join("");
  }
}

function _roundRect(ctx, x, y, w, h, r) {
  if (h < 1) h = 1;
  r = Math.min(r, w / 2, h);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function drawBars(cv, items, dark) {
  if (!cv || !items.length) return;
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || cv.parentElement.clientWidth || 280;
  const H = 200;
  cv.width = W * dpr;
  cv.height = H * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, W, H);
  const pad = { l: 10, r: 10, t: 22, b: 32 };
  const cw = W - pad.l - pad.r,
    ch = H - pad.t - pad.b;
  const max = Math.max(...items.map((i) => i.value), 0.01);
  const n = items.length;
  const gap = cw / n;
  const bw = Math.min(46, gap * 0.56);
  ctx.strokeStyle = dark ? "#2a3a55" : "#eef1f5";
  ctx.lineWidth = 1;
  for (let g = 0; g <= 3; g++) {
    const gy = pad.t + (ch * g) / 3;
    ctx.beginPath();
    ctx.moveTo(pad.l, gy);
    ctx.lineTo(W - pad.r, gy);
    ctx.stroke();
  }
  items.forEach((it, i) => {
    const x = pad.l + gap * i + gap / 2;
    const bh = ch * (it.value / max);
    const y = pad.t + ch - bh;
    ctx.fillStyle = it.color;
    _roundRect(ctx, x - bw / 2, y, bw, bh, 5);
    ctx.fill();
    ctx.fillStyle = dark ? "#e5edf7" : "#2b3648";
    ctx.font = "bold 11px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(it.value.toFixed(1), x, y - 5);
    ctx.fillStyle = dark ? "#9db3cf" : "#7a8aa0";
    ctx.font = "11px sans-serif";
    ctx.fillText(it.label, x, H - 11);
  });
}

function _loadScriptOnce(src) {
  return new Promise((resolve, reject) => {
    if (Array.prototype.some.call(document.scripts, (s) => s.src === src)) return resolve();
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("加载失败:" + src));
    document.head.appendChild(s);
  });
}

// 纯前端导出可视化报告 PDF:按需懒加载 html2canvas + jsPDF,失败则回退浏览器打印
async function exportVizPdf() {
  const btn = document.getElementById("viz-export-pdf");
  const target = document.getElementById("viz-report");
  if (!target) return;
  if (btn && btn.classList.contains("btn-loading")) return;
  if (typeof setBtnLoading === "function") setBtnLoading(btn, true, "生成中…");
  try {
    if (!window.html2canvas) await _loadScriptOnce("/static/html2canvas.min.js");
    if (!(window.jspdf && window.jspdf.jsPDF)) await _loadScriptOnce("/static/jspdf.umd.min.js");
    const bg = document.body.classList.contains("dark") ? "#0e1626" : "#ffffff";
    const canvas = await window.html2canvas(target, { scale: 2, backgroundColor: bg, useCORS: true });
    const JsPDF = (window.jspdf && window.jspdf.jsPDF) || window.jsPDF;
    const pdf = new JsPDF("p", "mm", "a4");
    const pw = pdf.internal.pageSize.getWidth();
    const ph = pdf.internal.pageSize.getHeight();
    const imgW = pw;
    const imgH = (canvas.height * pw) / canvas.width;
    const img = canvas.toDataURL("image/png");
    let heightLeft = imgH;
    let position = 0;
    pdf.addImage(img, "PNG", 0, position, imgW, imgH);
    heightLeft -= ph;
    while (heightLeft > 0) {
      position = heightLeft - imgH;
      pdf.addPage();
      pdf.addImage(img, "PNG", 0, position, imgW, imgH);
      heightLeft -= ph;
    }
    const who =
      (window.__lastProfile && window.__lastProfile.company_name) ||
      (window.__lastPersonalProfile && window.__lastPersonalProfile.name) ||
      "融资分析";
    pdf.save(who + "_可视化融资分析报告.pdf");
    if (typeof showToast === "function") showToast("报告已导出", "success");
  } catch (err) {
    if (typeof showToast === "function") showToast("在线导出组件加载失败,已改用打印/另存为 PDF", "error");
    window.print();
  } finally {
    if (typeof setBtnLoading === "function") setBtnLoading(btn, false);
  }
}

let _vizResizeTimer = null;
window.addEventListener("resize", () => {
  if (!window.__lastVizData) return;
  clearTimeout(_vizResizeTimer);
  _vizResizeTimer = setTimeout(() => {
    if (document.getElementById("viz-donut")) drawVizCharts(window.__lastVizData);
  }, 200);
});

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
    track("save_application");
    pushMsg("💾 申请记录已保存", "系统将模拟推进审核状态(提交→审核中→通过/放款),可在「申请记录」中查看进度。", "progress");
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

async function exportPdf(edition) {
  const isBank = edition === "bank";
  const ep = isBank ? "/api/export/pdf?edition=bank" : "/api/export/pdf?edition=self";
  const btnId = isBank ? "export-pdf-bank" : "export-pdf";
  const suffix = isBank ? "_贷款方案_银行提交版" : "_贷款方案_自查版";
  await exportReport(ep, "pdf", document.getElementById(btnId), suffix);
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

/* 补贴政策:按类别生成申报流程与材料清单(通用指引) */
function subsidyApplyFlow(s) {
  const cat = s.category || "";
  const baseMaterials = ["营业执照副本(统一社会信用代码清晰)", "法人身份证正反面", "对公银行账户信息"];
  const catExtra = {
    "财政贴息": ["银行贷款合同 / 放款凭证", "近期还款与结息回单", "贴息申请表(主管部门模板)"],
    "创业就业": ["社保参保缴费证明", "带动就业花名册 / 劳动合同", "创业担保贷款相关材料(如有)"],
    "科技创新": ["高新技术企业证书 / 研发立项材料", "研发费用辅助账或专项审计报告", "知识产权证书(专利/软著)"],
    "产业升级": ["设备采购合同与发票", "技改 / 数字化项目方案", "项目投资明细与验收材料"],
    "财税优惠": ["近一年纳税申报表", "财务报表(资产负债 / 利润表)", "税务信用等级证明"],
    "乡村振兴": ["经营场所 / 基地相关证明", "带动农户 / 合作社协议", "项目产出与销售凭证"],
  };
  const materials = baseMaterials.concat(catExtra[cat] || ["与政策要求对应的经营 / 项目佐证材料"]);
  const steps = [
    { t: "资格自查", d: "对照政策条件确认是否符合(行业、规模、注册地、时间窗口等)。" },
    { t: "备齐材料", d: "按下方清单准备并扫描存档,确保信息清晰、口径一致。" },
    { t: "线上/线下申报", d: `向【${escapeHtml(s.authority || "主管部门")}】指定渠道提交申请与材料。` },
    { t: "审核与拨付", d: "等待受理审核,通过后按政策发放补贴 / 贴息或享受减免。" },
  ];
  return `
    <ol class="sf-steps">
      ${steps.map((x, i) => `<li><span class="sf-no">${i + 1}</span><div><b>${x.t}</b><small>${x.d}</small></div></li>`).join("")}
    </ol>
    <div class="sf-mat">
      <div class="sf-mat-title">📎 建议准备材料</div>
      <ul>${materials.map((m) => `<li>${escapeHtml(m)}</li>`).join("")}</ul>
    </div>`;
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
    const activeForm = personal ? perForm : form;
    if (activeForm && activeForm.__stepper) activeForm.__stepper.reset();
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
    const f = (name) => perForm.querySelector(`[name="${name}"]`);
    perForm.querySelectorAll(".invalid").forEach((el) => clearFieldError(el));
    if (!(p.monthly_income > 0)) { setFieldError(f("monthly_income"), "税后月收入需大于 0"); errs.push("月收入"); }
    if (!(p.loan_amount > 0)) { setFieldError(f("loan_amount"), "期望贷款金额需大于 0"); errs.push("贷款金额"); }
    if (!(p.preferred_term_months >= 1)) { setFieldError(f("preferred_term_months"), "期望期限需大于 0"); errs.push("贷款期限"); }
    return errs;
  }

  const perBtn = document.getElementById("personal-submit-btn");
  perForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (perBtn.classList.contains("btn-loading")) return;
    const consentEl = document.getElementById("consent-personal");
    if (consentEl && !consentEl.checked) {
      if (perForm.__stepper) perForm.__stepper.gotoEl(consentEl);
      showToast("请先阅读并勾选同意《服务协议》与《隐私政策》", "error");
      consentEl.focus();
      return;
    }
    const profile = collectPersonalProfile();
    const errors = validatePersonal(profile);
    if (errors.length) {
      showToast(`请检查:${errors.join("、")}`, "error");
      const fi = perForm.querySelector(".invalid");
      if (fi) { if (perForm.__stepper) perForm.__stepper.gotoEl(fi); fi.focus(); }
      return;
    }
    setBtnLoading(perBtn, true, "匹配中…");
    renderSkeleton();
    track("personal_submit", { amount: profile.loan_amount });
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
      track((data.plans && data.plans.length) ? "personal_success" : "recommend_empty",
        { plans: (data.plans || []).length });
      showToast("已为你匹配最优方案", "success");
      resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      resultEl.innerHTML = `<div class="empty err-empty">😕 匹配遇到问题:${escapeHtml(err.message)}<br><button id="retry-personal" class="export-btn">🔄 重试一次</button></div>`;
      resultEl.classList.remove("hidden");
      const rb = document.getElementById("retry-personal");
      if (rb) rb.addEventListener("click", () => perForm.requestSubmit());
      showToast("匹配失败,请稍后重试", "error");
    } finally {
      setBtnLoading(perBtn, false);
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
  document.getElementById("tab-content").classList.toggle("hidden", tab !== "content");
  if (tab === "records") { loadRecords(); startRecPolling(); } else { stopRecPolling(); }
  if (tab === "game") initGame();
  if (tab === "content") initContent();
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
  if (typeof drawVizCharts === "function" && window.__lastVizData) drawVizCharts(window.__lastVizData);
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
function fetchBookings() {
  // 仅展示本浏览器本地记录的预约,不再拉取全部线索(避免暴露他人手机号)
  try { return JSON.parse(localStorage.getItem("my_bookings") || "[]"); } catch (e) { return []; }
}
function saveBooking(b) {
  const list = fetchBookings();
  list.unshift({ ...b, created_at: new Date().toISOString().slice(0, 16).replace("T", " "), status: "待回访" });
  localStorage.setItem("my_bookings", JSON.stringify(list.slice(0, 20)));
}
function openManagerBooking() {
  const today = new Date().toISOString().slice(0, 10);
  const list = fetchBookings();
  const rows = list.length ? list.map((b) => `<li>📅 ${escapeHtml((b.created_at||"").slice(5))} · ${escapeHtml(b.bank)} · ${escapeHtml(b.slot)} · ${escapeHtml(b.phone)} <span class="bk-st">${escapeHtml(b.status)}</span></li>`).join("") : '<li class="empty">暂无预约</li>';
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
      const bank = document.getElementById("bk-bank").value;
      const slot = document.getElementById("bk-slot").value;
      const amt = parseFloat(document.getElementById("bk-amt").value) || 0;
      await fetch("/api/leads", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: "预约", company_name: p.company_name || "", phone, industry: p.industry || "",
          loan_amount: amt, bank, slot }) });
      saveBooking({ phone, bank, slot, loan_amount: amt });
      track("lead_submit", { bank });
      showToast("预约成功,客户经理将在1个工作日内回访", "success");
      openManagerBooking();
    } catch (e) { showToast("提交失败,请稍后重试", "error"); btn.disabled = false; btn.textContent = "确认预约"; }
  });
}
const _cm = document.getElementById("chain-manager");
if (_cm) _cm.addEventListener("click", openManagerBooking);

/* ===== 商业化 & 私域转化 CTA(测算完成后) ===== */
let _PRICING = null;
async function fetchPricing() {
  if (_PRICING) return _PRICING;
  try {
    const r = await fetch("/api/pricing");
    _PRICING = await r.json();
  } catch (e) { _PRICING = null; }
  return _PRICING;
}

function buildAutoTags(data) {
  const p = window.__lastProfile || {};
  const tags = [];
  if (p.industry) tags.push(p.industry);
  const amt = p.loan_amount || 0;
  if (amt >= 150) tags.push("大额抵押客户");
  else if (amt) tags.push("短期周转客户");
  if (data && ((data.subsidies && data.subsidies.length) || p.wants_subsidy)) tags.push("想申请贴息");
  if (p.urgency === "urgent" || p.urgency === "紧急") tags.push("急需资金");
  const score = data && data.risk ? data.risk.score : null;
  if (score != null && score < 55) tags.push("待增信客户");
  return tags;
}

function getReferralCode() {
  let code = localStorage.getItem("referral_code");
  if (!code) {
    code = "LH" + Math.random().toString(36).slice(2, 8).toUpperCase();
    localStorage.setItem("referral_code", code);
  }
  return code;
}

async function renderCommerceCTA(data) {
  const el = document.getElementById("commerce-cta");
  if (!el) return;
  const pricing = await fetchPricing();
  const tags = buildAutoTags(data);
  const code = getReferralCode();
  const refLink = location.origin + "/?ref=" + code;

  const pkgHtml = pricing && pricing.packages ? pricing.packages.map((pk) => `
    <div class="pkg-card ${pk.highlight ? "pkg-hot" : ""}">
      ${pk.highlight ? '<span class="pkg-badge">推荐</span>' : ""}
      <div class="pkg-name">${escapeHtml(pk.name)}</div>
      <div class="pkg-price">${escapeHtml(pk.price)}<small>${escapeHtml(pk.price_note || "")}</small></div>
      <ul class="pkg-feats">${pk.features.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>
      <button class="pkg-cta ${pk.id === "free" ? "pkg-cta-ghost" : ""}" data-tier="${escapeHtml(pk.tier)}" data-pkg="${escapeHtml(pk.name)}">${escapeHtml(pk.cta)}</button>
    </div>`).join("") : "";

  const modelNote = pricing && pricing.business_model ? `
    <p class="commerce-model">💡 <b>${escapeHtml(pricing.business_model.primary)}</b>:${escapeHtml(pricing.business_model.desc)}</p>` : "";

  el.innerHTML = `
    <div class="commerce-box">
      <h2 class="commerce-h">🚀 让方案落地:选择适合你的服务</h2>
      ${modelNote}
      <div class="pkg-grid">${pkgHtml}</div>
    </div>
    <div class="private-box">
      <div class="pv-left">
        <h3>📲 加专属融资顾问,1 对 1 跟进</h3>
        <p class="pv-sub">添加企业微信,顾问将根据你的情况持续推送最优方案与政策提醒。</p>
        ${tags.length ? `<div class="pv-tags">已为你打标签:${tags.map((t) => `<span class="pv-tag">${escapeHtml(t)}</span>`).join("")}</div>` : ""}
        <button id="pv-wecom-btn" class="pv-wecom">➕ 添加企业微信</button>
      </div>
      <div class="pv-right">
        <div class="pv-qr" id="pv-qr">扫码添加<br>企业微信</div>
      </div>
    </div>
    <div class="referral-box">
      <h3>🎁 推荐同行,双方各得一份免费深度报告</h3>
      <p class="ref-sub">把你的专属邀请链接发给同行企业,对方完成测算后,你们都将获赠一次免费深度诊断。</p>
      <div class="ref-row">
        <input id="ref-link" class="ref-input" readonly value="${escapeHtml(refLink)}">
        <button id="ref-copy" class="ref-copy">复制邀请链接</button>
      </div>
      <div class="ref-code">你的邀请码:<b>${escapeHtml(code)}</b></div>
    </div>`;
  el.classList.remove("hidden");
  track("pricing_view");

  el.querySelectorAll(".pkg-cta").forEach((b) => b.addEventListener("click", () => {
    const tier = b.dataset.tier;
    if (!tier) { // 免费版:滚动到表单
      document.getElementById("loan-form")?.scrollIntoView({ behavior: "smooth" });
      return;
    }
    openUpgradeModal(b.dataset.pkg, tier, tags);
  }));

  const wecomBtn = document.getElementById("pv-wecom-btn");
  if (wecomBtn) wecomBtn.addEventListener("click", () => {
    track("wecom_add");
    document.getElementById("pv-qr")?.classList.add("pv-qr-active");
    showToast("请用微信扫描右侧二维码添加顾问", "info");
  });

  const refCopy = document.getElementById("ref-copy");
  if (refCopy) refCopy.addEventListener("click", () => {
    const inp = document.getElementById("ref-link");
    inp.select();
    try { navigator.clipboard.writeText(inp.value); } catch (e) { document.execCommand("copy"); }
    track("referral_copy");
    showToast("邀请链接已复制,发给同行即可", "success");
  });
}

function openUpgradeModal(pkgName, tier, tags) {
  const p = window.__lastProfile || {};
  document.getElementById("modal-content").innerHTML = `<h2>升级「${escapeHtml(pkgName)}」</h2>
    <p class="modal-sub">留下联系方式,专属顾问将在 1 个工作日内联系你,确认服务细节。平台不收取任何前置费用。</p>
    <div class="bk-grid">
      <label>联系电话<input type="tel" id="up-phone" placeholder="手机号" maxlength="11"></label>
      <label>融资需求(万)<input type="number" id="up-amt" value="${p.loan_amount || 100}"></label>
    </div>
    <button id="up-submit" class="export-btn save-btn">提交升级意向</button>`;
  document.getElementById("detail-modal").classList.remove("hidden");
  document.getElementById("up-submit").addEventListener("click", async () => {
    const phone = document.getElementById("up-phone").value.trim();
    if (!/^1\d{10}$/.test(phone)) return showToast("请填写正确的11位手机号", "error");
    const btn = document.getElementById("up-submit");
    btn.disabled = true; btn.textContent = "提交中...";
    try {
      const amt = parseFloat(document.getElementById("up-amt").value) || 0;
      await fetch("/api/leads", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: "增值意向", company_name: p.company_name || "", phone, industry: p.industry || "",
          loan_amount: amt, service_tier: tier, tags, note: "升级:" + pkgName }) });
      track("upgrade_intent", { tier });
      showToast("已收到,顾问将尽快联系你", "success");
      closeModal();
    } catch (e) { showToast("提交失败,请稍后重试", "error"); btn.disabled = false; btn.textContent = "提交升级意向"; }
  });
}

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
  if (!chatInited) track("chat_open");
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
  track("chat_send");

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

// ===== 融资资讯专栏 =====
let _contentState = { inited: false, cat: "", articles: [] };
async function initContent() {
  if (_contentState.inited) return;
  _contentState.inited = true;
  await loadArticles("");
}
async function loadArticles(cat) {
  const listEl = document.getElementById("content-list");
  listEl.innerHTML = '<div class="empty">加载中…</div>';
  try {
    const url = "/api/articles" + (cat ? "?category=" + encodeURIComponent(cat) : "");
    const res = await fetch(url);
    const data = await res.json();
    _contentState.articles = data.articles || [];
    _contentState.cat = cat;
    renderContentCats(data.categories || []);
    renderArticleList(_contentState.articles);
  } catch (e) {
    listEl.innerHTML = '<div class="empty">加载失败,请稍后重试。</div>';
  }
}
function renderContentCats(cats) {
  const el = document.getElementById("content-cats");
  const all = [""].concat(cats);
  el.innerHTML = all.map((c) => {
    const label = c || "全部";
    const active = c === _contentState.cat ? " active" : "";
    return `<button class="content-cat${active}" data-cat="${escapeHtml(c)}">${escapeHtml(label)}</button>`;
  }).join("");
  el.querySelectorAll(".content-cat").forEach((b) => {
    b.addEventListener("click", () => loadArticles(b.dataset.cat));
  });
}
function renderArticleList(articles) {
  const el = document.getElementById("content-list");
  if (!articles.length) { el.innerHTML = '<div class="empty">暂无文章。</div>'; return; }
  el.innerHTML = articles.map((a) => `
    <div class="article-card" data-id="${escapeHtml(a.id)}">
      <div class="article-cat">${escapeHtml(a.category || "")}</div>
      <h3>${escapeHtml(a.title || "")}</h3>
      <p>${escapeHtml(a.summary || "")}</p>
      <div class="article-meta"><span>${escapeHtml(a.updated || "")}${a.read_min ? " · 约 " + a.read_min + " 分钟" : ""}</span><span class="article-more">阅读全文 →</span></div>
    </div>`).join("");
  el.querySelectorAll(".article-card").forEach((c) => {
    c.addEventListener("click", () => openArticle(c.dataset.id));
  });
}
async function openArticle(id) {
  try {
    const res = await fetch("/api/articles/" + encodeURIComponent(id));
    if (!res.ok) { pushMsg("文章不可用", "该文章已下架。", "warn"); return; }
    const a = await res.json();
    track("article_read", { id: id });
    const body = (a.body || []).map((seg) => {
      const h = seg.h ? `<h4>${escapeHtml(seg.h)}</h4>` : "";
      const p = seg.p ? `<p>${escapeHtml(seg.p)}</p>` : "";
      return h + p;
    }).join("");
    document.getElementById("modal-content").innerHTML =
      `<div class="article-read">
        <div class="article-cat">${escapeHtml(a.category || "")}</div>
        <h2>${escapeHtml(a.title || "")}</h2>
        <div class="article-read-meta">${escapeHtml(a.updated || "")}${a.read_min ? " · 约 " + a.read_min + " 分钟阅读" : ""}</div>
        ${body}
        <div class="article-read-tip">📌 本文仅为融资科普,不构成放贷或投资建议。具体以持牌机构审批为准。</div>
      </div>`;
    document.getElementById("detail-modal").classList.remove("hidden");
  } catch (e) {
    pushMsg("加载失败", "文章加载失败,请稍后重试。", "warn");
  }
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

/* ============================================================
   商用交互标准化:分步表单 / 实时校验 / 加载态 / 确认弹窗
   ============================================================ */

// —— 按钮加载态(spinner + 置灰防重复点击)——
function setBtnLoading(btn, loading, loadingText) {
  if (!btn) return;
  if (loading) {
    if (!btn.dataset._html) btn.dataset._html = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add("btn-loading");
    btn.innerHTML = `<span class="btn-spinner" aria-hidden="true"></span>${loadingText || "处理中…"}`;
  } else {
    btn.disabled = false;
    btn.classList.remove("btn-loading");
    if (btn.dataset._html !== undefined) { btn.innerHTML = btn.dataset._html; delete btn.dataset._html; }
  }
}

// —— 确认弹窗组件(替代原生 confirm,返回 Promise<boolean>)——
function showConfirm(opts) {
  opts = opts || {};
  const title = opts.title || "确认操作";
  const message = opts.message || "";
  const okText = opts.okText || "确定";
  const cancelText = opts.cancelText || "取消";
  const danger = !!opts.danger;
  return new Promise((resolve) => {
    const ov = document.createElement("div");
    ov.className = "confirm-overlay";
    ov.innerHTML =
      `<div class="confirm-box" role="dialog" aria-modal="true">
        <div class="confirm-title">${escapeHtml(title)}</div>
        <div class="confirm-msg">${escapeHtml(message)}</div>
        <div class="confirm-btns">
          <button type="button" class="confirm-cancel ghost-btn">${escapeHtml(cancelText)}</button>
          <button type="button" class="confirm-ok${danger ? " danger" : ""}">${escapeHtml(okText)}</button>
        </div>
      </div>`;
    document.body.appendChild(ov);
    const done = (v) => { ov.remove(); document.removeEventListener("keydown", onKey); resolve(v); };
    function onKey(e) { if (e.key === "Escape") done(false); }
    ov.querySelector(".confirm-cancel").addEventListener("click", () => done(false));
    ov.querySelector(".confirm-ok").addEventListener("click", () => done(true));
    ov.addEventListener("click", (e) => { if (e.target === ov) done(false); });
    document.addEventListener("keydown", onKey);
    requestAnimationFrame(() => ov.classList.add("show"));
    setTimeout(() => ov.querySelector(".confirm-ok").focus(), 0);
  });
}

// —— 单字段规则校验,返回错误文案('' 表示通过)——
function validateField(el) {
  if (!el || el.disabled) return "";
  const type = (el.type || "").toLowerCase();
  const v = (el.value || "").trim();
  const isPhone = type === "tel" || el.dataset.validate === "phone";
  if (isPhone) {
    if (v === "") return el.required ? "请输入手机号" : "";
    if (!/^1[3-9]\d{9}$/.test(v)) return "请输入正确的 11 位手机号";
    return "";
  }
  if (type === "number") {
    if (v === "") return el.required ? "此项为必填" : "";
    const n = Number(v);
    if (Number.isNaN(n)) return "请输入数字";
    if (n < 0) return "不能为负数";
    const min = el.getAttribute("min");
    if (min !== null && min !== "" && n < Number(min)) return `不能小于 ${min}`;
    const max = el.getAttribute("max");
    if (max !== null && max !== "" && n > Number(max)) return `不能大于 ${max}`;
    return "";
  }
  if (el.required && v === "") return "此项为必填";
  return "";
}

// —— 为容器内的数字/手机号输入绑定实时校验(失焦标红、输入即清错)——
function attachLiveValidation(scope) {
  if (!scope) return;
  const sel = 'input[type="number"], input[type="tel"], input[data-validate]';
  scope.querySelectorAll(sel).forEach((el) => {
    if (el.dataset._live) return;
    el.dataset._live = "1";
    el.addEventListener("blur", () => {
      const err = validateField(el);
      if (err) setFieldError(el, err); else clearFieldError(el);
    });
    el.addEventListener("input", () => {
      if (el.classList.contains("invalid") && !validateField(el)) clearFieldError(el);
    });
  });
}

// —— 通用分步表单器 ——
function _stepWrap(id) {
  const e = document.getElementById(id);
  if (!e) return null;
  return e.closest(".field") || e;
}

function buildStepper(form, groups, titles) {
  if (!form || form.__stepper) return;
  groups.forEach((els, i) => els.forEach((el) => { if (el) el.dataset.step = String(i); }));
  const total = groups.length;

  const prog = document.createElement("div");
  prog.className = "form-progress";
  prog.innerHTML =
    `<div class="fp-track"><div class="fp-fill"></div></div>
     <div class="fp-steps">${titles.map((t, i) =>
       `<span class="fp-step" data-i="${i}"><b>${i + 1}</b><span>${escapeHtml(t)}</span></span>`).join("")}</div>`;
  form.insertBefore(prog, form.firstChild);

  const nav = document.createElement("div");
  nav.className = "step-nav";
  nav.innerHTML =
    `<button type="button" class="step-prev ghost-btn">← 上一步</button>
     <button type="button" class="step-next">下一步 →</button>`;
  form.appendChild(nav);

  const fill = prog.querySelector(".fp-fill");
  const spans = Array.from(prog.querySelectorAll(".fp-step"));
  const prevBtn = nav.querySelector(".step-prev");
  const nextBtn = nav.querySelector(".step-next");
  let cur = 0;

  function render() {
    groups.forEach((els, i) => els.forEach((el) => { if (el) el.classList.toggle("step-off", i !== cur); }));
    fill.style.width = (total <= 1 ? 100 : (cur / (total - 1)) * 100) + "%";
    spans.forEach((s, i) => { s.classList.toggle("active", i === cur); s.classList.toggle("done", i < cur); });
    prevBtn.classList.toggle("hidden", cur === 0);
    nextBtn.classList.toggle("hidden", cur === total - 1);
  }

  function validateStep(n) {
    let ok = true, first = null;
    groups[n].forEach((m) => {
      if (!m) return;
      const fields = m.matches("input,select,textarea") ? [m] : Array.from(m.querySelectorAll("input,select,textarea"));
      fields.forEach((el) => {
        if (el.type === "checkbox" || el.type === "hidden" || el.classList.contains("step-off")) return;
        const err = validateField(el);
        if (err) { setFieldError(el, err); if (!first) first = el; ok = false; }
      });
    });
    if (first) first.focus();
    return ok;
  }

  nextBtn.addEventListener("click", () => {
    if (!validateStep(cur)) { showToast("请先完善本步信息再继续", "error"); return; }
    if (cur < total - 1) { cur++; render(); prog.scrollIntoView({ behavior: "smooth", block: "center" }); }
  });
  prevBtn.addEventListener("click", () => {
    if (cur > 0) { cur--; render(); prog.scrollIntoView({ behavior: "smooth", block: "center" }); }
  });
  spans.forEach((s) => s.addEventListener("click", () => {
    const i = Number(s.dataset.i);
    if (i < cur) { cur = i; render(); }
  }));

  form.__stepper = {
    gotoEl(el) {
      if (!el) return;
      let holder = el.closest("[data-step]");
      let step = holder && holder.dataset.step != null ? Number(holder.dataset.step) : null;
      if (step == null) { const p = el.closest(".field"); if (p && p.dataset.step != null) step = Number(p.dataset.step); }
      if (step != null) { cur = step; render(); }
    },
    reset() { cur = 0; render(); },
    render,
  };
  render();
}

// —— 初始化两个测算表单的分步 + 实时校验 ——
(function initSteppedForms() {
  const ent = document.getElementById("loan-form");
  if (ent && !ent.__stepper) {
    buildStepper(ent, [
      ["f-company", "f-industry", "custom-industry-box", "industry-template-box", "f-years", "f-capital", "f-employees"].map(_stepWrap),
      ["f-revenue", "f-credit", "f-collateral"].map(_stepWrap).concat([ent.querySelector(".checks")]),
      ["f-amount", "f-purpose", "f-term"].map(_stepWrap).concat([ent.querySelector(".consent-row"), ent.querySelector(".form-btns")]),
    ], ["基础信息", "经营与征信", "融资需求"]);
    attachLiveValidation(ent);
  }
  const per = document.getElementById("personal-form");
  if (per && !per.__stepper) {
    buildStepper(per, [
      ["pf-name", "pf-occupation", "pf-age", "pf-workyears"].map(_stepWrap),
      ["pf-income", "pf-income-type", "pf-fund", "pf-house", "pf-car", "pf-debt"].map(_stepWrap).concat(Array.from(per.querySelectorAll(".checks"))),
      ["pf-credit", "pf-amount", "pf-purpose", "pf-term"].map(_stepWrap).concat([per.querySelector(".consent-row"), per.querySelector(".form-btns")]),
    ], ["基础信息", "收入与资产", "征信与需求"]);
    attachLiveValidation(per);
  }
  // 账号登录等页面上的手机号输入也接入格式校验
  attachLiveValidation(document.body);
})();
