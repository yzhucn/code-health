"""
报告生成器基类
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from ..config import Config
from ..providers.base import GitProvider, CommitInfo
from ..analyzers import (
    GitAnalyzer,
    ChurnAnalyzer,
    ReworkAnalyzer,
    HotspotAnalyzer,
    HealthScoreCalculator,
    calculate_large_commits,
)
from ..utils.helpers import (
    format_number,
    is_late_night,
    is_weekend,
    is_overtime,
    calculate_message_quality,
    parse_iso_datetime,
)


class BaseReporter(ABC):
    """
    报告生成器基类

    所有报告生成器都需要继承此类并实现 generate 方法
    """

    def __init__(self, provider: GitProvider, config: Config):
        """
        初始化报告生成器

        Args:
            provider: Git 数据提供者
            config: 配置对象
        """
        self.provider = provider
        self.config = config
        self.thresholds = config.thresholds

    @abstractmethod
    def generate(self) -> str:
        """生成报告内容"""
        pass

    def get_all_commits(
        self,
        since: str,
        until: Optional[str] = None
    ) -> List[Dict]:
        """
        获取所有仓库的提交

        Args:
            since: 开始时间
            until: 结束时间

        Returns:
            提交列表，每个提交包含 repo 字段
        """
        all_commits = []
        repos = self.provider.list_repositories()

        for repo in repos:
            try:
                commits = self.provider.get_commits(repo.id, since, until)
                for commit in commits:
                    all_commits.append({
                        'hash': commit.hash,
                        'author': commit.author,
                        'email': commit.email,
                        'date': commit.date,
                        'message': commit.message,
                        'files': [{'path': f.path, 'added': f.added, 'deleted': f.deleted} for f in commit.files],
                        'lines_added': commit.lines_added,
                        'lines_deleted': commit.lines_deleted,
                        'repo': repo.name,
                        'repo_type': repo.type,
                    })
            except Exception as e:
                print(f"  ⚠️  获取 {repo.name} 提交失败: {e}")

        return all_commits

    def analyze_repo(
        self,
        repo_id: str,
        since: str,
        until: Optional[str] = None,
        detailed: bool = False
    ) -> Dict:
        """
        分析单个仓库

        Args:
            repo_id: 仓库 ID
            since: 开始时间
            until: 结束时间
            detailed: 是否进行详细分析

        Returns:
            分析结果字典
        """
        git_analyzer = GitAnalyzer(self.provider, repo_id)
        commits = git_analyzer.get_commits(since, until)

        result = {
            'repo_id': repo_id,
            'commits': len(commits),
            'lines_added': sum(c.lines_added for c in commits),
            'lines_deleted': sum(c.lines_deleted for c in commits),
            'authors': list(set(c.author for c in commits)),
            'author_count': len(set(c.author for c in commits)),
        }

        if not commits:
            return result

        # 计算大提交
        result['large_commits'] = calculate_large_commits(
            commits,
            self.thresholds.get('large_commit', 500)
        )

        # 计算提交信息质量
        result['message_quality'] = calculate_message_quality(commits)

        # 计算异常工作时间提交
        config_dict = self.config.to_dict()
        result['late_night_commits'] = sum(
            1 for c in commits if is_late_night(c.date, config_dict)
        )
        result['weekend_commits'] = sum(
            1 for c in commits if is_weekend(c.date)
        )
        result['overtime_commits'] = sum(
            1 for c in commits if is_overtime(c.date, config_dict)
        )

        # 详细分析
        if detailed:
            # 震荡分析
            churn_analyzer = ChurnAnalyzer(
                git_analyzer,
                churn_days=self.thresholds.get('churn_days', 3),
                churn_count=self.thresholds.get('churn_count', 5)
            )
            churn_files, churn_rate = churn_analyzer.analyze()
            result['churn_rate'] = churn_rate
            result['churn_files'] = churn_files[:5]

            # 返工分析
            rework_analyzer = ReworkAnalyzer(
                git_analyzer,
                add_days=self.thresholds.get('rework_add_days', 7),
                delete_days=self.thresholds.get('rework_delete_days', 3)
            )
            rework_lines, total_added, rework_rate = rework_analyzer.analyze()
            result['rework_rate'] = rework_rate
            result['rework_lines'] = rework_lines

            # 高危文件分析
            hotspot_analyzer = HotspotAnalyzer(git_analyzer, self.thresholds)
            hotspots = hotspot_analyzer.analyze()
            result['high_risk_files'] = len([h for h in hotspots if h['risk_score'] > 70])
            result['hotspots'] = hotspots[:5]

        return result

    def calculate_health_score(self, results: List[Dict]) -> Dict:
        """
        计算整体健康分数

        Args:
            results: 各仓库分析结果

        Returns:
            健康评分报告
        """
        if not results:
            return {'score': 0, 'level': '无数据', 'emoji': '⚪', 'deductions': [], 'metrics': {}}

        # 聚合指标
        metrics = {
            'large_commits': sum(r.get('large_commits', 0) for r in results),
            'churn_rate': max((r.get('churn_rate', 0) for r in results), default=0),
            'rework_rate': max((r.get('rework_rate', 0) for r in results), default=0),
            'message_quality': sum(r.get('message_quality', 100) for r in results) / len(results),
            'late_night_commits': sum(r.get('late_night_commits', 0) for r in results),
            'weekend_commits': sum(r.get('weekend_commits', 0) for r in results),
            'high_risk_files': sum(r.get('high_risk_files', 0) for r in results),
        }

        calculator = HealthScoreCalculator(self.thresholds)
        return calculator.get_full_report(metrics)

    def _format_header(self, title: str, date_info: str) -> str:
        """格式化报告头部"""
        lines = [
            f"# {title}",
            "",
            f"**项目**: {self.config.project_name}",
            f"**日期**: {date_info}",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---"
        ]
        return '\n'.join(lines)

    def _format_footer(self) -> str:
        """格式化报告底部"""
        lines = [
            "---",
            "",
            "**📌 说明**:",
            "- 数据来源: Git 提交历史",
            "- 更新频率: 自动生成",
            "",
            "*由代码健康监控系统自动生成*"
        ]
        return '\n'.join(lines)
