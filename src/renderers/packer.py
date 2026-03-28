"""
图片打包模块
"""

import zipfile
from pathlib import Path
from typing import List
from ..utils.logger import get_logger


class ImagePacker:
    """图片打包器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def pack(self, image_paths: List[Path], output_path: Path) -> Path:
        """
        将图片打包为zip文件

        Args:
            image_paths: 图片路径列表
            output_path: 输出zip文件路径

        Returns:
            Path: zip文件路径
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for image_path in image_paths:
                    if image_path.exists():
                        zipf.write(image_path, image_path.name)
                        self.logger.debug(f"添加文件到zip: {image_path.name}")
                    else:
                        self.logger.warning(f"文件不存在，跳过: {image_path}")

            self.logger.info(f"图片打包成功: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"图片打包失败: {e}")
            raise
