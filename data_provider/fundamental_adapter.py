"""
基本面数据适配器

汇聚估值、财报、分红、板块等多维度基本面数据，
支持超时保护、LRU 缓存和降级（fail-open）机制。
"""

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from functools import lru_cache
from typing import Any, Dict, List, Optional

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# 默认超时（秒）
_FETCH_TIMEOUT_SECONDS = 10
_STAGE_TIMEOUT_SECONDS = 30

# LRU 缓存最大条目（利用 functools.lru_cache，maxsize 控制数量）
_CACHE_MAX_ENTRIES = 128

# 简单 TTL 内存缓存（股票代码 → (timestamp, data)）
_fund_cache: Dict[str, tuple] = {}
_CACHE_TTL_SECONDS = 3600  # 1 小时


def _is_cn_stock(code: str) -> bool:
    """判断是否是 A 股代码"""
    return code.isdigit() and len(code) == 6


# ──────────────────────────────────────────────────────────
# 各子模块数据获取函数（内部，带超时）
# ──────────────────────────────────────────────────────────


def _fetch_valuation(code: str) -> Optional[Dict[str, Any]]:
    """
    获取估值数据（PE / PB / PS）

    优先 AKShare，失败时返回 None。
    """
    try:
        import akshare as ak  # type: ignore

        # stock_a_lg_indicator: 个股 PE/PB/市值
        df = ak.stock_a_lg_indicator(symbol=code)
        if df is None or df.empty:
            return None
        row = df.iloc[-1]
        return {
            "pe_ttm": _safe_float(row.get("pe")),
            "pb": _safe_float(row.get("pb")),
            "ps_ttm": _safe_float(row.get("ps")),
            "total_mv": _safe_float(row.get("total_mv")),
        }
    except Exception as e:
        logger.debug(f"[{code}] 估值数据获取失败: {e}")
        return None


def _fetch_financial_report(code: str) -> Optional[Dict[str, Any]]:
    """
    获取最新财报摘要（营收/净利润/现金流/ROE）
    """
    try:
        import akshare as ak  # type: ignore

        # 获取利润表
        df = ak.stock_financial_report_sina(stock=code, symbol="利润表")
        if df is None or df.empty:
            return None

        df = df.set_index(df.columns[0]) if df.shape[0] > 0 else df
        latest_col = df.columns[0] if len(df.columns) > 0 else None
        if not latest_col:
            return None

        return {
            "report_date": str(latest_col),
            "revenue": _safe_float(
                df.loc["营业总收入", latest_col] if "营业总收入" in df.index else None
            ),
            "net_profit": _safe_float(
                df.loc["归母净利润", latest_col]
                if "归母净利润" in df.index
                else df.loc["净利润", latest_col]
                if "净利润" in df.index
                else None
            ),
            "operating_cash_flow": None,  # 需现金流量表，此处留空
            "roe": None,
        }
    except Exception as e:
        logger.debug(f"[{code}] 财报数据获取失败: {e}")
        return None


def _fetch_dividend(code: str) -> Optional[Dict[str, Any]]:
    """
    获取分红数据（近期分红事件/股息率）
    """
    try:
        import akshare as ak  # type: ignore

        df = ak.stock_history_dividend(symbol=code)
        if df is None or df.empty:
            return None

        events: List[Dict[str, Any]] = []
        for _, row in df.head(5).iterrows():
            events.append(
                {
                    "date": str(row.get("报告期", "")),
                    "cash_div": _safe_float(
                        row.get("现金分红（每股）", row.get("每股现金股利"))
                    ),
                }
            )

        return {
            "events": events,
            "ttm_cash_dividend_per_share": events[0].get("cash_div")
            if events
            else None,
            "ttm_dividend_yield_pct": None,  # 需结合最新股价计算
        }
    except Exception as e:
        logger.debug(f"[{code}] 分红数据获取失败: {e}")
        return None


def _fetch_sector_rankings() -> Optional[Dict[str, Any]]:
    """
    获取板块涨跌排名（今日）
    """
    try:
        import akshare as ak  # type: ignore

        df = ak.stock_board_industry_name_em()
        if df is None or df.empty:
            return None

        change_col = "涨跌幅" if "涨跌幅" in df.columns else df.columns[-1]
        sorted_df = df.sort_values(change_col, ascending=False)

        top = sorted_df.head(5)[["板块名称", change_col]].to_dict("records")
        bottom = sorted_df.tail(5)[["板块名称", change_col]].to_dict("records")

        return {"top": top, "bottom": bottom}
    except Exception as e:
        logger.debug(f"板块排名获取失败: {e}")
        return None


