## Why

用户需要一个个股订阅功能，让付费群成员可以订阅自己关注的股票，当有重要事件时收到邮件通知。为了支持这个功能，需要暴露配置接口，让用户可以：
1. 维护订阅用户的邮箱列表
2. 维护每个用户订阅的股票列表

## What Changes

- 创建用户订阅配置文件 `config/subscribers.json`
- 创建用户管理工具 `src/utils/subscribers.py`
- 支持添加/删除用户
- 支持添加/删除用户订阅的股票
- 支持查询用户订阅列表
- 支持按股票查询订阅用户

## Capabilities

### New Capabilities

- `subscriber-management`: 用户订阅管理功能

### Modified Capabilities

- 无

## Impact

- 新增 `config/subscribers.json` - 用户订阅配置文件
- 新增 `src/utils/subscribers.py` - 用户订阅管理工具
- 后续可用于个股提醒功能
