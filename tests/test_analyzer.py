"""
src/analyzer.py 单元测试

测试范围：
- AnalysisResult 数据类
- _parse_response JSON 解析与 Pydantic 验证
- _check_content_integrity 完整性检查
- _apply_placeholder_fill 占位符填充
- _build_system_prompt / _build_user_prompt 构建
- analyze() 完整流程（Mock LLM）
"""

import json
import unittest
from dataclasses import asdict
from unittest.mock import MagicMock, patch

from src.analyzer import PLACEHOLDER, AnalysisResult, StockAnalyzer
from src.schemas.report_schema import (
    AnalysisReportSchema,
    CoreConclusion,
    Dashboard,
)


class TestAnalysisResult(unittest.TestCase):
    """AnalysisResult 数据类测试"""

    def test_default_values(self):
        """默认值正确初始化"""
        r = AnalysisResult(stock_code="600519")
        self.assertEqual(r.stock_code, "600519")
        self.assertEqual(r.operation_advice, PLACEHOLDER)
        self.assertEqual(r.analysis_summary, PLACEHOLDER)
        self.assertTrue(r.success)
        self.assertEqual(r.integrity_mode, "strict")
        self.assertEqual(r.missing_fields, [])

    def test_to_dict_contains_required_keys(self):
        """to_dict 包含所有核心字段"""
        r = AnalysisResult(stock_code="AAPL", stock_name="苹果")
        d = r.to_dict()
        for key in [
            "stock_code",
            "stock_name",
            "sentiment_score",
            "operation_advice",
            "analysis_summary",
            "risk_level",
            "dashboard",
            "success",
            "integrity_mode",
        ]:
            self.assertIn(key, d)

    def test_to_dict_dashboard_none(self):
        """dashboard 为 None 时序列化为 None"""
        r = AnalysisResult(stock_code="000001")
        d = r.to_dict()
        self.assertIsNone(d["dashboard"])

    def test_to_dict_dashboard_serialized(self):
        """dashboard 非 None 时调用 model_dump"""
        r = AnalysisResult(stock_code="000001")
        r.dashboard = Dashboard(
            core_conclusion=CoreConclusion(
                one_sentence="测试",
                signal_type="🟢买入",
                confidence=80,
            )
        )
        d = r.to_dict()
        self.assertIsNotNone(d["dashboard"])
        self.assertIn("core_conclusion", d["dashboard"])


class TestParseResponse(unittest.TestCase):
    """_parse_response 测试"""

    def setUp(self):
        # 初始化时屏蔽 LLM 实际调用
        with patch.object(StockAnalyzer, "_init_llm", lambda self: None):
            self.analyzer = StockAnalyzer.__new__(StockAnalyzer)
            self.analyzer._router = None
            self.analyzer._fallback_client = None

    def _make_valid_json(self) -> str:
        return json.dumps(
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "sentiment_score": 75,
                "operation_advice": "逢低买入",
                "analysis_summary": "趋势良好，建议持有",
                "risk_level": "低",
            }
        )

    def test_valid_json_parsed(self):
        """有效 JSON 可正确解析"""
        schema = self.analyzer._parse_response(self._make_valid_json())
        self.assertIsInstance(schema, AnalysisReportSchema)
        self.assertEqual(schema.sentiment_score, 75)
        self.assertEqual(schema.operation_advice, "逢低买入")

    def test_markdown_code_block_stripped(self):
        """带 Markdown 代码块包裹的 JSON 可解析"""
        wrapped = "```json\n" + self._make_valid_json() + "\n```"
        schema = self.analyzer._parse_response(wrapped)
        self.assertIsInstance(schema, AnalysisReportSchema)
        self.assertEqual(schema.risk_level, "低")

    def test_invalid_json_returns_empty_schema(self):
        """无法修复的 JSON 返回空 Schema"""
        schema = self.analyzer._parse_response("这完全不是JSON {{{")
        self.assertIsInstance(schema, AnalysisReportSchema)
        self.assertIsNone(schema.sentiment_score)

    def test_extra_fields_ignored(self):
        """Pydantic 忽略额外字段，不抛异常"""
        data = json.loads(self._make_valid_json())
        data["unknown_field"] = "should_be_ignored"
        schema = self.analyzer._parse_response(json.dumps(data))
        self.assertIsInstance(schema, AnalysisReportSchema)

    def test_dashboard_nested_parsed(self):
        """嵌套 dashboard 结构可正确解析"""
        data = {
            "sentiment_score": 60,
            "operation_advice": "观望",
            "analysis_summary": "震荡市",
            "risk_level": "中",
            "dashboard": {
                "core_conclusion": {
                    "one_sentence": "短期震荡",
                    "signal_type": "🟡观望",
                    "confidence": 65,
                }
            },
        }
        schema = self.analyzer._parse_response(json.dumps(data))
        self.assertIsNotNone(schema.dashboard)
        self.assertEqual(schema.dashboard.core_conclusion.confidence, 65)


