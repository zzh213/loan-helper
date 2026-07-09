"""FastAPI 应用入口:中小微企业贷款服务小助手。"""
import json
import os
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import chatbot
import storage
import tts
import quiz
from excel_export import build_excel
from models import (ApplicationCreate, EnterpriseProfile, PersonalProfile,
                    RecommendResponse, StatusUpdate)
from pdf_export import build_pdf
from bank_forms import build_bank_package
from bank_forms_docx import build_bank_package_docx
from recommender import recommend
from personal_recommender import recommend_personal

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

app = FastAPI(title="中小微企业贷款服务小助手", version="1.0.0")

# CORS:默认仅放行本站与本地开发,可用环境变量 ALLOWED_ORIGINS 覆盖(逗号分隔)
_default_origins = (
    "https://loan-helper-665l.onrender.com,"
    "http://localhost:8000,http://127.0.0.1:8000"
)
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 轻量内存限流:防止接口被刷、导出/对话被滥用(Render 免费档单进程,内存计数即可)
_RATE_BUCKETS: dict = defaultdict(deque)
_RATE_WINDOW = 60.0  # 秒
_RATE_DEFAULT = int(os.environ.get("RATE_LIMIT_DEFAULT", "120"))   # 每分钟每 IP 通用上限
_RATE_HEAVY = int(os.environ.get("RATE_LIMIT_HEAVY", "24"))        # 昂贵接口(对话/导出/语音)上限
_HEAVY_PREFIXES = ("/api/chat", "/api/tts", "/api/export", "/api/recommend")


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or not path.startswith("/api/"):
        return await call_next(request)
    heavy = any(path.startswith(p) for p in _HEAVY_PREFIXES)
    limit = _RATE_HEAVY if heavy else _RATE_DEFAULT
    key = f"{_client_ip(request)}|{'heavy' if heavy else 'std'}"
    now = time.monotonic()
    bucket = _RATE_BUCKETS[key]
    while bucket and now - bucket[0] > _RATE_WINDOW:
        bucket.popleft()
    if len(bucket) >= limit:
        return JSONResponse(
            status_code=429,
            content={"detail": "请求过于频繁,请稍后再试(每分钟请求已达上限)。"},
            headers={"Retry-After": "30"},
        )
    bucket.append(now)
    return await call_next(request)


# 安全响应头 + 静态资源缓存:所有响应加固,/static 资源按是否带版本号分级缓存
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "media-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for k, v in _SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    path = request.url.path
    if path.startswith("/static/") and "cache-control" not in (
        h.lower() for h in response.headers.keys()
    ):
        # 带版本号(?v=)的资源可长期强缓存;其余给较短缓存并要求校验
        if "v=" in (request.url.query or ""):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "public, max-age=86400"
    return response


storage.init_db()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# 管理后台口令:优先取环境变量 ADMIN_TOKEN,本地开发默认 admin888
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "admin888").strip()


def require_admin(request: Request):
    """校验管理端口令(请求头 X-Admin-Token 或 ?token=)。"""
    token = request.headers.get("x-admin-token") or request.query_params.get("token") or ""
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="未授权:管理口令无效")
    return True


@app.post("/api/recommend", response_model=RecommendResponse)
def api_recommend(profile: EnterpriseProfile) -> RecommendResponse:
    """根据企业实际情况返回最优贷款方案。"""
    return recommend(profile)


@app.post("/api/recommend-personal", response_model=RecommendResponse)
def api_recommend_personal(profile: PersonalProfile) -> RecommendResponse:
    """根据个人实际情况返回最优贷款方案。"""
    return recommend_personal(profile)


@app.post("/api/preaudit")
def api_preaudit(profile: EnterpriseProfile):
    """前置预审:提交申请前模拟风控打分,输出扣分短板与整改方案。"""
    from preaudit import build_preaudit
    return build_preaudit(profile)


class HiddenSubsidyQuery(BaseModel):
    address: str
    industry: str = ""


