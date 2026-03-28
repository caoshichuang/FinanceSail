# 技术设计文档

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      系统架构图                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────────┐                         │
│                    │  定时触发   │                         │
│                    │ APScheduler │                         │
│                    └──────┬──────┘                         │
│                           │                                 │
│                           ▼                                 │
│        ┌─────────────────────────────────────┐             │
│        │           数据采集层                 │             │
│        │  AKShare (主) + Tushare (备)        │             │
│        │  数据校验 + 异常处理                 │             │
│        └─────────────────────────────────────┘             │
│                           │                                 │
│                           ▼                                 │
│        ┌─────────────────────────────────────┐             │
│        │           AI生成层                  │             │
│        │  DeepSeek API                       │             │
│        │  标题/正文/标签生成                  │             │
│        │  内容校验 + 敏感词过滤              │             │
│        └─────────────────────────────────────┘             │
│                           │                                 │
│                           ▼                                 │
│        ┌─────────────────────────────────────┐             │
│        │          图片渲染层                 │             │
│        │  Playwright + HTML模板              │             │
│        │  封面图 + 字卡 + zip打包            │             │
│        └─────────────────────────────────────┘             │
│                           │                                 │
│                           ▼                                 │
│        ┌─────────────────────────────────────┐             │
│        │          数据存储层                 │             │
│        │  SQLite (数据) + 本地文件 (图片)    │             │
│        └─────────────────────────────────────┘             │
│                           │                                 │
│                           ▼                                 │
│        ┌─────────────────────────────────────┐             │
│        │          邮件通知层                 │             │
│        │  QQ邮箱 SMTP                        │             │
│        │  标题列表 + 文案 + 图片zip          │             │
│        └─────────────────────────────────────┘             │
│                           │                                 │
│                           ▼                                 │
│                    ┌─────────────┐                         │
│                    │  人工发布   │                         │
│                    └─────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
redbook-auto/
├── src/
│   ├── collectors/              # 数据采集模块
│   │   ├── __init__.py
│   │   ├── base.py              # 基类 + 重试装饰器
│   │   ├── a_share.py           # A股数据采集
│   │   ├── us_stock.py          # 美股数据采集
│   │   ├── hk_stock.py          # 港股数据采集
│   │   └── ipo.py               # IPO数据采集
│   │
│   ├── generators/              # 内容生成模块
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── prompts/             # Prompt模板
│   │   │   ├── __init__.py
│   │   │   ├── us_summary.py
│   │   │   ├── a_share_summary.py
│   │   │   ├── ipo_analysis.py
│   │   │   └── hot_stock.py
│   │   └── market_summary.py    # 市场总结生成器
│   │
│   ├── renderers/               # 图片渲染模块
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── cover.py             # 封面图渲染
│   │   ├── cards.py             # 字卡渲染
│   │   └── templates/           # HTML模板
│   │       ├── cover.html
│   │       ├── card.html
│   │       └── styles/
│   │
│   ├── notifiers/               # 通知模块
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── email.py             # QQ邮件发送
│   │
│   ├── scheduler/               # 定时任务
│   │   ├── __init__.py
│   │   └── jobs.py              # 任务定义
│   │
│   ├── config/                  # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py          # 配置加载
│   │   └── constants.py         # 常量定义
│   │
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py            # 日志配置
│   │   ├── retry.py             # 重试装饰器
│   │   ├── validator.py         # 数据校验
│   │   └── sanitizer.py         # 敏感词过滤
│   │
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   └── db.py                # SQLite模型
│   │
│   ├── exceptions/              # 自定义异常
│   │   ├── __init__.py
│   │   └── errors.py
│   │
│   └── main.py                  # 应用入口
│
├── templates/                   # HTML模板
├── data/                        # 数据存储
│   ├── db.sqlite3
│   └── images/
│
├── tests/                       # 测试
│   ├── collectors/
│   ├── generators/
│   └── renderers/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── config/
│   └── .env.example
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 核心模块设计

### 1. 数据采集模块 (collectors/)

#### 基类设计

