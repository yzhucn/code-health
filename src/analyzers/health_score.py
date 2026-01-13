"""
健康评分计算器
综合多个维度计算代码健康分数
"""

from typing import Dict, List, Tuple


class HealthScoreCalculator:
    """
    健康评分计算器

    基于多个维度计算代码健康分数：
    - 大提交数量
    - 代码震荡率
    - 返工率
    - 提交信息质量
    - 异常工作时间
    - 高危文件数量
    """

    def __init__(self, config: Dict):
        """
        初始化健康评分计算器

        Args:
            config: 配置字典，包含阈值设置
        """
        self.config = config

    def calculate(self, metrics: Dict) -> Tuple[float, List[str]]:
        """
        计算健康评分

        Args:
            metrics: 指标字典，包含：
                - large_commits: 大提交数量
                - churn_rate: 代码震荡率
                - rework_rate: 返工率
                - message_quality: 提交信息质量
                - late_night_commits: 深夜提交数
                - weekend_commits: 周末提交数
                - high_risk_files: 高危文件数

        Returns:
            (分数, 扣分原因列表)
        """
        score = 100.0
        deductions = []

        # 大提交扣分（每次扣5分）
        large_commits = metrics.get('large_commits', 0)
        if large_commits > 0:
            deduction = large_commits * 5
            score -= deduction
            deductions.append(f"大提交 ({large_commits}次): -{deduction}分")

        # 震荡率扣分
        churn_rate = metrics.get('churn_rate', 0)
        churn_danger = self.config.get('churn_rate_danger', 30)
        churn_warning = self.config.get('churn_rate_warning', 10)

        if churn_rate > churn_danger:
            deduction = 20
            score -= deduction
            deductions.append(f"高震荡率 ({churn_rate:.1f}%): -{deduction}分")
        elif churn_rate > churn_warning:
            deduction = 10
            score -= deduction
            deductions.append(f"中等震荡率 ({churn_rate:.1f}%): -{deduction}分")

        # 返工率扣分
        rework_rate = metrics.get('rework_rate', 0)
        rework_danger = self.config.get('rework_rate_danger', 30)
        rework_warning = self.config.get('rework_rate_warning', 15)

        if rework_rate > rework_danger:
            deduction = 15
            score -= deduction
            deductions.append(f"高返工率 ({rework_rate:.1f}%): -{deduction}分")
        elif rework_rate > rework_warning:
            deduction = 8
            score -= deduction
            deductions.append(f"中等返工率 ({rework_rate:.1f}%): -{deduction}分")

        # 提交信息质量扣分
        message_quality = metrics.get('message_quality', 100)
        if message_quality < 60:
            deduction = 10
            score -= deduction
            deductions.append(f"提交信息质量差 ({message_quality:.0f}%): -{deduction}分")

        # 深夜/周末工作扣分（每次扣2分）
        late_commits = metrics.get('late_night_commits', 0)
        weekend_commits = metrics.get('weekend_commits', 0)
        abnormal_commits = late_commits + weekend_commits

        if abnormal_commits > 0:
            deduction = abnormal_commits * 2
            score -= deduction
            deductions.append(f"异常工作时间 ({abnormal_commits}次): -{deduction}分")

        # 高危文件扣分（每个扣3分，最多15分）
        high_risk_files = metrics.get('high_risk_files', 0)
        if high_risk_files > 0:
            deduction = min(high_risk_files * 3, 15)
            score -= deduction
            deductions.append(f"高危文件 ({high_risk_files}个): -{deduction}分")

        # 确保分数不低于0
        score = max(0, score)

        return round(score, 1), deductions

    def get_level(self, score: float) -> Tuple[str, str]:
        """
        获取评分等级

        Args:
            score: 健康分数

        Returns:
            (等级emoji, 等级描述)
        """
        excellent = self.config.get('health_score_excellent', 80)
        good = self.config.get('health_score_good', 60)
        warning = self.config.get('health_score_warning', 40)

        if score >= excellent:
            return "🟢", "优秀"
        elif score >= good:
            return "🟡", "良好"
        elif score >= warning:
            return "🟠", "警告"
        else:
            return "🔴", "危险"

    def get_full_report(self, metrics: Dict) -> Dict:
        """
        获取完整的健康评分报告

        Args:
            metrics: 指标字典

        Returns:
            {
                'score': 健康分数,
                'level': 等级描述,
                'emoji': 等级emoji,
                'deductions': 扣分原因列表,
                'metrics': 原始指标
            }
        """
        score, deductions = self.calculate(metrics)
        emoji, level = self.get_level(score)

        return {
            'score': score,
            'level': level,
            'emoji': emoji,
            'deductions': deductions,
            'metrics': metrics
        }


def calculate_large_commits(commits: list, threshold: int = 500) -> int:
    """
    计算大提交数量

    Args:
        commits: 提交列表
        threshold: 大提交阈值（行数）

    Returns:
        大提交数量
    """
    count = 0
    for commit in commits:
        # 支持 CommitInfo 对象和 dict
        if hasattr(commit, 'lines_added'):
            total_lines = commit.lines_added + commit.lines_deleted
        else:
            total_lines = commit.get('lines_added', 0) + commit.get('lines_deleted', 0)

        if total_lines > threshold:
            count += 1

    return count
