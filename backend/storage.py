"""申请记录持久化。

支持双后端:
- 默认使用本地 SQLite(开发/演示,文件在 APP_DB_PATH)。
- 若配置环境变量 DATABASE_URL(postgres://...),则使用云端 Postgres 持久化,
  避免 Render 等免费容器重启后数据丢失。

Postgres 通过一个轻量兼容层模拟 sqlite3 连接接口(execute / 上下文管理 /
字典与下标混合取值),因此上层业务代码与 SQL 基本无需改动。
"""
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
_USE_PG = DATABASE_URL.startswith("postgres")

DB_PATH = os.environ.get(
    "APP_DB_PATH", os.path.join(os.path.dirname(__file__), "applications.db")
)

# 自增主键 DDL 片段(方言差异)
_AUTO_PK = "BIGSERIAL PRIMARY KEY" if _USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"

_NAMED_PARAM = re.compile(r":(\w+)")


def _translate(sql: str) -> str:
    """把 sqlite 占位符转成 psycopg2 风格:':name' -> '%(name)s',  '?' -> '%s'。"""
    sql = _NAMED_PARAM.sub(r"%(\1)s", sql)
    sql = sql.replace("?", "%s")
    return sql


class _PGRow:
    """兼容 sqlite3.Row:支持 row[int]、row['col']、row.keys()、dict(row)、row.get()。"""
    __slots__ = ("_cols", "_vals", "_map")

    def __init__(self, cols, vals):
        self._cols = cols
        self._vals = vals
        self._map = {c: v for c, v in zip(cols, vals)}

    def __getitem__(self, k):
        if isinstance(k, int):
            return self._vals[k]
        return self._map[k]

    def keys(self):
        return list(self._cols)

    def get(self, k, default=None):
        return self._map.get(k, default)

    def __iter__(self):
        return iter(self._vals)


class _PGCursor:
    def __init__(self, cur):
        self._cur = cur

    @property
    def rowcount(self):
        return self._cur.rowcount

    def _cols(self):
        return [d[0] for d in self._cur.description] if self._cur.description else []

    def fetchone(self):
        row = self._cur.fetchone()
        return _PGRow(self._cols(), row) if row is not None else None

    def fetchall(self):
        cols = self._cols()
        return [_PGRow(cols, r) for r in self._cur.fetchall()]


class _PGConn:
    """psycopg2 连接的 sqlite3 兼容包装。每次进入 with 时新建连接,退出时提交并关闭。"""

    def __init__(self):
        import psycopg2
        self._conn = psycopg2.connect(DATABASE_URL)

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        if params is None:
            cur.execute(_translate(sql))
        else:
            cur.execute(_translate(sql), params)
        return _PGCursor(cur)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()


