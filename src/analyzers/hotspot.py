"""
高危文件分析器
识别可能存在风险的文件
"""

from typing import List, Dict

from .git_analyzer import GitAnalyzer


class HotspotAnalyzer:
    """
    高危文件分析器

    基于多个维度识别高风险文件：
    - 修改频率：频繁修改的文件可能不稳定
    - 文件大小：大文件往往复杂度高
    - 协作人数：多人编辑的文件容易冲突
    - 文件类型：某些类型的文件更容易出问题
    """

    def __init__(self, git_analyzer: GitAnalyzer, config: Dict):
        """
        初始化高危文件分析器

        Args:
            git_analyzer: Git 分析器实例
            config: 配置字典，包含阈值设置
        """
        self.git_analyzer = git_analyzer
        self.config = config

    def analyze(self, days: int = None) -> List[Dict]:
        """
        分析高危文件

        Args:
            days: 分析周期（天），默认使用配置中的 hotspot_days

        Returns:
            高危文件列表，每个元素包含：
            {
                'file': 文件路径,
                'risk_score': 风险分数 (0-100),
                'modify_count': 修改次数,
                'file_size': 文件行数,
                'author_count': 作者数量,
                'authors': 作者列表,
                'tags': 风险标签列表,
                'suggestion': 改进建议
            }
        """
        if days is None:
            days = self.config.get('hotspot_days', 7)

        since = f"{days} days ago"
        files = self.git_analyzer.get_all_modified_files(since)

        hotspots = []
        for filepath in files:
            # 跳过排除的文件
            if self._should_exclude(filepath):
                continue

            history = self.git_analyzer.get_file_history(filepath, since)
            modify_count = len(history)
            file_size = self.git_analyzer.get_file_size(filepath)
            authors = self.git_analyzer.get_file_authors(filepath, since)

            # 计算风险分数
            risk_score = self._calculate_risk_score(modify_count, file_size, len(authors))

            # 识别风险标签
            tags = self._get_risk_tags(modify_count, file_size, len(authors), filepath)

            # 只记录中等以上风险
            if risk_score > 40:
                hotspots.append({
                    'file': filepath,
                    'risk_score': risk_score,
                    'modify_count': modify_count,
                    'file_size': file_size,
                    'author_count': len(authors),
                    'authors': list(authors),
                    'tags': tags,
                    'suggestion': self._get_suggestion(tags, file_size)
                })

        # 按风险分数排序
        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)

        return hotspots

    def _calculate_risk_score(
        self,
        modify_count: int,
        file_size: int,
        author_count: int
    ) -> float:
        """
        计算风险分数

        评分维度：
        - 修改频率 (30%)
        - 文件大小 (25%)
        - 协作人数 (20%)
        - 复杂度预估 (25%)

        Args:
            modify_count: 修改次数
            file_size: 文件行数
            author_count: 作者数量

        Returns:
            风险分数 (0-100)
        """
        # 修改频率分数
        freq_score = min(modify_count / 10 * 100, 100)

        # 文件大小分数
        size_score = min(file_size / 1000 * 100, 100)

        # 协作人数分数
        author_score = min(author_count / 5 * 100, 100)

        # 综合计算
        risk = (freq_score * 0.3 + size_score * 0.25 + author_score * 0.2)

        return round(risk, 2)

    def _get_risk_tags(
        self,
        modify_count: int,
        file_size: int,
        author_count: int,
        filepath: str
    ) -> List[str]:
        """
        获取风险标签

        Args:
            modify_count: 修改次数
            file_size: 文件行数
            author_count: 作者数量
            filepath: 文件路径

        Returns:
            风险标签列表
        """
        tags = []

        hotspot_count = self.config.get('hotspot_count', 10)
        large_file = self.config.get('large_file', 1000)
        multi_author = self.config.get('multi_author_count', 3)

        if modify_count >= hotspot_count:
            tags.append("高频修改")

        if file_size >= large_file:
            tags.append("大型文件")

        if author_count >= multi_author:
            tags.append("多人协作")

        # 基于文件类型判断复杂度
        if filepath.endswith('.java'):
            if file_size > 800:
                tags.append("复杂文件")
        elif filepath.endswith('.py'):
            if file_size > 500:
                tags.append("复杂文件")
        elif filepath.endswith(('.ts', '.tsx', '.js', '.jsx')):
            if file_size > 600:
                tags.append("复杂文件")
        elif filepath.endswith('.vue'):
            if file_size > 500:
                tags.append("复杂文件")

        return tags

    def _get_suggestion(self, tags: List[str], file_size: int) -> str:
        """
        获取改进建议

        Args:
            tags: 风险标签列表
            file_size: 文件行数

        Returns:
            改进建议字符串
        """
        if "大型文件" in tags and "复杂文件" in tags:
            return "🔴 建议拆分文件，提取公共逻辑"
        elif "高频修改" in tags:
            return "🟠 建议稳定接口，减少频繁修改"
        elif "多人协作" in tags:
            return "🟡 建议明确模块职责，减少协作冲突"
        else:
            return "🟢 保持关注"

    def _should_exclude(self, filepath: str) -> bool:
        """
        判断是否应该排除此文件

        Args:
            filepath: 文件路径

        Returns:
            是否排除
        """
        exclude_patterns = self.config.get('exclude_patterns', [])
        exclude_dirs = self.config.get('exclude_dirs', [])

        # 检查目录
        for dir_pattern in exclude_dirs:
            if dir_pattern in filepath:
                return True

        # 检查文件模式
        for pattern in exclude_patterns:
            if pattern.startswith('*.'):
                ext = pattern[1:]
                if filepath.endswith(ext):
                    return True
            elif pattern in filepath:
                return True

        return False

    def get_summary(self, days: int = None) -> Dict:
        """
        获取高危文件分析摘要

        Args:
            days: 分析周期

        Returns:
            {
                'total': 高危文件总数,
                'high_risk': 高风险文件数 (分数>70),
                'medium_risk': 中风险文件数 (分数40-70),
                'top_files': 前5个高危文件,
                'by_tag': 按标签分类统计
            }
        """
        hotspots = self.analyze(days)

        high_risk = [h for h in hotspots if h['risk_score'] > 70]
        medium_risk = [h for h in hotspots if 40 < h['risk_score'] <= 70]

        # 按标签统计
        tag_counts = {}
        for h in hotspots:
            for tag in h['tags']:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            'total': len(hotspots),
            'high_risk': len(high_risk),
            'medium_risk': len(medium_risk),
            'top_files': hotspots[:5],
            'by_tag': tag_counts
        }
