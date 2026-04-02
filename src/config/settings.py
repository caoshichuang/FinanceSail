"""
配置管理模块
使用Pydantic管理所有配置项
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    # 项目路径
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    IMAGE_DIR: Path = DATA_DIR / "images"
    LOG_DIR: Path = PROJECT_ROOT / "logs"
    DB_PATH: Path = DATA_DIR / "db.sqlite3"

    # DeepSeek AI
    DEEPSEEK_API_KEY: Optional[str] = Field(
        default=None, description="DeepSeek API密钥"
    )
    DEEPSEEK_BASE_URL: str = Field(
        default="https://api.deepseek.com", description="DeepSeek API地址"
    )
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", description="使用的模型")

    # Tushare
    TUSHARE_TOKEN: Optional[str] = Field(default=None, description="Tushare API Token")

    # QQ邮箱
    QQ_EMAIL: Optional[str] = Field(default=None, description="发件人QQ邮箱")
    QQ_EMAIL_AUTH_CODE: Optional[str] = Field(default=None, description="QQ邮箱授权码")
    RECEIVER_EMAIL: Optional[str] = Field(default=None, description="收件人邮箱")

    # SMTP配置
    SMTP_SERVER: str = Field(default="smtp.qq.com", description="SMTP服务器")
    SMTP_PORT: int = Field(default=465, description="SMTP端口")

    # 应用配置
    BASE_URL: str = Field(
        default="http://139.224.40.205:8080", description="应用访问地址"
    )

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_ROTATION: str = Field(default="10 MB", description="日志轮转大小")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留时间")

    # 明星股列表（默认值，会被动态配置覆盖）
    A_SHARE_STAR_STOCKS: list = Field(
        default=[
            {"code": "600519", "name": "贵州茅台"},
            {"code": "300750", "name": "宁德时代"},
            {"code": "002594", "name": "比亚迪"},
            {"code": "601318", "name": "中国平安"},
            {"code": "000858", "name": "五粮液"},
            {"code": "600036", "name": "招商银行"},
            {"code": "000333", "name": "美的集团"},
            {"code": "601888", "name": "中国中免"},
        ],
        description="A股明星股列表",
    )

    HK_STAR_STOCKS: list = Field(
        default=[
            {"code": "00700", "name": "腾讯控股"},
            {"code": "09988", "name": "阿里巴巴"},
            {"code": "03690", "name": "美团"},
            {"code": "01810", "name": "小米集团"},
            {"code": "09618", "name": "京东集团"},
            {"code": "09888", "name": "百度集团"},
        ],
        description="港股明星股列表",
    )

    US_STAR_STOCKS: list = Field(
        default=[
            {"code": "AAPL", "name": "苹果"},
            {"code": "MSFT", "name": "微软"},
            {"code": "NVDA", "name": "英伟达"},
            {"code": "TSLA", "name": "特斯拉"},
            {"code": "GOOGL", "name": "谷歌"},
            {"code": "AMZN", "name": "亚马逊"},
            {"code": "META", "name": "Meta"},
        ],
        description="美股明星股列表",
    )

    # 涨跌阈值
    HOT_STOCK_THRESHOLD: float = Field(default=3.0, description="热点股票涨跌阈值（%）")
    LIMIT_UP_DOWN_THRESHOLD: float = Field(default=9.9, description="涨跌停阈值（%）")

    # 定时任务时间
    US_STOCK_TIME: str = Field(default="09:00", description="美股总结时间")
    A_SHARE_TIME: str = Field(default="17:00", description="A股港股总结时间")
    HOT_STOCK_TIME: str = Field(default="17:30", description="热点个股时间")
    IPO_TIME: str = Field(default="20:00", description="IPO分析时间")

    # ==================== Phase 8: 新增配置项 ====================

    # LiteLLM 多模型配置
    OPENAI_API_KEY: Optional[str] = Field(
        default=None, description="OpenAI API Key（备用模型）"
    )
    OPENAI_BASE_URL: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API 地址"
    )
    LITELLM_FALLBACK_MODEL: str = Field(
        default="openai/gpt-4o-mini", description="LiteLLM Fallback 模型"
    )
    LITELLM_ROUTING_STRATEGY: str = Field(
        default="simple-shuffle", description="LiteLLM 路由策略"
    )

    # 多渠道通知配置
    WECHAT_WEBHOOK_URL: Optional[str] = Field(
        default=None, description="企业微信 Webhook URL"
    )
    FEISHU_WEBHOOK_URL: Optional[str] = Field(
        default=None, description="飞书 Webhook URL"
    )
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default=None, description="Telegram Bot Token"
    )
    TELEGRAM_CHAT_ID: Optional[str] = Field(
        default=None, description="Telegram Chat ID"
    )
    EMAIL_SENDER: Optional[str] = Field(
        default=None, description="发件人邮箱（EMAIL_SENDER 或 QQ_EMAIL 二选一）"
    )
    EMAIL_PASSWORD: Optional[str] = Field(
        default=None, description="发件人邮箱密码/授权码"
    )
    EMAIL_RECEIVERS: Optional[str] = Field(
        default=None, description="收件人（逗号分隔多个）"
    )
    PUSHPLUS_TOKEN: Optional[str] = Field(default=None, description="PushPlus Token")
    PUSHPLUS_TOPIC: Optional[str] = Field(
        default=None, description="PushPlus 群组主题（可选）"
    )

    # 交易策略配置
    STRATEGIES_DIR: str = Field(default="strategies", description="策略 YAML 文件目录")
    ACTIVE_STRATEGIES: str = Field(
        default="bull_trend", description="激活的策略名称（逗号分隔）"
    )

    # 交易日历配置
    TRADING_CALENDAR_CN: str = Field(
        default="XSHG", description="A股日历 exchange-calendars 代码"
    )
    TRADING_CALENDAR_US: str = Field(
        default="XNYS", description="美股日历 exchange-calendars 代码"
    )
    TRADING_CALENDAR_HK: str = Field(
        default="XHKG", description="港股日历 exchange-calendars 代码"
    )

    # 报告渲染配置
    REPORT_LANGUAGE: str = Field(default="zh", description="报告语言（zh / en）")
    REPORT_TYPE: str = Field(
        default="full", description="报告类型（simple / full / brief）"
    )
    REPORT_SUMMARY_ONLY: bool = Field(default=False, description="仅输出摘要")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def ensure_dirs(self):
        """确保必要目录存在"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _load_dynamic_config(self) -> Dict[str, Any]:
        """加载动态配置文件"""
        dynamic_config_path = self.PROJECT_ROOT / "config" / "dynamic_config.json"
        try:
            if dynamic_config_path.exists():
                with open(dynamic_config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载动态配置失败: {e}")
        return {}

    def load_dynamic_config(self):
        """加载动态配置并更新设置"""
        dynamic_config = self._load_dynamic_config()

        # 更新明星股配置
        if "star_stocks" in dynamic_config:
            star_stocks = dynamic_config["star_stocks"]
            if "A股" in star_stocks:
                self.A_SHARE_STAR_STOCKS = star_stocks["A股"]
            if "港股" in star_stocks:
                self.HK_STAR_STOCKS = star_stocks["港股"]
            if "美股" in star_stocks:
                self.US_STAR_STOCKS = star_stocks["美股"]

        # 更新阈值配置
        if "thresholds" in dynamic_config:
            thresholds = dynamic_config["thresholds"]
            if "hot_stock_threshold" in thresholds:
                self.HOT_STOCK_THRESHOLD = thresholds["hot_stock_threshold"]
            if "limit_up_down_threshold" in thresholds:
                self.LIMIT_UP_DOWN_THRESHOLD = thresholds["limit_up_down_threshold"]

        # 更新定时任务时间
        if "scheduler" in dynamic_config:
            scheduler = dynamic_config["scheduler"]
            if "us_stock_time" in scheduler:
                self.US_STOCK_TIME = scheduler["us_stock_time"]
            if "a_share_time" in scheduler:
                self.A_SHARE_TIME = scheduler["a_share_time"]
            if "hot_stock_time" in scheduler:
                self.HOT_STOCK_TIME = scheduler["hot_stock_time"]
            if "ipo_time" in scheduler:
                self.IPO_TIME = scheduler["ipo_time"]


# 全局配置实例
settings = Settings()
settings.ensure_dirs()
settings.load_dynamic_config()