def _conn():
    if _USE_PG:
        return _PGConn()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                company_name TEXT,
                industry TEXT,
                loan_amount REAL,
                best_product TEXT,
                best_amount REAL,
                risk_score INTEGER,
                risk_grade TEXT,
                status TEXT DEFAULT '待提交',
                profile_json TEXT,
                result_json TEXT,
                created_at TEXT
            )
            """
        )
        if _USE_PG:
            conn.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS reject_reason TEXT DEFAULT ''")
            conn.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS manual_override INTEGER DEFAULT 0")
        else:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(applications)").fetchall()]
            if "reject_reason" not in cols:
                conn.execute("ALTER TABLE applications ADD COLUMN reject_reason TEXT DEFAULT ''")
            if "manual_override" not in cols:
                conn.execute("ALTER TABLE applications ADD COLUMN manual_override INTEGER DEFAULT 0")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id {_AUTO_PK},
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_players (
                player_id TEXT PRIMARY KEY,
                nickname TEXT,
                coins INTEGER DEFAULT 0,
                total_answered INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                kind TEXT,
                company_name TEXT,
                phone TEXT,
                industry TEXT,
                loan_amount REAL,
                bank TEXT,
                slot TEXT,
                note TEXT,
                status TEXT DEFAULT '待回访',
                created_at TEXT
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS events (
                id {_AUTO_PK},
                session_id TEXT,
                name TEXT NOT NULL,
                props TEXT,
                page TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_name ON events(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                phone TEXT PRIMARY KEY,
                profile_json TEXT DEFAULT '',
                roles_json TEXT DEFAULT '[]',
                created_at TEXT,
                last_login TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS account_sessions (
                token TEXT PRIMARY KEY,
                phone TEXT NOT NULL,
                created_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sess_phone ON account_sessions(phone)")

        # 工单/客户经理字段(对旧库补列)
        for col, ddl in (
            ("manager", "ALTER TABLE leads ADD COLUMN manager TEXT DEFAULT ''"),
            ("follow_up", "ALTER TABLE leads ADD COLUMN follow_up TEXT DEFAULT ''"),
            ("updated_at", "ALTER TABLE leads ADD COLUMN updated_at TEXT DEFAULT ''"),
            ("tags", "ALTER TABLE leads ADD COLUMN tags TEXT DEFAULT ''"),
            ("service_tier", "ALTER TABLE leads ADD COLUMN service_tier TEXT DEFAULT ''"),
            ("referrer", "ALTER TABLE leads ADD COLUMN referrer TEXT DEFAULT ''"),
        ):
            try:
                conn.execute(ddl)
            except Exception:
                pass

        # 审计日志(满足金融审计留存要求,建议留存 ≥5 年)
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id {_AUTO_PK},
                actor TEXT,
                action TEXT NOT NULL,
                target TEXT,
                detail TEXT,
                ip TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")


def add_audit_log(action: str, actor: str = "admin", target: str = "", detail: str = "", ip: str = "") -> None:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        conn.execute(
            "INSERT INTO audit_logs (actor, action, target, detail, ip, created_at) VALUES (?,?,?,?,?,?)",
            (actor, action, target, detail, ip, created_at),
        )


def list_audit_logs(limit: int = 200) -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
        return [dict(r) for r in rows]


def update_lead(lead_id: str, fields: dict) -> Optional[dict]:
    allowed = {"status", "manager", "follow_up", "note"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return None
    sets["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cols = ", ".join(f"{k} = :{k}" for k in sets)
    sets["_id"] = lead_id
    with _conn() as conn:
        conn.execute(f"UPDATE leads SET {cols} WHERE id = :_id", sets)
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None


def lead_stats() -> dict:
    """成单/工单统计(含金额、佣金预估、按经理业绩)。"""
    COMMISSION_RATE = 0.01  # 渠道返佣预估:放款额 1%
    with _conn() as conn:
        rows = conn.execute("SELECT status, COUNT(*) c FROM leads GROUP BY status").fetchall()
        by_status = {r["status"] or "未知": r["c"] for r in rows}
        total = sum(by_status.values())
        won = by_status.get("已放款", 0) + by_status.get("已通过", 0)
        won_amount = conn.execute(
            "SELECT COALESCE(SUM(loan_amount),0) s FROM leads WHERE status IN ('已放款','已通过')"
        ).fetchone()["s"] or 0
        mrows = conn.execute(
            """SELECT manager,
                      COUNT(*) c,
                      SUM(CASE WHEN status IN ('已放款','已通过') THEN 1 ELSE 0 END) won,
                      SUM(CASE WHEN status IN ('已放款','已通过') THEN loan_amount ELSE 0 END) won_amt
               FROM leads WHERE manager != '' AND manager IS NOT NULL GROUP BY manager"""
        ).fetchall()
        by_manager = []
        for r in mrows:
            c = r["c"] or 0
            w = r["won"] or 0
            by_manager.append({
                "manager": r["manager"],
                "count": c,
                "won": w,
                "won_amount": round(r["won_amt"] or 0, 1),
                "win_rate": round(w / c * 100, 1) if c else 0.0,
                "commission": round((r["won_amt"] or 0) * COMMISSION_RATE, 2),
            })
        by_manager.sort(key=lambda x: x["won_amount"], reverse=True)
    win_rate = round(won / total * 100, 1) if total else 0.0
    return {
        "total": total, "won": won, "win_rate": win_rate,
        "won_amount": round(won_amount, 1),
        "est_commission": round(won_amount * COMMISSION_RATE, 2),
        "by_status": by_status, "by_manager": by_manager,
    }


def seed_demo_leads() -> dict:
    """生成一批演示用工单/客户线索(带 demo 标记,可清除),让后台看板与业绩统计丰满。"""
    import random
    from datetime import timedelta
    industries = ["制造", "商贸", "餐饮", "建筑", "科技", "物流"]
    banks = ["工商银行", "建设银行", "招商银行", "网商银行", "地方农商行"]
    managers = ["李经理", "王经理", "张经理", "刘经理"]
    statuses = ["待回访", "已联系", "材料待补充", "银行审核中", "已放款", "已拒绝"]
    tiers = ["", "深度诊断版", "银行申报代办", "政策代办"]
    companies = ["顺发", "鑫隆", "恒通", "德盛", "宏图", "永泰", "金鼎", "华瑞", "利丰", "盛世"]
    suffix = ["贸易", "科技", "食品", "建材", "制造", "物流"]
    now = datetime.now()
    created = 0
    with _conn() as conn:
        for _ in range(28):
            days_ago = random.randint(0, 20)
            dt = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            ind = random.choice(industries)
            amt = random.choice([20, 30, 50, 80, 100, 150, 200, 300])
            st = random.choices(statuses, weights=[18, 20, 14, 16, 22, 10])[0]
            mgr = random.choice(managers) if st != "待回访" else random.choice(["", *managers])
            tags = [ind, ("大额抵押客户" if amt >= 150 else "短期周转客户")]
            if random.random() < 0.4:
                tags.append("想申请贴息")
            row = {
                "id": "demo-" + uuid.uuid4().hex[:10],
                "kind": random.choice(["预约", "咨询", "增值意向"]),
                "company_name": random.choice(companies) + random.choice(suffix) + "有限公司",
                "phone": "138" + "".join(str(random.randint(0, 9)) for _ in range(8)),
                "industry": ind,
                "loan_amount": amt,
                "bank": random.choice(banks),
                "slot": "",
                "note": "[demo]",
                "status": st,
                "created_at": dt,
                "manager": mgr,
                "follow_up": random.choice(["", "已电联,待补充流水", "客户考虑中", "已提交银行", "已放款完成"]),
                "updated_at": dt,
                "tags": "、".join(tags),
                "service_tier": random.choice(tiers),
                "referrer": random.choice(["", "", "老客推荐"]),
            }
            conn.execute(
                """INSERT INTO leads (id,kind,company_name,phone,industry,loan_amount,bank,slot,note,status,created_at,manager,follow_up,updated_at,tags,service_tier,referrer)
                   VALUES (:id,:kind,:company_name,:phone,:industry,:loan_amount,:bank,:slot,:note,:status,:created_at,:manager,:follow_up,:updated_at,:tags,:service_tier,:referrer)""",
                row,
            )
            created += 1
    return {"created": created}


def clear_demo_leads() -> dict:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM leads WHERE id LIKE 'demo-%' OR note = '[demo]'")
        return {"deleted": cur.rowcount}


def save_chat_message(session_id: str, role: str, content: str) -> None:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, created_at),
        )


def get_chat_history(session_id: str) -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_chat_sessions() -> List[dict]:
    """返回所有会话摘要(会话ID、消息数、首条用户消息、最后时间)。"""
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT session_id,
                   COUNT(*) AS message_count,
                   MAX(created_at) AS last_at
            FROM chat_messages
            GROUP BY session_id
            ORDER BY last_at DESC
            """
        ).fetchall()
        sessions = []
        for r in rows:
            first = conn.execute(
                "SELECT content FROM chat_messages WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
                (r["session_id"],),
            ).fetchone()
            sessions.append({
                "session_id": r["session_id"],
                "message_count": r["message_count"],
                "last_at": r["last_at"],
                "preview": (first["content"][:30] if first else "(无内容)"),
            })
    return sessions


