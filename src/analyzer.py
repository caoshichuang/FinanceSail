"""
AI 分析层模块
基于 LiteLLM Router 实现多模型负载均衡
使用 Pydantic Schema 验证 LLM 输出
输出结构化决策仪表盘（Dashboard）
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.schemas.report_schema import AnalysisReportSchema, Dashboard, CoreConclusion
from src.utils.logger import get_logger

logger = get_logger("analyzer")

# 占位符填充值
PLACEHOLDER = "N/A"

# 必须字段（integrity check 使用）
MANDATORY_FIELDS = [
    "sentiment_score",
    "operation_advice",
    "analysis_summary",
]


# ──────────────────────────────────────────────
# AnalysisResult 数据类
# ──────────────────────────────────────────────


@dataclass
class AnalysisResult:
    """AI 分析结果，包含决策仪表盘"""

    stock_code: str
    stock_name: str = ""
    analysis_date: str = ""
    market_type: str = ""

    # 核心指标
    sentiment_score: Optional[int] = None  # 情绪评分 0-100
    operation_advice: str = PLACEHOLDER  # 操作建议
    analysis_summary: str = PLACEHOLDER  # 分析摘要
    risk_level: str = "中"  # 风险等级

    # 决策仪表盘（核心新增）
    dashboard: Optional[Dashboard] = None

    # 向后兼容：字卡内容
    cards: List[str] = field(default_factory=list)
    titles: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # 元数据
    model_used: str = ""
    success: bool = True
    error_message: str = ""
    integrity_mode: str = "strict"  # strict / weak
    missing_fields: List[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于存储/序列化）"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "analysis_date": self.analysis_date,
            "market_type": self.market_type,
            "sentiment_score": self.sentiment_score,
            "operation_advice": self.operation_advice,
            "analysis_summary": self.analysis_summary,
            "risk_level": self.risk_level,
            "dashboard": self.dashboard.model_dump() if self.dashboard else None,
            "cards": self.cards,
            "titles": self.titles,
            "tags": self.tags,
            "model_used": self.model_used,
            "success": self.success,
            "integrity_mode": self.integrity_mode,
            "missing_fields": self.missing_fields,
        }


# ──────────────────────────────────────────────
# Analyzer 主类
# ──────────────────────────────────────────────


class StockAnalyzer:
    """
    股票 AI 分析器
    - 使用 LiteLLM Router 实现多模型负载均衡
    - Pydantic Schema 验证输出
    - 自动完整性检查和占位符填充
    """

    def __init__(self):
        self._router = None
        self._fallback_client = None
        self._init_llm()

    def _init_llm(self):
        """初始化 LLM 客户端（LiteLLM Router 优先，OpenAI 备用）"""
        try:
            from litellm import Router
            from src.config.settings import settings

            model_list = [
                {
                    "model_name": "primary",
                    "litellm_params": {
                        "model": f"deepseek/{settings.DEEPSEEK_MODEL}",
                        "api_key": settings.DEEPSEEK_API_KEY,
                        "api_base": settings.DEEPSEEK_BASE_URL,
                    },
                }
            ]

            # 若配置了备用模型，加入列表
            backup_models = getattr(settings, "BACKUP_MODELS", [])
            for i, bm in enumerate(backup_models):
                model_list.append(
                    {
                        "model_name": f"fallback_{i}",
                        "litellm_params": bm,
                    }
                )

            self._router = Router(
                model_list=model_list,
                routing_strategy="simple-shuffle",
                num_retries=2,
                retry_after=5,
            )
            logger.info(f"LiteLLM Router 初始化成功，模型数量: {len(model_list)}")

        except ImportError:
            logger.warning("litellm 未安装，使用 openai 客户端备用")
            self._init_fallback()
        except Exception as e:
            logger.warning(f"LiteLLM 初始化失败: {e}，使用备用客户端")
            self._init_fallback()

    def _init_fallback(self):
        """初始化备用 OpenAI 客户端"""
        try:
            import openai
            from src.config.settings import settings

            self._fallback_client = openai.OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
            )
        except Exception as e:
            logger.error(f"备用客户端初始化失败: {e}")

    def analyze(
        self,
        stock_code: str,
        stock_name: str,
        market_data: Dict[str, Any],
        news_context: str = "",
        strategy_name: str = "",
    ) -> AnalysisResult:
        """
        执行股票 AI 分析

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            market_data: 市场数据（日线、技术指标等）
            news_context: 新闻/舆情背景
            strategy_name: 使用的交易策略

        Returns:
            AnalysisResult: 结构化分析结果（含 dashboard）
        """
        start = time.time()

        result = AnalysisResult(
            stock_code=stock_code,
            stock_name=stock_name,
        )

        try:
            from datetime import datetime

            result.analysis_date = datetime.now().strftime("%Y-%m-%d")

            # 构建 Prompt
            system_prompt = self._build_system_prompt(strategy_name)
            user_prompt = self._build_user_prompt(
                stock_code, stock_name, market_data, news_context
            )

            # 调用 LLM
            raw_response, model_used = self._call_llm(system_prompt, user_prompt)
            result.model_used = model_used

            # 解析并验证响应
            schema = self._parse_response(raw_response)

            # 映射到 AnalysisResult
            result.sentiment_score = schema.sentiment_score
            result.operation_advice = schema.operation_advice or PLACEHOLDER
            result.analysis_summary = schema.analysis_summary or PLACEHOLDER
            result.risk_level = schema.risk_level or "中"
            result.dashboard = schema.dashboard
            result.cards = schema.cards or []
            result.titles = schema.titles or []
            result.tags = schema.tags or []

            # 完整性检查
            self._check_content_integrity(result)

        except Exception as e:
            logger.error(f"[{stock_code}] AI 分析失败: {e}")
            result.success = False
            result.error_message = str(e)
            result.operation_advice = PLACEHOLDER
            result.analysis_summary = PLACEHOLDER

        result.elapsed_seconds = time.time() - start
        return result

    def _call_llm(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        """
        调用 LLM，优先使用 LiteLLM Router

        Returns:
            Tuple[str, str]: (响应文本, 使用的模型名称)
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if self._router:
            try:
                from src.config.settings import settings

                response = self._router.completion(
                    model="primary",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=3000,
                    response_format={"type": "json_object"},
                )
                model_used = response.model or "primary"
                return response.choices[0].message.content, model_used
            except Exception as e:
                logger.warning(f"LiteLLM Router 调用失败: {e}，尝试备用客户端")

        # 备用 OpenAI 客户端
        if self._fallback_client:
            from src.config.settings import settings

            response = self._fallback_client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content, settings.DEEPSEEK_MODEL

        raise RuntimeError("无可用 LLM 客户端")

    def _parse_response(self, raw: str) -> AnalysisReportSchema:
        """
        解析并验证 LLM JSON 响应

        Args:
            raw: LLM 原始响应文本

        Returns:
            AnalysisReportSchema: 验证后的数据
        """
        # 提取 JSON 部分
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        # 尝试直接解析
        try:
            data = json.loads(text)
            return AnalysisReportSchema(**data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"JSON 直接解析失败: {e}，尝试 json-repair")

        # 尝试 json-repair 修复
        try:
            from json_repair import repair_json

            repaired = repair_json(text)
            data = json.loads(repaired)
            return AnalysisReportSchema(**data)
        except Exception as e2:
            logger.warning(f"json-repair 修复失败: {e2}，返回空 Schema")

        return AnalysisReportSchema()

    def _check_content_integrity(self, result: AnalysisResult):
        """
        完整性检查：验证必填字段，缺失时填充占位符
        """
        missing = []

        if not result.sentiment_score:
            missing.append("sentiment_score")
            result.sentiment_score = 50  # 中性默认值

        if result.operation_advice == PLACEHOLDER or not result.operation_advice:
            missing.append("operation_advice")
            self._apply_placeholder_fill(result, "operation_advice")

        if result.analysis_summary == PLACEHOLDER or not result.analysis_summary:
            missing.append("analysis_summary")
            self._apply_placeholder_fill(result, "analysis_summary")

        if result.dashboard and result.dashboard.core_conclusion:
            if not result.dashboard.core_conclusion.one_sentence:
                missing.append("dashboard.core_conclusion.one_sentence")
                result.dashboard.core_conclusion.one_sentence = PLACEHOLDER

        if missing:
            result.integrity_mode = "weak"
            result.missing_fields = missing
            logger.warning(
                f"[{result.stock_code}] 完整性检查 integrity_mode=weak，"
                f"缺失字段: {missing}"
            )
        else:
            result.integrity_mode = "strict"

    def _apply_placeholder_fill(self, result: AnalysisResult, field_name: str):
        """为缺失字段应用占位符"""
        placeholder_map = {
            "operation_advice": "数据不足，建议观望",
            "analysis_summary": "暂无分析摘要，请等待数据更新",
        }
        value = placeholder_map.get(field_name, PLACEHOLDER)
        setattr(result, field_name, value)

    def _build_system_prompt(self, strategy_name: str = "") -> str:
        """构建系统 Prompt"""
        strategy_section = ""
        if strategy_name:
            strategy_section = f"\n使用交易策略：{strategy_name}\n"

        return f"""你是一名资深量化分析师，擅长技术分析和基本面研究。
{strategy_section}
请对提供的股票数据进行专业分析，并以 JSON 格式返回结构化分析报告。

JSON 格式要求（严格遵守）：
{{
  "stock_code": "股票代码",
  "stock_name": "股票名称",
  "sentiment_score": 0-100的整数（市场情绪评分）,
  "operation_advice": "操作建议文字（50字以内）",
  "analysis_summary": "综合分析摘要（100字以内）",
  "risk_level": "低/中/高",
  "dashboard": {{
    "core_conclusion": {{
      "one_sentence": "一句话核心结论（≤30字）",
      "signal_type": "🟢买入/🟡观望/🔴卖出/🔵持有",
      "time_sensitivity": "短线/中线/长线",
      "confidence": 0-100的整数
    }},
    "data_perspective": {{
      "trend_status": {{
        "ma_alignment": "多头/空头/横盘",
        "trend_score": 0-100的整数,
        "trend_desc": "趋势描述",
        "volume_analysis": "量价分析"
      }},
      "price_position": {{
        "current_price": 当前价格（数字）,
        "ma5": MA5值,
        "ma10": MA10值,
        "ma20": MA20值,
        "bias_pct": 乖离率,
        "support_level": 支撑位,
        "resistance_level": 压力位,
        "position_desc": "位置描述"
      }}
    }},
    "intelligence": {{
      "risk_alerts": ["风险1", "风险2"],
      "positive_catalysts": ["利好1", "利好2"],
      "news_sentiment": "positive/negative/neutral",
      "key_events": ["事件1"]
    }},
    "battle_plan": {{
      "sniper_points": {{
        "ideal_buy": 理想买入价,
        "secondary_buy": 备选买入价,
        "stop_loss": 止损价,
        "take_profit": 止盈价,
        "position_size": "轻/中/重"
      }},
      "action_checklist": ["✅ 条件1", "⚠️ 注意2", "❌ 禁忌3"],
      "strategy_name": "策略名称",
      "execution_note": "执行说明"
    }}
  }},
  "tags": ["标签1", "标签2"]
}}

重要：
1. 只返回 JSON，不要有任何前缀或后缀说明
2. 所有数字字段使用数字类型，不要用字符串
3. 没有数据的字段用 null，不要省略
4. 不构成任何投资建议，仅作分析参考"""

    def _build_user_prompt(
        self,
        code: str,
        name: str,
        market_data: Dict[str, Any],
        news_context: str,
    ) -> str:
        """构建用户 Prompt"""
        # 提取最近行情
        recent_prices = market_data.get("recent_prices", "无数据")
        tech_indicators = market_data.get("technical_indicators", {})
        fundamental = market_data.get("fundamental", {})

        prompt = f"""分析股票：{name}（{code}）

【最近行情】
{recent_prices}

【技术指标】
MA5: {tech_indicators.get("ma5", "N/A")}
MA10: {tech_indicators.get("ma10", "N/A")}
MA20: {tech_indicators.get("ma20", "N/A")}
RSI(14): {tech_indicators.get("rsi", "N/A")}
MACD: {tech_indicators.get("macd", "N/A")}
成交量变化: {tech_indicators.get("volume_change", "N/A")}%
"""

        if fundamental:
            prompt += f"""
【基本面数据】
PE: {fundamental.get("pe", "N/A")}
PB: {fundamental.get("pb", "N/A")}
ROE: {fundamental.get("roe", "N/A")}%
"""

        if news_context:
            prompt += f"""
【新闻/舆情背景】
{news_context[:800]}
"""

        prompt += "\n请基于以上数据，生成完整的 JSON 分析报告。"
        return prompt
