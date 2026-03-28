# 实施任务列表

## 阶段1：基础搭建（第1周）

### 1.1 项目初始化
- [x] 创建项目目录结构
- [x] 初始化Git仓库
- [x] 创建GitHub仓库（私有）
- [x] 测试Docker构建（因网络限制，改用Python直接运行）
- [x] 配置GitHub Secrets
- [x] 测试CI/CD流水线（改用代码同步方案）

---

## 阶段2：数据采集模块（第1-2周）

### 2.1 基类实现
- [x] 实现collectors/base.py（BaseCollector）
- [x] 实现数据校验方法
- [x] 实现日志记录

### 2.2 A股数据采集
- [x] 实现collectors/a_share.py
- [x] 获取A股三大指数
- [x] 获取涨跌分布
- [x] 获取热点板块TOP3
- [x] 获取明星股数据
- [x] 获取北向资金
- [x] 检测涨跌停股票

### 2.3 美股数据采集
- [x] 实现collectors/us_stock.py
- [x] 获取三大指数（纳指、标普、道指）
- [x] 获取热门中概股
- [x] 获取美股明星股
- [x] 获取重要新闻

### 2.4 港股数据采集
- [x] 实现collectors/hk_stock.py
- [x] 获取恒生指数、恒生科技指数
- [x] 获取港股明星股
- [x] 获取南向资金

### 2.5 IPO数据采集
- [x] 实现collectors/ipo.py
- [x] 获取新股申购列表
- [x] 获取新股基本信息
- [x] 获取上市首日数据

### 2.6 热点检测
- [x] 实现涨跌停检测
- [x] 实现明星股异常检测（涨跌超3%）
- [x] 实现热搜股票获取

### 2.7 数据源降级
- [x] 实现FallbackCollector
- [x] 配置数据源优先级
- [x] 测试降级逻辑

---

## 阶段3：内容生成模块（第2周）

### 3.1 基类实现
- [x] 实现generators/base.py（BaseGenerator）
- [x] 配置DeepSeek客户端
- [x] 实现通用生成方法

### 3.2 Prompt模板
- [x] 创建generators/prompts/us_summary.py
- [x] 创建generators/prompts/a_share_summary.py
- [x] 创建generators/prompts/hk_summary.py
- [x] 创建generators/prompts/ipo_analysis.py
- [x] 创建generators/prompts/hot_stock.py

### 3.3 内容生成器
- [x] 实现generators/market_summary.py
  - [x] 标题生成（3个备选）
  - [x] 正文生成（7张字卡）
  - [x] 标签生成
- [x] 实现美股总结生成
- [x] 实现A股+港股总结生成
- [x] 实现IPO分析生成（待实现）
- [x] 实现热点个股分析生成（待实现）

### 3.4 内容校验
- [x] 实现敏感词过滤
- [x] 实现数据一致性检查
- [x] 实现格式校验

---

## 阶段4：图片渲染模块（第2-3周）

### 4.1 HTML模板设计
- [x] 设计封面图模板（cover.html）
- [x] 设计字卡模板（card.html）
- [x] 设计CSS样式
- [x] 设计配色方案

### 4.2 封面图渲染
- [x] 实现renderers/cover.py
- [x] 支持主标题、副标题
- [x] 支持日期角标
- [x] 支持AI标识

### 4.3 字卡渲染
- [x] 实现renderers/cards.py
- [x] 支持多张字卡批量渲染
- [x] 支持不同内容类型

### 4.4 图片打包
- [x] 实现zip打包功能
- [x] 生成完整图片包

---

## 阶段5：邮件通知模块（第3周）

### 5.1 邮件发送
- [x] 实现notifiers/email.py
- [x] 配置QQ邮箱SMTP
- [x] 实现邮件正文构建
- [x] 实现附件添加

### 5.2 邮件模板
- [x] 设计美股总结邮件模板
- [x] 设计A股港股总结邮件模板
- [x] 设计IPO提醒邮件模板
- [x] 设计热点个股邮件模板

### 5.3 错误通知
- [x] 实现错误邮件通知
- [x] 实现失败重试

---

## 阶段6：定时任务模块（第3周）

### 6.1 任务定义
- [x] 实现scheduler/jobs.py
- [x] 实现美股总结任务（09:00）
- [x] 实现A股+港股总结任务（17:00）
- [x] 实现热点检测任务
- [x] 实现IPO内容判断
- [x] 实现热点内容判断
- [x] 实现内容优先级逻辑
- [x] 测试端到端流程（待测试）
- [x] 数据采集模块测试
- [x] 内容生成模块测试
- [x] 图片渲染模块测试
- [x] 邮件通知模块测试
- [x] 端到端流程测试
- [x] 定时任务测试
- [x] 异常场景测试
- [x] 单篇内容生成耗时测试
- [x] 全套内容生成耗时测试
- [x] 邮件发送耗时测试
- [x] 购买云服务器
- [x] 配置服务器环境
- [x] 安装Docker
- [x] Docker镜像构建
- [x] Docker Compose部署
- [x] 手动触发测试
- [x] 定时任务测试
- [x] 监控运行状态
- [x] 修复发现的问题
- [x] 云服务器
- [x] Tushare API Token
- [x] DeepSeek API Key
- [x] QQ邮箱授权码
- [x] AKShare API可用性
- [x] Tushare API可用性
- [x] DeepSeek API可用性
- [x] QQ邮箱SMTP可用性