def delete_chat_session(session_id: str) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "DELETE FROM chat_messages WHERE session_id = ?", (session_id,)
        )
        return cur.rowcount


# 线索/预约入库(经理预约、咨询线索)
def create_lead(data: dict) -> dict:
    lead_id = uuid.uuid4().hex[:12]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "id": lead_id,
        "kind": data.get("kind", "咨询"),
        "company_name": data.get("company_name", ""),
        "phone": data.get("phone", ""),
        "industry": data.get("industry", ""),
        "loan_amount": data.get("loan_amount", 0) or 0,
        "bank": data.get("bank", ""),
        "slot": data.get("slot", ""),
        "note": data.get("note", ""),
        "status": "待回访",
        "created_at": created_at,
        "manager": "",
        "follow_up": "",
        "updated_at": created_at,
        "tags": "、".join(data.get("tags") or []) if isinstance(data.get("tags"), list) else (data.get("tags") or ""),
        "service_tier": data.get("service_tier", "") or "",
        "referrer": data.get("referrer", "") or "",
    }
    with _conn() as conn:
        conn.execute(
            """INSERT INTO leads (id,kind,company_name,phone,industry,loan_amount,bank,slot,note,status,created_at,manager,follow_up,updated_at,tags,service_tier,referrer)
               VALUES (:id,:kind,:company_name,:phone,:industry,:loan_amount,:bank,:slot,:note,:status,:created_at,:manager,:follow_up,:updated_at,:tags,:service_tier,:referrer)""",
            row,
        )
    return row