@app.post("/api/hidden-subsidies")
def api_hidden_subsidies(q: HiddenSubsidyQuery):
    """园区/区县隐藏贴息:按企业地址解锁通用搜索引擎查不到的专属补贴清单。"""
    from hidden_subsidies import match_hidden
    return {"address": q.address, "items": match_hidden(q.address, q.industry)}


@app.get("/api/regions")
def api_regions():
    """省/市/区县级联下拉数据。"""
    from regions import REGION_TREE
    return REGION_TREE


@app.get("/api/industry-templates")
def api_industry_templates():
    """垂直行业风控模板列表。"""
    from industry_templates import list_templates
    return list_templates()


@app.get("/api/industry-template/{industry}")
def api_industry_template(industry: str):
    """单个行业的专属授信加分项与材料清单。"""
    from industry_templates import get_template
    t = get_template(industry)
    return t or {}


class IndustryClassifyRequest(BaseModel):
    text: str


@app.post("/api/classify-industry")
def api_classify_industry(req: IndustryClassifyRequest):
    """AI 识别自定义行业描述,归类到平台规范行业类别。"""
    import industry_classify
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="请填写行业描述")
    return industry_classify.classify(text)


@app.post("/api/export/pdf")
def api_export_pdf(profile: EnterpriseProfile, edition: str = "self"):
    """生成并下载贷款方案 PDF 报告。edition=self 企业自查版 / bank 银行提交版。"""
    edition = "bank" if edition == "bank" else "self"
    result = recommend(profile)
    pdf_bytes = build_pdf(profile, result, edition=edition)
    filename = "loan_plan_bank.pdf" if edition == "bank" else "loan_plan_self.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/export/pdf-personal")
def api_export_pdf_personal(profile: PersonalProfile):
    """生成并下载个人贷款方案 PDF 报告。"""
    from pdf_export_personal import build_personal_pdf
    result = recommend_personal(profile)
    pdf_bytes = build_personal_pdf(profile, result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="personal_loan_plan.pdf"'},
    )


@app.post("/api/export/excel")
def api_export_excel(profile: EnterpriseProfile):
    """生成并下载贷款方案 Excel 报告。"""
    result = recommend(profile)
    xlsx_bytes = build_excel(profile, result)
    return Response(
        content=xlsx_bytes,
        media_type=XLSX_MIME,
        headers={"Content-Disposition": 'attachment; filename="loan_plan.xlsx"'},
    )


async def _hidden_from_request(request: Request):
    """从导出请求体提取已解锁的隐藏贴息(若有)。"""
    try:
        body = await request.json()
        return body.get("hidden_subsidies") or []
    except Exception:
        return []


@app.post("/api/export/bank-package")
async def api_export_bank_package(profile: EnterpriseProfile, request: Request, bank: str = ""):
    """一键生成可提交银行的成品材料(授信申请表+经营情况说明书+贴息申报台账)。"""
    result = recommend(profile)
    pdf_bytes = build_bank_package(profile, result, await _hidden_from_request(request), bank)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="bank_package.pdf"'},
    )


@app.post("/api/export/bank-package-docx")
async def api_export_bank_package_docx(profile: EnterpriseProfile, request: Request, bank: str = ""):
    """成品材料 Word 版,可二次编辑后盖章提交。"""
    result = recommend(profile)
    docx_bytes = build_bank_package_docx(profile, result, await _hidden_from_request(request), bank)
    docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return Response(
        content=docx_bytes,
        media_type=docx_mime,
        headers={"Content-Disposition": 'attachment; filename="bank_package.docx"'},
    )


@app.get("/api/banks")
def api_banks():
    """可选的银行专属申报模板列表。"""
    from bank_forms import BANKS
    return list(BANKS.keys())


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/data-info")
def data_info():
    """数据口径与更新日期,供前端展示"数据保鲜"标注。"""
    import lpr_reference as lp
    return {
        "lpr_1y": lp.LPR_1Y,
        "lpr_5y": lp.LPR_5Y,
        "lpr_updated": lp.LPR_UPDATED,
        "private_lending_cap": lp.PRIVATE_LENDING_CAP,
        "source_note": lp.DATA_SOURCE_NOTE,
    }


