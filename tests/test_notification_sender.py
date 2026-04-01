"""
src/notification_sender/ 通知渠道单元测试

测试范围：
- WechatSender: is_available / _split_content / send（Mock HTTP）
- FeishuSender: is_available / _split_content / send（Mock HTTP）
- PushPlusSender: is_available / send（Mock HTTP）
- EmailSender: is_available / send（Mock SMTP）
"""

import unittest
from unittest.mock import MagicMock, patch

from src.notification_sender.wechat_sender import WechatSender, _WECHAT_MAX_BYTES
from src.notification_sender.feishu_sender import FeishuSender, _FEISHU_MAX_BYTES
from src.notification_sender.pushplus_sender import PushPlusSender
from src.notification_sender.email_sender import EmailSender


# ──────────────────────────────────────────────
# WechatSender
# ──────────────────────────────────────────────


class TestWechatSender(unittest.TestCase):
    def _make_sender(self, url=None):
        """创建 WechatSender，绕过 settings 加载"""
        sender = WechatSender.__new__(WechatSender)
        sender._webhook_url = url
        return sender

    def test_is_available_false_when_no_url(self):
        sender = self._make_sender(url=None)
        self.assertFalse(sender.is_available())

    def test_is_available_true_when_url_set(self):
        sender = self._make_sender(
            url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
        )
        self.assertTrue(sender.is_available())

    def test_send_returns_false_when_not_configured(self):
        sender = self._make_sender(url=None)
        self.assertFalse(sender.send("hello"))

    def test_split_content_short_message_not_split(self):
        sender = self._make_sender(url="http://test")
        short_msg = "短消息"
        chunks = sender._split_content(short_msg)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_msg)

    def test_split_content_long_message_split(self):
        sender = self._make_sender(url="http://test")
        # 生成超过 4000 字节的消息（中文每字 3 字节）
        long_msg = "测" * 2000  # 6000 字节
        chunks = sender._split_content(long_msg)
        self.assertGreater(len(chunks), 1)
        # 每块不超过字节限制
        for chunk in chunks:
            self.assertLessEqual(len(chunk.encode("utf-8")), _WECHAT_MAX_BYTES)
        # 拼接还原
        self.assertEqual("".join(chunks), long_msg)

    def test_send_success_with_mock_http(self):
        sender = self._make_sender(url="http://fake-wechat-webhook")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errcode": 0, "errmsg": "ok"}

        with patch("src.notification_sender.wechat_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            result = sender.send("测试消息")

        self.assertTrue(result)
        mock_httpx.post.assert_called_once()

    def test_send_failure_with_error_code(self):
        sender = self._make_sender(url="http://fake-wechat-webhook")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errcode": 40060, "errmsg": "invalid key"}

        with patch("src.notification_sender.wechat_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            result = sender.send("测试消息")

        self.assertFalse(result)

    def test_send_network_exception_returns_false(self):
        sender = self._make_sender(url="http://fake-wechat-webhook")
        with patch("src.notification_sender.wechat_sender.httpx") as mock_httpx:
            mock_httpx.post.side_effect = Exception("网络超时")
            result = sender.send("测试消息")
        self.assertFalse(result)


# ──────────────────────────────────────────────
# FeishuSender
# ──────────────────────────────────────────────


class TestFeishuSender(unittest.TestCase):
    def _make_sender(self, url=None):
        sender = FeishuSender.__new__(FeishuSender)
        sender._webhook_url = url
        return sender

    def test_is_available_false_when_no_url(self):
        sender = self._make_sender(url=None)
        self.assertFalse(sender.is_available())

    def test_is_available_true_when_url_set(self):
        sender = self._make_sender(
            url="https://open.feishu.cn/open-apis/bot/v2/hook/test"
        )
        self.assertTrue(sender.is_available())

    def test_send_returns_false_when_not_configured(self):
        sender = self._make_sender(url=None)
        self.assertFalse(sender.send("hello"))

    def test_split_content_short_not_split(self):
        sender = self._make_sender(url="http://test")
        msg = "短消息"
        chunks = sender._split_content(msg)
        self.assertEqual(len(chunks), 1)

    def test_split_content_long_message_split(self):
        sender = self._make_sender(url="http://test")
        # 超过 20000 字节
        long_msg = "测" * 10000  # 30000 字节
        chunks = sender._split_content(long_msg)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.encode("utf-8")), _FEISHU_MAX_BYTES)
        self.assertEqual("".join(chunks), long_msg)

    def test_send_success_statuscode_0(self):
        sender = self._make_sender(url="http://fake-feishu-webhook")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"StatusCode": 0}

        with patch("src.notification_sender.feishu_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            result = sender.send("飞书消息")

        self.assertTrue(result)

    def test_send_success_code_0(self):
        """飞书也可能返回 code: 0"""
        sender = self._make_sender(url="http://fake-feishu-webhook")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 0}

        with patch("src.notification_sender.feishu_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            result = sender.send("飞书消息")

        self.assertTrue(result)

    def test_send_failure_non_zero_code(self):
        sender = self._make_sender(url="http://fake-feishu-webhook")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"StatusCode": 19021, "msg": "webhook not found"}

        with patch("src.notification_sender.feishu_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            result = sender.send("飞书消息")

        self.assertFalse(result)

    def test_send_network_exception_returns_false(self):
        sender = self._make_sender(url="http://fake-feishu-webhook")
        with patch("src.notification_sender.feishu_sender.httpx") as mock_httpx:
            mock_httpx.post.side_effect = Exception("连接失败")
            result = sender.send("飞书消息")
        self.assertFalse(result)


# ──────────────────────────────────────────────
# PushPlusSender
# ──────────────────────────────────────────────


class TestPushPlusSender(unittest.TestCase):
    def _make_sender(self, token=None, topic=None):
        sender = PushPlusSender.__new__(PushPlusSender)
        sender._token = token
        sender._topic = topic
        return sender

    def test_is_available_false_when_no_token(self):
        sender = self._make_sender(token=None)
        self.assertFalse(sender.is_available())

    def test_is_available_true_when_token_set(self):
        sender = self._make_sender(token="abc123token")
        self.assertTrue(sender.is_available())

    def test_send_returns_false_when_not_configured(self):
        sender = self._make_sender(token=None)
        self.assertFalse(sender.send("内容"))

    def test_send_success_code_200(self):
        sender = self._make_sender(token="test_token")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 200, "msg": "请求成功"}

        with patch("src.notification_sender.pushplus_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            result = sender.send("市场分析内容")

        self.assertTrue(result)

    def test_send_with_topic_in_payload(self):
        """配置 topic 时 payload 中应包含 topic"""
        sender = self._make_sender(token="test_token", topic="my_group")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 200}

        with patch("src.notification_sender.pushplus_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            sender.send("带群组推送")

        call_kwargs = mock_httpx.post.call_args
        payload = (
            call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        )
        self.assertEqual(payload.get("topic"), "my_group")

    def test_send_failure_non_200_code(self):
        sender = self._make_sender(token="test_token")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 900, "msg": "token不存在"}

        with patch("src.notification_sender.pushplus_sender.httpx") as mock_httpx:
            mock_httpx.post.return_value = mock_resp
            result = sender.send("内容")

        self.assertFalse(result)

    def test_send_network_exception_returns_false(self):
        sender = self._make_sender(token="test_token")
        with patch("src.notification_sender.pushplus_sender.httpx") as mock_httpx:
            mock_httpx.post.side_effect = Exception("超时")
            result = sender.send("内容")
        self.assertFalse(result)


