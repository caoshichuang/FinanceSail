"""
报告 Pydantic Schema 模块
用于验证 LLM JSON 输出的数据结构
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CoreConclusion(BaseModel):
    """核心结论"""

    one_sentence: Optional[str] = Field(None, description="一句话摘要，≤30字")
    signal_type: Optional[str] = Field(
        None, description="交易信号：🟢买入/🟡观望/🔴卖出/🔵持有"
    )
    time_sensitivity: Optional[str] = Field(None, description="时效性：短线/中线/长线")
    confidence: Optional[int] = Field(None, ge=0, le=100, description="置信度0-100")


class PricePosition(BaseModel):
    """价格位置"""

    current_price: Optional[float] = Field(None, description="当前价格")
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    bias_pct: Optional[float] = Field(None, description="乖离率%")
    support_level: Optional[float] = Field(None, description="支撑位")
    resistance_level: Optional[float] = Field(None, description="压力位")
    position_desc: Optional[str] = Field(None, description="位置描述文字")


class TrendStatus(BaseModel):
    """趋势状态"""

    ma_alignment: Optional[str] = Field(None, description="均线排列：多头/空头/横盘")
    trend_score: Optional[int] = Field(None, ge=0, le=100, description="趋势强度0-100")
    trend_desc: Optional[str] = Field(None, description="趋势描述")
    volume_analysis: Optional[str] = Field(None, description="量价分析")


class ChipStructure(BaseModel):
    """筹码结构"""

    main_cost: Optional[float] = Field(None, description="主力成本")
    retail_cost: Optional[float] = Field(None, description="散户成本")
    profit_ratio: Optional[float] = Field(None, description="获利比例%")
    concentration: Optional[str] = Field(None, description="筹码集中度：高/中/低")


class DataPerspective(BaseModel):
    """数据透视"""

    trend_status: Optional[TrendStatus] = None
    price_position: Optional[PricePosition] = None
    chip_structure: Optional[ChipStructure] = None
    technical_indicators: Optional[Dict[str, Any]] = Field(
        None, description="技术指标字典（RSI/MACD/KDJ等）"
    )


class Intelligence(BaseModel):
    """情报信息"""

    risk_alerts: Optional[List[str]] = Field(
        default_factory=list, description="风险提示列表"
    )
    positive_catalysts: Optional[List[str]] = Field(
        default_factory=list, description="利好催化剂列表"
    )
    news_sentiment: Optional[str] = Field(
        None, description="新闻情绪：positive/negative/neutral"
    )
    key_events: Optional[List[str]] = Field(
        default_factory=list, description="关键事件列表"
    )


class SniperPoints(BaseModel):
    """狙击点位"""

    ideal_buy: Optional[float] = Field(None, description="理想买入价")
    secondary_buy: Optional[float] = Field(None, description="备选买入价")
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")
    position_size: Optional[str] = Field(None, description="建议仓位：轻/中/重")


class BattlePlan(BaseModel):
    """作战计划"""

    sniper_points: Optional[SniperPoints] = None
    action_checklist: Optional[List[str]] = Field(
        default_factory=list, description="行动清单，含✅/⚠️/❌标记"
    )
    strategy_name: Optional[str] = Field(None, description="使用的策略名称")
    execution_note: Optional[str] = Field(None, description="执行说明")


class Dashboard(BaseModel):
    """决策仪表盘（核心输出）"""

    core_conclusion: Optional[CoreConclusion] = None
    data_perspective: Optional[DataPerspective] = None
    intelligence: Optional[Intelligence] = None
    battle_plan: Optional[BattlePlan] = None


class AnalysisReportSchema(BaseModel):
    """完整分析报告 Schema（用于验证 LLM 输出）"""

    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    analysis_date: Optional[str] = None
    market_type: Optional[str] = None

    # 核心指标
    sentiment_score: Optional[int] = Field(
        None, ge=0, le=100, description="情绪评分0-100"
    )
    operation_advice: Optional[str] = Field(None, description="操作建议文字")
    analysis_summary: Optional[str] = Field(None, description="分析摘要")
    risk_level: Optional[str] = Field(None, description="风险等级：低/中/高")

    # 决策仪表盘
    dashboard: Optional[Dashboard] = None

    # 向后兼容：保留原有字卡内容字段
    cards: Optional[List[str]] = Field(
        default_factory=list, description="字卡内容列表（向后兼容）"
    )
    titles: Optional[List[str]] = Field(
        default_factory=list, description="标题列表（向后兼容）"
    )
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
