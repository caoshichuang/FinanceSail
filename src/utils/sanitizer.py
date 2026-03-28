"""
敏感词过滤模块
"""

import re
from typing import List
from ..utils.logger import get_logger

logger = get_logger("sanitizer")


# 敏感词列表
SENSITIVE_WORDS = [
    # 投资建议相关
    "推荐买入",
    "建议买入",
    "强烈推荐",
    "买入评级",
    "目标价",
    "买入点",
    "卖出点",
    "加仓",
    "减仓",
    "抄底",
    "逃顶",
    "上车",
    "赶紧买",
    "快买",
    "快卖",
    "马上买",
    "马上卖",
    "必涨",
    "必跌",
    "肯定涨",
    "肯定跌",
    "稳赚",
    "稳赚不赔",
    "无风险",
    "包赚",
    "保本",
    # 违规词汇
    "内幕消息",
    "庄家",
    "主力资金",
    "拉升",
    "洗盘",
    "建仓完成",
    "即将暴涨",
    "即将暴跌",
]


class ContentSanitizer:
    """内容敏感词过滤器"""

    def __init__(self):
        self.sensitive_words = SENSITIVE_WORDS
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式"""
        self.patterns = [
            re.compile(re.escape(word), re.IGNORECASE) for word in self.sensitive_words
        ]

    def check(self, text: str) -> List[str]:
        """
        检查文本中的敏感词

        Args:
            text: 待检查文本

        Returns:
            List[str]: 发现的敏感词列表
        """
        found = []
        for pattern in self.patterns:
            matches = pattern.findall(text)
            found.extend(matches)
        return found

    def sanitize(self, text: str, replacement: "***") -> str:
        """
        过滤敏感词

        Args:
            text: 待过滤文本
            replacement: 替换字符串

        Returns:
            str: 过滤后的文本
        """
        result = text
        for pattern in self.patterns:
            result = pattern.sub(replacement, result)
        return result

    def validate(self, text: str) -> bool:
        """
        验证文本是否包含敏感词

        Args:
            text: 待验证文本

        Returns:
            bool: 是否通过验证（True表示无敏感词）
        """
        found = self.check(text)
        if found:
            logger.warning(f"发现敏感词: {found}")
            return False
        return True


# 全局实例
sanitizer = ContentSanitizer()
