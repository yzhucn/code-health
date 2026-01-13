"""
飞书通知器
"""

import time
import hmac
import hashlib
import base64
import json
from typing import Dict, Optional

try:
    import requests
except ImportError:
    requests = None

from .base import BaseNotifier
from ..config import Config


class FeishuNotifier(BaseNotifier):
    """
    飞书通知器

    支持功能:
    - Webhook 推送
    - 加签验证 (可选)
    - 富文本消息格式
    """

    def __init__(self, config: Config):
        """
        初始化飞书通知器

        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.webhook = config.get('notification.feishu.webhook', '')
        self.secret = config.get('notification.feishu.secret', '')

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return (
            self.config.get('notification.feishu.enabled', False) and
            self.webhook and
            self.webhook != 'YOUR_FEISHU_WEBHOOK'
        )

    def _generate_sign(self) -> tuple:
        """
        生成签名

        Returns:
            (timestamp, sign) 元组
        """
        if not self.secret:
            return None, None

        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self.secret}"

        # 计算 HMAC-SHA256
        hmac_code = hmac.new(
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        sign = base64.b64encode(hmac_code).decode('utf-8')
        return timestamp, sign

    def send(self, title: str, content: str, msg_type: str = 'markdown') -> bool:
        """
        发送飞书消息

        Args:
            title: 消息标题
            content: 消息内容
            msg_type: 消息类型 (text/markdown)

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            print("飞书通知未启用或未配置")
            return False

        if requests is None:
            print("请安装 requests 库: pip install requests")
            return False

        # 飞书使用富文本格式
        if msg_type == 'markdown':
            # 将 Markdown 转换为飞书富文本
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "content": title,
                            "tag": "plain_text"
                        },
                        "template": "blue"
                    },
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": content
                        }
                    ]
                }
            }
        else:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }

        # 添加签名
        timestamp, sign = self._generate_sign()
        if timestamp and sign:
            payload['timestamp'] = timestamp
            payload['sign'] = sign

        try:
            response = requests.post(
                self.webhook,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=10
            )
            result = response.json()

            if result.get('code') == 0 or result.get('StatusCode') == 0:
                print("飞书消息发送成功")
                return True
            else:
                print(f"飞书消息发送失败: {result}")
                return False
        except Exception as e:
            print(f"飞书消息发送异常: {e}")
            return False

    def _format_daily_message(self, report_date: str, data: Dict) -> str:
        """格式化日报消息"""
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/daily/{report_date}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        content = f"""**日期**: {report_date}
**系统**: {self.project_name}

---

**核心指标**
- 提交次数: {data.get('commits', '0')} 次
- 活跃开发者: {data.get('developers', '0')} 人
- 代码净增: {lines} 行
- 健康评分: {data.get('score', '0')} 分 {score_level}

---

**风险指标**
- 加班提交: {data.get('overtime', '0')} 次

---

[查看完整日报]({report_url}) | [可视化仪表盘]({dashboard_url})"""

        return content

    def _format_weekly_message(self, week_str: str, data: Dict) -> str:
        """格式化周报消息"""
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/weekly/{week_str}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        # 构建贡献者列表
        contributor_list = ""
        for i, c in enumerate(data.get('contributors', [])[:5], 1):
            net_lines = self._format_number(c.get('net_lines', '0'))
            contributor_list += f"{i}. {c['name']}: {c['commits']}次提交, +{net_lines}行\n"

        content = f"""**周期**: {week_str}
**系统**: {self.project_name}

---

**团队产出**
- 总提交数: {data.get('commits', '0')} 次
- 净增代码: {lines} 行
- 活跃开发者: {data.get('developers', '0')} 人

---

**TOP 5 贡献者**
{contributor_list}

---

**健康评分**: {data.get('score', '0')} 分 {score_level}

---

[完整周报]({report_url}) | [可视化仪表盘]({dashboard_url})"""

        return content

    def _format_monthly_message(self, month_str: str, data: Dict) -> str:
        """格式化月报消息"""
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/monthly/{month_str}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        content = f"""**月份**: {month_str}
**系统**: {self.project_name}
**工作日**: {data.get('work_days', '0')} 天

---

**月度总览**
- 总提交数: {data.get('commits', '0')} 次
- 代码净增: {lines} 行
- 活跃开发者: {data.get('developers', '0')} 人

---

**月度健康分**: {data.get('score', '0')} 分 {score_level}

---

[完整月报]({report_url}) | [可视化仪表盘]({dashboard_url})"""

        return content
