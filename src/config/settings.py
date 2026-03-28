"""
配置管理模块
使用Pydantic管理所有配置项
"""

from pathlib import Path
from typing import Optional
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
    DEEPSEEK_API_KEY: str = Field(..., description="DeepSeek API密钥")
    DEEPSEEK_BASE_URL: str = Field(
        default="https://api.deepseek.com", description="DeepSeek API地址"
    )
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", description="使用的模型")

    # Tushare
    TUSHARE_TOKEN: str = Field(..., description="Tushare API Token")

    # QQ邮箱
    QQ_EMAIL: str = Field(..., description="发件人QQ邮箱")
    QQ_EMAIL_AUTH_CODE: str = Field(..., description="QQ邮箱授权码")
    RECEIVER_EMAIL: str = Field(..., description="收件人邮箱")

    # SMTP配置
    SMTP_SERVER: str = Field(default="smtp.qq.com", description="SMTP服务器")
    SMTP_PORT: int = Field(default=465, description="SMTP端口")

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_ROTATION: str = Field(default="10 MB", description="日志轮转大小")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留时间")

    # 明星股列表
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def ensure_dirs(self):
        """确保必要目录存在"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()
settings.ensure_dirs()