def list_leads() -> List[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


# ------------------------- 产品埋点分析 -------------------------
# 允许上报的事件白名单(防止被灌垃圾数据),值为看板展示用中文名。
EVENT_LABELS = {
    "page_view": "访问首页",
    "form_start": "开始填表",
    "recommend_submit": "提交企业测算",
    "recommend_success": "得到企业方案",
    "recommend_empty": "企业未匹配",
    "personal_submit": "提交个人测算",
    "personal_success": "得到个人方案",
    "view_more": "展开完整方案",
    "view_glossary": "看名词小课堂",
    "more_tools": "打开更多功能",
    "export_pdf": "导出方案PDF",
    "export_pdf_bank": "导出银行提交版PDF",
    "subsidy_flow": "查看补贴申报流程",
    "export_excel": "导出Excel",
    "export_bank": "导银行材料",
    "share_poster": "生成分享海报",
    "growth_report": "查资质成长报告",
    "combo_credit": "用组合贷测算",
    "save_application": "保存申请记录",
    "lead_submit": "留资/预约",
    "chat_open": "打开AI助手",
    "chat_send": "向AI提问",
    "preaudit": "使用预审",
    "hidden_subsidy": "查隐藏贴息",
    "policy_filter": "筛选政策库",
    "policy_guide": "下载申报指南",
    "credit_check": "征信自查",
    "msg_center": "打开消息中心",
    "account_login": "手机号登录",
    "pricing_view": "查看服务套餐",
    "upgrade_intent": "升级增值意向",
    "wecom_add": "加企微引导",
    "referral_copy": "复制裂变邀请码",
}

# 转化漏斗定义:(事件名, 展示名)。按此顺序计算逐级转化。
FUNNEL_STEPS = [
    ("page_view", "访问"),
    ("form_start", "开始填表"),
    ("recommend_submit", "提交测算"),
    ("recommend_success", "看到方案"),
    ("view_more", "展开详情"),
    ("lead_submit", "留资/预约"),
]


def record_event(session_id: str, name: str, props=None, page: str = "") -> bool:
    """记录一个前端埋点事件。仅接受白名单内事件,失败静默返回 False。"""
    if name not in EVENT_LABELS:
        return False
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        props_json = json.dumps(props, ensure_ascii=False) if props else ""
    except Exception:
        props_json = ""
    row = {
        "session_id": (session_id or "")[:64],
        "name": name,
        "props": props_json[:500],
        "page": (page or "")[:64],
        "created_at": created_at,
    }
    with _conn() as conn:
        conn.execute(
            "INSERT INTO events (session_id, name, props, page, created_at) "
            "VALUES (:session_id, :name, :props, :page, :created_at)",
            row,
        )
    return True


def analytics_summary(days: int = 30) -> dict:
    """聚合埋点数据:总览、转化漏斗、功能使用、每日趋势。"""
    since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    since_str = (since - timedelta(days=max(0, days - 1))).strftime("%Y-%m-%d %H:%M:%S")

    with _conn() as conn:
        rows = conn.execute(
            "SELECT session_id, name, created_at FROM events WHERE created_at >= ?",
            (since_str,),
        ).fetchall()
    rows = [dict(r) for r in rows]

    total_events = len(rows)
    sessions = set(r["session_id"] for r in rows if r["session_id"])
    # 每个事件命中的独立会话集合
    sess_by_event = {}
    count_by_event = {}
    for r in rows:
        count_by_event[r["name"]] = count_by_event.get(r["name"], 0) + 1
        sess_by_event.setdefault(r["name"], set()).add(r["session_id"])

    # 转化漏斗:按独立会话数逐级计算
    funnel = []
    base = None
    prev = None
    for name, label in FUNNEL_STEPS:
        n = len(sess_by_event.get(name, set()))
        if base is None:
            base = n or 1
        step = {
            "name": name,
            "label": label,
            "count": n,
            "pct_of_top": round(n / base * 100, 1) if base else 0.0,
            "pct_of_prev": round(n / prev * 100, 1) if prev else 100.0,
        }
        funnel.append(step)
        prev = n if n else prev

    # 功能使用排行(排除漏斗基础事件)
    funnel_names = {n for n, _ in FUNNEL_STEPS}
    feature_usage = sorted(
        [
            {"name": k, "label": EVENT_LABELS.get(k, k), "count": v,
             "sessions": len(sess_by_event.get(k, set()))}
            for k, v in count_by_event.items()
            if k not in funnel_names or k in ("view_more",)
        ],
        key=lambda x: x["count"], reverse=True,
    )

    # 每日趋势(访问 & 提交)
    daily = {}
    for r in rows:
        day = (r["created_at"] or "")[:10]
        if not day:
            continue
        d = daily.setdefault(day, {"page_view": 0, "recommend_submit": 0, "personal_submit": 0})
        if r["name"] in d:
            d[r["name"]] += 1
    daily_list = [{"date": k, **v} for k, v in sorted(daily.items())]

    # 关键转化率
    n_visit = len(sess_by_event.get("page_view", set())) or 1
    n_submit = len(sess_by_event.get("recommend_submit", set())) + \
        len(sess_by_event.get("personal_submit", set()))
    n_lead = len(sess_by_event.get("lead_submit", set()))

    # 流失预警:漏斗中单步相对流失 >40% 的环节自动告警
    churn_alerts = []
    for i, step in enumerate(funnel):
        if i == 0:
            continue
        drop = round(100 - step["pct_of_prev"], 1)
        if drop > 40 and funnel[i - 1]["count"] > 0:
            churn_alerts.append({
                "from": funnel[i - 1]["label"],
                "to": step["label"],
                "drop": drop,
                "level": "high" if drop > 60 else "warn",
            })

    return {
        "range_days": days,
        "totals": {
            "events": total_events,
            "sessions": len(sessions),
            "form_conversion": round(n_submit / n_visit * 100, 1),
            "lead_conversion": round(n_lead / n_visit * 100, 1),
        },
        "funnel": funnel,
        "churn_alerts": churn_alerts,
        "feature_usage": feature_usage,
        "daily": daily_list,
    }


def seed_demo_events(days: int = 14, visitors_per_day: int = 40) -> dict:
    """生成一批演示用埋点数据(仅供答辩/演示,带 demo 标记,可一键清除)。

    模拟真实的逐级流失:并非每个访客都会走到最后,越往后人越少。
    """
    import random
    from datetime import timedelta

    # 各漏斗步骤的"通过率"(相对上一步),模拟真实转化衰减
    step_pass = {
        "page_view": 1.0,
        "form_start": 0.62,
        "recommend_submit": 0.71,
        "recommend_success": 0.90,
        "view_more": 0.48,
        "lead_submit": 0.22,
    }
    # 附带功能事件及其在"看到方案"用户中的触发概率
    feature_probs = {
        "view_glossary": 0.35, "more_tools": 0.20, "export_pdf": 0.28,
        "save_application": 0.18, "share_poster": 0.09, "growth_report": 0.11,
        "chat_open": 0.24, "chat_send": 0.16, "preaudit": 0.14,
        "hidden_subsidy": 0.12, "export_excel": 0.07, "personal_submit": 0.15,
    }
    now = datetime.now()
    rows = []
    for d in range(days):
        day = now - timedelta(days=days - 1 - d)
        # 周末流量略低,整体有小幅波动
        base = int(visitors_per_day * (0.7 if day.weekday() >= 5 else 1.0)
                   * random.uniform(0.75, 1.25))
        for _ in range(base):
            ts = day.replace(hour=random.randint(8, 22),
                             minute=random.randint(0, 59),
                             second=random.randint(0, 59))
            created = ts.strftime("%Y-%m-%d %H:%M:%S")
            sid = "demo_" + uuid.uuid4().hex[:10]
            reached = True
            for step in ["page_view", "form_start", "recommend_submit",
                         "recommend_success", "view_more", "lead_submit"]:
                if step != "page_view":
                    reached = reached and (random.random() < step_pass[step])
                if reached:
                    rows.append((sid, step, "demo", "/", created))
            # 到达"看到方案"的用户,可能触发一些功能事件
            if any(r[1] == "recommend_success" and r[0] == sid for r in rows[-6:]):
                for feat, prob in feature_probs.items():
                    if random.random() < prob:
                        rows.append((sid, feat, "demo", "/", created))
    with _conn() as conn:
        for r in rows:
            conn.execute(
                "INSERT INTO events (session_id, name, props, page, created_at) "
                "VALUES (?, ?, ?, ?, ?)", r,
            )
    return {"inserted": len(rows), "days": days}


def clear_demo_events() -> dict:
    """清除所有演示埋点数据(session_id 以 demo_ 开头或 props='demo')。"""
    with _conn() as conn:
        cur = conn.execute(
            "DELETE FROM events WHERE session_id LIKE 'demo_%' OR props = 'demo'"
        )
        n = cur.rowcount if hasattr(cur, "rowcount") else 0
    return {"deleted": n}


# 申请状态流转
VALID_STATUS = ["待提交", "已提交", "审核中", "已通过", "已拒绝", "已放款"]


def create_application(profile: dict, result: dict) -> dict:
    app_id = uuid.uuid4().hex[:12]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plans = result.get("plans", [])
    best = plans[0] if plans else {}
    risk = result.get("result_risk") or result.get("risk", {})

    row = {
        "id": app_id,
        "company_name": profile.get("company_name") or "未命名企业",
        "industry": profile.get("industry", ""),
        "loan_amount": profile.get("loan_amount", 0),
        "best_product": best.get("product_name", "暂无匹配产品"),
        "best_amount": best.get("estimated_amount", 0),
        "risk_score": risk.get("score", 0),
        "risk_grade": risk.get("grade", "-"),
        "status": "待提交",
        "profile_json": json.dumps(profile, ensure_ascii=False),
        "result_json": json.dumps(result, ensure_ascii=False),
        "created_at": created_at,
    }
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO applications
            (id, company_name, industry, loan_amount, best_product, best_amount,
             risk_score, risk_grade, status, profile_json, result_json, created_at)
            VALUES (:id, :company_name, :industry, :loan_amount, :best_product, :best_amount,
                    :risk_score, :risk_grade, :status, :profile_json, :result_json, :created_at)
            """,
            row,
        )
    return _summary(row)


def get_setting(key: str, default: str = "") -> str:
    with _conn() as conn:
        r = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return r["value"] if r else default


def set_setting(key: str, value: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


# 状态推进节奏:demo=按分钟快速演示;real=按天真实模拟
_ADVANCE_STEPS = {
    "demo": (1, 3, 6, 10, 12),       # 分钟
    "real": (60, 1440, 4320, 10080, 14400),  # 分钟≈1h/1d/3d/7d/10d
}


def _auto_advance(conn, r: dict) -> dict:
    """未被手动改过的记录,按提交后时长+风控等级自动模拟推进申请状态。"""
    if r.get("manual_override"):
        return r
    try:
        created = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return r
    mins = (datetime.now() - created).total_seconds() / 60.0
    grade = (r.get("risk_grade") or "B").upper()
    mode = get_setting("advance_mode", "demo")
    s1, s2, s3, s4, s5 = _ADVANCE_STEPS.get(mode, _ADVANCE_STEPS["demo"])
    if mins < s1:
        status = "待提交"
    elif mins < s2:
        status = "已提交"
    elif mins < s3:
        status = "审核中"
    else:
        if grade in ("A", "B"):
            status = "已放款" if mins >= s4 else "已通过"
        elif grade == "C":
            status = "已通过" if mins < s5 else "已放款"
        else:
            status = "已拒绝"
    reject = ""
    if status == "已拒绝":
        reject = r.get("reject_reason") or "风控等级偏低,建议先优化资质再申请"
    if status != r.get("status") or reject != (r.get("reject_reason") or ""):
        conn.execute(
            "UPDATE applications SET status = ?, reject_reason = ? WHERE id = ?",
            (status, reject, r["id"]),
        )
        r["status"], r["reject_reason"] = status, reject
    return r


def list_applications() -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY created_at DESC"
        ).fetchall()
        rows = [_auto_advance(conn, dict(r)) for r in rows]
    return [_summary(r) for r in rows]


def get_application(app_id: str) -> Optional[dict]:
    with _conn() as conn:
        r = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()
        if not r:
            return None
        r = _auto_advance(conn, dict(r))
    return {
        **_summary(r),
        "profile": json.loads(r["profile_json"]),
        "result": json.loads(r["result_json"]),
    }


def update_status(app_id: str, status: str, reject_reason: str = "") -> Optional[dict]:
    if status not in VALID_STATUS:
        return None
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE applications SET status = ?, reject_reason = ?, manual_override = 1 WHERE id = ?",
            (status, reject_reason if status == "已拒绝" else "", app_id),
        )
        if cur.rowcount == 0:
            return None
        r = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()
    return _summary(dict(r))


def reject_insights() -> dict:
    """聚合历史被拒原因,生成迭代优化建议,使匹配越用越准。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT reject_reason FROM applications WHERE status = '已拒绝' AND reject_reason != ''"
        ).fetchall()
    reasons = {}
    for r in rows:
        reasons[r[0]] = reasons.get(r[0], 0) + 1
    top = sorted(reasons.items(), key=lambda x: -x[1])
    tips = {
        "征信不达标": "下一次优先选择担保/抵押类产品,先做前置预审修复征信短板。",
        "额度过高被压": "建议把首次申请额度下调至年营收 50% 以内,通过率更高。",
        "经营年限不足": "匹配对成立年限要求低的产品,补充法人增信材料。",
        "材料不全": "导出银行成品材料并补齐纳税/流水凭证后再提交。",
        "抵押物不足": "选择纯信用银税贷,或引入担保人增信。",
        "行业受限": "关注对本行业准入更宽松的城商行/担保产品。",
        "其他": "结合前置预审报告逐项整改后再迭代申请。",
    }
    return {
        "rejected_total": len(rows),
        "reasons": [{"reason": k, "count": v, "tip": tips.get(k, tips["其他"])} for k, v in top],
    }


