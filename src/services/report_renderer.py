"""
报告渲染引擎

使用 Jinja2 将 AnalysisResult 列表渲染为 Markdown / 企业微信 / 纯文本报告。
支持 zh/en 双语标签，以及 simple/full/brief 三种报告类型。
"""

from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# 模板目录：项目根/templates/
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# 语言标签（中/英）
_LABELS = {
    "zh": {
        "signal_buy": "买入",
        "signal_hold": "观望",
        "signal_sell": "卖出",
        "sentiment": "情绪评分",
        "risk": "风险等级",
        "advice": "操作建议",
        "summary": "分析摘要",
        "disclaimer": "仅供参考，不构成投资建议",
    },
    "en": {
        "signal_buy": "Buy",
        "signal_hold": "Hold",
        "signal_sell": "Sell",
        "sentiment": "Sentiment Score",
        "risk": "Risk Level",
        "advice": "Operation Advice",
        "summary": "Analysis Summary",
        "disclaimer": "For reference only, not investment advice",
    },
}


class ReportRenderer:
    """
    Jinja2 报告渲染器

    使用示例：
        renderer = ReportRenderer(lang="zh")
        text = renderer.render(results, template="markdown")
    """

    def __init__(self, lang: str = "zh", report_type: str = "full"):
        """
        Args:
            lang: 报告语言（zh / en）
            report_type: 报告类型（simple / full / brief）
        """
        self._lang = lang if lang in ("zh", "en") else "zh"
        self._report_type = report_type
        self._jinja_env = None
        self._labels = _LABELS.get(self._lang, _LABELS["zh"])

        # 尝试初始化 Jinja2
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            self._jinja_env = Environment(
                loader=FileSystemLoader(str(_TEMPLATES_DIR)),
                autoescape=select_autoescape([]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            logger.debug(f"Jinja2 初始化成功，模板目录: {_TEMPLATES_DIR}")
        except ImportError:
            logger.warning("jinja2 未安装，将使用内置纯文本渲染")
        except Exception as e:
            logger.warning(f"Jinja2 初始化失败，将使用内置纯文本渲染: {e}")

    def render(
        self,
        results: List[Any],
        template: str = "markdown",
        report_date: Optional[str] = None,
        summary_only: bool = False,
    ) -> str:
        """
        渲染报告

        Args:
            results: AnalysisResult 列表
            template: 模板名称（markdown / wechat）
            report_date: 报告日期（默认今天）
            summary_only: 仅输出摘要

        Returns:
            渲染后的报告字符串
        """
        report_date = report_date or datetime.now().strftime("%Y-%m-%d")

        if summary_only:
            results = [r for r in results if r is not None]
            return self._render_summary(results, report_date)

        # 按报告类型筛选内容
        if self._report_type == "brief":
            return self._render_brief(results, report_date)

        # Jinja2 渲染
        if self._jinja_env:
            template_file = self._resolve_template_file(template)
            if template_file:
                try:
                    tmpl = self._jinja_env.get_template(template_file)
                    return tmpl.render(
                        results=results,
                        report_date=report_date,
                        lang=self._lang,
                        labels=self._labels,
                        report_type=self._report_type,
                    )
                except Exception as e:
                    logger.warning(f"Jinja2 渲染失败，降级纯文本: {e}")

        # 降级：内置渲染
        return self._render_fallback(results, report_date)

    def _resolve_template_file(self, template: str) -> Optional[str]:
        """解析模板文件名"""
        mapping = {
            "markdown": "report_markdown.j2",
            "wechat": "report_wechat.j2",
        }
        filename = mapping.get(template, f"report_{template}.j2")
        path = _TEMPLATES_DIR / filename
        if path.exists():
            return filename
        logger.warning(f"模板文件不存在: {path}，降级为内置渲染")
        return None

    def _render_fallback(self, results: List[Any], report_date: str) -> str:
        """内置 Markdown 纯文本渲染（无 Jinja2 依赖）"""
        lbl = self._labels
        lines = [
            f"# FinanceSail 市场分析报告 {report_date}",
            "",
        ]
        for r in results:
            if r is None:
                continue
            name = getattr(r, "stock_name", None) or getattr(r, "stock_code", "")
            code = getattr(r, "stock_code", "")
            lines.append(f"## {name} ({code})")
            lines.append(
                f"- {lbl['sentiment']}: {getattr(r, 'sentiment_score', 'N/A')}/100"
            )
            lines.append(f"- {lbl['risk']}: {getattr(r, 'risk_level', 'N/A')}")
            lines.append(f"- {lbl['advice']}: {getattr(r, 'operation_advice', 'N/A')}")
            summary = getattr(r, "analysis_summary", "")
            if summary:
                lines.append(f"- {lbl['summary']}: {summary}")
            lines.append("")

        lines.append(f"*{report_date} · {lbl['disclaimer']}*")
        return "\n".join(lines)

    def _render_brief(self, results: List[Any], report_date: str) -> str:
        """Brief 模式：每支股票 1-2 句话摘要"""
        lbl = self._labels
        parts = [f"FinanceSail | {report_date}"]
        for r in results:
            if r is None:
                continue
            name = getattr(r, "stock_name", None) or getattr(r, "stock_code", "")
            advice = getattr(r, "operation_advice", "")
            score = getattr(r, "sentiment_score", None)
            score_str = f"{score}/100" if score is not None else "-"
            parts.append(
                f"{name}: {lbl['advice']}={advice} | {lbl['sentiment']}={score_str}"
            )

        parts.append(f"\n⚠️ {lbl['disclaimer']}")
        return "\n".join(parts)

    def _render_summary(self, results: List[Any], report_date: str) -> str:
        """仅摘要模式"""
        lbl = self._labels
        lines = [f"# FinanceSail 摘要 {report_date}", ""]
        for r in results:
            if r is None:
                continue
            name = getattr(r, "stock_name", None) or getattr(r, "stock_code", "")
            summary = getattr(r, "analysis_summary", "")
            lines.append(f"**{name}**: {summary or '-'}")
        lines.append(f"\n*{lbl['disclaimer']}*")
        return "\n".join(lines)