@app.get("/api/qr")
def api_qr(text: str = "http://127.0.0.1:8000/"):
    """生成二维码 PNG,用于海报扫码体验。"""
    import io
    import qrcode
    img = qrcode.make(text[:300])
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/api/settings/advance-mode")
def get_advance_mode():
    return {"mode": storage.get_setting("advance_mode", "demo")}


class AdvanceMode(BaseModel):
    mode: str


@app.post("/api/settings/advance-mode")
def set_advance_mode(payload: AdvanceMode):
    mode = payload.mode if payload.mode in ("demo", "real") else "demo"
    storage.set_setting("advance_mode", mode)
    return {"mode": mode}


class ChatRequest(BaseModel):
    message: str
    history: list = []
    session_id: str = ""


@app.get("/api/chat/status")
def chat_status():
    """返回虚拟人当前对话后端(本地大模型 / 云端 / 内置知识库降级)。"""
    return {
        "llm_enabled": chatbot.is_llm_enabled(),
        "provider": chatbot.active_provider(),
        "azure_tts": tts.is_enabled(),
    }


class TtsRequest(BaseModel):
    text: str


@app.post("/api/tts")
def api_tts(req: TtsRequest):
    """用 Azure 语音合成把文本转成 MP3;未配置或失败返回 503,前端回退浏览器 TTS。"""
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本为空")
    if not tts.is_enabled():
        raise HTTPException(status_code=503, detail="Azure 语音未配置")
    try:
        audio = tts.synthesize(text[:1500])
    except Exception:
        raise HTTPException(status_code=502, detail="语音合成失败")
    return Response(content=audio, media_type="audio/mpeg")


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    """虚拟金融顾问对话,SSE 流式返回,并将对话存入数据库。"""
    session_id = req.session_id or uuid.uuid4().hex[:16]
    if req.message:
        storage.save_chat_message(session_id, "user", req.message)

    def event_stream():
        # 先把会话ID发给前端,便于持久化
        yield f"data: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"
        parts = []
        for chunk in chatbot.stream_reply(req.message, req.history):
            parts.append(chunk)
            yield f"data: {json.dumps({'delta': chunk}, ensure_ascii=False)}\n\n"
        full = "".join(parts)
        if full:
            storage.save_chat_message(session_id, "assistant", full)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/chat/sessions")
def chat_sessions():
    """返回所有历史会话摘要。"""
    return storage.list_chat_sessions()


@app.get("/api/chat/history/{session_id}")
def chat_history(session_id: str):
    """返回指定会话的完整对话记录。"""
    return storage.get_chat_history(session_id)


@app.delete("/api/chat/history/{session_id}")
def delete_chat_history(session_id: str):
    """删除指定会话的对话记录。"""
    deleted = storage.delete_chat_session(session_id)
    return {"deleted": deleted}


@app.post("/api/applications")
def create_application(payload: ApplicationCreate):
    """保存一条申请记录(自动跑一次推荐并存档结果)。"""
    profile_dict = payload.profile.model_dump(mode="json")
    result = recommend(payload.profile).model_dump(mode="json")
    return storage.create_application(profile_dict, result)


@app.get("/api/applications")
def list_applications():
    """获取全部申请记录列表。"""
    return storage.list_applications()


@app.get("/api/applications-summary/pdf")
def applications_summary_pdf():
    """导出全部申请记录的进度汇总报表 PDF。"""
    from records_summary import build_records_summary
    from hidden_subsidies import HIDDEN_SUBSIDIES
    records = storage.list_applications()
    hidden = [{k: v for k, v in s.items() if k != "keywords"} for s in HIDDEN_SUBSIDIES]
    pdf_bytes = build_records_summary(records, hidden)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="applications_summary.pdf"'},
    )


