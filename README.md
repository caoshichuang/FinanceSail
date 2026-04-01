# ⛵ FinanceSail

> AI 驱动的自动化股票分析与多渠道推送系统 | 📊 A股 + 港股 + 美股 | 🤖 LiteLLM 多模型 | 🔔 企业微信/飞书/Telegram/邮件/PushPlus | 🚀 CI/CD

AI 驱动的多市场股票分析系统，基于 LiteLLM 多模型路由实现结构化决策仪表盘输出，支持企业微信、飞书、Telegram、邮件、PushPlus 多渠道并发推送。

## 功能特性

### 内容类型

- **美股总结**：每日09:00，三大指数、中概股、明星股表现
- **A股+港股总结**：每日17:00，大盘指数、热点板块、明星股、资金流向
- **热点个股分析**：涨跌停股票分析（每日17:30）
- **IPO新股分析**：新股申购提醒、公司分析（每日20:00）

### 核心功能

- ✅ 多数据源自动切换（AKShare / Tushare / YFinance）+ 熔断器保护
- ✅ LiteLLM 多模型路由（DeepSeek 主模型 + 任意备用模型）
- ✅ Pydantic 结构化决策仪表盘（Dashboard）输出
- ✅ YAML 交易策略系统（多头趋势 / 均线金叉 / 缠论 / 波浪）
- ✅ 多渠道并发推送（企业微信 / 飞书 / Telegram / 邮件 / PushPlus）
- ✅ Jinja2 报告渲染（Markdown + 企业微信精简模板）
- ✅ 基本面数据管道（PE/PB/ROE/分红/板块排名）
- ✅ 交易日历（exchange-calendars + 静态文件双重 fallback）
- ✅ 后台管理系统（Vue3 + Element Plus）
- ✅ CI/CD自动部署（GitHub Actions）
- ✅ 全面配置管理（33项配置在线修改）

### 架构概览

```
APScheduler (定时任务)
    │
    ▼
StockAnalysisPipeline
    │
    ├─ DataFetcherManager (AKShare → Tushare → YFinance，熔断器保护)
    │       └─ FundamentalAdapter (PE/PB/ROE/分红/板块，TTL 缓存)
    │
    ├─ StockAnalyzer (LiteLLM Router → DeepSeek，Pydantic 验证)
    │       └─ SkillManager (YAML 策略注入)
    │
    ├─ ReportRenderer (Jinja2 → Markdown / 企业微信精简)
    │
    └─ NotificationService (并发推送)
            ├─ WechatSender    (企业微信 Webhook，4KB 自动分块)
            ├─ FeishuSender    (飞书 Webhook，20KB 自动分块)
            ├─ TelegramSender  (Bot API，4096 字符自动分块)
            ├─ EmailSender     (SMTP SSL，支持图片附件)
            └─ PushPlusSender  (国内推送，支持群组)
```

## 后台管理系统

系统提供Web后台管理界面，方便日常运维。

### 访问方式

- 地址：`http://你的服务器IP:8080`
- 默认用户名：`admin`
- 默认密码：`admin123`

### 功能模块


| 模块     | 功能                                   |
| -------- | -------------------------------------- |
| 仪表盘   | 统计数据、快捷操作、定时任务状态       |
| 用户管理 | 添加/删除/续费用户、订阅股票管理       |
| 内容管理 | 查看历史内容、手动触发生成             |
| 分发管理 | 多平台内容分发（小红书、公众号、头条） |
| 订阅管理 | 股票订阅、事件监控配置                 |
| 系统配置 | 全面配置管理（10大分类，33项配置）     |
| 日志查看 | 系统状态、应用日志、错误日志           |

### API接口


| 接口                           | 方法     | 说明             |
| ------------------------------ | -------- | ---------------- |
| `/api/auth/login`              | POST     | 登录获取Token    |
| `/api/users/`                  | GET/POST | 用户管理         |
| `/api/content/`                | GET      | 内容列表         |
| `/api/content/trigger/us`      | POST     | 手动生成美股总结 |
| `/api/content/trigger/a-share` | POST     | 手动生成A股总结  |
| `/api/config/env`              | GET/PUT  | 环境配置         |
| `/api/logs/app`                | GET      | 应用日志         |

