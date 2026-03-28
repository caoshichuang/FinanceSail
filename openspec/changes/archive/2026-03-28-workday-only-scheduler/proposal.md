## Why

当前定时任务每天都会发送邮件（包括周末和节假日），用户希望只在工作日发送邮件，周末和法定节假日不发送。这样可以避免在非交易日收到无意义的邮件。

## What Changes

- 修改定时任务调度逻辑，只在工作日执行
- 添加中国法定节假日判断（春节、国庆等）
- 添加周末判断（周六、周日）
- 非工作日跳过任务执行，不发送邮件

## Capabilities

### New Capabilities

- `workday-check`: 工作日判断功能，包括周末判断和法定节假日判断

### Modified Capabilities

- `scheduler`: 修改定时任务调度逻辑，添加工作日判断

## Impact

- 修改 `src/scheduler/jobs.py` - 添加工作日判断逻辑
- 新增 `src/utils/workday.py` - 工作日判断工具函数
- 修改定时任务配置 - 使用工作日判断
