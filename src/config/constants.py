"""
常量定义模块
"""


# 市场类型
class MarketType:
    A_SHARE = "A股"
    HK_STOCK = "港股"
    US_STOCK = "美股"


# 内容类型
class ContentType:
    SUMMARY = "市场总结"
    IPO = "IPO分析"
    HOT_STOCK = "热点个股"
    STAR_STOCK = "明星股"


# 内容状态
class ContentStatus:
    GENERATED = "generated"
    SENT = "sent"
    PUBLISHED = "published"
    FAILED = "failed"


# A股指数
class AShareIndex:
    SHANGHAI_COMPOSITE = "上证指数"
    SHENZHEN_COMPONENT = "深证成指"
    CHINEXT = "创业板指"


# 港股指数
class HKIndex:
    HANG_SENG = "恒生指数"
    HANG_SENG_TECH = "恒生科技指数"


# 美股指数
class USIndex:
    NASDAQ = "纳斯达克指数"
    SP500 = "标普500"
    DOW_JONES = "道琼斯指数"


# 数据源优先级
DATA_SOURCE_PRIORITY = {
    "A股": ["akshare", "tushare"],
    "港股": ["akshare"],
    "美股": ["akshare"],
}

# 免责声明
DISCLAIMER = """
⚠️ 免责声明
本文仅为市场数据整理和信息分享，不构成任何投资建议。
数据来源：AKShare、东方财富、新浪财经
AI辅助创作，请谨慎参考。
股市有风险，投资需谨慎，请以官方信息为准。
"""

# 邮件模板
EMAIL_SUBJECT_TEMPLATE = {
    "美股": "[美股] {date}｜{title}",
    "A股": "[A股港股] {date}｜{title}",
    "IPO": "[新股] {title}",
    "热点": "[热点] {title}",
}