def calibrate_industry(industry: str) -> dict:
    """用历史申请放款数据反哺:计算该行业实际通过率,用于校准通过率展示。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT status FROM applications WHERE industry = ? AND status IN "
            "('已通过','已放款','已拒绝')", (industry,)
        ).fetchall()
    done = sum(1 for r in rows if r[0] in ("已通过", "已放款"))
    total = len(rows)
    if total < 3:
        return {"calibrated": False, "samples": total}
    rate = round(done / total * 100)
    return {"calibrated": True, "samples": total, "actual_pass_rate": rate,
            "delta": rate - 70}


def scorecard_calibration() -> dict:
    """评分卡冷启动校准:按预测风控分档,统计真实审批通过率与平均放款额度差异。

    用于验证评分卡区分度(分越高实际通过率应越高),并为评分卡迭代提供依据。
    """
    bands = [
        ("A", 85, 101, "优质低风险"),
        ("B", 70, 85, "良好可控"),
        ("C", 55, 70, "中等风险"),
        ("D", 40, 55, "较高风险"),
        ("E", 0, 40, "高风险"),
    ]
    with _conn() as conn:
        rows = conn.execute(
            "SELECT risk_score, best_amount, status FROM applications "
            "WHERE status IN ('已通过','已放款','已拒绝')"
        ).fetchall()
    decided = [r for r in rows if r["risk_score"] is not None]
    total = len(decided)
    result = []
    for grade, lo, hi, label in bands:
        seg = [r for r in decided if lo <= (r["risk_score"] or 0) < hi]
        n = len(seg)
        approved = [r for r in seg if r["status"] in ("已通过", "已放款")]
        pass_rate = round(len(approved) / n * 100) if n else None
        avg_amt = round(sum((r["best_amount"] or 0) for r in approved) / len(approved), 1) if approved else None
        result.append({
            "grade": grade,
            "label": label,
            "range": f"{lo}-{hi - 1}",
            "samples": n,
            "actual_pass_rate": pass_rate,
            "avg_approved_amount": avg_amt,
        })
    # 区分度判断:高分档通过率是否单调高于低分档
    known = [b for b in result if b["actual_pass_rate"] is not None]
    monotonic = all(
        known[i]["actual_pass_rate"] >= known[i + 1]["actual_pass_rate"]
        for i in range(len(known) - 1)
    ) if len(known) >= 2 else None
    return {
        "total_samples": total,
        "enough": total >= 5,
        "bands": result,
        "discriminative": monotonic,
    }


def data_assets() -> dict:
    """沉淀的独家私有数据集统计:真实审批样本、贴息落地案例、行业分布。
    这是通用大模型无法获取的线下闭环数据,样本越多壁垒越厚。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT industry, status, best_amount, risk_score, result_json, created_at FROM applications"
        ).fetchall()
    total = len(rows)
    decided = [r for r in rows if r["status"] in ("已通过", "已放款", "已拒绝")]
    approved = [r for r in rows if r["status"] in ("已通过", "已放款")]
    pass_rate = round(len(approved) / len(decided) * 100) if decided else 0
    released_amt = round(sum((r["best_amount"] or 0) for r in approved), 1)
    avg_score = round(sum((r["risk_score"] or 0) for r in rows) / total) if total else 0

    subsidy_cases = 0
    subsidy_amt = 0.0
    ind = {}
    for r in rows:
        ind[r["industry"]] = ind.get(r["industry"], 0) + 1
        try:
            res = json.loads(r["result_json"] or "{}")
            subs = res.get("subsidies", []) or []
            if subs:
                subsidy_cases += 1
        except Exception:
            pass
    industries = sorted(({"name": k, "count": v} for k, v in ind.items()),
                        key=lambda x: -x["count"])[:8]
    moat = min(100, total * 4)

    monthly = {}
    for r in rows:
        m = (r["created_at"] or "")[:7] if "created_at" in r.keys() else ""
        if not m:
            continue
        d = monthly.setdefault(m, {"samples": 0, "approved": 0})
        d["samples"] += 1
        if r["status"] in ("已通过", "已放款"):
            d["approved"] += 1
    trend = [{"month": k, "samples": v["samples"], "approved": v["approved"]}
             for k, v in sorted(monthly.items())][-6:]
    return {
        "total_samples": total,
        "decided_samples": len(decided),
        "approved_samples": len(approved),
        "pass_rate": pass_rate,
        "released_amount": released_amt,
        "avg_risk_score": avg_score,
        "subsidy_cases": subsidy_cases,
        "industries": industries,
        "moat_index": moat,
        "trend": trend,
    }


