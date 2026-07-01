"""结构化地区树:省 → 市 → 区县/园区,覆盖全国 34 个省级行政区。

数据来源于国家标准行政区划(省/市/区县完整列表),并为部分城市附加了
「独家园区/新区」选项(如张江科学城、天府新区、松山湖),选到具体园区可
解锁独家贴息;其余命中省级通用兜底。数据文件为 region_tree.json,可持续维护。
"""
import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "region_tree.json")

with open(_DATA_PATH, "r", encoding="utf-8") as _f:
    REGION_TREE = json.load(_f)
