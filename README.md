# 小红书股票内容自动运营系统

> 🤖 AI驱动 | 📊 A股+港股+美股 | 📧 自动邮件推送 | ✅ CI/CD自动部署

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
- ✅ 图片自动渲染（Pillow）
- ✅ 邮件自动推送（QQ邮箱）
- ✅ 定时任务调度（APScheduler）
- ✅ 工作日判断（周末/节假日不发送）
- ✅ 用户订阅配置（个股提醒预留）
- ✅ Docker部署支持
- ✅ 代码同步部署脚本

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
| 09:00 | 美股总结 | 昨日美股市场分析（仅美股开盘日） |
| 17:00 | A股+港股总结 | 今日A股和港股分析（仅A股/港股开盘日） |
| 17:30 | 热点个股 | 涨跌停股票分析（仅A股开盘日） |
| 20:00 | IPO分析 | 明日新股申购提醒（仅A股开盘日） |

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

### 方式1：代码同步部署（推荐）

1. **服务器配置**

```bash
ssh admin@your-server
cd /home/admin/redbook-auto
git init
git remote add origin https://github.com/caoshichuang/redbook_auto.git
git pull origin main
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

```bash
cp config/.env.example .env
# 编辑 .env 填入配置
```

4. **启动服务**

```bash
nohup python3 -m src.main > /tmp/redbook-auto.log 2>&1 &
```

5. **代码更新**

本地修改后推送到GitHub：

```bash
git add .
git commit -m "更新说明"
git push
```

服务器同步更新：

```bash
ssh admin@your-server "cd /home/admin/redbook-auto && bash scripts/deploy.sh"
```

### 方式2：Docker部署（需要网络支持）

```bash
docker-compose up -d
```

### 方式3：GitHub Actions（需要配置Secrets）

GitHub仓库设置 → Secrets → 添加：
- `SERVER_HOST`: 服务器IP
- `SERVER_USER`: 服务器用户名
- `SERVER_PASSWORD`: 服务器密码

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
