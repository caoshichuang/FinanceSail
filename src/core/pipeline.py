"""
股票分析核心 Pipeline

负责串联数据获取 → 技术分析 → AI 分析 → 报告渲染 → 通知推送的完整流程。
"""

import asyncio
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class StockAnalysisPipeline:
    """
    股票分析流水线

    使用示例：
        pipeline = StockAnalysisPipeline()
        results = pipeline.run(["600519", "AAPL", "00700"])
    """

    def __init__(self, config=None, max_workers: int = 4):
        """
        初始化 Pipeline

        Args:
            config: 配置对象（settings 实例或任意带属性的对象）
            max_workers: 并发分析最大线程数
        """
        self._config = config or self._load_default_config()
        self._max_workers = max_workers

        # 延迟初始化各子模块（避免循环导入）
        self._data_manager = None
        self._analyzer = None
        self._strategy_manager = None
        self._notification_service = None
        self._report_renderer = None

        self._initialized = False

    # ──────────────────────────────────────────────
    # 初始化
    # ──────────────────────────────────────────────

    def _load_default_config(self):
        """加载默认全局配置"""
        try:
            from src.config.settings import settings

            return settings
        except Exception as e:
            logger.warning(f"加载默认配置失败，使用空配置: {e}")
            return None

    def _ensure_initialized(self) -> None:
        """懒加载初始化各子模块"""
        if self._initialized:
            return

        # 数据源管理器
        try:
            from data_provider.base import DataFetcherManager

            self._data_manager = DataFetcherManager()
            logger.debug("DataFetcherManager 初始化成功")
        except Exception as e:
            logger.error(f"DataFetcherManager 初始化失败: {e}")

        # AI 分析器
        try:
            from src.analyzer import StockAnalyzer

            self._analyzer = StockAnalyzer(config=self._config)
            logger.debug("StockAnalyzer 初始化成功")
        except Exception as e:
            logger.error(f"StockAnalyzer 初始化失败: {e}")

        # 策略管理器
        try:
            from src.strategies import SkillManager

            self._strategy_manager = SkillManager()
            logger.debug("SkillManager 初始化成功")
        except Exception as e:
            logger.warning(f"SkillManager 初始化失败，将使用默认 Prompt: {e}")

        # 通知服务
        try:
            from src.notifiers.notification_service import NotificationService

            self._notification_service = NotificationService(config=self._config)
            logger.debug("NotificationService 初始化成功")
        except Exception as e:
            logger.error(f"NotificationService 初始化失败: {e}")

        # 报告渲染器（可选）
        try:
            from src.services.report_renderer import ReportRenderer

            self._report_renderer = ReportRenderer()
            logger.debug("ReportRenderer 初始化成功")
        except Exception as e:
            logger.warning(f"ReportRenderer 初始化失败，将使用纯文本输出: {e}")

        self._initialized = True

    # ──────────────────────────────────────────────
    # Step 1: 数据获取
    # ──────────────────────────────────────────────

    def fetch_and_save_stock_data(
        self, stock_code: str, days: int = 60
    ) -> Tuple[Optional[Any], str]:
        """
        获取并返回标准化股票数据

        Args:
            stock_code: 股票代码
            days: 获取天数

        Returns:
            (DataFrame 或 None, 数据源名称)
        """
        if not self._data_manager:
            logger.error("DataFetcherManager 未初始化")
            return None, ""

        try:
            df, source = self._data_manager.get_daily_data(stock_code, days=days)
            logger.info(f"[{stock_code}] 数据获取成功，来源: {source}，行数: {len(df)}")
            return df, source
        except Exception as e:
            logger.error(f"[{stock_code}] 数据获取失败: {e}")
            return None, ""

    # ──────────────────────────────────────────────
    # Step 2: 上下文增强
    # ──────────────────────────────────────────────

    def _enhance_context(
        self,
        stock_code: str,
        df: Any,
        source: str,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        构建分析上下文，融合行情数据 + 策略 Prompt + 扩展信息

        Args:
            stock_code: 股票代码
            df: 行情 DataFrame
            source: 数据来源名称
            extra_context: 外部传入的额外上下文

        Returns:
            增强后的上下文字典
        """
        context: Dict[str, Any] = {
            "stock_code": stock_code,
            "data_source": source,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "extra": extra_context or {},
        }

        # 行情数据摘要
        if df is not None and len(df) > 0:
            try:
                latest = df.iloc[-1]
                context["latest_close"] = float(latest.get("close", 0))
                context["latest_pct_chg"] = float(latest.get("pct_chg", 0))
                context["data_rows"] = len(df)
                context["date_range"] = (
                    f"{df.iloc[0].get('date', '')} ~ {df.iloc[-1].get('date', '')}"
                    if "date" in df.columns
                    else ""
                )
            except Exception as e:
                logger.debug(f"[{stock_code}] 构建行情摘要时出错: {e}")

        # 策略 Prompt 注入
        if self._strategy_manager:
            try:
                strategy_prompt = self._strategy_manager.build_combined_prompt()
                if strategy_prompt:
                    context["strategy_prompt"] = strategy_prompt
            except Exception as e:
                logger.debug(f"[{stock_code}] 策略 Prompt 构建失败: {e}")

        return context

    # ──────────────────────────────────────────────
    # Step 3: AI 分析
    # ──────────────────────────────────────────────

    def analyze_stock(
        self,
        stock_code: str,
        df: Any,
        context: Dict[str, Any],
        news_context: str = "",
    ):
        """
        调用 AI 分析器对单支股票进行分析

        Args:
            stock_code: 股票代码
            df: 行情 DataFrame
            context: 增强上下文
            news_context: 新闻/资讯文本

        Returns:
            AnalysisResult 或 None
        """
        if not self._analyzer:
            logger.error("StockAnalyzer 未初始化")
            return None

        try:
            result = self._analyzer.analyze(
                stock_code=stock_code,
                df=df,
                context=context,
                news_context=news_context,
            )
            logger.info(
                f"[{stock_code}] AI 分析完成，情绪评分: {result.sentiment_score}, "
                f"模型: {result.model_used}"
            )
            return result
        except Exception as e:
            logger.error(f"[{stock_code}] AI 分析失败: {e}")
            return None

    # ──────────────────────────────────────────────
    # Step 4: 单支股票完整处理
    # ──────────────────────────────────────────────

    def process_single_stock(
        self,
        stock_code: str,
        days: int = 60,
        news_context: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        处理单支股票的完整分析流程：
        数据获取 → 上下文增强 → AI 分析

        Args:
            stock_code: 股票代码
            days: 历史数据天数
            news_context: 新闻/资讯
            extra_context: 额外上下文

        Returns:
            AnalysisResult 或 None（失败时）
        """
        self._ensure_initialized()

        logger.info(f"[{stock_code}] 开始处理")

        # Step 1: 数据获取
        df, source = self.fetch_and_save_stock_data(stock_code, days=days)
        if df is None:
            logger.warning(f"[{stock_code}] 数据获取失败，跳过")
            return None

        # Step 2: 上下文增强
        context = self._enhance_context(
            stock_code, df, source, extra_context=extra_context
        )

        # Step 3: AI 分析
        result = self.analyze_stock(stock_code, df, context, news_context=news_context)
        if result is None:
            logger.warning(f"[{stock_code}] AI 分析失败，跳过")
            return None

        logger.info(f"[{stock_code}] 处理完成 ✓")
        return result

    # ──────────────────────────────────────────────
    # Step 5: 报告渲染 & 推送
    # ──────────────────────────────────────────────

    def _render_report(self, results: List[Any], template: str = "markdown") -> str:
        """
        渲染分析报告

        Args:
            results: AnalysisResult 列表
            template: 模板名称（markdown / wechat）

        Returns:
            渲染后的报告字符串
        """
        if self._report_renderer:
            try:
                return self._report_renderer.render(results, template=template)
            except Exception as e:
                logger.warning(f"报告渲染失败，降级为纯文本: {e}")

        # 降级：拼接纯文本
        lines: List[str] = [
            f"# FinanceSail 市场分析报告 {datetime.now().strftime('%Y-%m-%d')}",
            "",
        ]
        for r in results:
            lines.append(f"## {r.stock_name or r.stock_code} ({r.stock_code})")
            lines.append(f"- 情绪评分: {r.sentiment_score}")
            lines.append(f"- 操作建议: {r.operation_advice}")
            lines.append(f"- 风险等级: {r.risk_level}")
            lines.append(f"- 分析摘要: {r.analysis_summary}")
            lines.append("")
        return "\n".join(lines)

    def _send_report(self, report_content: str, subject: str = "") -> bool:
        """
        推送报告到所有已配置渠道

        Args:
            report_content: 报告正文
            subject: 邮件主题

        Returns:
            bool: 是否至少一个渠道成功
        """
        if not self._notification_service:
            logger.warning("NotificationService 未初始化，跳过推送")
            return False

        subject = (
            subject or f"FinanceSail 市场报告 {datetime.now().strftime('%Y-%m-%d')}"
        )
        return self._notification_service.send(report_content, subject=subject)

    # ──────────────────────────────────────────────
    # Step 6: 主入口
    # ──────────────────────────────────────────────

    def run(
        self,
        stock_codes: List[str],
        days: int = 60,
        news_context: str = "",
        send_notification: bool = True,
        template: str = "markdown",
    ) -> List[Any]:
        """
        并发分析多支股票，汇总后推送报告

        Args:
            stock_codes: 股票代码列表
            days: 历史数据天数
            news_context: 新闻/资讯文本（全局）
            send_notification: 是否推送通知
            template: 报告模板（markdown / wechat）

        Returns:
            成功的 AnalysisResult 列表
        """
        self._ensure_initialized()

        if not stock_codes:
            logger.warning("stock_codes 为空，跳过")
            return []

        logger.info(
            f"开始批量分析 {len(stock_codes)} 支股票，并发数: {self._max_workers}"
        )

        results: List[Any] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers
        ) as executor:
            future_to_code = {
                executor.submit(
                    self.process_single_stock,
                    code,
                    days,
                    news_context,
                ): code
                for code in stock_codes
            }

            for future in concurrent.futures.as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    logger.error(f"[{code}] 处理时发生未预期异常: {e}")

        logger.info(f"批量分析完成：{len(results)}/{len(stock_codes)} 支成功")

        # 渲染 & 推送报告
        if results and send_notification:
            report = self._render_report(results, template=template)
            self._send_report(report)

        return results

    async def run_async(
        self,
        stock_codes: List[str],
        days: int = 60,
        news_context: str = "",
        send_notification: bool = True,
        template: str = "markdown",
    ) -> List[Any]:
        """
        异步版本的 run（在事件循环中执行阻塞 IO）
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.run(
                stock_codes,
                days=days,
                news_context=news_context,
                send_notification=send_notification,
                template=template,
            ),
        )
