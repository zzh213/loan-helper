"""请求与响应数据模型。"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CreditLevel(str, Enum):
    excellent = "excellent"  # 优秀:无逾期,征信良好
    good = "good"            # 良好:偶有轻微逾期
    fair = "fair"            # 一般:有少量逾期记录
    poor = "poor"            # 较差:存在较多逾期或当前逾期


class LoanPurpose(str, Enum):
    working_capital = "working_capital"  # 流动资金周转
    equipment = "equipment"              # 设备采购
    expansion = "expansion"              # 扩大经营
    inventory = "inventory"              # 备货采购
    rd = "rd"                            # 研发投入
    other = "other"                      # 其他


class EnterpriseProfile(BaseModel):
    """企业实际情况。"""

    company_name: Optional[str] = Field(default="", description="企业名称")
    industry: str = Field(description="所属行业,如 制造业/批发零售/餐饮/科技/建筑/物流/农业/服务业")
    industry_detail: Optional[str] = Field(default="", description="用户填写的具体/自定义行业描述,展示与留存用")
    years_in_business: float = Field(ge=0, description="经营年限(年)")
    annual_revenue: float = Field(ge=0, description="年营业额(万元)")
    registered_capital: float = Field(default=0, ge=0, description="注册资本(万元)")
    employees: int = Field(default=0, ge=0, description="员工人数")

    credit_level: CreditLevel = Field(description="企业/法人征信状况")
    has_overdue: bool = Field(default=False, description="当前是否存在逾期")

    has_collateral: bool = Field(default=False, description="是否有可抵押资产(房产/设备等)")
    collateral_value: float = Field(default=0, ge=0, description="抵押物估值(万元)")
    has_tax_record: bool = Field(default=False, description="是否有连续纳税记录")
    has_invoice: bool = Field(default=False, description="是否有稳定开票流水")

    loan_amount: float = Field(gt=0, description="期望贷款金额(万元)")
    loan_purpose: LoanPurpose = Field(description="贷款用途")
    preferred_term_months: int = Field(default=12, ge=1, description="期望贷款期限(月)")
    urgent: bool = Field(default=False, description="是否急需放款")
    industry_bonus: List[str] = Field(default_factory=list, description="已具备的行业专属增信项,如餐饮的外卖平台流水")


class OccupationType(str, Enum):
    salaried = "salaried"            # 上班族(企业职工)
    civil_servant = "civil_servant"  # 公务员 / 事业编
    self_employed = "self_employed"  # 个体工商户 / 小微业主
    freelancer = "freelancer"        # 自由职业 / 灵活就业
    professional = "professional"    # 医生/律师/教师等专业人士
    retired = "retired"              # 退休
    student = "student"              # 学生


class PersonalLoanPurpose(str, Enum):
    consumption = "consumption"      # 日常消费
    decoration = "decoration"        # 装修
    car = "car"                      # 购车
    education = "education"          # 教育
    medical = "medical"              # 医疗
    marriage = "marriage"            # 婚庆
    travel = "travel"                # 旅游
    turnover = "turnover"            # 资金周转
    startup = "startup"              # 创业 / 个体经营
    debt_optimize = "debt_optimize"  # 债务优化 / 以低息换高息


class PersonalProfile(BaseModel):
    """个人借款人实际情况。金额单位:万元;收入单位:元/月。"""

    name: Optional[str] = Field(default="", description="姓名(选填)")
    age: int = Field(default=30, ge=18, le=70, description="年龄")
    occupation_type: OccupationType = Field(description="职业身份")
    occupation_detail: Optional[str] = Field(default="", description="具体职业描述,选填")

    monthly_income: float = Field(ge=0, description="税后月收入(元/月)")
    income_type: str = Field(default="salary", description="收入形式:salary 打卡工资 / cash 现金或混合 / business 经营流水")
    work_years: float = Field(default=1, ge=0, description="现单位/当前职业持续年限(年)")

    has_social_security: bool = Field(default=False, description="是否连续缴纳社保")
    has_housing_fund: bool = Field(default=False, description="是否连续缴存公积金")
    housing_fund_monthly: float = Field(default=0, ge=0, description="公积金月缴存额(元)")

    has_house: bool = Field(default=False, description="是否有自有房产")
    house_value: float = Field(default=0, ge=0, description="房产估值(万元)")
    has_car: bool = Field(default=False, description="是否有自有车辆")
    car_value: float = Field(default=0, ge=0, description="车辆估值(万元)")
    has_insurance_policy: bool = Field(default=False, description="是否持有寿险/年金保单")

    credit_level: CreditLevel = Field(description="个人征信状况")
    has_overdue: bool = Field(default=False, description="当前是否存在逾期")
    monthly_debt_payment: float = Field(default=0, ge=0, description="名下现有月还款额(房贷/车贷/信用卡等,元/月)")

    is_entrepreneur: bool = Field(default=False, description="是否在创业或经营个体工商户")
    special_identity: List[str] = Field(default_factory=list, description="特殊身份:高校毕业生/退役军人/返乡农民工等,解锁专项政策")

    loan_amount: float = Field(gt=0, description="期望贷款金额(万元)")
    loan_purpose: PersonalLoanPurpose = Field(description="贷款用途")
    preferred_term_months: int = Field(default=12, ge=1, description="期望贷款期限(月)")
    urgent: bool = Field(default=False, description="是否急需放款")


class RecommendedPlan(BaseModel):
    product_id: str
    product_name: str
    provider_type: str
    score: int
    approval_probability: str
    estimated_amount: float
    annual_rate_min: float
    annual_rate_max: float
    suggested_term_months: int
    monthly_payment_estimate: float
    total_interest_estimate: float
    requires_collateral: bool
    expected_release_days: str
    match_reasons: List[str]
    cautions: List[str]
    hidden_criteria: str = ""
    local_approval_rate: int = 0
    subsidy_linked: bool = False


class PlanTier(BaseModel):
    key: str          # steady / sprint / subsidy
    name: str         # 稳妥方案 / 冲刺方案 / 贴息最优方案
    tagline: str      # 一句话定位
    product_id: str
    product_name: str
    headline: str     # 核心卖点数字
    reason: str       # 推荐理由
    risk_note: str = ""
    after_subsidy: str = ""   # 贴息后真实年化与月省提示


class RiskFactorModel(BaseModel):
    name: str
    impact: str  # positive / negative / neutral
    detail: str


class ScorecardDimension(BaseModel):
    key: str
    name: str
    score: int
    max: int
    level: str   # good / mid / weak
    reason: str
    advice: str = ""


class WeakPoint(BaseModel):
    name: str
    lost: int
    reason: str
    advice: str = ""


class RiskAssessment(BaseModel):
    score: int
    grade: str
    grade_label: str
    debt_ratio: Optional[float] = None
    industry_coefficient: float = 1.0
    scorecard: List[ScorecardDimension] = []
    bonus_add: int = 0
    weak_points: List[WeakPoint] = []
    factors: List[RiskFactorModel] = []


class SubsidyPolicy(BaseModel):
    id: str
    name: str
    category: str
    authority: str
    benefit: str
    apply_points: str
    apply_window: str = "常年可申报"
    updated: str = "2026-06"


class RecommendResponse(BaseModel):
    summary: str
    profile_highlights: List[str]
    risk: RiskAssessment
    improvement_tips: List[str]
    personalized_advice: List[str]
    subsidies: List[SubsidyPolicy]
    plans: List[RecommendedPlan]
    tiers: List[PlanTier] = []
    guarantee: Optional[dict] = None
    plain_language: Optional[dict] = None
    match_strategy: Optional[dict] = None
    risk_alerts: List[dict] = []


class ApplicationCreate(BaseModel):
    """保存申请记录的请求体。"""
    profile: EnterpriseProfile


class StatusUpdate(BaseModel):
    status: str
    reject_reason: str = ""
