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
        self.at_mobiles = config.dingtalk_at_mobiles
        self.at_userids = config.dingtalk_at_userids

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

    def send(self, title: str, content: str, msg_type: str = 'markdown', at_mobiles: list = None, at_userids: list = None) -> bool:
        """
        发送钉钉消息

        Args:
            title: 消息标题
            content: 消息内容
            msg_type: 消息类型 (text/markdown)
            at_mobiles: 需要 @ 的手机号列表
            at_userids: 需要 @ 的钉钉 userId 列表

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

        # 添加 @ 人
        if at_mobiles or at_userids:
            payload["at"] = {
                "isAtAll": False
            }
            if at_mobiles:
                payload["at"]["atMobiles"] = at_mobiles
            if at_userids:
                # 钉钉 API 同时支持 atUserIds 和 atDingtalkIds，都加上确保生效
                payload["at"]["atUserIds"] = at_userids
                payload["at"]["atDingtalkIds"] = at_userids

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

    def send_daily_report(self, report_date: str, report_content: str) -> bool:
        """
        发送日报通知（重写基类方法，支持 @ 人）

        Args:
            report_date: 报告日期 (YYYY-MM-DD)
            report_content: 报告内容 (Markdown)

        Returns:
            是否发送成功
        """
        data = self._extract_daily_data(report_content)
        title = "代码健康日报"
        content, has_risk = self._format_daily_message(report_date, data)

        # 如果有风险且配置了 @ 人，传递 at 参数给钉钉 API
        at_mobiles = None
        at_userids = None
        if has_risk and (self.at_mobiles or self.at_userids):
            at_mobiles = self.at_mobiles if self.at_mobiles else None
            at_userids = self.at_userids if self.at_userids else None

        return self.send(title, content, at_mobiles=at_mobiles, at_userids=at_userids)

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

    def _generate_daily_summary(self, data: Dict, at_users: str = "") -> str:
        """生成日报执行摘要 - 专业简洁风格"""
        commits = int(data.get('commits', 0))
        developers = int(data.get('developers', 0))
        repos = int(data.get('repos', 0))
        lines_str = str(data.get('lines', '0')).replace('+', '').replace(',', '').replace('-', '')
        try:
            lines = abs(int(lines_str))
        except ValueError:
            lines = 0

        # 判断代码是净增还是净减
        lines_raw = str(data.get('lines', '0'))
        is_negative = lines_raw.startswith('-')

        late_night = int(data.get('late_night', 0))
        overtime = int(data.get('overtime', 0))
        weekend = int(data.get('weekend', 0))

        # 获取 MVP
        top_developers = data.get('top_developers', [])
        mvp_name = ""
        mvp_commits = 0
        if top_developers:
            top_dev = top_developers[0]
            mvp_name = top_dev.get('name', '')
            mvp_commits = top_dev.get('commits', 0)

        # 构建概述 - 分行显示
        if developers == 0:
            overview_lines = ["今日无代码提交记录"]
        else:
            overview_lines = [
                f"👥 **参与人数**: {developers} 人",
                f"📦 **涉及仓库**: {repos} 个",
                f"📝 **提交次数**: {commits} 次",
            ]
            if is_negative:
                overview_lines.append(f"📉 **代码变更**: 优化 {lines} 行")
            else:
                overview_lines.append(f"📈 **代码变更**: 净增 {lines} 行")

        # MVP
        if mvp_name:
            overview_lines.append(f"🏆 **最佳贡献**: {mvp_name}（{mvp_commits} 次提交）")

        # 风险提示 - 专业措辞
        has_risk = late_night > 0 or weekend > 0
        risk_parts = []
        if late_night > 0:
            risk_parts.append(f"深夜提交 {late_night} 次")
        if weekend > 0:
            risk_parts.append(f"周末提交 {weekend} 次")

        if risk_parts:
            risk_text = "、".join(risk_parts)
            if at_users:
                overview_lines.append(f"⚠️ **需关注**: {risk_text} {at_users}")
            else:
                overview_lines.append(f"⚠️ **需关注**: {risk_text}")
        elif commits > 0:
            overview_lines.append("✅ **工作状态**: 正常")

        # 组装摘要
        summary_content = "\n".join([f"> {line}" for line in overview_lines])
        summary = f"""### 📋 执行摘要

