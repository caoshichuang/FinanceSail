# FinanceSail API 文档

> **v2.0 新增**：Pipeline 直接调用接口、多渠道通知接口

## 认证

所有 API 都需要 JWT Token 认证。

### 登录获取 Token

```
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 使用 Token

在请求头中添加：
```
Authorization: Bearer <access_token>
```

---

## 配置管理 API

### 获取所有配置分类

```
GET /api/config/categories

Response:
{
  "categories": [
    {
      "id": "ai",
      "name": "AI配置",
      "icon": "Cpu",
      "description": "DeepSeek AI 配置"
    },
    {
      "id": "datasource",
      "name": "数据源配置",
      "icon": "Connection",
      "description": "Tushare 数据源配置"
    },
    ...
  ]
}
```

### 获取分类配置

```
GET /api/config/category/{category}

支持的 category:
- ai: AI 配置
- datasource: 数据源配置
- email: 邮件配置
- app: 应用配置
- star_stocks: 明星股配置
- thresholds: 业务阈值配置
- scheduler: 定时任务配置
- project: 项目信息配置
- holidays: 节假日配置
- distribution: 分发平台配置

Response (以 ai 为例):
{
  "DEEPSEEK_API_KEY": "sk-xxxxxxxx",
  "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
  "DEEPSEEK_MODEL": "deepseek-chat"
}
```

### 更新分类配置

```
PUT /api/config/category/{category}
Content-Type: application/json

Request (以 thresholds 为例):
{
  "hot_stock_threshold": 5.0,
  "limit_up_down_threshold": 9.5
}

Response:
{
  "message": "配置已更新"
}
```

### 获取所有配置

```
GET /api/config/all

Response:
{
  "ai": {...},
  "datasource": {...},
  "email": {...},
  "app": {...},
  "star_stocks": {...},
  "thresholds": {...},
  "scheduler": {...},
  "project": {...},
  "holidays": {...},
  "distribution": {...}
}
```

### 获取单个配置项

```
GET /api/config/item/{key}

Response:
{
  "key": "HOT_STOCK_THRESHOLD",
  "value": 3.0,
  "source": "dynamic"
}
```

### 更新单个配置项

```
PUT /api/config/item/{key}
Content-Type: application/json

Request:
{
  "value": 5.0
}

Response:
{
  "message": "配置已更新"
}
```

### 批量更新配置

```
PUT /api/config/batch
Content-Type: application/json

Request:
{
  "configs": {
    "HOT_STOCK_THRESHOLD": 5.0,
    "LIMIT_UP_DOWN_THRESHOLD": 9.5
  }
}

Response:
{
  "message": "批量更新成功",
  "updated": 2
}
```

### 验证配置

```
POST /api/config/validate
Content-Type: application/json

Request:
{
  "key": "HOT_STOCK_THRESHOLD",
  "value": 5.0
}

Response:
{
  "valid": true,
  "message": "配置有效"
}
```

### 测试邮件配置

```
POST /api/config/test/email

Response:
{
  "success": true,
  "message": "测试邮件发送成功"
}
```

### 备份配置

```
POST /api/config/backup

Response:
{
  "success": true,
  "message": "配置备份成功",
  "backup_file": "config/dynamic_config_backup_20260329_140000.json"
}
```

### 恢复配置

```
POST /api/config/restore

Response:
{
  "success": true,
  "message": "配置恢复成功"
}
```

### 获取环境配置

```
GET /api/config/env

Response:
{
  "DEEPSEEK_API_KEY": "sk-xxxxxxxx",
  "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
  "TUSHARE_TOKEN": "xxxxxxxx",
  "QQ_EMAIL": "example@qq.com",
  ...
}
```

### 更新环境配置

```
PUT /api/config/env
Content-Type: application/json

Request:
{
  "DEEPSEEK_API_KEY": "sk-new-key",
  "QQ_EMAIL": "newemail@qq.com"
}

Response:
{
  "message": "环境配置已更新，需要重启服务生效"
}
```

### 获取调度器配置

```
GET /api/config/scheduler

Response:
{
  "us_stock_time": "09:00",
  "a_share_time": "17:00",
  "hot_stock_time": "17:30",
  "ipo_time": "20:00"
}
```

### 获取明星股配置

```
GET /api/config/star-stocks

