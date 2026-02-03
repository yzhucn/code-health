"""
月报生成器
"""

from datetime import datetime, timedelta
from collections import defaultdict
from calendar import monthrange
from typing import Optional

from .base import BaseReporter
from ..providers.base import GitProvider
from ..config import Config
from ..utils.helpers import (
    format_number,
    is_late_night,
    is_weekend,
    calculate_message_quality,
    parse_iso_datetime,
)


class MonthlyReporter(BaseReporter):
    """
    月报生成器

    生成每月代码健康报告，包含：
    - 月度总览
    - 团队表现
    - 趋势分析
    - 健康指标
    - 风险分析
    - 代码质量
    - 下月建议
    """

    def __init__(
        self,
        provider: GitProvider,
        config: Config,
        month_str: Optional[str] = None
    ):
        """
        初始化月报生成器

        Args:
            provider: Git 数据提供者
            config: 配置对象
            month_str: 月份标识 (YYYY-MM)，默认为上个月
        """
        super().__init__(provider, config)

        # 解析月份
        if month_str:
            year, month = month_str.split('-')
            self.year = int(year)
            self.month = int(month)
        else:
            # 使用上个月
            now = datetime.now()
            if now.month == 1:
                self.year = now.year - 1
                self.month = 12
            else:
                self.year = now.year
                self.month = now.month - 1

        self.month_str = f"{self.year}-{self.month:02d}"

        # 计算月份的起始和结束
        _, last_day = monthrange(self.year, self.month)
        self.month_start = datetime(self.year, self.month, 1)
        self.month_end = datetime(self.year, self.month, last_day, 23, 59, 59)

        self.since_time = self.month_start.strftime("%Y-%m-%d")
        self.until_time = (self.month_end + timedelta(days=1)).strftime("%Y-%m-%d")

        # 计算工作日数量
        self.work_days = self._count_work_days()

    def _count_work_days(self) -> int:
        """计算当月工作日数量"""
        work_days = 0
        current = self.month_start
        while current <= self.month_end:
            if current.weekday() < 5:
                work_days += 1
            current += timedelta(days=1)
        return work_days

    def generate(self) -> str:
        """生成月报"""
        report = []

        month_names = {
            1: '一月', 2: '二月', 3: '三月', 4: '四月',
            5: '五月', 6: '六月', 7: '七月', 8: '八月',
            9: '九月', 10: '十月', 11: '十一月', 12: '十二月'
        }

        # 标题
        header = self._format_header(
            f"{self.year}年{month_names[self.month]} 代码健康月报",
            f"{self.month_start.strftime('%Y-%m-%d')} ~ {self.month_end.strftime('%Y-%m-%d')} (工作日: {self.work_days}天)"
        )
        report.append(header)

        # 获取所有提交
        all_commits = self.get_all_commits(self.since_time, self.until_time)

        # 一、月度总览
        report.append("## 一、月度总览 📊")
        report.append(self._generate_overview(all_commits))

        # 二、团队表现
        report.append("## 二、团队表现 👥")
        report.append(self._generate_team_performance(all_commits))

        # 三、趋势分析
        report.append("## 三、趋势分析 📈")
        report.append(self._generate_trends(all_commits))

        # 四、健康指标
        report.append("## 四、健康指标 ❤️")
        report.append(self._generate_health_metrics(all_commits))

        # 五、代码质量
        report.append("## 五、代码质量 💎")
        report.append(self._generate_quality_metrics(all_commits))

        # 六、下月建议
        report.append("## 六、下月计划建议 💡")
        report.append(self._generate_recommendations(all_commits))

        # 底部
        report.append(self._format_footer())

        return '\n\n'.join(report)

    def _generate_overview(self, all_commits: list) -> str:
        """生成月度总览"""
        lines = []

        total_commits = len(all_commits)
        total_added = sum(c['lines_added'] for c in all_commits)
        total_deleted = sum(c['lines_deleted'] for c in all_commits)
        total_net = total_added - total_deleted

        active_authors = set(c['author'] for c in all_commits)
        active_repos = set(c['repo'] for c in all_commits)

        # 按日统计
        daily_commits = defaultdict(int)
        for c in all_commits:
            date = c['date'][:10]
            daily_commits[date] += 1

        most_active_day = max(daily_commits.items(), key=lambda x: x[1]) if daily_commits else ("N/A", 0)

        lines.append("### 📌 核心指标")
        lines.append("")
        lines.append("| 指标 | 数值 | 说明 |")
        lines.append("|------|------|------|")
        lines.append(f"| 总提交次数 | **{format_number(total_commits)}** | 本月全部代码提交 |")
        lines.append(f"| 代码新增 | **{format_number(total_added)}** 行 | 新增代码行数 |")
        lines.append(f"| 代码删除 | **{format_number(total_deleted)}** 行 | 删除代码行数 |")
        lines.append(f"| 代码净增 | **{'+' if total_net >= 0 else ''}{format_number(total_net)}** 行 | 新增减去删除 |")
        lines.append(f"| 活跃开发者 | **{len(active_authors)}** 人 | 有代码提交的开发者 |")
        lines.append(f"| 活跃仓库 | **{len(active_repos)}** 个 | 有代码变更的仓库 |")
        lines.append(f"| 日均提交量 | **{total_commits / max(1, self.work_days):.1f}** 次 | 工作日平均 |")
        lines.append(f"| 最活跃日 | {most_active_day[0]} | {most_active_day[1]} 次提交 |")

        return '\n'.join(lines)

    def _generate_team_performance(self, all_commits: list) -> str:
        """生成团队表现"""
        lines = []

        # 按作者统计
        author_stats = defaultdict(lambda: {
            'commits': 0, 'added': 0, 'deleted': 0, 'files': 0, 'repos': set()
        })

        for c in all_commits:
            author = c['author']
            author_stats[author]['commits'] += 1
            author_stats[author]['added'] += c['lines_added']
            author_stats[author]['deleted'] += c['lines_deleted']
            author_stats[author]['files'] += len(c['files'])
            author_stats[author]['repos'].add(c['repo'])

        # 贡献排行榜
        # 综合评分: 提交次数(30%) + 新增行数(50%) + 涉及仓库数(20%)
        lines.append("### 🏆 贡献排行榜")
        lines.append("")
        lines.append("| 排名 | 开发者 | 提交 | 新增 | 删除 | 净增 | 涉及仓库 | 综合分 |")
        lines.append("|------|--------|------|------|------|------|----------|--------|")

        # 计算综合评分
        max_commits = max((s['commits'] for s in author_stats.values()), default=1)
        max_added = max((s['added'] for s in author_stats.values()), default=1)
        max_repos = max((len(s['repos']) for s in author_stats.values()), default=1)

        def calc_score(stats):
            commit_score = (stats['commits'] / max_commits) * 30
            added_score = (stats['added'] / max_added) * 50
            repo_score = (len(stats['repos']) / max_repos) * 20
            return commit_score + added_score + repo_score

        sorted_authors = sorted(author_stats.items(), key=lambda x: calc_score(x[1]), reverse=True)
        for rank, (author, stats) in enumerate(sorted_authors[:10], 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else str(rank)
            net = stats['added'] - stats['deleted']
            score = calc_score(stats)
            lines.append(
                f"| {medal} | {author} | {stats['commits']} | "
                f"{format_number(stats['added'])} | {format_number(stats['deleted'])} | "
                f"{'+' if net >= 0 else ''}{format_number(net)} | {len(stats['repos'])} | {score:.1f} |"
            )

        # 仓库贡献统计
        lines.append("")
        lines.append("### 📦 仓库贡献统计")
        lines.append("")

        repo_authors = defaultdict(set)
        repo_commits = defaultdict(int)
        for c in all_commits:
            repo_authors[c['repo']].add(c['author'])
            repo_commits[c['repo']] += 1

        lines.append("| 仓库 | 贡献人数 | 提交次数 |")
        lines.append("|------|---------|---------|")

        for repo in sorted(repo_authors.keys()):
            lines.append(f"| {repo} | {len(repo_authors[repo])} | {repo_commits[repo]} |")

        return '\n'.join(lines)

    def _generate_trends(self, all_commits: list) -> str:
        """生成趋势分析"""
        lines = []

        # 按周统计
        weekly_stats = defaultdict(lambda: {
            'commits': 0, 'added': 0, 'deleted': 0, 'authors': set()
        })

        for c in all_commits:
            try:
                commit_date = datetime.strptime(c['date'][:10], '%Y-%m-%d')
                # 计算周的起始和结束日期
                days_since_monday = commit_date.weekday()
                week_start = commit_date - timedelta(days=days_since_monday)
                week_end = week_start + timedelta(days=6)
                # 格式: "12/30-01/05"
                week_key = f"{week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')}"

                weekly_stats[week_key]['commits'] += 1
                weekly_stats[week_key]['added'] += c['lines_added']
                weekly_stats[week_key]['deleted'] += c['lines_deleted']
                weekly_stats[week_key]['authors'].add(c['author'])
                weekly_stats[week_key]['start'] = week_start  # 用于排序
            except Exception:
                pass

        lines.append("### 📊 每周趋势")
        lines.append("")
        lines.append("| 周期 | 提交 | 新增 | 删除 | 净增 | 活跃人数 |")
        lines.append("|------|------|------|------|------|---------|")

        # 按周起始日期排序
        sorted_weeks = sorted(weekly_stats.items(), key=lambda x: x[1].get('start', datetime.min))
        for week_key, stats in sorted_weeks:
            net = stats['added'] - stats['deleted']
            lines.append(
                f"| {week_key} | {stats['commits']} | "
                f"{format_number(stats['added'])} | {format_number(stats['deleted'])} | "
                f"{'+' if net >= 0 else ''}{format_number(net)} | {len(stats['authors'])} |"
            )

        return '\n'.join(lines)

    def _generate_health_metrics(self, all_commits: list) -> str:
        """生成健康指标"""
        lines = []
        config_dict = self.config.to_dict()

        if not all_commits:
            lines.append("本月无提交数据")
            return '\n'.join(lines)

        # 工作时间分布
        normal_hours = 0
        overtime_hours = 0
        late_night_hours = 0
        weekend_hours = 0

        for c in all_commits:
            try:
                commit_dt = parse_iso_datetime(c['date'])
                if is_weekend(c['date']):
                    weekend_hours += 1
                elif is_late_night(c['date'], config_dict):
                    late_night_hours += 1
                elif commit_dt.hour >= 18:
                    overtime_hours += 1
                else:
                    normal_hours += 1
            except Exception:
                pass

        total = len(all_commits)

        # 计算健康分
        risk_ratio = (late_night_hours + weekend_hours) / total if total > 0 else 0
        health_score = max(60, 100 - risk_ratio * 50)

        if health_score >= 80:
            rating = "🟢 优秀"
        elif health_score >= 60:
            rating = "🟡 良好"
        else:
            rating = "🔴 需改进"

        lines.append("### 💯 月度健康评分")
        lines.append("")
        lines.append(f"**综合健康分**: {health_score:.1f} / 100 ({rating})")
        lines.append("")

        lines.append("### ⏰ 工作时间分布")
        lines.append("")
        lines.append("| 时段 | 提交次数 | 占比 |")
        lines.append("|------|---------|------|")
        lines.append(f"| 正常工作时间 (9-18点) | {normal_hours} | {normal_hours/total*100:.1f}% |")
        lines.append(f"| 加班时间 (18-22点) | {overtime_hours} | {overtime_hours/total*100:.1f}% |")
        lines.append(f"| 深夜时间 (22-6点) | {late_night_hours} | {late_night_hours/total*100:.1f}% |")
        lines.append(f"| 周末时间 | {weekend_hours} | {weekend_hours/total*100:.1f}% |")

        return '\n'.join(lines)

    def _generate_quality_metrics(self, all_commits: list) -> str:
        """生成代码质量指标"""
        lines = []

        if not all_commits:
            lines.append("本月无提交数据")
            return '\n'.join(lines)

        # 提交粒度分析
        commit_sizes = [c['lines_added'] + c['lines_deleted'] for c in all_commits]
        avg_size = sum(commit_sizes) / len(commit_sizes)

        small_commits = len([s for s in commit_sizes if s < 50])
        medium_commits = len([s for s in commit_sizes if 50 <= s < 200])
        large_commits = len([s for s in commit_sizes if s >= 200])

        lines.append("### 📏 提交粒度分析")
        lines.append("")
        lines.append("| 大小分类 | 数量 | 占比 | 建议 |")
        lines.append("|---------|------|------|------|")
        lines.append(f"| 小型 (<50行) | {small_commits} | {small_commits/len(commit_sizes)*100:.1f}% | 最佳实践 ✅ |")
        lines.append(f"| 中型 (50-200行) | {medium_commits} | {medium_commits/len(commit_sizes)*100:.1f}% | 合理范围 |")
        lines.append(f"| 大型 (>200行) | {large_commits} | {large_commits/len(commit_sizes)*100:.1f}% | 建议拆分 |")
        lines.append("")
        lines.append(f"**平均提交大小**: {avg_size:.1f} 行")
        lines.append("")

        # 文件修改热点
        file_changes = defaultdict(int)
        for c in all_commits:
            for f in c['files']:
                file_changes[f['path']] += 1

        if file_changes:
            lines.append("### 🔥 文件修改热点 (TOP 10)")
            lines.append("")
            lines.append("| 文件 | 修改次数 |")
            lines.append("|------|---------|")

            sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)
            for filepath, count in sorted_files[:10]:
                short_path = filepath if len(filepath) < 50 else '...' + filepath[-47:]
                lines.append(f"| `{short_path}` | {count} |")

        return '\n'.join(lines)

    def _generate_recommendations(self, all_commits: list) -> str:
        """生成下月计划建议"""
        lines = []
        config_dict = self.config.to_dict()

        if not all_commits:
            lines.append("基于本月数据不足，无法生成建议")
            return '\n'.join(lines)

        total = len(all_commits)
        late_night = len([c for c in all_commits if is_late_night(c['date'], config_dict)])
        weekend = len([c for c in all_commits if is_weekend(c['date'])])
        large = len([c for c in all_commits if c['lines_added'] + c['lines_deleted'] > 500])

        lines.append("基于本月数据分析，建议下月重点关注：")
        lines.append("")
        lines.append("### 🎯 行动计划")
        lines.append("")

        if late_night / total > 0.1:
            lines.append("1. **优化工作时间**: 深夜提交占比较高，建议合理安排开发任务")
        else:
            lines.append("1. **保持良好节奏**: 继续保持健康的工作时间分布")

        if weekend / total > 0.15:
            lines.append("2. **工作生活平衡**: 减少周末加班，提升团队可持续性")
        else:
            lines.append("2. **持续改进**: 保持良好的工作生活平衡")

        if large / total > 0.2:
            lines.append("3. **提交粒度优化**: 推广小步提交，提高代码审查质量")
        else:
            lines.append("3. **代码质量**: 继续保持良好的提交习惯")

        lines.append("")
        lines.append("### 📈 持续改进")
        lines.append("")
        lines.append("- 定期回顾代码健康报告")
        lines.append("- 关注高频修改文件，考虑重构")
        lines.append("- 加强代码审查，提升整体质量")
        lines.append("- 优化团队协作流程")

        return '\n'.join(lines)
