"""贷款产品库。

每个产品包含准入条件、利率区间、额度规则等。真实场景可替换为数据库或对接银行 API。
所有金额单位为万元,利率为年化。
"""

# provider_type: 国有银行 / 股份制银行 / 城商行 / 政策性/普惠 / 互联网银行 / 小额贷款公司

PRODUCTS = [
    {
        "id": "puhui-credit",
        "name": "普惠小微信用贷",
        "provider_type": "政策性/普惠",
        "requires_collateral": False,
        "min_years": 1.0,
        "min_annual_revenue": 50,        # 万元
        "max_amount": 300,               # 万元
        "base_amount_ratio": 0.30,       # 可贷额度 ≈ 年营业额 * 比例
        "annual_rate_min": 3.45,
        "annual_rate_max": 5.5,
        "max_term_months": 36,
        "min_credit": "good",            # 至少需要 good
        "need_tax_or_invoice": True,
        "release_days": "3-7 个工作日",
        "highlights": "国家普惠政策贴息,利率低,纯信用无需抵押",
        "subsidy_linked": True,
        "hidden_criteria": "支行隐性门槛:法人本地社保连续满 6 个月,户均纳税额≥3 万;季末额度紧张时优先批小微首贷户",
        "local_approval_rate": 93,
    },
    {
        "id": "online-bank-flow",
        "name": "互联网银行流水贷",
        "provider_type": "互联网银行",
        "requires_collateral": False,
        "min_years": 0.5,
        "min_annual_revenue": 20,
        "max_amount": 100,
        "base_amount_ratio": 0.20,
        "annual_rate_min": 7.2,
        "annual_rate_max": 14.4,
        "max_term_months": 24,
        "min_credit": "fair",
        "need_tax_or_invoice": False,
        "release_days": "当天-2 个工作日",
        "highlights": "线上审批,放款快,门槛低,适合急用与初创",
        "hidden_criteria": "实测准入:近 6 个月日均流水≥2 万更易批;法人手机号实名满 1 年,无多头借贷(近 1 月查询≤3 次)",
        "local_approval_rate": 88,
    },
    {
        "id": "tax-credit-loan",
        "name": "银税互动信用贷",
        "provider_type": "股份制银行",
        "requires_collateral": False,
        "min_years": 2.0,
        "min_annual_revenue": 100,
        "max_amount": 500,
        "base_amount_ratio": 0.35,
        "annual_rate_min": 4.0,
        "annual_rate_max": 7.0,
        "max_term_months": 36,
        "min_credit": "good",
        "need_tax_or_invoice": True,
        "need_tax_strict": True,         # 必须有连续纳税记录
        "release_days": "5-10 个工作日",
        "highlights": "以纳税信用换贷款额度,纳税越规范额度越高",
        "hidden_criteria": "支行偏好:纳税信用 B 级以上、近 2 年无欠税;法人征信查询近 3 月≤4 次,优先批制造/批发零售",
        "local_approval_rate": 81,
    },
    {
        "id": "mortgage-biz-loan",
        "name": "抵押经营贷",
        "provider_type": "国有银行",
        "requires_collateral": True,
        "min_years": 1.0,
        "min_annual_revenue": 50,
        "max_amount": 2000,
        "base_amount_ratio": 0.50,       # 信用部分参考
        "collateral_ratio": 0.7,         # 抵押物估值 * 比例
        "annual_rate_min": 3.2,
        "annual_rate_max": 5.0,
        "max_term_months": 120,
        "min_credit": "fair",
        "need_tax_or_invoice": False,
        "release_days": "10-20 个工作日",
        "highlights": "有抵押物可获大额低息,期限长,适合扩产与设备投入",
        "hidden_criteria": "支行隐性条件:抵押房龄≤25 年、所在城区核心地段;评估按市价 7 折,首贷需法人到场面签,郊区/厂房放款偏慢",
        "local_approval_rate": 76,
    },
    {
        "id": "equipment-loan",
        "name": "设备分期/融资租赁",
        "provider_type": "城商行",
        "requires_collateral": False,    # 设备本身作为标的
        "min_years": 1.0,
        "min_annual_revenue": 80,
        "max_amount": 800,
        "base_amount_ratio": 0.40,
        "annual_rate_min": 5.0,
        "annual_rate_max": 8.5,
        "max_term_months": 60,
        "min_credit": "good",
        "need_tax_or_invoice": False,
        "purpose_fit": ["equipment", "expansion"],
        "release_days": "7-15 个工作日",
        "highlights": "专为设备采购设计,以设备为标的,首付低、期限长",
        "hidden_criteria": "实测准入:设备需正规厂商发票、可登记;首付通常 2-3 成,二手/进口设备审批趋严,优先批新增产能项目",
        "local_approval_rate": 79,
    },
    {
        "id": "micro-loan-company",
        "name": "小贷公司应急周转贷",
        "provider_type": "小额贷款公司",
        "requires_collateral": False,
        "min_years": 0.0,
        "min_annual_revenue": 0,
        "max_amount": 50,
        "base_amount_ratio": 0.15,
        "annual_rate_min": 12.0,
        "annual_rate_max": 23.0,
        "max_term_months": 12,
        "min_credit": "poor",
        "need_tax_or_invoice": False,
        "release_days": "当天-1 个工作日",
        "highlights": "门槛最低、放款最快,但利率高,仅建议短期应急",
        "hidden_criteria": "几乎无隐性门槛,但综合费率高;放款看流水真实性,频繁续贷会被风控,仅建议 3 个月内周转",
        "local_approval_rate": 95,
    },
]

CREDIT_RANK = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}
