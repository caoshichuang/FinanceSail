# FinanceSail 配置说明文档

> **v2.0 新增配置项**：LiteLLM 多模型、多渠道通知（企业微信/飞书/Telegram/PushPlus）、交易策略、交易日历、报告渲染。详见下方各节。

## 配置文件结构

```
config/
├── .env                    # 环境变量配置（敏感信息）
├── dynamic_config.json     # 动态配置（可通过管理后台修改）
└── project_config.json     # 项目信息配置
```

---

## 环境变量配置 (.env)

`.env` 文件存储敏感配置，**不会提交到 Git**。

### AI 配置

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| DEEPSEEK_API_KEY | string | ✅ | DeepSeek API 密钥 |
| DEEPSEEK_BASE_URL | string | ❌ | API 地址，默认 `https://api.deepseek.com` |
| DEEPSEEK_MODEL | string | ❌ | 模型名称，默认 `deepseek-chat` |

**获取方式**：访问 [DeepSeek](https://platform.deepseek.com/) 注册并获取 API Key。

### 数据源配置

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| TUSHARE_TOKEN | string | ✅ | Tushare API Token |

**获取方式**：访问 [Tushare](https://tushare.pro/) 注册并获取 Token。

### 邮件配置

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| QQ_EMAIL | string | ✅ | 发件人 QQ 邮箱 |
| QQ_EMAIL_AUTH_CODE | string | ✅ | QQ 邮箱授权码 |
| RECEIVER_EMAIL | string | ✅ | 收件人邮箱 |
| SMTP_SERVER | string | ❌ | SMTP 服务器，默认 `smtp.qq.com` |
| SMTP_PORT | int | ❌ | SMTP 端口，默认 `465` |

**获取授权码**：
1. 登录 QQ 邮箱
2. 设置 → 账户 → POP3/IMAP/SMTP 服务
3. 开启 POP3/SMTP 服务
4. 生成授权码

### 应用配置

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| BASE_URL | string | ❌ | 应用访问地址 |
| LOG_LEVEL | string | ❌ | 日志级别，默认 `INFO` |
| LOG_ROTATION | string | ❌ | 日志轮转大小，默认 `10 MB` |
| LOG_RETENTION | string | ❌ | 日志保留时间，默认 `30 days` |

### .env 示例

```env
# DeepSeek AI
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Tushare
TUSHARE_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx

# QQ邮箱
QQ_EMAIL=your_email@qq.com
QQ_EMAIL_AUTH_CODE=xxxxxxxxxxxxxxxx
RECEIVER_EMAIL=receiver@example.com

# SMTP配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465

# 应用配置
BASE_URL=http://your-server:8080
LOG_LEVEL=INFO
```

---

## 动态配置 (dynamic_config.json)

动态配置可以通过管理后台在线修改，**无需重启服务**（除邮件配置外）。

### 明星股配置

```json
{
  "star_stocks": {
    "A股": [
      {"code": "600519", "name": "贵州茅台"},
      {"code": "300750", "name": "宁德时代"},
      {"code": "002594", "name": "比亚迪"}
    ],
    "港股": [
      {"code": "00700", "name": "腾讯控股"},
      {"code": "09988", "name": "阿里巴巴"}
    ],
    "美股": [
      {"code": "AAPL", "name": "苹果"},
      {"code": "MSFT", "name": "微软"},
      {"code": "NVDA", "name": "英伟达"}
    ]
  }
}
```

**说明**：
- A 股代码：6 位数字，如 `600519`
- 港股代码：5 位数字，如 `00700`
- 美股代码：字母，如 `AAPL`

### 业务阈值配置

```json
{
  "thresholds": {
    "hot_stock_threshold": 3.0,
    "limit_up_down_threshold": 9.9
  }
}
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| hot_stock_threshold | float | 3.0 | 热点股票涨跌阈值（%），超过此值标记为热点 |
| limit_up_down_threshold | float | 9.9 | 涨跌停阈值（%），超过此值认为涨跌停 |

### 定时任务配置

```json
{
  "scheduler": {
    "us_stock_time": "09:00",
    "a_share_time": "17:00",
    "hot_stock_time": "17:30",
    "ipo_time": "20:00"
  }
}
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| us_stock_time | string | 09:00 | 美股总结执行时间 |
| a_share_time | string | 17:00 | A股+港股总结执行时间 |
| hot_stock_time | string | 17:30 | 热点个股分析执行时间 |
| ipo_time | string | 20:00 | IPO分析执行时间 |

**时间格式**：`HH:MM`，24小时制

### 分发平台配置

```json
{
  "distribution": {
    "wechat_app_id": "",
    "wechat_app_secret": "",
    "toutiao_access_token": "",
    "wxpusher_app_token": ""
  }
}
```

| 配置项 | 说明 |
|--------|------|
| wechat_app_id | 微信公众号 AppID |
| wechat_app_secret | 微信公众号 AppSecret |
| toutiao_access_token | 今日头条 Access Token |
| wxpusher_app_token | WxPusher App Token |

### 完整示例

```json
{
  "star_stocks": {
    "A股": [
      {"code": "600519", "name": "贵州茅台"},
      {"code": "300750", "name": "宁德时代"},
      {"code": "002594", "name": "比亚迪"},
      {"code": "601318", "name": "中国平安"}
    ],
    "港股": [
      {"code": "00700", "name": "腾讯控股"},
      {"code": "09988", "name": "阿里巴巴"},
      {"code": "03690", "name": "美团"}
    ],
    "美股": [
      {"code": "AAPL", "name": "苹果"},
      {"code": "MSFT", "name": "微软"},
      {"code": "NVDA", "name": "英伟达"}
    ]
  },
  "thresholds": {
    "hot_stock_threshold": 3.0,
    "limit_up_down_threshold": 9.9
  },
  "scheduler": {
    "us_stock_time": "09:00",
    "a_share_time": "17:00",
    "hot_stock_time": "17:30",
    "ipo_time": "20:00"
  },
  "distribution": {
    "wechat_app_id": "",
    "wechat_app_secret": "",
    "toutiao_access_token": "",
    "wxpusher_app_token": ""
  }
}
```

---

## 项目配置 (project_config.json)

项目配置存储项目元信息，可通过管理后台修改。

```json
{
  "project_name": "财帆",
  "project_name_en": "FinanceSail",
  "project_version": "1.0.0",
  "project_description": "AI驱动的多平台财经内容自动生成与分发系统",
  "project_logo": "⛵",
  "project_slogan": "Empowering Financial Content Creation"
}
```

---

## 配置生效机制

### 实时生效（无需重启）

- ✅ 明星股配置
- ✅ 业务阈值配置
- ✅ 定时任务时间配置
- ✅ 分发平台配置

**生效方式**：修改后立即生效，下次执行任务时使用新配置。

### 需要重启服务

- ⚠️ 邮件配置（SMTP 相关）
- ⚠️ AI 配置（API Key 等）
- ⚠️ 数据源配置（Tushare Token）
- ⚠️ 日志配置

**生效方式**：修改后需要重启服务才能生效。

### 重启服务方法

```bash
# 方法1：使用 screen
screen -X -S finance-sail quit
screen -dmS finance-sail bash -c 'cd /path/to/project && python3 -m src.main'

# 方法2：使用 systemctl（如果配置了服务）
sudo systemctl restart finance-sail
```

---

## 配置备份与恢复

### 自动备份

系统在以下情况自动备份：
1. 批量更新配置前
2. 恢复配置前

备份文件位置：`config/dynamic_config_backup_YYYYMMDD_HHMMSS.json`

### 手动备份

通过管理后台：
1. 进入"系统配置"页面
2. 点击"备份"按钮
3. 系统自动下载备份文件

### 恢复配置

通过管理后台：
1. 进入"系统配置"页面
2. 点击"恢复"按钮
3. 选择备份文件上传
4. 系统自动恢复配置

### 命令行恢复

```bash
# 查看备份文件
ls config/dynamic_config_backup_*.json

# 恢复到指定备份
cp config/dynamic_config_backup_20260329_140000.json config/dynamic_config.json

# 重启服务使配置生效
screen -X -S finance-sail quit
screen -dmS finance-sail bash -c 'cd /path/to/project && python3 -m src.main'
```

---

## 配置验证

### 格式验证

系统自动验证以下格式：
- 时间格式：必须为 `HH:MM`
- 邮箱格式：必须包含 `@`
- 数值范围：阈值必须为正数

### 业务验证

- 明星股数量：建议每类 3-10 只
- 定时任务时间：避免设置在非工作时间
- 阈值范围：建议在 1-20% 之间

---

## 常见问题

### Q: 修改配置后没有生效？

A: 检查配置类型：
- 动态配置（明星股、阈值等）：立即生效，无需重启
- 环境配置（邮件、AI等）：需要重启服务

### Q: 配置文件损坏怎么办？

A: 使用备份恢复：
1. 查找最近的备份文件
2. 复制备份文件为 `dynamic_config.json`
3. 重启服务

### Q: 如何重置为默认配置？

A: 删除 `dynamic_config.json` 文件，系统会自动使用默认配置。

### Q: 定时任务时间设置无效？

A: 检查以下几点：
1. 时间格式是否正确（HH:MM）
2. 是否已重启服务
3. 检查日志确认配置已加载

---

## 配置优先级

配置加载顺序（后者覆盖前者）：

1. **默认值**（代码中定义）
2. **环境变量**（.env 文件）
3. **动态配置**（dynamic_config.json）

优先级：`动态配置 > 环境变量 > 默认值`
