"""
自定义异常模块
"""


class RedbookAutoError(Exception):
    """基础异常类"""

    pass


class DataCollectionError(RedbookAutoError):
    """数据采集异常"""

    pass


class DataSourceError(DataCollectionError):
    """数据源异常"""

    pass


class DataValidationError(DataCollectionError):
    """数据校验异常"""

    pass


class ContentGenerationError(RedbookAutoError):
    """内容生成异常"""

    pass


class AIModelError(ContentGenerationError):
    """AI模型调用异常"""

    pass


class ContentValidationError(ContentGenerationError):
    """内容校验异常"""

    pass


class SensitiveWordError(ContentValidationError):
    """敏感词异常"""

    pass


class ImageRenderError(RedbookAutoError):
    """图片渲染异常"""

    pass


class NotificationError(RedbookAutoError):
    """通知发送异常"""

    pass


class EmailError(NotificationError):
    """邮件发送异常"""

    pass


class ConfigError(RedbookAutoError):
    """配置异常"""

    pass


class DatabaseError(RedbookAutoError):
    """数据库异常"""

    pass
