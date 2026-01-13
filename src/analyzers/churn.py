"""
代码震荡分析器
检测频繁修改的文件，识别不稳定代码
"""

from typing import List, Dict, Tuple

from .git_analyzer import GitAnalyzer


class ChurnAnalyzer:
    """
    代码震荡分析器

    检测在短时间内被频繁修改的文件，这些文件可能：
    - 设计不合理，需要重构
    - 需求不清晰，反复变更
    - 存在 bug，需要多次修复
    """

    def __init__(
        self,
        git_analyzer: GitAnalyzer,
        churn_days: int = 3,
        churn_count: int = 5
    ):
        """
        初始化震荡分析器

        Args:
            git_analyzer: Git 分析器实例
            churn_days: 检测周期（天）
            churn_count: 震荡阈值（修改次数）
        """
        self.git_analyzer = git_analyzer
        self.churn_days = churn_days
        self.churn_count = churn_count

    def analyze(self) -> Tuple[List[Dict], float]:
        """
        分析代码震荡

        Returns:
            (震荡文件列表, 震荡率百分比)

        震荡文件结构:
            {
                'file': 文件路径,
                'count': 修改次数,
                'authors': 修改作者列表,
                'size': 文件行数
            }
        """
        since = f"{self.churn_days} days ago"

        # 获取时间范围内修改的所有文件
        files = self.git_analyzer.get_all_modified_files(since)

        churn_files = []
        for filepath in files:
            history = self.git_analyzer.get_file_history(filepath, since)
            modify_count = len(history)

            if modify_count >= self.churn_count:
                authors = self.git_analyzer.get_file_authors(filepath, since)
                file_size = self.git_analyzer.get_file_size(filepath)

                churn_files.append({
                    'file': filepath,
                    'count': modify_count,
                    'authors': list(authors),
                    'size': file_size
                })

        # 计算震荡率
        total_files = len(files) if files else 1
        churn_rate = (len(churn_files) / total_files) * 100

        # 按修改次数排序
        churn_files.sort(key=lambda x: x['count'], reverse=True)

        return churn_files, churn_rate

    def get_churn_summary(self) -> Dict:
        """
        获取震荡分析摘要

        Returns:
            {
                'churn_files': 震荡文件数,
                'churn_rate': 震荡率,
                'top_files': 前5个震荡文件,
                'level': 风险等级 (low/medium/high)
            }
        """
        churn_files, churn_rate = self.analyze()

        # 判断风险等级
        if churn_rate > 30:
            level = 'high'
        elif churn_rate > 10:
            level = 'medium'
        else:
            level = 'low'

        return {
            'churn_files': len(churn_files),
            'churn_rate': round(churn_rate, 2),
            'top_files': churn_files[:5],
            'level': level
        }
