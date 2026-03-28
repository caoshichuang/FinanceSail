"""
字卡渲染模块（Pillow版本，无需浏览器）
"""

from pathlib import Path
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
from ..utils.logger import get_logger
from ..exceptions.errors import ImageRenderError


class CardsRenderer:
    """字卡渲染器（Pillow版）"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.width = 1080
        self.height = 1440

    async def render(
        self, cards: List[str], output_dir: Path, prefix: str = "card"
    ) -> List[Path]:
        """
        渲染多张字卡

        Args:
            cards: 字卡内容列表
            output_dir: 输出目录
            prefix: 文件名前缀

        Returns:
            List[Path]: 输出文件路径列表
        """
        output_paths = []

        try:
            for i, card_content in enumerate(cards, 1):
                output_path = output_dir / f"{prefix}_{i}.png"
                self._render_single_card(i, card_content, output_path)
                output_paths.append(output_path)

            self.logger.info(f"字卡渲染成功: {len(output_paths)}张")
            return output_paths

        except Exception as e:
            self.logger.error(f"字卡渲染失败: {e}")
            raise ImageRenderError(f"字卡渲染失败: {e}") from e

    def _render_single_card(self, card_number: int, content: str, output_path: Path):
        """
        渲染单张字卡

        Args:
            card_number: 字卡编号
            content: 字卡内容
            output_path: 输出路径
        """
        # 创建白色背景
        img = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(img)

        # 获取字体
        number_font = self._get_font(28)
        title_font = self._get_font(42)
        body_font = self._get_font(28)
        footer_font = self._get_font(18)

        # 绘制字卡编号圆圈
        self._draw_number_circle(draw, card_number, number_font)

        # 解析内容
        title, body = self._parse_content(content)

        # 绘制标题
        self._draw_text(draw, title, 160, title_font, "#333333")

        # 绘制正文
        self._draw_multiline_text(draw, body, 260, body_font, "#666666")

        # 绘制页脚
        self._draw_footer(draw, footer_font)

        # 保存图片
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path), "PNG")

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """获取字体"""
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]

        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (OSError, IOError):
                continue

        self.logger.warning("未找到中文字体，使用默认字体")
        return ImageFont.load_default()

    def _draw_number_circle(
        self, draw: ImageDraw.Draw, number: int, font: ImageFont.FreeTypeFont
    ):
        """绘制编号圆圈"""
        x, y = 60, 60
        radius = 30

        # 绘制紫色圆圈
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill="#667eea")

        # 绘制数字
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = x - text_width // 2
        text_y = y - text_height // 2 - 5
        draw.text((text_x, text_y), text, font=font, fill="white")

    def _draw_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: str = "#333333",
    ):
        """绘制单行文本"""
        x = 80
        draw.text((x, y), text, font=font, fill=color)

    def _draw_multiline_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        start_y: int,
        font: ImageFont.FreeTypeFont,
        color: str = "#666666",
    ):
        """绘制多行文本"""
        x = 80
        y = start_y
        line_height = 50
        max_width = self.width - 160

        # 按行分割
        lines = text.split("\n")

        for line in lines:
            if not line.strip():
                y += line_height // 2
                continue

            # 处理长行自动换行
            wrapped_lines = self._wrap_text(line, font, max_width)
            for wrapped_line in wrapped_lines:
                if y > self.height - 150:  # 留出页脚空间
                    return
                draw.text((x, y), wrapped_line, font=font, fill=color)
                y += line_height

    def _wrap_text(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int
    ) -> List[str]:
        """文本自动换行"""
        words = list(text)
        lines = []
        current_line = ""

        for char in words:
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            if bbox[2] > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = char
            else:
                current_line = test_line

        if current_line:
            lines.append(current_line)

        return lines if lines else [text]

    def _draw_footer(self, draw: ImageDraw.Draw, font: ImageFont.FreeTypeFont):
        """绘制页脚"""
        y = self.height - 80

        # 绘制分隔线
        draw.line([(80, y - 20), (self.width - 80, y - 20)], fill="#eeeeee", width=2)

        # 绘制数据来源
        draw.text((80, y), "数据来源：AKShare、东方财富", font=font, fill="#999999")

    def _parse_content(self, content: str) -> tuple:
        """
        解析字卡内容

        Args:
            content: 字卡内容

        Returns:
            tuple: (标题, 正文)
        """
        lines = content.strip().split("\n")
        if len(lines) > 1:
            title = lines[0].strip("# ").strip()
            body = "\n".join(lines[1:])
        else:
            title = "详情"
            body = content

        return title, body