@app.get("/api/applications/{app_id}")
def get_application(app_id: str):
    """获取单条申请记录详情(含企业信息与方案结果)。"""
    rec = storage.get_application(app_id)
    if not rec:
        raise HTTPException(status_code=404, detail="申请记录不存在")
    return rec


@app.patch("/api/applications/{app_id}/status")
def update_application_status(app_id: str, payload: StatusUpdate):
    """更新申请记录状态。被拒时可记录原因,用于迭代优化匹配模型。"""
    rec = storage.update_status(app_id, payload.status, payload.reject_reason)
    if not rec:
        raise HTTPException(status_code=400, detail="记录不存在或状态非法")
    return rec


@app.get("/api/applications-insights")
def applications_insights():
    """汇总被拒原因并给出迭代优化建议(学习型工具核心)。"""
    return storage.reject_insights()


@app.get("/api/data-assets")
def data_assets():
    """独家私有数据集看板:真实审批样本、贴息案例、行业分布与数据壁垒指数。"""
    return storage.data_assets()


@app.post("/api/leads")
def create_lead(payload: dict):
    """提交预约/咨询线索入库,客户经理后台可见。"""
    phone = (payload.get("phone") or "").strip()
    if not (phone.isdigit() and len(phone) == 11 and phone.startswith("1")):
        raise HTTPException(status_code=400, detail="请填写正确的11位手机号")
    return storage.create_lead(payload)


@app.get("/api/leads")
def list_leads(request: Request):
    """客户经理后台:查看全部预约/咨询线索(含手机号,需管理口令)。"""
    require_admin(request)
    return storage.list_leads()


@app.post("/api/track")
async def track_event(request: Request):
    """接收前端埋点事件(公开,轻量,失败静默)。"""
    try:
        payload = await request.json()
    except Exception:
        return {"ok": False}
    ok = storage.record_event(
        session_id=str(payload.get("sid", "")),
        name=str(payload.get("name", "")),
        props=payload.get("props"),
        page=str(payload.get("page", "")),
    )
    return {"ok": ok}


@app.get("/api/admin/analytics")
def admin_analytics(request: Request, days: int = 30):
    """管理后台:产品使用数据分析(转化漏斗、功能使用、趋势)。"""
    require_admin(request)
    return storage.analytics_summary(days=max(1, min(365, days)))


@app.post("/api/admin/analytics/seed-demo")
def admin_seed_demo(request: Request):
    """管理后台:一键生成演示用埋点数据(仅供答辩演示,可一键清除)。"""
    require_admin(request)
    return storage.seed_demo_events()


@app.post("/api/admin/analytics/clear-demo")
def admin_clear_demo(request: Request):
    """管理后台:清除所有演示埋点数据。"""
    require_admin(request)
    return storage.clear_demo_events()


@app.get("/api/admin/overview")
def admin_overview(request: Request):
    """管理后台总览:申请、线索、数据资产统计汇总。"""
    require_admin(request)
    apps = storage.list_applications()
    leads = storage.list_leads()
    return {
        "applications": apps,
        "leads": leads,
        "assets": storage.data_assets(),
        "insights": storage.reject_insights(),
        "counts": {
            "applications": len(apps),
            "leads": len(leads),
            "bookings": sum(1 for l in leads if l.get("kind") == "预约"),
        },
    }


@app.delete("/api/applications/{app_id}")
def delete_application(app_id: str):
    """删除一条申请记录。"""
    if not storage.delete_application(app_id):
        raise HTTPException(status_code=404, detail="申请记录不存在")
    return {"deleted": True}


@app.post("/api/applications/{app_id}/pdf")
def application_pdf(app_id: str):
    """根据已保存的申请记录生成 PDF。"""
    rec = storage.get_application(app_id)
    if not rec:
        raise HTTPException(status_code=404, detail="申请记录不存在")
    profile = EnterpriseProfile(**rec["profile"])
    result = recommend(profile)
    pdf_bytes = build_pdf(profile, result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="loan_plan.pdf"'},
    )