class TestContentIntegrity(unittest.TestCase):
    """_check_content_integrity 测试"""

    def setUp(self):
        with patch.object(StockAnalyzer, "_init_llm", lambda self: None):
            self.analyzer = StockAnalyzer.__new__(StockAnalyzer)
            self.analyzer._router = None
            self.analyzer._fallback_client = None

    def test_all_fields_present_strict_mode(self):
        """所有字段完整时为 strict 模式"""
        r = AnalysisResult(
            stock_code="600519",
            sentiment_score=70,
            operation_advice="买入",
            analysis_summary="趋势向上",
        )
        self.analyzer._check_content_integrity(r)
        self.assertEqual(r.integrity_mode, "strict")
        self.assertEqual(r.missing_fields, [])

    def test_missing_sentiment_score_filled(self):
        """缺失 sentiment_score 时填充为 50（中性）"""
        r = AnalysisResult(
            stock_code="000001",
            sentiment_score=None,
            operation_advice="持有",
            analysis_summary="横盘整理",
        )
        self.analyzer._check_content_integrity(r)
        self.assertEqual(r.sentiment_score, 50)
        self.assertIn("sentiment_score", r.missing_fields)
        self.assertEqual(r.integrity_mode, "weak")

    def test_placeholder_operation_advice_filled(self):
        """operation_advice 为 PLACEHOLDER 时触发填充"""
        r = AnalysisResult(
            stock_code="TSLA",
            sentiment_score=55,
            operation_advice=PLACEHOLDER,
            analysis_summary="波动较大",
        )
        self.analyzer._check_content_integrity(r)
        self.assertIn("operation_advice", r.missing_fields)
        self.assertNotEqual(r.operation_advice, PLACEHOLDER)

    def test_missing_analysis_summary_filled(self):
        """analysis_summary 缺失时使用默认占位文字"""
        r = AnalysisResult(
            stock_code="AAPL",
            sentiment_score=80,
            operation_advice="买入",
            analysis_summary="",
        )
        self.analyzer._check_content_integrity(r)
        self.assertIn("analysis_summary", r.missing_fields)
        self.assertNotEqual(r.analysis_summary, "")

    def test_dashboard_one_sentence_filled(self):
        """dashboard.core_conclusion.one_sentence 为空时填充"""
        r = AnalysisResult(stock_code="000001", sentiment_score=60)
        r.operation_advice = "观望"
        r.analysis_summary = "横盘"
        r.dashboard = Dashboard(core_conclusion=CoreConclusion(one_sentence=""))
        self.analyzer._check_content_integrity(r)
        self.assertIn("dashboard.core_conclusion.one_sentence", r.missing_fields)
        self.assertEqual(r.dashboard.core_conclusion.one_sentence, PLACEHOLDER)