{summary_content}"""

        return summary, has_risk

    def _format_daily_message(self, report_date: str, data: Dict) -> tuple:
        """格式化日报消息 (V1兼容格式)

        Returns:
            tuple: (消息内容, 是否需要@人)
        """
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/daily/{report_date}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        # 构建 @ 人文本
        at_parts = []
        for mobile in (self.at_mobiles or []):
            at_parts.append(f"@{mobile}")
        for userid in (self.at_userids or []):
            at_parts.append(f"@{userid}")
        at_users = " ".join(at_parts)

        # 生成执行摘要（传入 @ 人文本）
        summary, has_risk = self._generate_daily_summary(data, at_users if (self.at_mobiles or self.at_userids) else "")

        # 构建开发者表格
        top_developers = data.get('top_developers', [])
        top3_table = ""
        for dev in top_developers:
            name = dev.get('name', 'Unknown')
            commits = dev.get('commits', 0)
            net_lines = self._format_number(str(dev.get('net_lines', 0)))
            repos = dev.get('repos', [])
            langs = dev.get('langs', []) or self._infer_langs_from_repos(repos)
            detail_str = self._format_tech_repos(langs, repos)
            top3_table += f"| {name} | {commits}次 | {net_lines}行 | {detail_str} |\n"

        # 根据人数调整标题
        dev_count = len(top_developers)
        if dev_count == 0:
            top_section = "### 👥 今日活跃开发者\n\n暂无提交记录"
        elif dev_count == 1:
            top_section = f"""### 👤 今日活跃开发者

| 开发者 | 提交 | 净增代码 | 技术栈/仓库 |
|--------|------|---------|-----------|
{top3_table}"""
        else:
            top_title = f"TOP {min(dev_count, 3)}" if dev_count <= 3 else "TOP 3"
            top_section = f"""### 👥 {top_title} 活跃开发者

| 开发者 | 提交 | 净增代码 | 技术栈/仓库 |
|--------|------|---------|-----------|
{top3_table}"""

        # 计算异常提交
        overtime = int(data.get('overtime', 0))
        late_night = int(data.get('late_night', 0))
        weekend = int(data.get('weekend', 0))

        content = f"""## 📊 代码健康日报

**日期**: {report_date} | **系统**: {self.project_name}

---

{summary}

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

