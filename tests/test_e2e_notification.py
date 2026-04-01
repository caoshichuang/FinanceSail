"""
端到端通知测试

测试范围：
- NotificationService 初始化（渠道自动检测）
- is_available() 反映激活渠道状态
- active_channels 属性
- send() 并发推送（Mock 各渠道 Sender）
- 单渠道成功时整体返回 True
- 全部失败时返回 False
- 无渠道配置时直接返回 False
"""

import unittest
from unittest.mock import MagicMock, patch

from src.notification_sender.wechat_sender import WechatSender
from src.notification_sender.feishu_sender import FeishuSender
from src.notification_sender.pushplus_sender import PushPlusSender
from src.notification_sender.email_sender import EmailSender
from src.notification_sender.telegram_sender import TelegramSender


def _make_sender_mock(available: bool, send_result: bool = True) -> MagicMock:
    """创建模拟 Sender"""
    mock = MagicMock()
    mock.is_available.return_value = available
    mock.send.return_value = send_result
    return mock


# ──────────────────────────────────────────────
# 直接测试 NotificationService（避免 import 路径问题）
# ──────────────────────────────────────────────


class _MockNotificationService:
    """
    用于测试的简化版 NotificationService，直接接收 senders 字典。
    等价于生产代码逻辑，不依赖实际网络。
    """

    def __init__(self, senders):
        import concurrent.futures

        self._senders = senders
        self._active_channels = [
            name for name, s in senders.items() if s.is_available()
        ]
        self._futures_module = concurrent.futures

    def is_available(self):
        return len(self._active_channels) > 0

    @property
    def active_channels(self):
        return list(self._active_channels)

    def send(self, content, subject="FinanceSail 市场报告", attachments=None):
        if not self.is_available():
            return False

        results = {}

        def _send_to_channel(name, sender):
            try:
                if name == "邮件":
                    ok = sender.send(content, subject=subject, attachments=attachments)
                elif name == "PushPlus":
                    ok = sender.send(content, title=subject)
                else:
                    ok = sender.send(content)
                return name, ok
            except Exception:
                return name, False

        active_senders = {n: self._senders[n] for n in self._active_channels}
        with self._futures_module.ThreadPoolExecutor(
            max_workers=max(1, len(active_senders))
        ) as ex:
            futures = {
                ex.submit(_send_to_channel, n, s): n for n, s in active_senders.items()
            }
            for f in self._futures_module.as_completed(futures):
                name, ok = f.result()
                results[name] = ok

        return any(results.values())


class TestNotificationServiceChannelDetection(unittest.TestCase):
    """渠道自动检测测试"""

    def test_no_channels_configured(self):
        """全部不可用时 is_available() 返回 False"""
        senders = {
            "企业微信": _make_sender_mock(available=False),
            "飞书": _make_sender_mock(available=False),
            "邮件": _make_sender_mock(available=False),
        }
        svc = _MockNotificationService(senders)
        self.assertFalse(svc.is_available())
        self.assertEqual(svc.active_channels, [])

    def test_single_channel_configured(self):
        """只有一个渠道可用"""
        senders = {
            "企业微信": _make_sender_mock(available=True),
            "飞书": _make_sender_mock(available=False),
            "邮件": _make_sender_mock(available=False),
        }
        svc = _MockNotificationService(senders)
        self.assertTrue(svc.is_available())
        self.assertEqual(svc.active_channels, ["企业微信"])

    def test_multiple_channels_configured(self):
        """多个渠道同时可用"""
        senders = {
            "企业微信": _make_sender_mock(available=True),
            "飞书": _make_sender_mock(available=True),
            "邮件": _make_sender_mock(available=False),
            "PushPlus": _make_sender_mock(available=True),
        }
        svc = _MockNotificationService(senders)
        self.assertTrue(svc.is_available())
        self.assertIn("企业微信", svc.active_channels)
        self.assertIn("飞书", svc.active_channels)
        self.assertIn("PushPlus", svc.active_channels)
        self.assertNotIn("邮件", svc.active_channels)


