"""
日报生成器
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

from .base import BaseReporter
from ..providers.base import GitProvider
from ..config import Config
from ..utils.helpers import (
    format_number,
    is_late_night,
    is_weekend,
    is_overtime,
    calculate_message_quality,
    parse_iso_datetime,
)

# 文件扩展名到语言的映射
EXTENSION_TO_LANGUAGE = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.jsx': 'JavaScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C/C++',
    '.hpp': 'C++',
    '.cs': 'C#',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.vue': 'Vue',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.less': 'Less',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.md': 'Markdown',
}


def get_language_from_file(filepath: str) -> str:
    """从文件路径获取语言"""
    import os
    ext = os.path.splitext(filepath.lower())[1]
    return EXTENSION_TO_LANGUAGE.get(ext, '')


class DailyReporter(BaseReporter):
    """
    日报生成器

    生成每日代码健康报告，包含：
    - 今日概况
    - 代码变更统计
    - 风险预警
    - 健康评分
    - 提交详情
    """

    def __init__(
        self,
        provider: GitProvider,
        config: Config,
        report_date: Optional[str] = None
    ):
        """
        初始化日报生成器

        Args:
            provider: Git 数据提供者
            config: 配置对象
            report_date: 报告日期 (YYYY-MM-DD)，默认为今天
        """
        super().__init__(provider, config)

        if report_date:
            self.report_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            self.report_date = datetime.now().date()

        # 计算时间范围
        self.since_time = self.report_date.isoformat()
        self.until_time = (self.report_date + timedelta(days=1)).isoformat()

    def generate(self) -> str:
        """生成日报"""
        report = []

        # 标题
        report.append(self._format_header(
            "代码健康日报",
            self.report_date.strftime("%Y-%m-%d")
        ))

        # 获取所有提交
        all_commits = self.get_all_commits(self.since_time, self.until_time)

        # 一、今日概况
        report.append("## 一、今日概况")
        report.append(self._generate_overview(all_commits))

        # 二、代码变更
        report.append("## 二、代码变更统计")
        report.append(self._generate_code_changes(all_commits))

        # 三、风险预警
        report.append("## 三、风险预警 🚨")
        report.append(self._generate_risk_alerts(all_commits))

        # 四、健康评分
        report.append("## 四、今日健康评分")
        report.append(self._generate_health_score(all_commits))

        # 五、提交详情
        report.append("## 五、提交详情")
        report.append(self._generate_commit_details(all_commits))

        # 底部
        report.append(self._format_footer())

        return '\n\n'.join(report)

    def _generate_overview(self, all_commits: list) -> str:
        """生成今日概况"""
        total_commits = len(all_commits)
        active_authors = set(c['author'] for c in all_commits)
        active_repos = set(c['repo'] for c in all_commits)
        total_files = sum(len(c['files']) for c in all_commits)

        # 统计每人提交次数
        author_counts = defaultdict(int)
        for c in all_commits:
            author_counts[c['author']] += 1

        lines = [
            "### 📊 基本数据",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 提交次数 | **{total_commits}** 次 |",
            f"| 活跃开发者 | **{len(active_authors)}** 人 |",
            f"| 涉及仓库 | **{len(active_repos)}** 个 |",
            f"| 修改文件数 | **{total_files}** 个 |",
            ""
        ]

        # 生成活跃开发者详情表格
        if active_authors:
            # 统计每个开发者的详细数据
            author_stats = defaultdict(lambda: {
                'commits': 0, 'added': 0, 'deleted': 0, 'repos': set(), 'languages': set()
            })
            for c in all_commits:
                author = c['author']
                author_stats[author]['commits'] += 1
                author_stats[author]['added'] += c['lines_added']
                author_stats[author]['deleted'] += c['lines_deleted']
                author_stats[author]['repos'].add(c['repo'])

                # 推断主要语言
                inferred_from_file = False
                for f in c['files']:
                    filepath = f.get('path', '')
                    lang = get_language_from_file(filepath)
                    if lang and lang not in ('Markdown', 'YAML', 'JSON', 'XML'):
                        author_stats[author]['languages'].add(lang)
                        inferred_from_file = True

                # 如果无法从文件推断，使用仓库类型推断
                if not inferred_from_file:
                    repo_type = c.get('repo_type', '')
                    if repo_type == 'java':
                        author_stats[author]['languages'].add('Java')
                    elif repo_type == 'python':
                        author_stats[author]['languages'].add('Python')
                    elif repo_type in ('vue', 'frontend'):
                        author_stats[author]['languages'].add('Vue/JS')
                    elif repo_type in ('android', 'flutter'):
                        author_stats[author]['languages'].add('Dart/Kotlin')
                    elif repo_type == 'ios':
                        author_stats[author]['languages'].add('Swift')
                    elif repo_type == 'go':
                        author_stats[author]['languages'].add('Go')

            lines.append("### 👥 活跃开发者详情")
            lines.append("")
            lines.append("| 排名 | 开发者 | 提交次数 | 新增行数 | 删除行数 | 净增行数 | 主要语言 | 涉及仓库 |")
            lines.append("|------|--------|----------|----------|----------|----------|----------|----------|")

            sorted_authors = sorted(author_stats.items(), key=lambda x: x[1]['commits'], reverse=True)
            for rank, (author, stats) in enumerate(sorted_authors, 1):
                net = stats['added'] - stats['deleted']
                languages = ', '.join(sorted(stats['languages'])) if stats['languages'] else '-'
                repos = ', '.join(sorted(stats['repos']))
                lines.append(
                    f"| {rank} | {author} | {stats['commits']} | "
                    f"+{stats['added']} | -{stats['deleted']} | "
                    f"{'+' if net >= 0 else ''}{net} | {languages} | {repos} |"
                )
            lines.append("")

        return '\n'.join(lines)

    def _generate_code_changes(self, all_commits: list) -> str:
        """生成代码变更统计"""
        total_added = sum(c['lines_added'] for c in all_commits)
        total_deleted = sum(c['lines_deleted'] for c in all_commits)
        net_lines = total_added - total_deleted

        large_commits = 0
        tiny_commits = 0
        large_threshold = self.thresholds.get('large_commit', 500)
        tiny_threshold = self.thresholds.get('tiny_commit', 10)

        for c in all_commits:
            total_change = c['lines_added'] + c['lines_deleted']
            if total_change > large_threshold:
                large_commits += 1
            elif total_change < tiny_threshold:
                tiny_commits += 1

        lines = [
            "### 📈 代码变更量",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 新增行数 | +{format_number(total_added)} 行 |",
            f"| 删除行数 | -{format_number(total_deleted)} 行 |",
            f"| **净增行数** | **{'+' if net_lines >= 0 else ''}{format_number(net_lines)}** 行 |",
            "",
            "### 📝 提交质量",
            "",
            "| 指标 | 数值 | 状态 |",
            "|------|------|------|",
            f"| 大提交 (>{large_threshold}行) | {large_commits} 次 | "
            f"{'🔴 警告' if large_commits > 3 else '🟢 正常'} |",
            f"| 微小提交 (<{tiny_threshold}行) | {tiny_commits} 次 | "
            f"{'🟡 关注' if tiny_commits > 5 else '🟢 正常'} |",
            ""
        ]

        # 按仓库统计
        repo_stats = defaultdict(lambda: {'commits': 0, 'added': 0, 'deleted': 0})
        for c in all_commits:
            repo_stats[c['repo']]['commits'] += 1
            repo_stats[c['repo']]['added'] += c['lines_added']
            repo_stats[c['repo']]['deleted'] += c['lines_deleted']

        if repo_stats:
            lines.extend([
                "### 📦 各仓库变更",
                "",
                "| 仓库 | 提交 | 新增 | 删除 | 净增 |",
                "|------|------|------|------|------|"
            ])

            sorted_repos = sorted(
                repo_stats.items(),
                key=lambda x: x[1]['added'] - x[1]['deleted'],
                reverse=True
            )
            for repo, stats in sorted_repos:
                net = stats['added'] - stats['deleted']
                lines.append(
                    f"| {repo} | {stats['commits']} | "
                    f"+{format_number(stats['added'])} | "
                    f"-{format_number(stats['deleted'])} | "
                    f"**{'+' if net >= 0 else ''}{format_number(net)}** |"
                )
            lines.append("")

        return '\n'.join(lines)

    def _generate_risk_alerts(self, all_commits: list) -> str:
        """生成风险预警"""
        lines = []
        config_dict = self.config.to_dict()

        # 1. 工作时间异常
        lines.append("### ⏰ 工作时间分析")
        lines.append("")

        late_night = [c for c in all_commits if is_late_night(c['date'], config_dict)]
        weekend = [c for c in all_commits if is_weekend(c['date'])]
        overtime = [c for c in all_commits if is_overtime(c['date'], config_dict)]

        if late_night or weekend or overtime:
            lines.append("| 类型 | 数量 | 说明 |")
            lines.append("|------|------|------|")

            if overtime:
                lines.append(f"| ⏰ 加班提交 | {len(overtime)} 次 | 18:00-21:00 |")
            if late_night:
                lines.append(f"| 🌙 深夜提交 | {len(late_night)} 次 | 22:00-06:00 |")
            if weekend:
                lines.append(f"| 📅 周末提交 | {len(weekend)} 次 | 周六/周日 |")

            lines.append("")

            # 涉及人员
            abnormal_authors = set()
            for c in late_night + weekend:
                abnormal_authors.add(c['author'])

            if abnormal_authors:
                lines.append(f"**涉及人员**: {', '.join(abnormal_authors)}")
                lines.append("")
                lines.append("**建议**: 关注团队工作压力，保持工作生活平衡")
        else:
            lines.append("✅ 工作时间正常，无加班/深夜/周末提交")

        lines.append("")

        # 2. 大提交预警
        lines.append("### 📦 大提交预警")
        lines.append("")

        large_threshold = self.thresholds.get('large_commit', 500)
        large_commits = [
            c for c in all_commits
            if c['lines_added'] + c['lines_deleted'] > large_threshold
        ]

        if large_commits:
            lines.append(f"发现 {len(large_commits)} 次大提交 (>{large_threshold}行):")
            lines.append("")
            lines.append("| 仓库 | 作者 | 变更行数 | 提交信息 |")
            lines.append("|------|------|---------|---------|")

            for c in large_commits[:5]:
                total = c['lines_added'] + c['lines_deleted']
                msg = c['message'][:40] + '...' if len(c['message']) > 40 else c['message']
                lines.append(f"| {c['repo']} | {c['author']} | {format_number(total)} | {msg} |")

            lines.append("")
            lines.append("**建议**: 将大型变更拆分为多个小提交，便于代码审查")
        else:
            lines.append("✅ 无大提交")

        lines.append("")

        return '\n'.join(lines)

    def _generate_health_score(self, all_commits: list) -> str:
        """生成健康评分"""
        config_dict = self.config.to_dict()

        # 收集指标
        large_threshold = self.thresholds.get('large_commit', 500)
        large_commits = sum(
            1 for c in all_commits
            if c['lines_added'] + c['lines_deleted'] > large_threshold
        )

        late_night = sum(1 for c in all_commits if is_late_night(c['date'], config_dict))
        weekend = sum(1 for c in all_commits if is_weekend(c['date']))
        message_quality = calculate_message_quality(all_commits)

        # 简化评分
        score = 100.0
        deductions = []

        if large_commits > 0:
            d = large_commits * 5
            score -= d
            deductions.append(f"大提交 ({large_commits}次): -{d}分")

        if message_quality < 60:
            score -= 10
            deductions.append(f"提交信息质量差 ({message_quality:.0f}%): -10分")

        abnormal = late_night + weekend
        if abnormal > 0:
            d = abnormal * 2
            score -= d
            deductions.append(f"异常工作时间 ({abnormal}次): -{d}分")

        score = max(0, score)

        # 评级
        if score >= 80:
            emoji, level = "🟢", "优秀"
        elif score >= 60:
            emoji, level = "🟡", "良好"
        elif score >= 40:
            emoji, level = "🟠", "警告"
        else:
            emoji, level = "🔴", "危险"

        lines = [
            f"### {emoji} 综合评分: {score:.1f} 分 ({level})",
            "",
            "**评分说明**:",
            "- 🟢 优秀 (≥80分): 代码质量高，工作时间健康",
            "- 🟡 良好 (60-79分): 有改进空间",
            "- 🟠 警告 (40-59分): 存在问题，需改进",
            "- 🔴 危险 (<40分): 严重问题，需立即处理",
            ""
        ]

        if deductions:
            lines.append("**扣分项**:")
            for d in deductions:
                lines.append(f"- {d}")
            lines.append("")

        return '\n'.join(lines)

    def _generate_commit_details(self, all_commits: list) -> str:
        """生成提交详情"""
        if not all_commits:
            return "今日无提交记录"

        # 按作者分组
        author_commits = defaultdict(list)
        for c in all_commits:
            author_commits[c['author']].append(c)

        lines = []

        for author, commits in sorted(author_commits.items()):
            total_added = sum(c['lines_added'] for c in commits)
            total_deleted = sum(c['lines_deleted'] for c in commits)
            net = total_added - total_deleted

            # 统计主要语言
            lang_counts = defaultdict(int)
            for c in commits:
                for f in c.get('files', []):
                    lang = get_language_from_file(f.get('path', ''))
                    if lang:
                        lang_counts[lang] += 1

            # 取前2个主要语言
            top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:2]
            lang_str = ', '.join(lang for lang, _ in top_langs) if top_langs else ''

            lines.append(f"### 👤 {author}")
            stats_line = (
                f"提交: {len(commits)} 次 | "
                f"新增: +{format_number(total_added)} | "
                f"删除: -{format_number(total_deleted)} | "
                f"净增: {'+' if net >= 0 else ''}{format_number(net)}"
            )
            if lang_str:
                stats_line += f" | 技术栈: {lang_str}"
            lines.append(stats_line)
            lines.append("")

            for c in commits:
                try:
                    time_obj = parse_iso_datetime(c['date'])
                    time_str = time_obj.strftime("%H:%M")
                except Exception:
                    time_str = "??:??"

                c_net = c['lines_added'] - c['lines_deleted']
                msg = c['message'][:50] + '...' if len(c['message']) > 50 else c['message']

                lines.append(
                    f"- [{c['repo']}] {time_str} | "
                    f"+{c['lines_added']}/-{c['lines_deleted']} ({'+' if c_net >= 0 else ''}{c_net}) | "
                    f"{msg}"
                )

            lines.append("")

        return '\n'.join(lines)