# ──────────────────────────────────────────────────────────
# 主适配器类
# ──────────────────────────────────────────────────────────


class FundamentalAdapter:
    """
    基本面数据适配器

    使用示例：
        adapter = FundamentalAdapter()
        ctx = adapter.get_fundamental_context("600519")
        # ctx["valuation"]["pe_ttm"] → 30.5
        # ctx["status"] → "complete" / "partial" / "failed"
    """

    def __init__(
        self,
        fetch_timeout: int = _FETCH_TIMEOUT_SECONDS,
        stage_timeout: int = _STAGE_TIMEOUT_SECONDS,
        cache_ttl: int = _CACHE_TTL_SECONDS,
    ):
        self._fetch_timeout = fetch_timeout
        self._stage_timeout = stage_timeout
        self._cache_ttl = cache_ttl

    # ──────────────────────────────────────────────
    # 缓存管理
    # ──────────────────────────────────────────────

    def _cache_get(self, code: str) -> Optional[Dict[str, Any]]:
        """从缓存取数据（TTL 未过期）"""
        entry = _fund_cache.get(code)
        if entry is None:
            return None
        ts, data = entry
        if time.time() - ts < self._cache_ttl:
            return data
        return None

    def _cache_set(self, code: str, data: Dict[str, Any]) -> None:
        """写入缓存（超出上限时清除最旧的条目）"""
        if len(_fund_cache) >= _CACHE_MAX_ENTRIES:
            oldest = min(_fund_cache.items(), key=lambda kv: kv[1][0])
            del _fund_cache[oldest[0]]
        _fund_cache[code] = (time.time(), data)

    # ──────────────────────────────────────────────
    # 超时保护包装
    # ──────────────────────────────────────────────

    def _run_with_timeout(self, fn, *args, timeout: int = None) -> Optional[Any]:
        """在独立线程中执行函数，超时后返回 None"""
        t = timeout or self._fetch_timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, *args)
            try:
                return future.result(timeout=t)
            except FuturesTimeout:
                logger.warning(f"{fn.__name__} 超时（{t}s）")
                return None
            except Exception as e:
                logger.debug(f"{fn.__name__} 异常: {e}")
                return None

    # ──────────────────────────────────────────────
    # 主接口
    # ──────────────────────────────────────────────

    def get_fundamental_context(self, code: str) -> Dict[str, Any]:
        """
        获取股票基本面上下文（含缓存 + 超时保护）

        Args:
            code: 股票代码

        Returns:
            dict，包含:
              valuation, earnings(growth/financial_report/dividend),
              boards, status, source_chain
        """
        # 缓存命中
        cached = self._cache_get(code)
        if cached is not None:
            logger.debug(f"[{code}] 基本面数据命中缓存")
            return cached

        context: Dict[str, Any] = {
            "stock_code": code,
            "status": "failed",
            "source_chain": [],
            "valuation": None,
            "earnings": {
                "growth": None,
                "financial_report": None,
                "dividend": None,
            },
            "boards": None,
        }

        # 仅 A 股才拉取 AKShare 基本面
        if not _is_cn_stock(code):
            context["status"] = "partial"
            context["source_chain"].append("unsupported_market")
            return context

        success_count = 0

        # 估值
        valuation = self._run_with_timeout(_fetch_valuation, code)
        if valuation:
            context["valuation"] = valuation
            context["source_chain"].append("valuation:akshare")
            success_count += 1

        # 财报
        financial = self._run_with_timeout(_fetch_financial_report, code)
        if financial:
            context["earnings"]["financial_report"] = financial
            context["source_chain"].append("financial_report:akshare")
            success_count += 1

        # 分红
        dividend = self._run_with_timeout(_fetch_dividend, code)
        if dividend:
            context["earnings"]["dividend"] = dividend
            context["source_chain"].append("dividend:akshare")
            success_count += 1

        # 板块排名（不依赖 code）
        boards = self._run_with_timeout(_fetch_sector_rankings)
        if boards:
            context["boards"] = boards
            context["source_chain"].append("boards:akshare")
            success_count += 1

        # 更新状态
        total_tasks = 4
        if success_count == total_tasks:
            context["status"] = "complete"
        elif success_count > 0:
            context["status"] = "partial"
        else:
            context["status"] = "failed"

        # 写入缓存
        self._cache_set(code, context)
        logger.info(f"[{code}] 基本面数据获取完成，状态: {context['status']}")
        return context


def _safe_float(val: Any) -> Optional[float]:
    """安全转换为 float，失败返回 None"""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
