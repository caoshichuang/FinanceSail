"""
WxPusher微信推送模块
"""

import requests
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..config.settings import settings


class WxPusherNotifier:
    """WxPusher微信推送器"""

    def __init__(self, app_token: str = None):
        self.logger = get_logger(self.__class__.__name__)
        self.app_token = app_token or getattr(settings, "WXPUSHER_APP_TOKEN", "")
        self.base_url = "https://wxpusher.zjiecode.com"

    def send_message(
        self,
        uids: List[str],
        content: str,
        summary: str = None,
        content_type: int = 1,
        url: str = None,
    ) -> Dict[str, Any]:
        """
        发送消息

        Args:
            uids: 用户UID列表
            content: 消息内容
            summary: 消息摘要
            content_type: 内容类型（1=文字，2=HTML，3=Markdown）
            url: 跳转链接

        Returns:
            Dict: 发送结果
        """
        if not self.app_token:
            self.logger.error("WxPusher未配置")
            return {"success": False, "message": "WxPusher未配置"}

        api_url = f"{self.base_url}/api/send/message"

        payload = {
            "appToken": self.app_token,
            "content": content,
            "contentType": content_type,
            "uids": uids,
        }

        if summary:
            payload["summary"] = summary[:100]  # 摘要最多100字

        if url:
            payload["url"] = url

        try:
            response = requests.post(api_url, json=payload, timeout=30)
            data = response.json()

            if data.get("code") == 1000:
                self.logger.info(f"WxPusher发送成功: {len(uids)}个用户")
                return {"success": True, "data": data}
            else:
                self.logger.error(f"WxPusher发送失败: {data}")
                return {"success": False, "message": data.get("msg", "Unknown error")}

        except Exception as e:
            self.logger.error(f"WxPusher发送异常: {e}")
            return {"success": False, "message": str(e)}

    def send_stock_alert(
        self,
        uids: List[str],
        stock_name: str,
        stock_code: str,
        event_type: str,
        event_data: Dict[str, Any],
        preview_url: str = None,
    ) -> Dict[str, Any]:
        """
        发送股票预警

        Args:
            uids: 用户UID列表
            stock_name: 股票名称
            stock_code: 股票代码
            event_type: 事件类型
            event_data: 事件数据
            preview_url: 预览链接

        Returns:
            Dict: 发送结果
        """
        # 生成消息内容
        summary = f"📊 {stock_name} 预警"
        content = self._format_alert_content(
            stock_name, stock_code, event_type, event_data
        )

        return self.send_message(
            uids=uids,
            content=content,
            summary=summary,
            content_type=2,  # HTML
            url=preview_url,
        )

    def _format_alert_content(
        self,
        stock_name: str,
        stock_code: str,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> str:
        """格式化预警内容"""
        event_type_names = {
            "change": "涨跌幅预警",
            "announce": "公告预警",
            "earning": "财报预警",
            "dividend": "分红预警",
        }

        event_name = event_type_names.get(event_type, "预警")

        if event_type == "change":
            change_pct = event_data.get("change_pct", 0)
            price = event_data.get("price", 0)
            emoji = "📈" if change_pct > 0 else "📉"

            content = f"""
<div style="font-family: -apple-system, sans-serif; padding: 20px;">
    <h2 style="color: #333;">{emoji} {stock_name} ({stock_code})</h2>
    <h3 style="color: #666;">{event_name}</h3>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <p style="margin: 0; font-size: 18px;">
            <strong>涨跌幅: </strong>
            <span style="color: {"#ff4444" if change_pct > 0 else "#00aa00"}; font-size: 24px;">
                {change_pct:+.2f}%
            </span>
        </p>
        <p style="margin: 10px 0 0 0; font-size: 16px;">
            <strong>当前价: </strong>{price}
        </p>
    </div>
    
    <p style="color: #999; font-size: 12px;">
        数据来源: AKShare | FinanceSail
    </p>
</div>
"""
        elif event_type == "announce":
            title = event_data.get("title", "")
            keywords = event_data.get("keywords", [])

            content = f"""
<div style="font-family: -apple-system, sans-serif; padding: 20px;">
    <h2 style="color: #333;">📢 {stock_name} ({stock_code})</h2>
    <h3 style="color: #666;">{event_name}</h3>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <p style="margin: 0; font-size: 16px;">
            <strong>公告标题: </strong>{title}
        </p>
        <p style="margin: 10px 0 0 0; font-size: 14px;">
            <strong>关键词: </strong>{", ".join(keywords)}
        </p>
    </div>
    
    <p style="color: #999; font-size: 12px;">
        数据来源: AKShare | FinanceSail
    </p>
</div>
"""
        elif event_type == "earning":
            report_date = event_data.get("report_date", "")
            report_type = event_data.get("report_type", "")

            content = f"""
<div style="font-family: -apple-system, sans-serif; padding: 20px;">
    <h2 style="color: #333;">📊 {stock_name} ({stock_code})</h2>
    <h3 style="color: #666;">{event_name}</h3>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <p style="margin: 0; font-size: 16px;">
            <strong>财报日期: </strong>{report_date}
        </p>
        <p style="margin: 10px 0 0 0; font-size: 14px;">
            <strong>财报类型: </strong>{report_type}
        </p>
    </div>
    
    <p style="color: #999; font-size: 12px;">
        数据来源: AKShare | FinanceSail
    </p>
</div>
"""
        elif event_type == "dividend":
            dividend_plan = event_data.get("dividend_plan", "")
            ex_date = event_data.get("ex_dividend_date", "")

            content = f"""
<div style="font-family: -apple-system, sans-serif; padding: 20px;">
    <h2 style="color: #333;">💰 {stock_name} ({stock_code})</h2>
    <h3 style="color: #666;">{event_name}</h3>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <p style="margin: 0; font-size: 16px;">
            <strong>分红方案: </strong>{dividend_plan}
        </p>
        <p style="margin: 10px 0 0 0; font-size: 14px;">
            <strong>除权除息日: </strong>{ex_date}
        </p>
    </div>
    
    <p style="color: #999; font-size: 12px;">
        数据来源: AKShare | FinanceSail
    </p>
</div>
"""
        else:
            content = f"""
<div style="font-family: -apple-system, sans-serif; padding: 20px;">
    <h2 style="color: #333;">📊 {stock_name} ({stock_code})</h2>
    <h3 style="color: #666;">{event_name}</h3>
    <p style="color: #999; font-size: 12px;">
        数据来源: AKShare | FinanceSail
    </p>
</div>
"""

        return content

    def get_user_qrcode(self, uid: str) -> Optional[str]:
        """
        获取用户二维码

        Args:
            uid: 用户UID

        Returns:
            str: 二维码URL
        """
        api_url = f"{self.base_url}/api/user/qrcode"

        params = {
            "appToken": self.app_token,
            "uid": uid,
        }

        try:
            response = requests.get(api_url, params=params, timeout=30)
            data = response.json()

            if data.get("code") == 1000:
                return data.get("data", {}).get("url")
            else:
                self.logger.error(f"获取用户二维码失败: {data}")
                return None

        except Exception as e:
            self.logger.error(f"获取用户二维码异常: {e}")
            return None

    def create_user(self, name: str = None) -> Optional[str]:
        """
        创建用户

        Args:
            name: 用户名称

        Returns:
            str: 用户UID
        """
        api_url = f"{self.base_url}/api/user/create"

        payload = {
            "appToken": self.app_token,
        }

        if name:
            payload["extra"] = name

        try:
            response = requests.post(api_url, json=payload, timeout=30)
            data = response.json()

            if data.get("code") == 1000:
                uid = data.get("data", {}).get("uid")
                self.logger.info(f"创建用户成功: {uid}")
                return uid
            else:
                self.logger.error(f"创建用户失败: {data}")
                return None

        except Exception as e:
            self.logger.error(f"创建用户异常: {e}")
            return None
