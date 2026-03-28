# 小红书股票内容自动运营系统

AI驱动的小红书股票内容自动生成系统，支持A股、港股、美股市场分析。

## 功能特性

### 内容类型
- **美股总结**：每日09:00，三大指数、中概股、明星股表现
- **A股+港股总结**：每日17:00，大盘指数、热点板块、明星股、资金流向
- **热点个股分析**：涨跌停股票分析（每日17:30）
- **IPO新股分析**：新股申购提醒、公司分析（每日20:00）

### 核心功能
- ✅ 自动数据采集（AKShare/Tushare）
- ✅ AI内容生成（DeepSeek）
- ✅ 图片自动渲染（Playwright）
- ✅ 邮件自动推送（QQ邮箱）
- ✅ 定时任务调度（APScheduler）
- ✅ Docker部署支持
- ✅ CI/CD自动部署

## 项目结构

```
redbook-auto/
├── src/
│   ├── collectors/          # 数据采集
│   │   ├── a_share.py       # A股数据
│   │   ├── us_stock.py      # 美股数据
│   │   ├── hk_stock.py      # 港股数据
│   │   ├── ipo.py           # IPO数据
│   │   ├── news.py          # 新闻数据
│   │   └── hot_search.py    # 热搜股票
│   ├── generators/          # 内容生成
│   │   ├── market_summary.py
│   │   ├── ipo_analysis.py
│   │   ├── hot_stock.py
│   │   └── prompts/         # Prompt模板
│   ├── renderers/           # 图片渲染
│   │   ├── cover.py         # 封面图
│   │   ├── cards.py         # 字卡
│   │   └── templates/       # HTML模板
│   ├── notifiers/           # 通知
│   │   └── email.py         # QQ邮件
│   ├── scheduler/           # 定时任务
│   │   ├── jobs.py          # 任务定义
│   │   └── smart_scheduler.py
│   ├── config/              # 配置
│   ├── utils/               # 工具
│   ├── models/              # 数据模型
│   └── main.py              # 入口
├── docker/
├── .github/workflows/
├── requirements.txt
└── docker-compose.yml
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
python -m src.main
```

### 4. Docker部署

```bash
docker-compose up -d
```

## 定时任务

| 时间 | 任务 | 说明 |
|------|------|------|
| 09:00 | 美股总结 | 昨日美股市场分析 |
| 17:00 | A股+港股总结 | 今日A股和港股分析 |
| 17:30 | 热点个股 | 涨跌停股票分析 |
| 20:00 | IPO分析 | 明日新股申购提醒 |

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

## 合规说明

⚠️ **重要声明**

本系统仅用于市场数据整理和信息分享，不构成任何投资建议。

- ✅ 可以做：市场数据分析、事件解读、IPO信息整理
- ❌ 不能做：推荐买卖、提供目标价、投资建议

## 部署

### GitHub Actions

1. Fork本仓库
2. 配置GitHub Secrets：
   - `DOCKER_USERNAME`: Docker Hub用户名
   - `DOCKER_PASSWORD`: Docker Hub密码
   - `SERVER_HOST`: 服务器IP
   - `SERVER_USER`: 服务器用户名
   - `SERVER_SSH_KEY`: 服务器SSH密钥
3. 推送代码自动部署

### 手动部署

```bash
# 构建镜像
docker build -t redbook-auto -f docker/Dockerfile .

# 运行
docker-compose up -d
```

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式化

```bash
black src/
isort src/
```

## 许可证

MIT License
