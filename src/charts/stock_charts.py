"""
股票图表生成模块
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import akshare as ak
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Pie, HeatMap
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot as driver

from ..utils.logger import get_logger
from ..config.settings import settings


class StockChartGenerator:
    """股票图表生成器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.output_dir = settings.IMAGE_DIR / "charts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_kline_chart(
        self,
        stock_code: str,
        stock_name: str,
        market: str = "A股",
        days: int = 90,
        output_path: Path = None,
    ) -> Optional[Path]:
        """
        生成K线图

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            market: 市场类型
            days: 历史天数
            output_path: 输出路径

        Returns:
            Path: 图表文件路径
        """
        try:
            # 获取历史数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

            if market == "A股":
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
            elif market == "港股":
                df = ak.stock_hk_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
            elif market == "美股":
                df = ak.stock_us_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
            else:
                self.logger.error(f"不支持的市场类型: {market}")
                return None

            if df.empty:
                self.logger.error(f"获取数据为空: {stock_code}")
                return None

            # 准备数据
            dates = df["日期"].tolist()
            kline_data = df[["开盘", "收盘", "最低", "最高"]].values.tolist()
            volumes = df["成交量"].tolist()

            # 创建K线图
            kline = (
                Kline()
                .add_xaxis(dates)
                .add_yaxis(
                    "K线",
                    kline_data,
                    itemstyle_opts=opts.ItemStyleOpts(
                        color="#ef232a",
                        color0="#14b143",
                        border_color="#ef232a",
                        border_color0="#14b143",
                    ),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{stock_name} ({stock_code})"),
                    xaxis_opts=opts.AxisOpts(is_scale=True),
                    yaxis_opts=opts.AxisOpts(
                        is_scale=True,
                        splitarea_opts=opts.SplitAreaOpts(
                            is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                        ),
                    ),
                    tooltip_opts=opts.TooltipOpts(
                        trigger="axis", axis_pointer_type="cross"
                    ),
                    datazoom_opts=[
                        opts.DataZoomOpts(type_="inside", xaxis_index=[0, 1]),
                        opts.DataZoomOpts(type_="slider", xaxis_index=[0, 1]),
                    ],
                )
            )

            # 创建成交量柱状图
            bar = (
                Bar()
                .add_xaxis(dates)
                .add_yaxis(
                    "成交量",
                    volumes,
                    xaxis_index=1,
                    yaxis_index=1,
                    label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(
                        color="#ef232a",
                        color0="#14b143",
                    ),
                )
                .set_global_opts(
                    xaxis_opts=opts.AxisOpts(
                        type_="category",
                        is_scale=True,
                        grid_index=1,
                        boundary_gap=False,
                        axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                        axistick_opts=opts.AxisTickOpts(is_show=False),
                        splitline_opts=opts.SplitLineOpts(is_show=False),
                        axislabel_opts=opts.LabelOpts(is_show=False),
                        split_number=20,
                        min_="dataMin",
                        max_="dataMax",
                    ),
                    yaxis_opts=opts.AxisOpts(
                        grid_index=1,
                        is_scale=True,
                        split_number=2,
                        axislabel_opts=opts.LabelOpts(is_show=False),
                        axisline_opts=opts.AxisLineOpts(is_show=False),
                        axistick_opts=opts.AxisTickOpts(is_show=False),
                        splitline_opts=opts.SplitLineOpts(is_show=False),
                    ),
                )
            )

            # 组合图表
            from pyecharts.charts import Grid

            grid = (
                Grid(init_opts=opts.InitOpts(width="1200px", height="600px"))
                .add(
                    kline,
                    grid_opts=opts.GridOpts(
                        pos_left="10%", pos_right="10%", height="50%"
                    ),
                )
                .add(
                    bar,
                    grid_opts=opts.GridOpts(
                        pos_left="10%", pos_right="10%", pos_top="60%", height="25%"
                    ),
                )
            )

            # 保存图表
            if output_path is None:
                output_path = (
                    self.output_dir
                    / f"kline_{stock_code}_{datetime.now().strftime('%Y%m%d')}.html"
                )

            grid.render(str(output_path))

            self.logger.info(f"K线图生成成功: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"生成K线图失败: {e}")
            return None

    def generate_sector_heatmap(self, output_path: Path = None) -> Optional[Path]:
        """
        生成板块热力图

        Args:
            output_path: 输出路径

        Returns:
            Path: 图表文件路径
        """
        try:
            # 获取板块数据
            df = ak.stock_sector_spot()

            if df.empty:
                self.logger.error("获取板块数据为空")
                return None

            # 准备数据
            data = []
            for _, row in df.iterrows():
                sector_name = row.get("板块名称", "")
                change_pct = row.get("涨跌幅", 0)
                if sector_name and change_pct is not None:
                    data.append([sector_name, float(change_pct)])

            # 创建热力图
            heatmap = (
                HeatMap()
                .add(
                    "板块",
                    data,
                    xaxis_data=[d[0] for d in data[:20]],
                    yaxis_data=["涨跌幅"],
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="板块热力图"),
                    visualmap_opts=opts.VisualMapOpts(
                        min_=-5,
                        max_=5,
                        is_piecewise=True,
                        pieces=[
                            {
                                "min": -10,
                                "max": -5,
                                "label": "<-5%",
                                "color": "#00aa00",
                            },
                            {
                                "min": -5,
                                "max": -2,
                                "label": "-5%~-2%",
                                "color": "#88cc88",
                            },
                            {
                                "min": -2,
                                "max": 0,
                                "label": "-2%~0%",
                                "color": "#cccccc",
                            },
                            {"min": 0, "max": 2, "label": "0%~2%", "color": "#ffcccc"},
                            {"min": 2, "max": 5, "label": "2%~5%", "color": "#ff8888"},
                            {"min": 5, "max": 10, "label": ">5%", "color": "#ff4444"},
                        ],
                    ),
                )
            )

            # 保存图表
            if output_path is None:
                output_path = (
                    self.output_dir
                    / f"heatmap_{datetime.now().strftime('%Y%m%d')}.html"
                )

            heatmap.render(str(output_path))

            self.logger.info(f"板块热力图生成成功: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"生成板块热力图失败: {e}")
            return None

    def generate_money_flow_chart(self, output_path: Path = None) -> Optional[Path]:
        """
        生成资金流向柱状图

        Args:
            output_path: 输出路径

        Returns:
            Path: 图表文件路径
        """
        try:
            # 获取资金流向数据
            df = ak.stock_market_fund_flow()

            if df.empty:
                self.logger.error("获取资金流向数据为空")
                return None

            # 准备数据
            dates = df["日期"].tolist()[-30:]  # 最近30天
            main_inflow = df["主力净流入"].tolist()[-30:]

            # 创建柱状图
            bar = (
                Bar()
                .add_xaxis(dates)
                .add_yaxis(
                    "主力净流入",
                    main_inflow,
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=lambda params: (
                            "#ff4444" if params.data >= 0 else "#00aa00"
                        )
                    ),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="主力资金流向"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                    yaxis_opts=opts.AxisOpts(name="亿元"),
                )
            )

            # 保存图表
            if output_path is None:
                output_path = (
                    self.output_dir
                    / f"money_flow_{datetime.now().strftime('%Y%m%d')}.html"
                )

            bar.render(str(output_path))

            self.logger.info(f"资金流向图生成成功: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"生成资金流向图失败: {e}")
            return None

    def generate_distribution_pie(self, output_path: Path = None) -> Optional[Path]:
        """
        生成涨跌分布饼图

        Args:
            output_path: 输出路径

        Returns:
            Path: 图表文件路径
        """
        try:
            # 获取涨跌数据
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                self.logger.error("获取涨跌数据为空")
                return None

            # 统计涨跌分布
            up_count = len(df[df["涨跌幅"] > 0])
            down_count = len(df[df["涨跌幅"] < 0])
            flat_count = len(df[df["涨跌幅"] == 0])
            limit_up = len(df[df["涨跌幅"] >= 9.9])
            limit_down = len(df[df["涨跌幅"] <= -9.9])

            # 创建饼图
            pie = (
                Pie()
                .add(
                    "",
                    [
                        ["涨停", limit_up],
                        ["上涨", up_count - limit_up],
                        ["平盘", flat_count],
                        ["下跌", down_count - limit_down],
                        ["跌停", limit_down],
                    ],
                    radius=["30%", "75%"],
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="涨跌分布"),
                    legend_opts=opts.LegendOpts(
                        orient="vertical", pos_top="15%", pos_left="2%"
                    ),
                )
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)"))
            )

            # 保存图表
            if output_path is None:
                output_path = (
                    self.output_dir
                    / f"distribution_{datetime.now().strftime('%Y%m%d')}.html"
                )

            pie.render(str(output_path))

            self.logger.info(f"涨跌分布图生成成功: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"生成涨跌分布图失败: {e}")
            return None

    def render_chart_to_image(
        self, chart_path: Path, output_path: Path = None
    ) -> Optional[Path]:
        """
        将图表渲染为图片

        Args:
            chart_path: 图表HTML文件路径
            output_path: 输出图片路径

        Returns:
            Path: 图片文件路径
        """
        try:
            if output_path is None:
                output_path = chart_path.with_suffix(".png")

            # 使用selenium截图
            make_snapshot(driver, str(chart_path), str(output_path))

            self.logger.info(f"图表渲染为图片成功: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"渲染图表为图片失败: {e}")
            return None
