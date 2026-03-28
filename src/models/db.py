"""
数据库模型模块
"""

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config.settings import settings

Base = declarative_base()
engine = create_engine(f"sqlite:///{settings.DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)


class Content(Base):
    """内容记录表"""

    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market = Column(String(20), nullable=False)  # A股/美股/港股
    content_type = Column(String(50), nullable=False)  # summary/ipo/hot_stock
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(500))
    status = Column(String(20), default="generated")  # generated/sent/published/failed
    image_paths = Column(Text)  # JSON格式的图片路径列表
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Subscription(Base):
    """个股订阅表（预留）"""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(50), nullable=False)
    market = Column(String(20), nullable=False)  # A股/港股/美股
    rules = Column(Text)  # JSON格式的订阅规则
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class User(Base):
    """用户表（预留）"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    contact = Column(String(100), nullable=False)  # 微信/邮箱
    contact_type = Column(String(20), nullable=False)  # wechat/email
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class StockEvent(Base):
    """股票事件表（预留）"""

    __tablename__ = "stock_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(50), nullable=False)
    market = Column(String(20), nullable=False)
    event_type = Column(String(50), nullable=False)  # change/announce/earning/dividend
    event_data = Column(Text)  # JSON格式的事件数据
    change_pct = Column(Float)  # 涨跌幅
    created_at = Column(DateTime, default=datetime.now)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(engine)


def get_session():
    """获取数据库会话"""
    return Session()