## 项目结构

```
redbook-auto/
├── src/
│   ├── api/               # 后台管理API
│   │   ├── auth.py        # 登录认证
│   │   ├── users.py       # 用户管理
│   │   ├── content.py     # 内容管理
│   │   ├── config_api.py  # 配置管理
│   │   └── logs.py        # 日志查询
│   ├── collectors/        # 数据采集
│   │   ├── a_share.py     # A股数据
│   │   ├── us_stock.py    # 美股数据
│   │   ├── hk_stock.py    # 港股数据
│   │   ├── ipo.py         # IPO数据
│   │   ├── news.py        # 新闻数据
│   │   └── hot_search.py  # 热搜股票
│   ├── generators/        # 内容生成
│   │   ├── market_summary.py
│   │   ├── ipo_analysis.py
│   │   ├── hot_stock.py
│   │   └── prompts/       # Prompt模板
│   ├── renderers/         # 图片渲染
│   │   ├── cover.py       # 封面图
│   │   ├── cards.py       # 字卡
│   │   └── templates/     # HTML模板
│   ├── notifiers/         # 通知
│   │   └── email.py       # QQ邮件
│   ├── scheduler/         # 定时任务
│   │   ├── jobs.py        # 任务定义
│   │   └── smart_scheduler.py
│   ├── utils/             # 工具
│   │   ├── workday.py     # 工作日判断
│   │   └── subscribers.py # 用户订阅管理
│   ├── models/            # 数据模型
│   └── main.py            # 入口（FastAPI + 定时任务）
├── admin/                 # 后台管理前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   └── utils/         # API封装
│   ├── package.json
│   └── vite.config.js
├── data/                  # 数据文件
│   ├── holidays.json      # 节假日数据
│   └── images/            # 生成的图片
├── config/                # 配置文件
│   ├── .env.example       # 环境变量模板
│   └── subscribers.json   # 用户订阅配置
├── scripts/               # 脚本
│   └── deploy.sh          # 部署脚本
├── .github/workflows/     # CI/CD
│   └── deploy.yml
├── requirements.txt       # Python依赖
└── docker-compose.yml     # Docker配置
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `config/.env.example` 为 `.env`，填入以下配置：

```env
# DeepSeek AI
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Tushare
TUSHARE_TOKEN=your_token

# QQ邮箱
QQ_EMAIL=your_email@qq.com
QQ_EMAIL_AUTH_CODE=your_auth_code
RECEIVER_EMAIL=receiver@example.com
```

### 3. 运行

```bash
# 启动服务（包含API和定时任务）
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080

# 或者使用screen后台运行
screen -dmS redbook python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

启动后访问：

- 后台管理：`http://localhost:8080`
- API文档：`http://localhost:8080/docs`

### 4. Docker部署

```bash
docker-compose up -d
```

## 定时任务


| 时间  | 任务         | 说明                                  |
| ----- | ------------ | ------------------------------------- |
| 09:00 | 美股总结     | 昨日美股市场分析（仅美股开盘日）      |
| 17:00 | A股+港股总结 | 今日A股和港股分析（仅A股/港股开盘日） |
| 17:30 | 热点个股     | 涨跌停股票分析（仅A股开盘日）         |
| 20:00 | IPO分析      | 明日新股申购提醒（仅A股开盘日）       |

**工作日判断规则：**

- 周六、周日：不发送
- 法定节假日：不发送
- 股市休市日：不发送

节假日数据文件：`data/holidays.json`（每年需要更新）

## 内容模板

### 美股总结

- 字卡1：三大指数表现
- 字卡2：热门中概股
- 字卡3：美股明星股
- 字卡4：市场情绪
- 字卡5：重要事件
- 字卡6：明日关注

### A股+港股总结

- 字卡1：大盘指数
- 字卡2：涨跌分布
- 字卡3：热点板块
- 字卡4：明星股表现
- 字卡5：资金流向
- 字卡6：明日关注
- 字卡7：免责声明

## 用户订阅配置

系统支持用户订阅功能（预留），配置文件：`config/subscribers.json`

### 配置格式