{top_section}
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

        return content, has_risk

    def _format_weekly_message(self, week_str: str, data: Dict) -> str:
        """格式化周报消息"""
        score = float(data.get('score', 0))
        score_level = self._get_score_level(score)
        lines = self._format_number(data.get('lines', '0'))

        report_url = f"{self.base_url}/reports/weekly/{week_str}.html"
        dashboard_url = f"{self.base_url}/dashboard/index.html"

        # 构建贡献者表格
        contributor_table = ""
        mvp = None
        for i, c in enumerate(data.get('contributors', [])[:5]):
            name = c.get('name', 'Unknown')
            commits = c.get('commits', '0')
            net_lines = self._format_number(c.get('net_lines', '0'))
            repos = c.get('repos', [])
            langs = c.get('langs', []) or self._infer_langs_from_repos(repos)
            detail_str = self._format_tech_repos(langs, repos)
            contributor_table += f"| {name} | {commits}次 | {net_lines}行 | {detail_str} |\n"
            # 第一个就是MVP
            if i == 0:
                mvp = {'name': name, 'commits': commits, 'net_lines': net_lines, 'repos': repos}

        # MVP 部分
        mvp_section = ""
        if mvp:
            repos_str = ', '.join(mvp['repos'][:3])
            if len(mvp['repos']) > 3:
                repos_str += f" 等{len(mvp['repos'])}个"
            mvp_section = f"""
---

### 🏆 本周MVP (综合评分最高)

- **姓名**: {mvp['name']}
- **提交数**: {mvp['commits']} 次
- **净增代码**: {mvp['net_lines']} 行
- **涉及仓库**: {repos_str if repos_str else 'N/A'}"""

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
{contributor_table}{mvp_section}

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
        """格式化月报消息 (丰富格式)"""
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

        # 核心指标表格 - 使用 with_sign=False 避免重复符号
        added = self._format_number(data.get('added', '0'), with_sign=False)
        deleted = self._format_number(data.get('deleted', '0'), with_sign=False)

        # TOP 10 贡献者表格
        top10_table = ""
        for c in data.get('contributors', [])[:10]:
            rank = c.get('rank', '')
            name = c.get('name', '')
            commits = c.get('commits', '0')
            net = self._format_number(c.get('net', '0'))
            c_score = c.get('score', '0')
            top10_table += f"| {rank} | {name} | {commits}次 | {net}行 | {c_score} |\n"

        # 每周趋势表格
        weekly_table = ""
        for w in data.get('weekly_trends', []):
            week = w.get('week', '')
            w_commits = w.get('commits', '0')
            w_net = self._format_number(w.get('net', '0'))
            w_authors = w.get('authors', '0')
            weekly_table += f"| {week} | {w_commits}次 | {w_net}行 | {w_authors}人 |\n"

        # MVP 信息 (综合评分最高) - 丰富展示内容
        mvp_name = data.get('mvp_name', '')
        mvp_commits = data.get('mvp_commits', '0')
        mvp_score = data.get('mvp_score', '0')
        mvp_section = ""
        if mvp_name:
            # 从contributors中获取MVP的更多信息
            mvp_net = '0'
            mvp_added = '0'
            for c in data.get('contributors', []):
                if c.get('rank') == '🥇':
                    mvp_net = self._format_number(c.get('net', '0'))
                    mvp_added = self._format_number(c.get('added', '0'), with_sign=False)
                    break
            mvp_section = f"""
---

### 🏆 本月MVP (综合评分最高)

- **姓名**: {mvp_name}
- **综合分**: {mvp_score} 分
- **提交数**: {mvp_commits} 次
- **新增代码**: {mvp_added} 行
- **净增代码**: {mvp_net} 行"""

        # 风险监控
        late_night = int(data.get('late_night', 0))
        weekend = int(data.get('weekend', 0))
        normal_hours = int(data.get('normal_hours', 0))
        overtime = int(data.get('overtime', 0))
        total_commits = int(data.get('commits', 0)) or 1

        risk_section = ""
        if late_night > 0 or weekend > 0:
            late_pct = late_night / total_commits * 100
            weekend_pct = weekend / total_commits * 100
            risk_section = f"""

---

### ⚠️ 风险监控

| 类型 | 次数 | 占比 |
|------|------|------|
| 深夜提交 | {late_night}次 | {late_pct:.1f}% |
| 周末提交 | {weekend}次 | {weekend_pct:.1f}% |"""

        # 构建完整消息
        content = f"""## 📊 代码管理 - {year}年{month_name}月报

**报告周期**: {month_str} | **系统**: {self.project_name}

---

### 📈 核心指标

| 指标 | 数值 |
|------|------|
| 总提交数 | {data.get('commits', '0')} 次 |
| 活跃开发者 | {data.get('developers', '0')} 人 |
| 活跃仓库 | {data.get('repos', '0')} 个 |
| 代码新增 | +{added} 行 |
| 代码删除 | -{deleted} 行 |
| 代码净增 | {lines} 行 |
| 工作日数 | {data.get('work_days', '0')} 天 |
| 日均提交 | {data.get('daily_avg', '0')} 次 |
| 健康评分 | {data.get('score', '0')} 分 {score_level} |

---

### 🏆 TOP 10 月度贡献

| 排名 | 开发者 | 提交 | 净增 | 综合分 |
|------|--------|------|------|--------|
{top10_table}"""

        # 添加每周趋势 (如果有数据)
        if weekly_table:
            content += f"""
---

### 📊 每周趋势对比

| 周期 | 提交 | 净增 | 活跃人数 |
|------|------|------|---------|
{weekly_table}"""

        # 添加 MVP 和风险监控
        content += mvp_section
        content += risk_section

        # 添加链接和底部
        content += f"""

---

### 🔗 详细报告

[📄 完整月报]({report_url}) | [📊 可视化仪表盘]({dashboard_url})

---

> 🤖 由代码管理系统自动生成"""

        return content