```python
# base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..utils.retry import retry
from ..utils.logger import get_logger

class BaseCollector(ABC):
    """数据采集基类"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    @retry(max_retries=3, delay=1)
    async def collect(self, **kwargs) -> Dict[str, Any]:
        """采集数据（带重试）"""
        try:
            data = await self._fetch_data(**kwargs)
            self._validate_data(data)
            return data
        except Exception as e:
            self.logger.error(f"数据采集失败: {e}")
            raise
    
    @abstractmethod
    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        """获取数据（子类实现）"""
        pass
    
    def _validate_data(self, data: Dict[str, Any]):
        """校验数据"""
        if not data:
            raise ValueError("数据为空")
```

#### A股采集器

```python
# a_share.py
import akshare as ak
from .base import BaseCollector

class AShareCollector(BaseCollector):
    """A股数据采集器"""
    
    async def _fetch_data(self, **kwargs) -> Dict[str, Any]:
        # 获取大盘指数
        indices = self._get_indices()
        
        # 获取涨跌分布
        distribution = self._get_distribution()
        
        # 获取热点板块
        hot_sectors = self._get_hot_sectors()
        
        # 获取明星股数据
        star_stocks = self._get_star_stocks()
        
        # 获取资金流向
        capital_flow = self._get_capital_flow()
        
        return {
            "market": "A股",
            "indices": indices,
            "distribution": distribution,
            "hot_sectors": hot_sectors,
            "star_stocks": star_stocks,
            "capital_flow": capital_flow,
        }
    
    def _get_indices(self):
        """获取A股三大指数"""
        # 上证指数、深证成指、创业板指
        pass
    
    def _get_distribution(self):
        """获取涨跌分布"""
        pass
    
    def _get_hot_sectors(self):
        """获取热点板块TOP3"""
        pass
    
    def _get_star_stocks(self):
        """获取明星股数据"""
        star_list = [
            {"code": "600519", "name": "贵州茅台"},
            {"code": "300750", "name": "宁德时代"},
            {"code": "002594", "name": "比亚迪"},
            # ...
        ]
        pass
    
    def _get_capital_flow(self):
        """获取资金流向"""
        # 北向资金
        pass
```

### 2. 内容生成模块 (generators/)

#### 基类设计

```python
# base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import openai
from ..config.settings import settings
from ..utils.logger import get_logger

class BaseGenerator(ABC):
    """内容生成基类"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.client = openai.OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
    
    async def generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成内容"""
        titles = await self._generate_titles(data)
        content = await self._generate_content(data)
        tags = await self._generate_tags(data)
        
        return {
            "titles": titles,
            "content": content,
            "tags": tags,
        }
    
    @abstractmethod
    async def _generate_titles(self, data: Dict[str, Any]) -> List[str]:
        """生成标题（子类实现）"""
        pass
    
    @abstractmethod
    async def _generate_content(self, data: Dict[str, Any]) -> str:
        """生成正文（子类实现）"""
        pass
    
    async def _generate_tags(self, data: Dict[str, Any]) -> List[str]:
        """生成标签"""
        market = data.get("market", "")
        tags = ["#股票", "#投资理财"]
        
        if market == "A股":
            tags.extend(["#A股", "#股市分析"])
        elif market == "美股":
            tags.extend(["#美股", "#纳斯达克"])
        elif market == "港股":
            tags.extend(["#港股", "#恒生指数"])
        
        return tags
```

#### Prompt模板

```python
# prompts/us_summary.py

US_SUMMARY_PROMPT = """
你是一个专业的美股市场分析师，请根据以下数据生成小红书风格的美股收盘总结。

## 数据
{data}

## 要求
1. 生成3个吸引人的标题（15-25字）
2. 生成7张字卡的内容（Markdown格式）
3. 风格：专业但易懂，适合小红书用户
4. 每张字卡控制在100字以内
5. 最后必须包含免责声明

## 字卡结构
- 字卡1：今日大盘（三大指数表现）
- 字卡2：热门中概股表现
- 字卡3：美股明星股表现（苹果、英伟达、特斯拉等）
- 字卡4：重要事件/新闻
- 字卡5：市场情绪分析
- 字卡6：明日关注点
- 字卡7：免责声明

## 输出格式
```json
{
  "titles": ["标题1", "标题2", "标题3"],
  "cards": [
    "字卡1内容",
    "字卡2内容",
    ...
  ]
}
```
"""
```

### 3. 图片渲染模块 (renderers/)

