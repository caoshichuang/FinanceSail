## Context

当前系统只发送统一的市场总结邮件给固定收件人。用户需要为付费群成员提供个股订阅功能，让成员可以订阅自己关注的股票，在有重要事件时收到个性化邮件通知。

## Goals / Non-Goals

**Goals:**
- 支持用户通过邮箱订阅
- 支持用户通过股票代码或股票名称订阅股票
- 支持用户退订（取消全部订阅或取消部分股票）
- 支持查询用户订阅列表
- 支持按股票查询订阅用户
- 提供简单的配置文件管理方式

**Non-Goals:**
- 不实现完整的用户注册系统
- 不实现Web管理界面（先用配置文件）
- 不实现个股提醒发送功能（后续单独实现）

## Decisions

### 决策1：使用JSON配置文件存储订阅信息

**选择方案：** `config/subscribers.json`

**备选方案：**
- 数据库存储（过度设计）
- YAML文件（Python生态JSON更通用）

**理由：** 简单直接，易于手动维护，后续可迁移到数据库

### 决策2：支持股票代码和股票名称两种方式

**选择方案：** 订阅时同时记录代码和名称

**数据结构：**
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

**字段说明：**
- `email`: 用户邮箱（唯一标识）
- `name`: 用户昵称（可选）
- `expire_date`: 订阅到期日期（YYYY-MM-DD格式）
- `stocks`: 订阅的股票列表

**理由：** 用户可能只知道股票名称不知道代码，两种方式都要支持

### 决策3：提供Python工具函数管理配置

**选择方案：** `src/utils/subscribers.py`

**功能：**
- 添加/删除用户
- 添加/删除用户订阅的股票（支持代码或名称）
- 查询用户订阅列表
- 按股票查询订阅用户

**理由：** 封装操作，避免直接编辑JSON出错

**功能清单：**
- 添加用户 `add_user(email, name, expire_days=30)`
- 删除用户 `remove_user(email)` - 退订全部
- 续费用户 `renew_user(email, days=30)` - 延长到期时间
- 添加订阅 `add_subscription(email, stock_code_or_name)`
- 删除订阅 `remove_subscription(email, stock_code_or_name)` - 退订部分
- 查询用户订阅 `get_user_subscriptions(email)` - 自动过滤过期用户
- 查询股票订阅者 `get_stock_subscribers(stock_code_or_name)` - 自动过滤过期用户
- 检查用户是否过期 `is_user_expired(email)`
- 清理过期用户 `cleanup_expired_users()`

**退订方式：**
- 全部退订：删除用户
- 部分退订：删除用户对某只股票的订阅

**过期机制：**
- 添加用户时设置到期日期（默认30天）
- 查询时自动过滤过期用户
- 提供清理过期用户的工具函数

## Risks / Trade-offs

- **风险：** JSON文件并发写入可能冲突
  - **缓解：** 当前单进程，暂不考虑；后续可迁移到数据库

- **风险：** 手动维护配置文件容易出错
  - **缓解：** 提供工具函数封装，减少直接编辑

## Migration Plan

1. 创建 `config/subscribers.json` 配置文件
2. 创建 `src/utils/subscribers.py` 工具函数
3. 测试工具函数
4. 部署到服务器

## Open Questions

- 是否需要支持用户退订？
- 是否需要支持按板块订阅？