def delete_application(app_id: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        return cur.rowcount > 0


def _summary(r: dict) -> dict:

    return {
        "id": r["id"],
        "company_name": r["company_name"],
        "industry": r["industry"],
        "loan_amount": r["loan_amount"],
        "best_product": r["best_product"],
        "best_amount": r["best_amount"],
        "risk_score": r["risk_score"],
        "risk_grade": r["risk_grade"],
        "status": r["status"],
        "reject_reason": r["reject_reason"] if "reject_reason" in r.keys() else "",
        "created_at": r["created_at"],
    }


# ------------------------- 金融闯关游戏 -------------------------
import quiz as _quizmod  # noqa: E402


def _ensure_player(conn, player_id: str) -> dict:
    r = conn.execute(
        "SELECT * FROM quiz_players WHERE player_id = ?", (player_id,)
    ).fetchone()
    if r:
        return dict(r)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO quiz_players (player_id, coins, total_answered, total_correct, best_streak, level, updated_at) "
        "VALUES (?, 0, 0, 0, 0, 1, ?)",
        (player_id, now),
    )
    return {
        "player_id": player_id, "nickname": None, "coins": 0,
        "total_answered": 0, "total_correct": 0, "best_streak": 0,
        "level": 1, "updated_at": now,
    }


def _player_payload(row: dict) -> dict:
    coins = row["coins"]
    info = _quizmod.level_info(coins)
    answered = row["total_answered"] or 0
    correct = row["total_correct"] or 0
    accuracy = round(correct / answered * 100) if answered else 0
    return {
        "player_id": row["player_id"],
        "nickname": row.get("nickname"),
        "coins": coins,
        "total_answered": answered,
        "total_correct": correct,
        "best_streak": row.get("best_streak", 0),
        "accuracy": accuracy,
        **info,
    }


