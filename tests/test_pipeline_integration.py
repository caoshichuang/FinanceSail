"""
src/core/pipeline.py 集成测试

测试范围：
- StockAnalysisPipeline 初始化（延迟加载）
- _enhance_context 上下文构建
- fetch_and_save_stock_data（Mock DataFetcherManager）
- analyze_stock（Mock StockAnalyzer）
- process_single_stock 完整流程（全 Mock）
- run / run_async 并发处理多股票
"""

import json
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

import pandas as pd

from src.core.pipeline import StockAnalysisPipeline
from src.analyzer import AnalysisResult


def _make_df(rows=10) -> pd.DataFrame:
    """创建模拟行情 DataFrame"""
    import numpy as np

    dates = pd.date_range("2024-01-01", periods=rows)
    return pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "open": [100.0 + i for i in range(rows)],
            "close": [101.0 + i for i in range(rows)],
            "high": [103.0 + i for i in range(rows)],
            "low": [99.0 + i for i in range(rows)],
            "volume": [1000000 + i * 10000 for i in range(rows)],
            "pct_chg": [0.5 + i * 0.01 for i in range(rows)],
        }
    )


def _make_analysis_result(stock_code="600519") -> AnalysisResult:
    """创建模拟 AnalysisResult"""
    result = AnalysisResult(
        stock_code=stock_code,
        stock_name="贵州茅台",
        sentiment_score=75,
        operation_advice="逢低买入",
        analysis_summary="趋势稳健",
        success=True,
        integrity_mode="strict",
    )
    return result


class TestPipelineInit(unittest.TestCase):
    """Pipeline 初始化测试"""

    def test_init_with_no_config_does_not_crash(self):
        """无配置初始化不报错"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            pipeline = StockAnalysisPipeline(config=None)
        self.assertIsNone(pipeline._config)
        self.assertFalse(pipeline._initialized)

    def test_init_default_max_workers(self):
        """默认线程数为 4"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            pipeline = StockAnalysisPipeline(config=None)
        self.assertEqual(pipeline._max_workers, 4)

    def test_init_custom_max_workers(self):
        """自定义线程数"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            pipeline = StockAnalysisPipeline(config=None, max_workers=8)
        self.assertEqual(pipeline._max_workers, 8)


class TestEnhanceContext(unittest.TestCase):
    """_enhance_context 上下文构建测试"""

    def _make_pipeline(self):
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            p = StockAnalysisPipeline(config=None)
        p._strategy_manager = None
        return p

    def test_enhance_context_basic_fields(self):
        """基本字段正确填充"""
        pipeline = self._make_pipeline()
        df = _make_df()
        ctx = pipeline._enhance_context("600519", df, "akshare")
        self.assertEqual(ctx["stock_code"], "600519")
        self.assertEqual(ctx["data_source"], "akshare")
        self.assertIn("analysis_date", ctx)

    def test_enhance_context_with_df_latest_close(self):
        """从 DataFrame 提取最新收盘价"""
        pipeline = self._make_pipeline()
        df = _make_df(5)
        ctx = pipeline._enhance_context("000001", df, "tushare")
        # 第 5 行 close = 101 + 4 = 105
        self.assertAlmostEqual(ctx["latest_close"], 105.0)

    def test_enhance_context_without_df(self):
        """df 为 None 时不崩溃，且不包含 latest_close"""
        pipeline = self._make_pipeline()
        ctx = pipeline._enhance_context("AAPL", None, "yfinance")
        self.assertNotIn("latest_close", ctx)

    def test_enhance_context_extra_context_merged(self):
        """extra_context 正确合并"""
        pipeline = self._make_pipeline()
        extra = {"custom_key": "custom_value"}
        ctx = pipeline._enhance_context("TSLA", None, "yfinance", extra_context=extra)
        self.assertEqual(ctx["extra"]["custom_key"], "custom_value")

    def test_enhance_context_strategy_prompt_injected(self):
        """策略管理器存在时，strategy_prompt 被注入"""
        pipeline = self._make_pipeline()
        mock_strategy_manager = MagicMock()
        mock_strategy_manager.build_combined_prompt.return_value = "均线金叉策略 Prompt"
        pipeline._strategy_manager = mock_strategy_manager

        ctx = pipeline._enhance_context("600519", None, "akshare")
        self.assertEqual(ctx.get("strategy_prompt"), "均线金叉策略 Prompt")


class TestFetchAndSaveStockData(unittest.TestCase):
    """fetch_and_save_stock_data 测试"""

    def _make_pipeline_with_data_manager(self, df=None, source="akshare", raises=False):
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            p = StockAnalysisPipeline(config=None)
        p._initialized = True  # 跳过 _ensure_initialized

        mock_manager = MagicMock()
        if raises:
            mock_manager.get_daily_data.side_effect = Exception("数据源不可用")
        else:
            mock_manager.get_daily_data.return_value = (df or _make_df(), source)
        p._data_manager = mock_manager
        return p

    def test_fetch_success_returns_df_and_source(self):
        """正常获取返回 (df, source)"""
        pipeline = self._make_pipeline_with_data_manager()
        df, source = pipeline.fetch_and_save_stock_data("600519")
        self.assertIsNotNone(df)
        self.assertEqual(source, "akshare")

    def test_fetch_failure_returns_none(self):
        """数据源异常时返回 (None, '')"""
        pipeline = self._make_pipeline_with_data_manager(raises=True)
        df, source = pipeline.fetch_and_save_stock_data("600519")
        self.assertIsNone(df)
        self.assertEqual(source, "")

    def test_fetch_without_data_manager_returns_none(self):
        """_data_manager 为 None 时返回 (None, '')"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            pipeline = StockAnalysisPipeline(config=None)
        pipeline._initialized = True
        pipeline._data_manager = None
        df, source = pipeline.fetch_and_save_stock_data("600519")
        self.assertIsNone(df)


