"""
钉钉通知器
"""

import time
import hmac
import hashlib
import base64
import urllib.parse
import json
from typing import Dict, Optional

try:
    import requests
except ImportError:
    requests = None

from .base import BaseNotifier
from ..config import Config


class DingtalkNotifier(BaseNotifier):
    """
    钉钉通知器

    支持功能:
    - Webhook 推送
    - 加签验证 (SHA256-HMAC)
    - Markdown 消息格式
    """

    def __init__(self, config: Config):
        """
        初始化钉钉通知器

        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.webhook = config.dingtalk_webhook
        self.secret = config.dingtalk_secret

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return (
            self.config.dingtalk_enabled and
            self.webhook and
            self.webhook != 'YOUR_DINGTALK_WEBHOOK'
        )

    def _generate_sign(self) -> str:
        """
        生成签名参数

        Returns:
            签名参数字符串 "timestamp=xxx&sign=xxx"
        """
        if not self.secret or self.secret == 'YOUR_DINGTALK_SECRET':
            return ''

        timestamp = str(int(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"

        # 计算 HMAC-SHA256
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        # Base64 编码后 URL 编码
        sign = base64.b64encode(hmac_code).decode('utf-8')
        encoded_sign = urllib.parse.quote(sign, safe='')

        return f"timestamp={timestamp}&sign={encoded_sign}"

    def _get_full_webhook(self) -> str:
        """获取完整的 webhook URL（包含签名）"""
        sign_params = self._generate_sign()
        if sign_params:
            return f"{self.webhook}&{sign_params}"
        return self.webhook

    def send(self, title: str, content: str, msg_type: str = 'markdown') -> bool:
        """
        发送钉钉消息

        Args:
            title: 消息标题
            content: 消息内容
            msg_type: 消息类型 (text/markdown)

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            print("钉钉通知未启用或未配置")
            return False

        if requests is None:
            print("请安装 requests 库: pip install requests")
            return False

        if msg_type == 'markdown':
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": content
                }
            }
        else:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }

        try:
            url = self._get_full_webhook()
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=10
            )
            result = response.json()

            if result.get('errcode') == 0:
                print("钉钉消息发送成功")
                return True
            else:
                print(f"钉钉消息发送失败: {result}")
                return False
        except Exception as e:
            print(f"钉钉消息发送异常: {e}")
            return False

    def _infer_langs_from_repos(self, repos: list) -> list:
        """从仓库名称推断技术栈"""
        repo_lang_map = {
            'web': 'Vue', 'h5': 'Vue', 'frontend': 'Vue',
            'backend': 'Java', 'server': 'Java', 'api': 'Java', 'file': 'Java',
            'service': 'Python', 'multiagent': 'Python', 'agent': 'Python',
            'ai': 'Python', 'ml': 'Python', 'pipeline': 'Python', 'knowledge': 'Python',
            'infra': 'Shell', 'ops': 'Shell', 'devops': 'Shell',
        }
        langs = set()
        for repo in repos:
            repo_lower = repo.lower()
            for keyword, lang in repo_lang_map.items():
                if keyword in repo_lower:
                    langs.add(lang)
                    break
        return list(langs)[:2]

    def _format_tech_repos(self, langs: list, repos: list) -> str:
        """格式化技术栈/仓库信息（分行显示）"""
        parts = []
        for lang in langs[:2]:
            parts.append(f"💻 {lang}")
        for repo in repos[:2]:
            parts.append(f"📦 {repo}")
        if len(repos) > 2:
            parts.append(f"📦 ...等{len(repos)}个")
        return '<br/>'.join(parts) if parts else "N/A"

    def _format_daily_message(self, report_date: str, data: Dict) -> str:
        """格式化日报消息 (V1兼容格式)"""
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/daily/{report_date}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        # 构建 TOP 3 开发者表格
        top3_table = ""
        for dev in data.get('top_developers', []):
            name = dev.get('name', 'Unknown')
            commits = dev.get('commits', 0)
            net_lines = self._format_number(str(dev.get('net_lines', 0)))
            repos = dev.get('repos', [])
            langs = dev.get('langs', []) or self._infer_langs_from_repos(repos)
            detail_str = self._format_tech_repos(langs, repos)
            top3_table += f"| {name} | {commits}次 | {net_lines}行 | {detail_str} |\n"

        # 计算异常提交
        overtime = int(data.get('overtime', 0))
        late_night = int(data.get('late_night', 0))
        weekend = int(data.get('weekend', 0))

        content = f"""## 📊 代码健康日报

**日期**: {report_date} | **系统**: {self.project_name}

---

### 📈 核心指标

| 指标 | 数值 |
|------|------|
| 提交次数 | {data.get('commits', '0')} 次 |
| 活跃开发者 | {data.get('developers', '0')} 人 |
| 涉及仓库 | {data.get('repos', '0')} 个 |
| 代码净增 | {lines} 行 |
| 健康评分 | {data.get('score', '0')} 分 {score_level} |

---

### 👥 TOP 3 活跃开发者

| 开发者 | 提交 | 净增代码 | 技术栈/仓库 |
|--------|------|---------|-----------|
{top3_table}
---

### 🚨 风险指标

- 加班提交: **{overtime}** 次
- 深夜提交: **{late_night}** 次
- 周末提交: **{weekend}** 次

---

### 🔗 详细报告

[📄 完整日报]({report_url}) | [📊 可视化仪表盘]({dashboard_url})

---

> 🤖 由代码管理系统自动生成"""

        return content

    def _format_weekly_message(self, week_str: str, data: Dict) -> str:
        """格式化周报消息 (V1兼容格式)"""
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/weekly/{week_str}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        # 构建贡献者表格
        contributor_table = ""
        for c in data.get('contributors', [])[:5]:
            name = c.get('name', 'Unknown')
            commits = c.get('commits', '0')
            net_lines = self._format_number(c.get('net_lines', '0'))
            repos = c.get('repos', [])
            langs = c.get('langs', []) or self._infer_langs_from_repos(repos)
            detail_str = self._format_tech_repos(langs, repos)
            contributor_table += f"| {name} | {commits}次 | {net_lines}行 | {detail_str} |\n"

        content = f"""## 📈 代码健康周报

**周期**: {week_str} | **系统**: {self.project_name}

---

### 📊 团队产出

| 指标 | 数值 |
|------|------|
| 总提交数 | {data.get('commits', '0')} 次 |
| 净增代码 | {lines} 行 |
| 活跃开发者 | {data.get('developers', '0')} 人 |

---

### 🏆 TOP 5 代码贡献

| 开发者 | 提交 | 净增代码 | 技术栈/仓库 |
|--------|------|---------|-----------|
{contributor_table}
---

### 🎯 健康评分

**综合评分**: {data.get('score', '0')} 分 {score_level}

---

### 🔗 详细报告

[📄 完整周报]({report_url}) | [📊 可视化仪表盘]({dashboard_url})

---

> 🤖 由代码管理系统自动生成"""

        return content

    def _format_monthly_message(self, month_str: str, data: Dict) -> str:
        """格式化月报消息 (V1兼容格式)"""
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/monthly/{month_str}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        # 提取月份名称
        year = month_str.split('-')[0]
        month_num = int(month_str.split('-')[1])
        month_names = ["", "一月", "二月", "三月", "四月", "五月", "六月",
                       "七月", "八月", "九月", "十月", "十一月", "十二月"]
        month_name = month_names[month_num] if month_num <= 12 else f"{month_num}月"

        # MVP 信息
        mvp_name = data.get('mvp_name', '')
        mvp_commits = data.get('mvp_commits', '0')
        mvp_section = ""
        if mvp_name:
            mvp_section = f"""
---

### 🏆 本月MVP

- **姓名**: {mvp_name}
- **提交数**: {mvp_commits} 次"""

        # 风险信息
        late_night = data.get('late_night', '0')
        weekend = data.get('weekend', '0')
        risk_section = ""
        if int(late_night) > 0 or int(weekend) > 0:
            risk_section = f"""

---

### ⚠️ 风险提示

- **深夜提交**: {late_night} 次
- **周末提交**: {weekend} 次"""

        content = f"""## 📊 代码管理 - {year}年{month_name}月报

**报告周期**: {month_str} | **系统**: {self.project_name}

---

### 📈 月度总览

| 指标 | 数值 |
|------|------|
| 总提交数 | {data.get('commits', '0')} 次 |
| 代码净增 | {lines} 行 |
| 活跃开发者 | {data.get('developers', '0')} 人 |
| 工作日数 | {data.get('work_days', '0')} 天 |{mvp_section}

---

### 🎯 健康评分

**月度健康分**: {data.get('score', '0')} 分 {score_level}{risk_section}

---

### 🔗 详细报告

[📄 完整月报]({report_url}) | [📊 可视化仪表盘]({dashboard_url})

---

> 🤖 由代码管理系统自动生成"""

        return content
