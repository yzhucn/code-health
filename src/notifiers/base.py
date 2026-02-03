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
        # 表格格式: | 排名 | 开发者 | 提交 | 新增 | 删除 | 净增 | 涉及仓库 | 综合分 |
        lines = content.split('\n')
        in_table = False
        for line in lines:
            if '贡献排行榜' in line or '提交量排行榜' in line:
                in_table = True
                continue
            if in_table and line.startswith('| ') and not line.startswith('| 排名') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]
                # parts: ['', 排名, 开发者, 提交, 新增, 删除, 净增, 涉及仓库, 综合分, '']
                if len(parts) >= 9:
                    try:
                        rank = parts[1]
                        if rank.isdigit() or rank in ['🥇', '🥈', '🥉', '1', '2', '3', '4', '5']:
                            # 固定列索引
                            name = parts[2]
                            commits = parts[3]
                            net_lines_str = parts[6].replace('**', '').replace('+', '').replace(',', '').replace('-', '')
                            repos_str = parts[7] if len(parts) > 7 else ''

                            # 提取仓库列表
                            repos = []
                            if repos_str and repos_str != 'N/A':
                                # 移除"等N个"后缀
                                repos_str = re.sub(r'\s*等\d+个$', '', repos_str)
                                repos = [r.strip() for r in repos_str.split(',') if r.strip()]

                            contributor = {
                                'rank': rank.replace('🥇', '1').replace('🥈', '2').replace('🥉', '3'),
                                'name': name,
                                'commits': commits,
                                'net_lines': net_lines_str,
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
            'repos': '0',
            'lines': '+0',
            'added': '0',
            'deleted': '0',
            'score': '0',
            'work_days': '0',
            'daily_avg': '0',
            'most_active_day': '',
            'mvp_name': '',
            'mvp_commits': '0',
            'mvp_score': '0',
            'late_night': '0',
            'weekend': '0',
            'normal_hours': '0',
            'overtime': '0',
            'contributors': [],
            'weekly_trends': [],
        }

        # 提取总提交次数
        match = re.search(r'\| 总提交次数 \| \*\*([,\d]+)\*\*', content)
        if match:
            data['commits'] = match.group(1).replace(',', '')

        # 提取活跃开发者
        match = re.search(r'\| 活跃开发者 \| \*\*(\d+)\*\*', content)
        if match:
            data['developers'] = match.group(1)

        # 提取活跃仓库
        match = re.search(r'\| 活跃仓库 \| \*\*(\d+)\*\*', content)
        if match:
            data['repos'] = match.group(1)

        # 提取代码新增
        match = re.search(r'\| 代码新增 \| \*\*([,\d]+)\*\*', content)
        if match:
            data['added'] = match.group(1).replace(',', '')

        # 提取代码删除
        match = re.search(r'\| 代码删除 \| \*\*([,\d]+)\*\*', content)
        if match:
            data['deleted'] = match.group(1).replace(',', '')

        # 提取代码净增
        match = re.search(r'\| 代码净增 \| \*\*([+-]?[,\d]+)\*\*', content)
        if match:
            data['lines'] = match.group(1).replace(',', '')

        # 提取日均提交量
        match = re.search(r'\| 日均提交量 \| \*\*([\d.]+)\*\*', content)
        if match:
            data['daily_avg'] = match.group(1)

        # 提取最活跃日
        match = re.search(r'\| 最活跃日 \| ([^|]+) \|', content)
        if match:
            data['most_active_day'] = match.group(1).strip()

        # 提取健康分
        match = re.search(r'(?:综合健康分|月度健康分).*?:\s*([\d.]+)', content)
        if match:
            data['score'] = match.group(1)

        # 提取工作日
        match = re.search(r'工作日[^:]*:\s*(\d+)', content)
        if match:
            data['work_days'] = match.group(1)

        # 提取工作时间分布
        match = re.search(r'正常工作时间[^|]*\|\s*(\d+)', content)
        if match:
            data['normal_hours'] = match.group(1)
        match = re.search(r'加班时间[^|]*\|\s*(\d+)', content)
        if match:
            data['overtime'] = match.group(1)
        match = re.search(r'深夜时间[^|]*\|\s*(\d+)', content)
        if match:
            data['late_night'] = match.group(1)
        match = re.search(r'周末时间[^|]*\|\s*(\d+)', content)
        if match:
            data['weekend'] = match.group(1)

        # 提取 TOP 10 贡献者 (表格格式: | 排名 | 开发者 | 提交 | 新增 | 删除 | 净增 | 涉及仓库 | 综合分 |)
        lines = content.split('\n')
        in_table = False
        for line in lines:
            if '贡献排行榜' in line:
                in_table = True
                continue
            if in_table and line.startswith('| ') and not line.startswith('| 排名') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 9:
                    try:
                        rank = parts[1]
                        name = parts[2]
                        commits = parts[3]
                        added = parts[4].replace('+', '').replace(',', '')
                        deleted = parts[5].replace('-', '').replace(',', '')
                        net = parts[6].replace('**', '').replace('+', '').replace(',', '')
                        score = parts[8] if len(parts) > 8 else '0'

                        contributor = {
                            'rank': rank,
                            'name': name,
                            'commits': commits,
                            'added': added,
                            'deleted': deleted,
                            'net': net,
                            'score': score,
                        }
                        data['contributors'].append(contributor)

                        # MVP 是第一个 (🥇)
                        if rank == '🥇':
                            data['mvp_name'] = name
                            data['mvp_commits'] = commits
                            data['mvp_score'] = score

                        if len(data['contributors']) >= 10:
                            break
                    except (IndexError, ValueError):
                        pass
            elif in_table and line.startswith('## '):
                break

        # 提取每周趋势
        in_weekly = False
        for line in lines:
            if '每周趋势' in line:
                in_weekly = True
                continue
            if in_weekly and line.startswith('| ') and not line.startswith('| 周') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 6:
                    try:
                        week_data = {
                            'week': parts[1],
                            'commits': parts[2],
                            'added': parts[3].replace('+', '').replace(',', ''),
                            'net': parts[5].replace('+', '').replace(',', '').replace('**', ''),
                            'authors': parts[6] if len(parts) > 6 else '0',
                        }
                        data['weekly_trends'].append(week_data)
                    except (IndexError, ValueError):
                        pass
            elif in_weekly and line.startswith('## '):
                break

        return data

    def _format_number(self, num_str: str, with_sign: bool = True) -> str:
        """格式化数字，添加千分位

        Args:
            num_str: 数字字符串
            with_sign: 是否添加正负号前缀，默认True
        """
        try:
            # 检查原始是否为负数
            is_negative = num_str.strip().startswith('-')
            num = int(num_str.replace(',', '').replace('+', '').replace('-', ''))
            formatted = f"{num:,}"

            if with_sign:
                if is_negative:
                    return f"-{formatted}"
                elif num > 0:
                    return f"+{formatted}"
            return formatted
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