class TestAnalyzeStock(unittest.TestCase):
    """analyze_stock 测试"""

    def _make_pipeline_with_analyzer(self, result=None, raises=False):
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            p = StockAnalysisPipeline(config=None)
        p._initialized = True

        mock_analyzer = MagicMock()
        if raises:
            mock_analyzer.analyze.side_effect = Exception("LLM 超时")
        else:
            mock_analyzer.analyze.return_value = result or _make_analysis_result()
        p._analyzer = mock_analyzer
        return p

    def test_analyze_stock_success(self):
        """正常调用返回 AnalysisResult"""
        pipeline = self._make_pipeline_with_analyzer()
        result = pipeline.analyze_stock("600519", _make_df(), {"stock_code": "600519"})
        self.assertIsNotNone(result)
        self.assertEqual(result.stock_code, "600519")
        self.assertEqual(result.sentiment_score, 75)

    def test_analyze_stock_exception_returns_none(self):
        """分析器异常时返回 None"""
        pipeline = self._make_pipeline_with_analyzer(raises=True)
        result = pipeline.analyze_stock("600519", _make_df(), {})
        self.assertIsNone(result)

    def test_analyze_stock_without_analyzer_returns_none(self):
        """_analyzer 为 None 时返回 None"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            pipeline = StockAnalysisPipeline(config=None)
        pipeline._initialized = True
        pipeline._analyzer = None
        result = pipeline.analyze_stock("600519", _make_df(), {})
        self.assertIsNone(result)


class TestProcessSingleStock(unittest.TestCase):
    """process_single_stock 完整流程测试"""

    def _make_full_pipeline(self, fetch_ok=True, analyze_ok=True):
        """构造全 Mock Pipeline"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            p = StockAnalysisPipeline(config=None)

        # 替换各子组件
        p._data_manager = MagicMock()
        if fetch_ok:
            p._data_manager.get_daily_data.return_value = (_make_df(), "akshare")
        else:
            p._data_manager.get_daily_data.return_value = (None, "")

        p._analyzer = MagicMock()
        if analyze_ok:
            p._analyzer.analyze.return_value = _make_analysis_result()
        else:
            p._analyzer.analyze.side_effect = Exception("AI 失败")

        p._strategy_manager = None
        p._notification_service = None
        p._report_renderer = None
        p._initialized = True
        return p

    def test_process_single_stock_success(self):
        """完整流程成功时返回 AnalysisResult"""
        pipeline = self._make_full_pipeline()
        result = pipeline.process_single_stock("600519")
        self.assertIsNotNone(result)
        self.assertTrue(result.success)

    def test_process_single_stock_data_fetch_fails(self):
        """数据获取失败时返回 None"""
        pipeline = self._make_full_pipeline(fetch_ok=False)
        result = pipeline.process_single_stock("600519")
        self.assertIsNone(result)

    def test_process_single_stock_analyze_fails(self):
        """AI 分析失败时返回 None"""
        pipeline = self._make_full_pipeline(analyze_ok=False)
        result = pipeline.process_single_stock("600519")
        self.assertIsNone(result)

    def test_process_single_stock_with_news_context(self):
        """传入新闻背景时正确透传到分析器"""
        pipeline = self._make_full_pipeline()
        pipeline.process_single_stock("600519", news_context="公司发布季报")
        call_kwargs = pipeline._analyzer.analyze.call_args
        # 检查 news_context 传入
        all_args = list(call_kwargs[0]) + list(call_kwargs[1].values())
        self.assertTrue(any("公司发布季报" in str(a) for a in all_args))