```python
# cover.py
from playwright.async_api import async_playwright
from pathlib import Path
from typing import Dict, Any
from ..config.settings import settings
from ..utils.logger import get_logger

class CoverRenderer:
    """封面图渲染器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.template_dir = Path(__file__).parent / "templates"
    
    async def render(self, data: Dict[str, Any], output_path: Path) -> Path:
        """渲染封面图"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # 加载模板
            template_path = self.template_dir / "cover.html"
            await page.goto(f"file://{template_path.absolute()}")
            
            # 注入数据
            await page.evaluate(f"""
                document.title = '{data["title"]}';
                document.querySelector('.main-title').textContent = '{data["title"]}';
                document.querySelector('.sub-title').textContent = '{data["subtitle"]}';
                document.querySelector('.date').textContent = '{data["date"]}';
            """)
            
            # 截图
            await page.screenshot(
                path=str(output_path),
                type="png",
                clip={"x": 0, "y": 0, "width": 1080, "height": 1440}
            )
            
            await browser.close()
            
            return output_path
```

### 4. 邮件通知模块 (notifiers/)

```python
# email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Dict, Any
from ..config.settings import settings
from ..utils.logger import get_logger

class EmailNotifier:
    """QQ邮件通知器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.smtp_server = "smtp.qq.com"
        self.smtp_port = 465
        self.sender = settings.QQ_EMAIL
        self.password = settings.QQ_EMAIL_AUTH_CODE
    
    async def send(
        self,
        subject: str,
        titles: List[str],
        content: str,
        tags: List[str],
        attachments: List[Path] = None
    ):
        """发送邮件"""
        try:
            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = settings.RECEIVER_EMAIL
            msg["Subject"] = subject
            
            # 邮件正文
            body = self._build_body(titles, content, tags)
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # 发送
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            self.logger.info(f"邮件发送成功: {subject}")
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            raise
    
    def _build_body(self, titles: List[str], content: str, tags: List[str]) -> str:
        """构建邮件正文"""
        body = "📊 今日市场总结\n\n"
        
        # 标题选项
        body += "【标题选项】\n"
        for i, title in enumerate(titles, 1):
            body += f"{i}. {title}\n"
        
        body += "\n【完整文案】\n"
        body += "-" * 40 + "\n"
        body += content
        body += "\n" + "-" * 40 + "\n"
        
        # 标签
        body += "\n【标签】\n"
        body += " ".join(tags)
        
        return body
    
    def _attach_file(self, msg: MIMEMultipart, file_path: Path):
        """添加附件"""
        with open(file_path, "rb") as f:
            attachment = MIMEApplication(f.read())
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=file_path.name
            )
            msg.attach(attachment)
```

### 5. 定时任务模块 (scheduler/)

```python
# jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from ..collectors.us_stock import USStockCollector
from ..collectors.a_share import AShareCollector
from ..collectors.hk_stock import HKStockCollector
from ..generators.market_summary import MarketSummaryGenerator
from ..renderers.cover import CoverRenderer
from ..renderers.cards import CardsRenderer
from ..notifiers.email import EmailNotifier
from ..utils.logger import get_logger

logger = get_logger("scheduler")

async def us_stock_job():
    """美股总结任务"""
    try:
        logger.info("开始执行美股总结任务")
        
        # 1. 采集数据
        collector = USStockCollector()
        data = await collector.collect()
        
        # 2. 生成内容
        generator = MarketSummaryGenerator(market="美股")
        content = await generator.generate(data)
        
        # 3. 渲染图片
        cover_renderer = CoverRenderer()
        cards_renderer = CardsRenderer()
        
        # ... 渲染逻辑
        
        # 4. 发送邮件
        notifier = EmailNotifier()
        await notifier.send(
            subject=f"[美股] {data['date']}｜{content['titles'][0]}",
            titles=content["titles"],
            content=content["content"],
            tags=content["tags"],
            attachments=[...]  # 图片附件
        )
        
        logger.info("美股总结任务完成")
        
    except Exception as e:
        logger.error(f"美股总结任务失败: {e}")
        # 发送错误通知
        # ...

async def a_share_job():
    """A股+港股总结任务"""
    # 类似实现
    pass

def setup_scheduler():
    """设置定时任务"""
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    
    # 美股总结：每日09:00
    scheduler.add_job(
        us_stock_job,
        CronTrigger(hour=9, minute=0),
        id="us_stock_summary"
    )
    
    # A股+港股总结：每日17:00
    scheduler.add_job(
        a_share_job,
        CronTrigger(hour=17, minute=0),
        id="a_share_summary"
    )
    
    return scheduler
```