class TestPromptBuilding(unittest.TestCase):
    """_build_system_prompt / _build_user_prompt 测试"""

    def setUp(self):
        with patch.object(StockAnalyzer, "_init_llm", lambda self: None):
            self.analyzer = StockAnalyzer.__new__(StockAnalyzer)
            self.analyzer._router = None
            self.analyzer._fallback_client = None

    def test_system_prompt_contains_json_format(self):
        """系统提示包含 JSON 格式说明"""
        prompt = self.analyzer._build_system_prompt()
        self.assertIn("JSON", prompt)
        self.assertIn("sentiment_score", prompt)

    def test_system_prompt_with_strategy(self):
        """带策略名称时系统提示包含策略信息"""
        prompt = self.analyzer._build_system_prompt(strategy_name="均线金叉策略")
        self.assertIn("均线金叉策略", prompt)

    def test_user_prompt_contains_stock_info(self):
        """用户提示包含股票代码和名称"""
        market_data = {
            "recent_prices": "2024-01-01 100.5",
            "technical_indicators": {"ma5": 100.0, "rsi": 55.0},
        }
        prompt = self.analyzer._build_user_prompt("600519", "贵州茅台", market_data, "")
        self.assertIn("600519", prompt)
        self.assertIn("贵州茅台", prompt)

    def test_user_prompt_with_news_context(self):
        """有新闻背景时包含在提示中"""
        prompt = self.analyzer._build_user_prompt(
            "000001",
            "平安银行",
            {},
            news_context="公司发布季报，营收超预期",
        )
        self.assertIn("公司发布季报", prompt)

    def test_user_prompt_news_truncated(self):
        """超长新闻背景被截断为 800 字符"""
        long_news = "X" * 2000
        prompt = self.analyzer._build_user_prompt(
            "AAPL", "苹果", {}, news_context=long_news
        )
        # 截断后不超过 800 个 X
        count = prompt.count("X")
        self.assertLessEqual(count, 800)


class TestAnalyzeIntegration(unittest.TestCase):
    """analyze() 端到端集成测试（Mock LLM）"""

    def _make_mock_response(self) -> str:
        return json.dumps(
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "sentiment_score": 78,
                "operation_advice": "逢低分批买入",
                "analysis_summary": "白马龙头，趋势稳健向上",
                "risk_level": "低",
                "dashboard": {
                    "core_conclusion": {
                        "one_sentence": "稳健上涨",
                        "signal_type": "🟢买入",
                        "confidence": 82,
                    }
                },
                "tags": ["白马股", "消费龙头"],
            }
        )

    def test_analyze_with_mock_router(self):
        """Mock LiteLLM Router，验证 analyze() 返回正确结果"""
        with patch.object(StockAnalyzer, "_init_llm", lambda self: None):
            analyzer = StockAnalyzer.__new__(StockAnalyzer)
            analyzer._router = None
            analyzer._fallback_client = None

        # 模拟 _call_llm 直接返回 mock 响应
        analyzer._call_llm = MagicMock(
            return_value=(self._make_mock_response(), "deepseek-chat")
        )

        result = analyzer.analyze(
            stock_code="600519",
            stock_name="贵州茅台",
            market_data={"recent_prices": "2024-01-01 1700"},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.stock_code, "600519")
        self.assertEqual(result.sentiment_score, 78)
        self.assertEqual(result.operation_advice, "逢低分批买入")
        self.assertEqual(result.model_used, "deepseek-chat")
        self.assertEqual(result.integrity_mode, "strict")
        self.assertIsNotNone(result.dashboard)
        self.assertEqual(result.dashboard.core_conclusion.signal_type, "🟢买入")

    def test_analyze_llm_failure_returns_safe_result(self):
        """LLM 调用失败时，analyze() 返回 success=False 的安全结果"""
        with patch.object(StockAnalyzer, "_init_llm", lambda self: None):
            analyzer = StockAnalyzer.__new__(StockAnalyzer)
            analyzer._router = None
            analyzer._fallback_client = None

        analyzer._call_llm = MagicMock(side_effect=RuntimeError("API 超时"))

        result = analyzer.analyze(
            stock_code="TSLA",
            stock_name="特斯拉",
            market_data={},
        )

        self.assertFalse(result.success)
        self.assertIn("API 超时", result.error_message)
        self.assertEqual(result.operation_advice, PLACEHOLDER)

    def test_analyze_elapsed_seconds_recorded(self):
        """analyze() 应记录耗时"""
        with patch.object(StockAnalyzer, "_init_llm", lambda self: None):
            analyzer = StockAnalyzer.__new__(StockAnalyzer)
            analyzer._router = None
            analyzer._fallback_client = None

        analyzer._call_llm = MagicMock(
            return_value=(self._make_mock_response(), "mock")
        )
        result = analyzer.analyze("600519", "贵州茅台", {})
        self.assertGreater(result.elapsed_seconds, 0)


if __name__ == "__main__":
    unittest.main()
