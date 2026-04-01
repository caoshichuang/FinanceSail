# FinanceSail 交易策略系统

## 概述

交易策略系统使用 YAML 文件定义策略，通过 `StrategyLoader` 加载，`SkillManager` 管理激活与优先级，最终将策略 Prompt 注入到 AI 分析中。

---

## 策略文件格式

策略文件存放于 `strategies/` 目录，文件名即策略 ID。

```yaml
# strategies/my_strategy.yaml

name: 策略显示名称          # 必填
description: 策略详细说明   # 必填
enabled: true               # 是否启用，默认 true
priority: 1                 # 优先级，数值越小越高
version: "1.0"              # 版本号（可选）

# 触发条件（可选）
conditions:
  - type: ma_cross           # 条件类型
    short_period: 5
    long_period: 20
    direction: golden_cross  # golden_cross / death_cross

  - type: rsi_threshold
    period: 14
    operator: "<"
    value: 30

# 交易信号定义
signals:
  buy:
    - condition: ma5_cross_above_ma20
      confidence: 0.7        # 置信度 0-1
      description: "5日均线上穿20日均线，多头信号"

  sell:
    - condition: ma5_cross_below_ma20
      confidence: 0.8
      description: "5日均线下穿20日均线，空头信号"

# 风险控制参数（可选）
risk_control:
  stop_loss_pct: 5.0         # 止损比例 %
  take_profit_pct: 15.0      # 止盈比例 %
  max_holding_days: 20       # 最大持仓天数
  position_size: "medium"    # 建议仓位：light/medium/heavy

# AI Prompt 扩展（注入到分析提示中）
prompt_extension: |
  请重点关注以下策略要素：
  1. 短期均线（MA5）与长期均线（MA20）的交叉关系
  2. 成交量配合情况（量价齐升为有效金叉）
  3. 整体趋势方向（需在上升趋势中寻找金叉机会）
```

---

## 内置策略

### 多头趋势策略 (`bull_trend.yaml`)

判断股票是否处于上升趋势中。

**核心逻辑**：
- MA5 > MA10 > MA20（均线多头排列）
- 成交量温和放大
- 近期无明显高点阻力

**适用场景**：趋势跟踪、中线持有

### 均线金叉策略 (`ma_golden_cross.yaml`)

捕捉短期均线上穿长期均线的买入信号。

**核心逻辑**：
- MA5 上穿 MA20（金叉）
- 成交量配合放大（量价齐升）
- 整体趋势为上升

**适用场景**：短线至中线，趋势初段介入

### 缠论策略 (`chan_theory.yaml`)

基于缠论的走势分析（顶底分型、笔、线段）。

**核心逻辑**：
- 识别底部分型结构
- 确认向上的笔和线段
- 背驰信号辅助判断

**适用场景**：精确定点位，适合有缠论基础的用户

### 波浪理论策略 (`wave_theory.yaml`)

基于艾略特波浪理论的波形计数。

**核心逻辑**：
- 五浪上升 + 三浪调整
- 当前处于第三浪（最强势浪）判断
- 调整浪结束后的反弹机会

**适用场景**：中长线，大级别趋势判断

---

## 策略加载与使用

### 代码示例

```python
from src.strategies import StrategyLoader, SkillManager

# 加载所有策略
loader = StrategyLoader(strategies_dir="strategies/")
strategies = loader.load_all()

# 激活策略
manager = SkillManager()
manager.activate("bull_trend")
manager.activate("ma_golden_cross")

# 构建注入 Prompt
prompt = manager.build_combined_prompt()
print(prompt)
```

### 通过 Pipeline 自动使用

```python
from src.core.pipeline import StockAnalysisPipeline

pipeline = StockAnalysisPipeline()
# Pipeline 初始化时自动加载 SkillManager，策略自动注入到 AI 分析
result = pipeline.process_single_stock("600519")
```

---

## 添加自定义策略

1. 在 `strategies/` 目录创建新的 YAML 文件，例如 `strategies/my_custom.yaml`
2. 按照上述格式填写策略定义
3. 重启服务后自动加载（或调用 `StrategyLoader.reload()`）
4. 通过 `SkillManager.activate("my_custom")` 激活

---

## 策略优先级

当多个策略同时激活时，按 `priority` 数值升序排列（数值越小优先级越高）。

构建组合 Prompt 时，高优先级策略的说明排在前面。

默认最大同时激活数：3（可通过 `STRATEGY_MAX_ACTIVE` 配置）。