def get_quiz_progress(player_id: str) -> dict:
    with _conn() as conn:
        row = _ensure_player(conn, player_id)
    return _player_payload(row)


def record_quiz_answer(player_id: str, correct: bool, coins_earned: int, streak: int) -> dict:
    """记录一次答题结果,更新金币、答对数、连胜与等级。返回最新进度。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        row = _ensure_player(conn, player_id)
        coins = row["coins"] + (coins_earned if correct else 0)
        answered = (row["total_answered"] or 0) + 1
        correct_n = (row["total_correct"] or 0) + (1 if correct else 0)
        best_streak = max(row.get("best_streak", 0) or 0, streak or 0)
        level = _quizmod.level_info(coins)["level"]
        conn.execute(
            "UPDATE quiz_players SET coins = ?, total_answered = ?, total_correct = ?, "
            "best_streak = ?, level = ?, updated_at = ? WHERE player_id = ?",
            (coins, answered, correct_n, best_streak, level, now, player_id),
        )
        row = conn.execute(
            "SELECT * FROM quiz_players WHERE player_id = ?", (player_id,)
        ).fetchone()
    return _player_payload(dict(row))


def set_quiz_nickname(player_id: str, nickname: str) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as conn:
        _ensure_player(conn, player_id)
        conn.execute(
            "UPDATE quiz_players SET nickname = ?, updated_at = ? WHERE player_id = ?",
            (nickname[:20] if nickname else None, now, player_id),
        )
        row = conn.execute(
            "SELECT * FROM quiz_players WHERE player_id = ?", (player_id,)
        ).fetchone()
    return _player_payload(dict(row))


def quiz_leaderboard(limit: int = 10) -> List[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM quiz_players WHERE total_answered > 0 "
            "ORDER BY coins DESC, total_correct DESC LIMIT ?",
            (limit,),
        ).fetchall()
    board = []
    for i, r in enumerate(rows):
        p = _player_payload(dict(r))
        board.append({
            "rank": i + 1,
            "nickname": p["nickname"] or ("玩家" + p["player_id"][:4]),
            "coins": p["coins"],
            "level": p["level"],
            "title": p["title"],
            "emoji": p["emoji"],
            "accuracy": p["accuracy"],
        })
    return board