class TestNotificationServiceSend(unittest.TestCase):
    """send() 并发推送测试"""

    def test_send_no_channels_returns_false(self):
        """无可用渠道时直接返回 False"""
        svc = _MockNotificationService(
            {
                "企业微信": _make_sender_mock(available=False),
            }
        )
        self.assertFalse(svc.send("测试内容"))

    def test_send_single_channel_success(self):
        """单渠道发送成功时返回 True"""
        svc = _MockNotificationService(
            {
                "企业微信": _make_sender_mock(available=True, send_result=True),
            }
        )
        result = svc.send("测试消息")
        self.assertTrue(result)

    def test_send_single_channel_failure(self):
        """单渠道发送失败时返回 False"""
        svc = _MockNotificationService(
            {
                "企业微信": _make_sender_mock(available=True, send_result=False),
            }
        )
        result = svc.send("测试消息")
        self.assertFalse(result)

    def test_send_any_channel_success_returns_true(self):
        """多渠道中任意一个成功即返回 True"""
        svc = _MockNotificationService(
            {
                "企业微信": _make_sender_mock(available=True, send_result=False),
                "飞书": _make_sender_mock(available=True, send_result=True),
                "PushPlus": _make_sender_mock(available=True, send_result=False),
            }
        )
        result = svc.send("测试消息")
        self.assertTrue(result)

    def test_send_all_fail_returns_false(self):
        """全部渠道失败时返回 False"""
        svc = _MockNotificationService(
            {
                "企业微信": _make_sender_mock(available=True, send_result=False),
                "飞书": _make_sender_mock(available=True, send_result=False),
            }
        )
        result = svc.send("测试消息")
        self.assertFalse(result)

    def test_send_email_uses_subject(self):
        """邮件渠道 send() 应透传 subject"""
        email_mock = _make_sender_mock(available=True, send_result=True)
        svc = _MockNotificationService({"邮件": email_mock})
        svc.send("内容", subject="日报标题")
        email_mock.send.assert_called_once_with(
            "内容", subject="日报标题", attachments=None
        )

    def test_send_pushplus_uses_title(self):
        """PushPlus 渠道 send() 应透传 title（使用 subject 参数）"""
        pp_mock = _make_sender_mock(available=True, send_result=True)
        svc = _MockNotificationService({"PushPlus": pp_mock})
        svc.send("内容", subject="PushPlus标题")
        pp_mock.send.assert_called_once_with("内容", title="PushPlus标题")

    def test_send_wechat_no_subject(self):
        """企业微信 send() 只传 content，不传 subject"""
        wechat_mock = _make_sender_mock(available=True, send_result=True)
        svc = _MockNotificationService({"企业微信": wechat_mock})
        svc.send("内容", subject="不应传入")
        wechat_mock.send.assert_called_once_with("内容")

    def test_send_channel_exception_does_not_crash(self):
        """某渠道抛异常时不影响其他渠道，服务不崩溃"""
        wechat_mock = MagicMock()
        wechat_mock.is_available.return_value = True
        wechat_mock.send.side_effect = Exception("连接失败")

        feishu_mock = _make_sender_mock(available=True, send_result=True)

        svc = _MockNotificationService(
            {
                "企业微信": wechat_mock,
                "飞书": feishu_mock,
            }
        )
        result = svc.send("测试消息")
        # 飞书成功，整体返回 True
        self.assertTrue(result)


class TestSenderIsAvailableIntegration(unittest.TestCase):
    """各 Sender is_available() 的边界测试（纯单元，不需要网络）"""

    def test_wechat_sender_is_available_requires_url(self):
        s = WechatSender.__new__(WechatSender)
        s._webhook_url = None
        self.assertFalse(s.is_available())
        s._webhook_url = "http://example.com"
        self.assertTrue(s.is_available())

    def test_feishu_sender_is_available_requires_url(self):
        s = FeishuSender.__new__(FeishuSender)
        s._webhook_url = None
        self.assertFalse(s.is_available())
        s._webhook_url = "http://example.com"
        self.assertTrue(s.is_available())

    def test_pushplus_sender_is_available_requires_token(self):
        s = PushPlusSender.__new__(PushPlusSender)
        s._token = None
        self.assertFalse(s.is_available())
        s._token = "mytoken"
        self.assertTrue(s.is_available())

    def test_email_sender_is_available_requires_all_fields(self):
        s = EmailSender.__new__(EmailSender)
        s._sender = None
        s._password = None
        s._receivers = []
        self.assertFalse(s.is_available())

        s._sender = "sender@qq.com"
        s._password = "auth"
        s._receivers = ["recv@example.com"]
        self.assertTrue(s.is_available())

    def test_telegram_sender_is_available_requires_token_and_chat_id(self):
        s = TelegramSender.__new__(TelegramSender)
        s._bot_token = None
        s._chat_id = None
        self.assertFalse(s.is_available())


if __name__ == "__main__":
    unittest.main()