class TestRunMethod(unittest.TestCase):
    """run / run_async 多股票并发测试"""

    def _make_runnable_pipeline(self, stock_codes):
        """构造 run() 可执行的 Pipeline"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            p = StockAnalysisPipeline(config=None, max_workers=2)

        # Mock process_single_stock
        def mock_process(code, **kwargs):
            return _make_analysis_result(stock_code=code)

        p._initialized = True
        p._data_manager = MagicMock()
        p._analyzer = MagicMock()
        p._strategy_manager = None
        p._notification_service = None
        p._report_renderer = None
        p.process_single_stock = MagicMock(side_effect=mock_process)
        return p

    def test_run_returns_results_for_all_stocks(self):
        """run() 对每只股票都生成结果"""
        codes = ["600519", "000001", "AAPL"]
        pipeline = self._make_runnable_pipeline(codes)
        results = pipeline.run(codes)
        self.assertEqual(len(results), 3)
        result_codes = {r.stock_code for r in results}
        self.assertEqual(result_codes, set(codes))

    def test_run_empty_list_returns_empty(self):
        """空列表输入返回空列表"""
        pipeline = self._make_runnable_pipeline([])
        results = pipeline.run([])
        self.assertEqual(results, [])

    def test_run_partial_failure_skips_failed(self):
        """部分股票失败时只返回成功的"""
        with patch(
            "src.core.pipeline.StockAnalysisPipeline._load_default_config",
            return_value=None,
        ):
            p = StockAnalysisPipeline(config=None, max_workers=2)

        p._initialized = True
        p._data_manager = MagicMock()
        p._analyzer = MagicMock()
        p._strategy_manager = None
        p._notification_service = None
        p._report_renderer = None

        def mock_process(code, **kwargs):
            if code == "FAIL":
                return None
            return _make_analysis_result(stock_code=code)

        p.process_single_stock = MagicMock(side_effect=mock_process)

        results = p.run(["600519", "FAIL", "000001"])
        self.assertEqual(len(results), 2)
        result_codes = {r.stock_code for r in results}
        self.assertNotIn("FAIL", result_codes)


if __name__ == "__main__":
    unittest.main()