### 6. 数据库模型 (models/)

```python
# db.py
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config.settings import settings

Base = declarative_base()
engine = create_engine(f"sqlite:///{settings.DB_PATH}")
Session = sessionmaker(bind=engine)

class Content(Base):
    """内容记录表"""
    __tablename__ = "contents"
    
    id = Column(Integer, primary_key=True)
    market = Column(String(20))  # A股/美股/港股
    content_type = Column(String(50))  # summary/ipo/hot_stock
    title = Column(String(200))
    content = Column(Text)
    tags = Column(String(500))
    status = Column(String(20))  # generated/sent/published
    created_at = Column(DateTime, default=datetime.now)
    
class Subscription(Base):
    """个股订阅表（预留）"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    stock_code = Column(String(20))
    stock_name = Column(String(50))
    market = Column(String(20))  # A股/港股/美股
    rules = Column(Text)  # JSON格式的订阅规则
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class User(Base):
    """用户表（预留）"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    contact = Column(String(100))  # 微信/邮箱
    contact_type = Column(String(20))  # wechat/email
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(engine)
```

### 7. 配置管理 (config/)

```python
# settings.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """应用配置"""
    
    # DeepSeek
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    # Tushare
    TUSHARE_TOKEN: str
    
    # QQ邮箱
    QQ_EMAIL: str
    QQ_EMAIL_AUTH_CODE: str
    RECEIVER_EMAIL: str
    
    # 数据库
    DB_PATH: str = "data/db.sqlite3"
    
    # 图片
    IMAGE_DIR: str = "data/images"
    
    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

## 容错设计

### 重试机制

```python
# utils/retry.py
import asyncio
from functools import wraps
from typing import Callable

def retry(max_retries: int = 3, delay: float = 1):
    """重试装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # 指数退避
                        await asyncio.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator
```

### 数据源降级

```python
# collectors/fallback.py
from typing import Dict, Any
from .a_share import AShareCollector
from ..utils.logger import get_logger

class FallbackCollector:
    """数据源降级采集器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.collectors = [
            ("Tushare", TushareCollector()),
            ("AKShare", AShareCollector()),
            ("东方财富", EastMoneyCollector()),
        ]
    
    async def collect(self, **kwargs) -> Dict[str, Any]:
        """尝试多个数据源"""
        for name, collector in self.collectors:
            try:
                self.logger.info(f"尝试数据源: {name}")
                return await collector.collect(**kwargs)
            except Exception as e:
                self.logger.warning(f"数据源 {name} 失败: {e}")
                continue
        
        raise Exception("所有数据源均失败")
```

## Docker配置

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 安装Playwright依赖
RUN pip install playwright && \
    playwright install chromium

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/
COPY templates/ ./templates/
COPY config/ ./config/

# 创建数据目录
RUN mkdir -p data/images logs

# 创建非root用户
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# 暴露端口（健康检查用）
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "src.main"]
```

## CI/CD配置

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/redbook-auto:latest
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/redbook-auto
            docker-compose pull
            docker-compose down
            docker-compose up -d
```

## 环境变量

```bash
# .env.example

# DeepSeek
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Tushare
TUSHARE_TOKEN=your_token_here

# QQ邮箱
QQ_EMAIL=your_email@qq.com
QQ_EMAIL_AUTH_CODE=your_auth_code_here
RECEIVER_EMAIL=receiver@example.com

# 数据库
DB_PATH=data/db.sqlite3

# 图片
IMAGE_DIR=data/images

# 日志
LOG_LEVEL=INFO
LOG_DIR=logs
```

## 依赖清单

```txt
# requirements.txt

# 核心
fastapi==0.104.1
uvicorn==0.24.0

# 数据采集
akshare==1.12.0
tushare==1.3.0

# AI
openai==1.6.1

# 图片渲染
playwright==1.40.0

# 定时任务
apscheduler==3.10.4

# 数据库
sqlalchemy==2.0.23

# 配置
pydantic==2.5.0
pydantic-settings==2.1.0

# 工具
python-dotenv==1.0.0
loguru==0.7.2
```