# ──────────────────────────────────────────────
# EmailSender
# ──────────────────────────────────────────────


class TestEmailSender(unittest.TestCase):
    def _make_sender(self, sender_email=None, password=None, receivers=None):
        """直接操作 EmailSender 内部字段，绕过 settings"""
        sender = EmailSender.__new__(EmailSender)
        sender._smtp_server = "smtp.qq.com"
        sender._smtp_port = 465
        sender._sender = sender_email
        sender._password = password
        sender._receivers = receivers or []
        return sender

    def test_is_available_false_when_no_sender(self):
        sender = self._make_sender(
            sender_email=None, password="pwd", receivers=["r@example.com"]
        )
        self.assertFalse(sender.is_available())

    def test_is_available_false_when_no_password(self):
        sender = self._make_sender(
            sender_email="s@qq.com", password=None, receivers=["r@example.com"]
        )
        self.assertFalse(sender.is_available())

    def test_is_available_false_when_no_receivers(self):
        sender = self._make_sender(
            sender_email="s@qq.com", password="pwd", receivers=[]
        )
        self.assertFalse(sender.is_available())

    def test_is_available_true_when_all_configured(self):
        sender = self._make_sender(
            sender_email="sender@qq.com",
            password="auth_code",
            receivers=["receiver@example.com"],
        )
        self.assertTrue(sender.is_available())

    def test_send_returns_false_when_not_configured(self):
        sender = self._make_sender(sender_email=None)
        self.assertFalse(sender.send("邮件内容", "标题"))

    def test_parse_receivers_comma_separated(self):
        """逗号分隔的收件人字符串应正确解析"""
        sender = self._make_sender()
        result = sender._parse_receivers("a@example.com, b@example.com , c@example.com")
        self.assertEqual(result, ["a@example.com", "b@example.com", "c@example.com"])

    def test_parse_receivers_empty_returns_empty_list(self):
        sender = self._make_sender()
        self.assertEqual(sender._parse_receivers(None), [])
        self.assertEqual(sender._parse_receivers(""), [])


if __name__ == "__main__":
    unittest.main()
