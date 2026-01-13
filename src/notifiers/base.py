"""
通知器基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import re

from ..config import Config


class BaseNotifier(ABC):
    """
    通知器抽象基类

    所有通知器（钉钉、飞书等）都继承此类
    """

    def __init__(self, config: Config):
        """
        初始化通知器

        Args:
            config: 配置对象
        """
        self.config = config
        self.project_name = config.project_name
        self.base_url = config.web_base_url

    @abstractmethod
    def is_enabled(self) -> bool:
        """检查是否启用"""
        pass

    @abstractmethod
    def send(self, title: str, content: str, msg_type: str = 'markdown') -> bool:
        """
        发送通知

        Args:
            title: 消息标题
            content: 消息内容
            msg_type: 消息类型 (text/markdown)

        Returns:
            是否发送成功
        """
        pass

    def send_daily_report(self, report_date: str, report_content: str) -> bool:
        """
        发送日报通知

        Args:
            report_date: 报告日期 (YYYY-MM-DD)
            report_content: 报告内容 (Markdown)

        Returns:
            是否发送成功
        """
        data = self._extract_daily_data(report_content)
        title = "代码健康日报"
        content = self._format_daily_message(report_date, data)
        return self.send(title, content)

    def send_weekly_report(self, week_str: str, report_content: str) -> bool:
        """
        发送周报通知

        Args:
            week_str: 周标识 (YYYY-Wxx)
            report_content: 报告内容 (Markdown)

        Returns:
            是否发送成功
        """
        data = self._extract_weekly_data(report_content)
        title = "代码健康周报"
        content = self._format_weekly_message(week_str, data)
        return self.send(title, content)

    def send_monthly_report(self, month_str: str, report_content: str) -> bool:
        """
        发送月报通知

        Args:
            month_str: 月份标识 (YYYY-MM)
            report_content: 报告内容 (Markdown)

        Returns:
            是否发送成功
        """
        data = self._extract_monthly_data(report_content)
        title = "代码健康月报"
        content = self._format_monthly_message(month_str, data)
        return self.send(title, content)

    def _extract_daily_data(self, content: str) -> Dict:
        """从日报中提取关键数据"""
        data = {
            'commits': '0',
            'developers': '0',
            'repos': '0',
            'lines': '+0',
            'score': '0',
            'churn_rate': '0',
            'rework_rate': '0',
            'overtime': '0',
            'late_night': '0',
            'weekend': '0',
            'top_developers': [],
        }

        # 提取提交次数
        match = re.search(r'\| 提交次数 \| \*\*(\d+)\*\*', content)
        if match:
            data['commits'] = match.group(1)

        # 提取活跃开发者数
        match = re.search(r'\| 活跃开发者 \| \*\*(\d+)\*\*', content)
        if match:
            data['developers'] = match.group(1)

        # 提取涉及仓库数
        match = re.search(r'\| 涉及仓库 \| \*\*(\d+)\*\*', content)
        if match:
            data['repos'] = match.group(1)

        # 提取净增行数
        match = re.search(r'\| \*\*净增行数\*\* \| \*\*([+-]?[\d,]+)\*\*', content)
        if match:
            data['lines'] = match.group(1).replace(',', '')

        # 提取综合评分
        match = re.search(r'综合评分: ([\d.]+)', content)
        if match:
            data['score'] = match.group(1)

        # 提取加班提交
        match = re.search(r'加班提交 \| (\d+) 次', content)
        if match:
            data['overtime'] = match.group(1)

        # 提取深夜提交
        match = re.search(r'深夜提交 \| (\d+) 次', content)
        if match:
            data['late_night'] = match.group(1)

        # 提取周末提交
        match = re.search(r'周末提交 \| (\d+) 次', content)
        if match:
            data['weekend'] = match.group(1)

        # 提取 TOP 开发者信息 (从提交详情中)
        data['top_developers'] = self._extract_top_developers(content)

        return data

    def _extract_top_developers(self, content: str) -> List[Dict]:
        """从报告中提取 TOP 开发者信息"""
        developers = []
        lines = content.split('\n')

        in_detail = False
        current_dev = None

        for line in lines:
            # 查找开发者信息 (格式: ### 👤 开发者名)
            if line.startswith('### 👤 '):
                # 先保存上一个开发者
                if current_dev:
                    current_dev['repos'] = list(current_dev['repos'])
                    developers.append(current_dev)
                in_detail = True
                dev_name = line.replace('### 👤 ', '').strip()
                current_dev = {'name': dev_name, 'commits': 0, 'net_lines': 0, 'repos': set(), 'langs': []}
                continue

            # 提取开发者统计 (格式: 提交: X 次 | ... | 技术栈: Python, Shell)
            if in_detail and current_dev and line.startswith('提交:'):
                match = re.search(r'提交: (\d+) 次.*净增: ([+-]?[\d,]+)', line)
                if match:
                    current_dev['commits'] = int(match.group(1))
                    current_dev['net_lines'] = int(match.group(2).replace(',', '').replace('+', ''))
                # 提取技术栈
                lang_match = re.search(r'技术栈: ([^|]+)$', line)
                if lang_match:
                    langs = [l.strip() for l in lang_match.group(1).split(',')]
                    current_dev['langs'] = langs[:2]
                continue

            # 提取仓库信息 (格式: - [仓库名] ...)
            if in_detail and current_dev and line.startswith('- ['):
                match = re.search(r'- \[([^\]]+)\]', line)
                if match:
                    current_dev['repos'].add(match.group(1))
                continue

            # 遇到新章节，保存当前开发者
            if line.startswith('## ') and current_dev:
                current_dev['repos'] = list(current_dev['repos'])
                developers.append(current_dev)
                current_dev = None
                in_detail = False

        # 保存最后一个开发者
        if current_dev:
            current_dev['repos'] = list(current_dev['repos'])
            developers.append(current_dev)

        # 按提交次数排序，取前3
        developers.sort(key=lambda x: x['commits'], reverse=True)
        return developers[:3]

    def _extract_weekly_data(self, content: str) -> Dict:
        """从周报中提取关键数据"""
        data = {
            'commits': '0',
            'developers': '0',
            'lines': '+0',
            'score': '0',
            'contributors': [],
        }

        # 提取总提交数
        match = re.search(r'\| 总提交数 \| (\d+)', content)
        if match:
            data['commits'] = match.group(1)

        # 提取活跃开发者
        match = re.search(r'\| 活跃开发者 \| (\d+)', content)
        if match:
            data['developers'] = match.group(1)

        # 提取总净增行数
        match = re.search(r'\| \*\*总净增行数\*\* \| \*\*([+-]?[\d,]+)\*\*', content)
        if match:
            data['lines'] = match.group(1).replace(',', '')

        # 提取综合评分 (支持多种格式)
        match = re.search(r'综合评分:\s*([\d.]+)', content)
        if match:
            data['score'] = match.group(1)

        # 提取贡献排行榜（TOP 5）
        lines = content.split('\n')
        in_table = False
        for line in lines:
            if '贡献排行榜' in line or '提交量排行榜' in line:
                in_table = True
                continue
            if in_table and line.startswith('| ') and not line.startswith('| 排名') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 7:
                    try:
                        rank = parts[1]
                        if rank.isdigit() or rank in ['🥇', '🥈', '🥉', '1', '2', '3', '4', '5']:
                            # 找到净增行数列 (包含 ** 标记或 + 号)
                            net_lines_idx = -1
                            for i, p in enumerate(parts):
                                if '**' in p or ('+' in p and i > 3):
                                    net_lines_idx = i
                                    break

                            # 找到仓库列 (最后一个非空列，通常是最后一列)
                            repos_idx = len(parts) - 2  # 倒数第二个 (最后一个是空的)
                            repos_str = parts[repos_idx] if repos_idx > 0 else ''

                            # 提取净增行数
                            net_lines = '0'
                            if net_lines_idx > 0:
                                net_lines = parts[net_lines_idx].replace('**', '').replace('+', '').replace(',', '')

                            # 提取仓库列表
                            repos = []
                            if repos_str and repos_str != 'N/A':
                                # 移除"等N个"和"X个"后缀
                                repos_str = re.sub(r'\s*等?\d+个$', '', repos_str)
                                repos = [r.strip() for r in repos_str.split(',') if r.strip()]

                            contributor = {
                                'rank': rank.replace('🥇', '1').replace('🥈', '2').replace('🥉', '3'),
                                'name': parts[2],
                                'commits': parts[3],
                                'net_lines': net_lines,
                                'repos': repos,
                                'langs': [],
                            }
                            data['contributors'].append(contributor)
                            if len(data['contributors']) >= 5:
                                break
                    except (IndexError, ValueError):
                        pass

        return data

    def _extract_monthly_data(self, content: str) -> Dict:
        """从月报中提取关键数据"""
        data = {
            'commits': '0',
            'developers': '0',
            'lines': '+0',
            'score': '0',
            'work_days': '0',
            'mvp_name': '',
            'mvp_commits': '0',
            'late_night': '0',
            'weekend': '0',
        }

        # 提取总提交次数
        match = re.search(r'\| 总提交次数 \| \*\*(\d+)\*\*', content)
        if match:
            data['commits'] = match.group(1)

        # 提取活跃开发者
        match = re.search(r'\| 活跃开发者 \| \*\*(\d+)\*\*', content)
        if match:
            data['developers'] = match.group(1)

        # 提取代码净增
        match = re.search(r'\| 代码净增 \| \*\*([+-]?[\d,]+)\*\*', content)
        if match:
            data['lines'] = match.group(1).replace(',', '')

        # 提取健康分 (支持多种格式)
        match = re.search(r'(?:综合健康分|平均健康分).*?:\s*([\d.]+)', content)
        if match:
            data['score'] = match.group(1)

        # 提取工作日 (支持多种格式: "工作日数: 23 天" 或 "**工作日数**: 23 天")
        match = re.search(r'\*?\*?工作日(?:数)?\*?\*?:\s*(\d+)\s*天', content)
        if match:
            data['work_days'] = match.group(1)

        # 提取 MVP 信息 (🥇 排名第一的贡献者)
        match = re.search(r'\| 🥇 \| ([^|]+) \| (\d+)', content)
        if match:
            data['mvp_name'] = match.group(1).strip()
            data['mvp_commits'] = match.group(2)

        # 提取深夜提交数
        match = re.search(r'深夜(?:时间|提交)[^|]*\|\s*(\d+)', content)
        if match:
            data['late_night'] = match.group(1)

        # 提取周末提交数
        match = re.search(r'周末(?:时间|提交)[^|]*\|\s*(\d+)', content)
        if match:
            data['weekend'] = match.group(1)

        return data

    def _format_number(self, num_str: str) -> str:
        """格式化数字，添加千分位"""
        try:
            num = int(num_str.replace(',', '').replace('+', '').replace('-', ''))
            prefix = '+' if not num_str.startswith('-') and num > 0 else ''
            formatted = f"{num:,}"
            return f"{prefix}{formatted}"
        except ValueError:
            return num_str

    def _get_score_level(self, score: float) -> str:
        """获取评分等级"""
        if score >= 90:
            return "🟢 优秀"
        elif score >= 80:
            return "🟡 良好"
        elif score >= 60:
            return "🟠 中等"
        else:
            return "🔴 需改进"

    @abstractmethod
    def _format_daily_message(self, report_date: str, data: Dict) -> str:
        """格式化日报消息"""
        pass

    @abstractmethod
    def _format_weekly_message(self, week_str: str, data: Dict) -> str:
        """格式化周报消息"""
        pass

    @abstractmethod
    def _format_monthly_message(self, month_str: str, data: Dict) -> str:
        """格式化月报消息"""
        pass