```json
{
  "users": [
    {
      "email": "user@example.com",
      "name": "用户昵称",
      "expire_date": "2026-04-28",
      "stocks": [
        {"code": "600519", "name": "贵州茅台"},
        {"code": "00700", "name": "腾讯控股"}
      ]
    }
  ]
}
```

### 管理工具

```python
from src.utils.subscribers import *

# 添加用户（默认30天）
add_user('user@example.com', '用户昵称', expire_days=30)

# 续费用户
renew_user('user@example.com', days=60)

# 添加订阅（代码或名称）
add_subscription('user@example.com', '600519')
add_subscription('user@example.com', '腾讯控股')

# 删除订阅
remove_subscription('user@example.com', '600519')

# 删除用户（全部退订）
remove_user('user@example.com')

# 查询用户订阅
get_user_subscriptions('user@example.com')

# 查询股票订阅者
get_stock_subscribers('600519')

# 清理过期用户
cleanup_expired_users()
```

## 合规说明

⚠️ **重要声明**

本系统仅用于市场数据整理和信息分享，不构成任何投资建议。

- ✅ 可以做：市场数据分析、事件解读、IPO信息整理
- ❌ 不能做：推荐买卖、提供目标价、投资建议

## 部署

### 方式1：CI/CD自动部署（推荐）

1. Fork本仓库：https://github.com/caoshichuang/FinanceSail
2. 配置GitHub Secrets：

   - `SERVER_HOST`: 服务器IP
   - `SERVER_USER`: 服务器用户名
   - `SERVER_KEY`: 服务器SSH私钥
3. 推送代码自动部署：

   ```bash
   git add .
   git commit -m "更新说明"
   git push
   ```
4. **部署脚本自动执行**（scripts/deploy.sh）：

   - 备份敏感文件（`.env`、`holidays.json`、`db.sqlite3`）
   - 从 GitHub 拉取最新代码（带重试机制）
   - 恢复敏感文件
   - 构建前端（`npm run build`）
   - 重启服务（`nohup` 方式）

**网络优化**：国内服务器访问 GitHub 可能超时，部署脚本已配置以下优化：

- 使用 HTTP/1.1 协议
- 设置低速限制 1000 字节/秒，超时时间 60 秒
- 最多重试 5 次
- 使用 `--depth=1` 浅克隆

**CI/CD 流程**：

```
推送代码 → GitHub Actions 触发 → SSH 连接服务器 → 执行 deploy.sh → 服务重启
```

**验证部署成功**：

```bash
# 检查服务状态
curl http://你的服务器IP:8080/api/health

# 检查代码版本
ssh admin@你的服务器 "cd /home/admin/redbook-auto && git log -1 --oneline"
```

### 方式2：手动部署

1. **服务器配置**

```bash
ssh admin@your-server
cd /home/admin/redbook-auto
git init
git remote add origin https://github.com/caoshichuang/FinanceSail.git
git pull origin main
```

2. **安装依赖**

```bash
# Python依赖
pip3 install -r requirements.txt

# Node.js（用于构建前端）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

3. **配置环境变量**

```bash
cp config/.env.example .env
# 编辑 .env 填入配置
```

4. **构建前端**

```bash
cd admin
npm install --registry=https://registry.npmmirror.com
npm run build
cd ..
```

5. **启动服务**

```bash
screen -dmS redbook python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

6. **开放端口**

在阿里云/腾讯云控制台，安全组中开放8080端口。

### 方式3：Docker部署（需要网络支持）

```bash
docker-compose up -d
```

## 开发

### 本地开发

```bash
# 后端
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8080

# 前端
cd admin
npm install
npm run dev  # 开发服务器：http://localhost:3000
```

### 代码规范

```bash
# 格式化
black src/
isort src/

# 检查
flake8 src/
```

## 国内服务器配置

国内服务器访问GitHub受限，需要配置hosts：

```bash
sudo vim /etc/hosts
```

添加：

```
140.82.114.4                  github.com
185.199.108.154               github.githubassets.com
140.82.114.6                  api.github.com
185.199.108.133               raw.githubusercontent.com
```

## 项目仓库

- GitHub: https://github.com/caoshichuang/FinanceSail

## 许可证

MIT License
