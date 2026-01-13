"""
返工率分析器
检测新增代码被快速删除的情况
"""

from typing import List, Dict, Tuple
from collections import defaultdict

from .git_analyzer import GitAnalyzer
from ..utils.helpers import parse_iso_datetime


class ReworkAnalyzer:
    """
    返工率分析器

    返工定义：新增的代码在短时间内被删除
    这可能表示：
    - 需求变更
    - 实现方案不合理
    - 代码 review 后重写
    """

    def __init__(
        self,
        git_analyzer: GitAnalyzer,
        add_days: int = 7,
        delete_days: int = 3
    ):
        """
        初始化返工分析器

        Args:
            git_analyzer: Git 分析器实例
            add_days: 新增代码观察周期（天）
            delete_days: 删除检测周期（天），在此期间内删除视为返工
        """
        self.git_analyzer = git_analyzer
        self.add_days = add_days
        self.delete_days = delete_days

    def analyze(self) -> Tuple[int, int, float]:
        """
        分析返工率

        Returns:
            (返工行数, 总新增行数, 返工率百分比)
        """
        since = f"{self.add_days} days ago"
        commits = self.git_analyzer.get_commits(since)

        # 统计每个文件的变更历史
        file_changes: Dict[str, List[Dict]] = defaultdict(list)

        for commit in commits:
            try:
                commit_date = parse_iso_datetime(commit.date)
            except Exception:
                continue

            for file_change in commit.files:
                file_changes[file_change.path].append({
                    'date': commit_date,
                    'added': file_change.added,
                    'deleted': file_change.deleted
                })

        # 检测返工：N天内新增，M天内被删除
        rework_lines = 0
        total_added = 0

        for filepath, changes in file_changes.items():
            # 按时间排序
            changes.sort(key=lambda x: x['date'])

            for i, change in enumerate(changes):
                total_added += change['added']

                # 检查这次新增是否在后续几天内被删除
                for j in range(i + 1, len(changes)):
                    days_diff = (changes[j]['date'] - change['date']).days
                    if days_diff <= self.delete_days:
                        # 简化计算：如果后续有删除，认为是部分返工
                        estimated_rework = min(change['added'], changes[j]['deleted'])
                        rework_lines += estimated_rework

        # 计算返工率
        rework_rate = (rework_lines / total_added * 100) if total_added > 0 else 0

        return rework_lines, total_added, rework_rate

    def get_rework_summary(self) -> Dict:
        """
        获取返工分析摘要

        Returns:
            {
                'rework_lines': 返工行数,
                'total_added': 总新增行数,
                'rework_rate': 返工率,
                'level': 风险等级 (low/medium/high)
            }
        """
        rework_lines, total_added, rework_rate = self.analyze()

        # 判断风险等级
        if rework_rate > 30:
            level = 'high'
        elif rework_rate > 15:
            level = 'medium'
        else:
            level = 'low'

        return {
            'rework_lines': rework_lines,
            'total_added': total_added,
            'rework_rate': round(rework_rate, 2),
            'level': level
        }

    def get_rework_by_author(self) -> Dict[str, Dict]:
        """
        按作者统计返工情况

        Returns:
            {
                author: {
                    'added': 新增行数,
                    'rework': 返工行数,
                    'rate': 返工率
                }
            }
        """
        since = f"{self.add_days} days ago"
        commits = self.git_analyzer.get_commits(since)

        # 按作者统计
        author_stats: Dict[str, Dict] = defaultdict(lambda: {'added': 0, 'rework': 0})

        # 按文件跟踪变更
        file_changes: Dict[str, List[Dict]] = defaultdict(list)

        for commit in commits:
            try:
                commit_date = parse_iso_datetime(commit.date)
            except Exception:
                continue

            author = commit.author

            for file_change in commit.files:
                author_stats[author]['added'] += file_change.added

                file_changes[file_change.path].append({
                    'date': commit_date,
                    'author': author,
                    'added': file_change.added,
                    'deleted': file_change.deleted
                })

        # 计算每个作者的返工
        for filepath, changes in file_changes.items():
            changes.sort(key=lambda x: x['date'])

            for i, change in enumerate(changes):
                for j in range(i + 1, len(changes)):
                    days_diff = (changes[j]['date'] - change['date']).days
                    if days_diff <= self.delete_days:
                        estimated_rework = min(change['added'], changes[j]['deleted'])
                        author_stats[change['author']]['rework'] += estimated_rework

        # 计算返工率
        result = {}
        for author, stats in author_stats.items():
            rate = (stats['rework'] / stats['added'] * 100) if stats['added'] > 0 else 0
            result[author] = {
                'added': stats['added'],
                'rework': stats['rework'],
                'rate': round(rate, 2)
            }

        return result
