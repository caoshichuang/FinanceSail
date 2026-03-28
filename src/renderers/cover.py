"""
封面图渲染模块（Pillow版本，无需浏览器）
"""

from pathlib import Path
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
from ..utils.logger import get_logger
from ..exceptions.errors import ImageRenderError


class CoverRenderer:
    """封面图渲染器（Pillow版）"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.width = 1080
        self.height = 1440

    async def render(self, data: Dict[str, Any], output_path: Path) -> Path:
        """
        渲染封面图

        Args:
            data: 封面数据
                - title: 主标题
                - subtitle: 副标题
                - date: 日期
            output_path: 输出路径

        Returns:
            Path: 输出文件路径
        """
        try:
            # 创建渐变背景
            img = self._create_gradient_background()
            draw = ImageDraw.Draw(img)

            # 获取字体
            title_font = self._get_font(60)
            subtitle_font = self._get_font(32)
            date_font = self._get_font(24)
            badge_font = self._get_font(18)

            # 绘制日期角标
            date_text = data.get("date", "")
            self._draw_badge(draw, date_text, (self.width - 200, 40), date_font)

            # 绘制主标题
            title = data.get("title", "")
            self._draw_centered_text(
                draw, title, self.height // 2 - 80, title_font, "white"
            )

            # 绘制副标题
            subtitle = data.get("subtitle", "")
            if subtitle:
                self._draw_centered_text(
                    draw,
                    subtitle,
                    self.height // 2 + 40,
                    subtitle_font,
                    "white",
                    alpha=200,
                )

            # 绘制AI标识
            self._draw_badge(draw, "AI辅助创作", (60, self.height - 100), badge_font)

            # 保存图片
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_path), "PNG")

            self.logger.info(f"封面图渲染成功: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"封面图渲染失败: {e}")
            raise ImageRenderError(f"封面图渲染失败: {e}") from e

    def _create_gradient_background(self) -> Image.Image:
        """创建渐变背景"""
        img = Image.new("RGBA", (self.width, self.height))
        draw = ImageDraw.Draw(img)

        # 渐变色：从 #667eea 到 #764ba2
        for y in range(self.height):
            r = int(102 + (118 - 102) * y / self.height)
            g = int(126 + (75 - 126) * y / self.height)
            b = int(234 + (162 - 234) * y / self.height)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b, 255))

        return img

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """获取字体"""
        # 尝试系统字体
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

        # 如果没有找到字体，使用默认字体
        self.logger.warning("未找到中文字体，使用默认字体")
        return ImageFont.load_default()

    def _draw_centered_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: str = "white",
        alpha: int = 255,
    ):
        """绘制居中文本"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2

        # 添加阴影效果
        if alpha == 255:
            draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 100))

        draw.text((x, y), text, font=font, fill=color)

    def _draw_badge(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position: tuple,
        font: ImageFont.FreeTypeFont,
    ):
        """绘制角标"""
        x, y = position
        padding = 15

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 绘制半透明背景
        badge_x = x - padding
        badge_y = y - padding
        badge_width = text_width + padding * 2
        badge_height = text_height + padding * 2

        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_width, badge_y + badge_height],
            radius=20,
            fill=(255, 255, 255, 50),
        )

        # 绘制文字
        draw.text((x, y), text, font=font, fill="white")