Response:
{
  "star_stocks": {
    "A股": [
      {"code": "600519", "name": "贵州茅台"},
      {"code": "300750", "name": "宁德时代"}
    ],
    "港股": [...],
    "美股": [...]
  }
}
```

---

## 用户管理 API

### 获取用户列表

```
GET /api/users/

Response:
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "用户昵称",
      "expire_date": "2026-04-28",
      "stocks": [...]
    }
  ]
}
```

### 创建用户

```
POST /api/users/
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "name": "用户昵称",
  "expire_days": 30
}

Response:
{
  "id": 1,
  "email": "user@example.com",
  "message": "用户创建成功"
}
```

### 删除用户

```
DELETE /api/users/{user_id}

Response:
{
  "message": "用户删除成功"
}
```

### 续费用户

```
POST /api/users/{user_id}/renew
Content-Type: application/json

Request:
{
  "days": 30
}

Response:
{
  "message": "续费成功",
  "new_expire_date": "2026-05-28"
}
```

---

## 内容管理 API

### 获取内容列表

```
GET /api/content/?limit=20&offset=0

Response:
{
  "contents": [
    {
      "id": 1,
      "market": "A股",
      "type": "daily_summary",
      "title": "A股收盘总结",
      "created_at": "2026-03-29T17:00:00",
      "status": "sent"
    }
  ],
  "total": 100
}
```

### 获取内容详情

```
GET /api/content/{content_id}

Response:
{
  "id": 1,
  "market": "A股",
  "type": "daily_summary",
  "title": "A股收盘总结",
  "content": "...",
  "tags": ["A股", "收盘", "总结"],
  "images": [...],
  "created_at": "2026-03-29T17:00:00",
  "status": "sent"
}
```

### 手动生成内容

```
POST /api/content/trigger/{market}

支持的 market:
- us: 美股总结
- a-share: A股总结
- hk: 港股总结
- hot: 热点个股
- ipo: IPO分析

Response:
{
  "success": true,
  "message": "内容生成任务已启动",
  "task_id": "xxx"
}
```

---

## 分发管理 API

### 获取分发状态

```
GET /api/distribution/status

Response:
{
  "xiaohongshu": {"enabled": true, "last_post": "..."},
  "wechat": {"enabled": false, "reason": "未配置"},
  "toutiao": {"enabled": false, "reason": "未配置"}
}
```

### 发布内容到平台

```
POST /api/distribution/publish
Content-Type: application/json

Request:
{
  "content_id": 1,
  "platform": "xiaohongshu"
}

Response:
{
  "success": true,
  "message": "已跳转到预览页面"
}
```

---

## 订阅管理 API

### 获取订阅列表

```
GET /api/subscriptions/

Response:
{
  "subscriptions": [...]
}
```

### 添加订阅

```
POST /api/subscriptions/
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "stock_code": "600519",
  "events": ["price_change", "announcement"]
}

Response:
{
  "success": true,
  "message": "订阅成功"
}
```

### 删除订阅

```
DELETE /api/subscriptions/{subscription_id}

Response:
{
  "success": true,
  "message": "订阅已删除"
}
```

---

## 日志 API

### 获取系统状态

```
GET /api/logs/status

Response:
{
  "status": "running",
  "uptime": "3 days",
  "version": "1.0.0",
  "scheduler": {
    "running": true,
    "jobs": [...]
  }
}
```

### 获取应用日志

```
GET /api/logs/app?lines=100

Response:
{
  "logs": [
    "2026-03-29 17:00:00 | INFO | 开始执行A股总结任务",
    ...
  ]
}
```

### 获取错误日志

```
GET /api/logs/error?lines=50

Response:
{
  "logs": [
    "2026-03-29 17:05:00 | ERROR | 数据采集失败: ...",
    ...
  ]
}
```

---

## 预览 API

### 获取预览页面

```
GET /preview/{content_id}

Response: HTML 页面（手机端优化）
```

---

## 错误响应格式

所有 API 错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

常见错误码：
- 401: 未认证或 Token 过期
- 403: 无权限
- 404: 资源不存在
- 422: 请求参数错误
- 500: 服务器内部错误