@app.post("/api/applications/{app_id}/excel")
def application_excel(app_id: str):
    """根据已保存的申请记录生成 Excel。"""
    rec = storage.get_application(app_id)
    if not rec:
        raise HTTPException(status_code=404, detail="申请记录不存在")
    profile = EnterpriseProfile(**rec["profile"])
    result = recommend(profile)
    xlsx_bytes = build_excel(profile, result)
    return Response(
        content=xlsx_bytes,
        media_type=XLSX_MIME,
        headers={"Content-Disposition": 'attachment; filename="loan_plan.xlsx"'},
    )


# ------------------------- 金融知识闯关游戏 -------------------------
class QuizAnswer(BaseModel):
    player_id: str
    question_id: str
    choice: int
    streak: int = 0


class QuizNickname(BaseModel):
    player_id: str
    nickname: str


@app.get("/api/quiz/levels")
def quiz_levels():
    """返回所有关卡及题量。"""
    return quiz.list_levels()


@app.get("/api/quiz/courses")
def quiz_courses():
    """返回体系化课程列表及题量。"""
    return quiz.list_courses()


@app.get("/api/quiz/questions")
def quiz_questions(level: int = 0, count: int = 5, course: str = ""):
    """抽取题目(不含答案)。level=0 表示跨关卡混合;course 指定课程。"""
    lv = level if level and level > 0 else None
    return quiz.get_questions(level=lv, count=count, course=course or None)


@app.get("/api/quiz/progress/{player_id}")
def quiz_progress(player_id: str):
    """获取玩家的金币、等级、正确率等进度。"""
    return storage.get_quiz_progress(player_id)


@app.post("/api/quiz/answer")
def quiz_answer(payload: QuizAnswer):
    """提交答案:服务端校验,返回对错、解析与最新进度。"""
    result = quiz.check_answer(payload.question_id, payload.choice)
    if result is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    streak = payload.streak + 1 if result["correct"] else 0
    progress = storage.record_quiz_answer(
        payload.player_id, result["correct"], result["coins"], streak
    )
    return {**result, "streak": streak, "progress": progress}


@app.post("/api/quiz/nickname")
def quiz_nickname(payload: QuizNickname):
    """设置玩家昵称(用于排行榜)。"""
    return storage.set_quiz_nickname(payload.player_id, payload.nickname)


@app.get("/api/quiz/leaderboard")
def quiz_leaderboard(limit: int = 10):
    """金币排行榜。"""
    return storage.quiz_leaderboard(limit)


# 提供前端静态页面
if os.path.isdir(FRONTEND_DIR):
    import re as _re

    def _asset_ver(fname: str) -> str:
        try:
            return str(int(os.path.getmtime(os.path.join(FRONTEND_DIR, fname))))
        except OSError:
            return "0"

    @app.get("/")
    def index():
        with open(os.path.join(FRONTEND_DIR, "index.html"), encoding="utf-8") as f:
            html = f.read()
        html = _re.sub(r"style\.css\?v=[\w]+", f"style.css?v={_asset_ver('style.css')}", html)
        html = _re.sub(r"app\.js\?v=[\w]+", f"app.js?v={_asset_ver('app.js')}", html)
        html = _re.sub(r"avatars\.js\?v=[\w]+", f"avatars.js?v={_asset_ver('avatars.js')}", html)
        return Response(content=html, media_type="text/html")

    @app.get("/admin")
    def admin_page():
        return FileResponse(
            os.path.join(FRONTEND_DIR, "admin.html"),
            media_type="text/html",
        )

    @app.get("/legal")
    def legal_page():
        return FileResponse(
            os.path.join(FRONTEND_DIR, "legal.html"),
            media_type="text/html",
        )

    @app.get("/sw.js")
    def service_worker():
        """Service Worker 必须从根路径提供,才能控制整个站点。"""
        return FileResponse(
            os.path.join(FRONTEND_DIR, "sw.js"),
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
        )

    @app.get("/manifest.webmanifest")
    def manifest():
        return FileResponse(
            os.path.join(FRONTEND_DIR, "manifest.webmanifest"),
            media_type="application/manifest+json",
        )

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
