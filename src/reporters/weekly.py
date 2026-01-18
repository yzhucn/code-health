"""
周报生成器
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
    calculate_message_quality,
    parse_iso_datetime,
)


class WeeklyReporter(BaseReporter):
    """
    周报生成器

    生成每周代码健康报告，包含：
    - 生产力统计
    - 高危文件分析
    - 团队健康度
    - 代码质量趋势
    - 改进建议
    """

    def __init__(
        self,
        provider: GitProvider,
        config: Config,
        week_str: Optional[str] = None
    ):
        """
        初始化周报生成器

        Args:
            provider: Git 数据提供者
            config: 配置对象
            week_str: 周标识 (YYYY-Wxx 或 YYYY-MM-DD)，默认为上周
        """
        super().__init__(provider, config)

        # 解析周期
        if week_str:
            if '-W' in week_str:
                # ISO 周格式: 2026-W02
                # 使用 Python 的 ISO 周格式解析，%G=ISO年，%V=ISO周，%u=周几(1=周一)
                year, week = week_str.split('-W')
                self.year = int(year)
                week_num = int(week)
                # 获取该 ISO 周的周一
                week_start = datetime.strptime(f'{year}-W{week_num:02d}-1', '%G-W%V-%u')
            else:
                # 日期格式: 2025-12-30
                date_obj = datetime.strptime(week_str, "%Y-%m-%d")
                days_since_monday = date_obj.weekday()
                week_start = date_obj - timedelta(days=days_since_monday)
                self.year = week_start.year
        else:
            # 使用上周
            now = datetime.now()
            days_since_monday = now.weekday()
            this_monday = now - timedelta(days=days_since_monday)
            week_start = this_monday - timedelta(weeks=1)
            self.year = week_start.year

        # 计算周的起始和结束
        self.week_start = week_start.date() if isinstance(week_start, datetime) else week_start
        self.week_end = self.week_start + timedelta(days=6)

        self.since_time = self.week_start.isoformat()
        self.until_time = (self.week_end + timedelta(days=1)).isoformat()

        # 计算周数
        jan1 = datetime(self.week_start.year, 1, 1)
        days_to_first_monday = (7 - jan1.weekday()) % 7
        if days_to_first_monday == 0 and jan1.weekday() != 0:
            days_to_first_monday = 7
        first_monday = jan1 + timedelta(days=days_to_first_monday if jan1.weekday() != 0 else 0)
        week_start_dt = datetime.combine(self.week_start, datetime.min.time())
        week_number = ((week_start_dt - first_monday).days // 7) + 1

        self.week_str = f"{self.week_start.year}-W{week_number:02d}"
        self.date_range_str = f"{self.week_start.strftime('%m月%d日')} - {self.week_end.strftime('%m月%d日')}"

    def generate(self) -> str:
        """生成周报"""
        report = []

        # 标题
        report.append(self._format_header(
            "代码健康周报",
            f"{self.week_str} ({self.date_range_str})"
        ))

        # 获取所有提交
        all_commits = self.get_all_commits(self.since_time, self.until_time)

        # 一、生产力统计
        report.append("## 一、生产力统计 📊")
        report.append(self._generate_productivity(all_commits))

        # 二、代码质量
        report.append("## 二、代码质量分析 💎")
        report.append(self._generate_quality(all_commits))

        # 三、团队健康度
        report.append("## 三、团队健康度 👥")
        report.append(self._generate_team_health(all_commits))

        # 四、健康评分
        report.append("## 四、本周健康评分 ❤️")
        report.append(self._generate_health_score_section(all_commits))

        # 五、改进建议
        report.append("## 五、改进建议 💡")
        report.append(self._generate_recommendations(all_commits))

        # 底部
        report.append(self._format_footer())

        return '\n\n'.join(report)

    def _generate_productivity(self, all_commits: list) -> str:
        """生成生产力统计"""
        lines = []

        # 按作者统计
        author_stats = defaultdict(lambda: {
            'commits': 0,
            'added': 0,
            'deleted': 0,
            'files': 0,
            'repos': set()
        })

        for c in all_commits:
            author = c['author']
            author_stats[author]['commits'] += 1
            author_stats[author]['added'] += c['lines_added']
            author_stats[author]['deleted'] += c['lines_deleted']
            author_stats[author]['files'] += len(c['files'])
            author_stats[author]['repos'].add(c['repo'])

        # 1. 提交量排行榜
        # 综合评分: 提交次数(30%) + 新增行数(50%) + 涉及仓库数(20%)
        # 归一化后加权计算
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

        sorted_authors = sorted(
            author_stats.items(),
            key=lambda x: calc_score(x[1]),
            reverse=True
        )

        for rank, (author, stats) in enumerate(sorted_authors, 1):
            net = stats['added'] - stats['deleted']
            score = calc_score(stats)
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else str(rank)
            # 显示具体仓库名（最多3个）
            repos_list = list(stats['repos'])[:3]
            repos_str = ', '.join(repos_list)
            if len(stats['repos']) > 3:
                repos_str += f" 等{len(stats['repos'])}个"
            lines.append(
                f"| {medal} | {author} | {stats['commits']} | "
                f"+{format_number(stats['added'])} | "
                f"-{format_number(stats['deleted'])} | "
                f"**{'+' if net >= 0 else ''}{format_number(net)}** | "
                f"{repos_str} | {score:.1f} |"
            )

        lines.append("")

        # 2. 团队总产出
        total_commits = len(all_commits)
        total_added = sum(c['lines_added'] for c in all_commits)
        total_deleted = sum(c['lines_deleted'] for c in all_commits)
        total_net = total_added - total_deleted

        lines.append("### 📈 团队总产出")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 总提交数 | {total_commits} 次 |")
        lines.append(f"| 总新增行数 | +{format_number(total_added)} 行 |")
        lines.append(f"| 总删除行数 | -{format_number(total_deleted)} 行 |")
        lines.append(f"| **总净增行数** | **{'+' if total_net >= 0 else ''}{format_number(total_net)}** 行 |")
        lines.append(f"| 活跃开发者 | {len(author_stats)} 人 |")
        lines.append("")

        # 3. 仓库分布
        repo_stats = defaultdict(lambda: {'added': 0, 'deleted': 0, 'commits': 0})
        for c in all_commits:
            repo_stats[c['repo']]['added'] += c['lines_added']
            repo_stats[c['repo']]['deleted'] += c['lines_deleted']
            repo_stats[c['repo']]['commits'] += 1

        if repo_stats:
            lines.append("### 📦 仓库分布")
            lines.append("")
            lines.append("| 仓库 | 提交 | 新增 | 删除 | 净增 |")
            lines.append("|------|------|------|------|------|")

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

    def _generate_quality(self, all_commits: list) -> str:
        """生成代码质量分析"""
        lines = []

        # 1. 提交质量
        large_threshold = self.thresholds.get('large_commit', 500)
        tiny_threshold = self.thresholds.get('tiny_commit', 10)

        large_commits = sum(1 for c in all_commits if c['lines_added'] + c['lines_deleted'] > large_threshold)
        tiny_commits = sum(1 for c in all_commits if c['lines_added'] + c['lines_deleted'] < tiny_threshold)
        message_quality = calculate_message_quality(all_commits)

        lines.append("### 📝 提交质量")
        lines.append("")
        lines.append("| 指标 | 数值 | 状态 |")
        lines.append("|------|------|------|")
        lines.append(f"| 大提交 (>{large_threshold}行) | {large_commits} 次 | "
                    f"{'🔴 需改进' if large_commits > 5 else '🟢 正常'} |")
        lines.append(f"| 微小提交 (<{tiny_threshold}行) | {tiny_commits} 次 | "
                    f"{'🟡 关注' if tiny_commits > 10 else '🟢 正常'} |")
        lines.append(f"| 提交信息质量 | {message_quality:.0f}% | "
                    f"{'🔴 差' if message_quality < 60 else '🟡 中' if message_quality < 80 else '🟢 好'} |")
        lines.append("")

        # 2. 文件修改热点
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
                short_path = filepath if len(filepath) < 60 else '...' + filepath[-57:]
                lines.append(f"| `{short_path}` | {count} |")
            lines.append("")

        return '\n'.join(lines)

    def _generate_team_health(self, all_commits: list) -> str:
        """生成团队健康度分析"""
        lines = []
        config_dict = self.config.to_dict()

        # 1. 工作时间分布
        lines.append("### ⏰ 工作时间分布")
        lines.append("")

        time_slots = defaultdict(int)
        late_night_count = 0
        weekend_count = 0

        for c in all_commits:
            try:
                dt = parse_iso_datetime(c['date'])
                hour = dt.hour

                if 0 <= hour < 6:
                    time_slots['00-06'] += 1
                    late_night_count += 1
                elif 6 <= hour < 9:
                    time_slots['06-09'] += 1
                elif 9 <= hour < 12:
                    time_slots['09-12'] += 1
                elif 12 <= hour < 14:
                    time_slots['12-14'] += 1
                elif 14 <= hour < 18:
                    time_slots['14-18'] += 1
                elif 18 <= hour < 22:
                    time_slots['18-22'] += 1
                else:
                    time_slots['22-24'] += 1
                    late_night_count += 1

                if is_weekend(c['date']):
                    weekend_count += 1
            except Exception:
                pass

        total = len(all_commits)

        if total > 0:
            lines.append("**时段分布**:")
            lines.append("```")
            slot_names = {
                '00-06': '深夜', '06-09': '早晨', '09-12': '上午',
                '12-14': '午休', '14-18': '下午', '18-22': '晚上', '22-24': '深夜'
            }
            for slot in ['06-09', '09-12', '12-14', '14-18', '18-22', '22-24', '00-06']:
                count = time_slots.get(slot, 0)
                pct = count / total * 100
                bar_len = int(pct / 3)
                bar = '█' * bar_len + '░' * (33 - bar_len)
                lines.append(f"{slot} ({slot_names[slot]}): {bar} {pct:5.1f}% ({count})")
            lines.append("```")
            lines.append("")

            # 健康评估
            late_pct = late_night_count / total * 100
            weekend_pct = weekend_count / total * 100

            if late_pct > 20 or weekend_pct > 20:
                health_status = "🔴 需要关注"
            elif late_pct > 10 or weekend_pct > 10:
                health_status = "🟡 中等"
            else:
                health_status = "🟢 健康"

            lines.append(f"**工作时间健康度**: {health_status}")
            lines.append(f"- 深夜提交: {late_night_count} 次 ({late_pct:.1f}%)")
            lines.append(f"- 周末提交: {weekend_count} 次 ({weekend_pct:.1f}%)")
            lines.append("")

        return '\n'.join(lines)

    def _generate_health_score_section(self, all_commits: list) -> str:
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

        # 计算评分
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
            d = min(abnormal * 2, 20)
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
            ""
        ]

        if deductions:
            lines.append("**扣分项**:")
            for d in deductions:
                lines.append(f"- {d}")
            lines.append("")

        return '\n'.join(lines)

    def _generate_recommendations(self, all_commits: list) -> str:
        """生成改进建议"""
        lines = []
        config_dict = self.config.to_dict()

        # 收集数据
        large_threshold = self.thresholds.get('large_commit', 500)
        large_commits = sum(1 for c in all_commits if c['lines_added'] + c['lines_deleted'] > large_threshold)
        message_quality = calculate_message_quality(all_commits)
        late_night = sum(1 for c in all_commits if is_late_night(c['date'], config_dict))
        weekend = sum(1 for c in all_commits if is_weekend(c['date']))

        lines.append("### 🎯 本周行动项")
        lines.append("")

        actions = []

        if large_commits > 5:
            actions.append({
                'priority': '🔴 高',
                'task': '控制提交粒度',
                'detail': f'本周有 {large_commits} 次大提交，建议拆分为小提交'
            })

        if message_quality < 60:
            actions.append({
                'priority': '🔴 高',
                'task': '规范提交信息',
                'detail': '使用规范格式: feat/fix/refactor(scope): description'
            })

        if late_night + weekend > 10:
            actions.append({
                'priority': '🟠 中',
                'task': '关注工作时间',
                'detail': f'深夜/周末提交 {late_night + weekend} 次，建议调整工作节奏'
            })

        if not actions:
            actions.append({
                'priority': '🟢 良好',
                'task': '保持当前质量',
                'detail': '本周代码质量良好，继续保持'
            })

        for i, action in enumerate(actions[:3], 1):
            lines.append(f"**{i}. {action['task']}** ({action['priority']})")
            lines.append(f"   {action['detail']}")
            lines.append("")

        # 本周亮点
        lines.append("### ✨ 本周亮点")
        lines.append("")

        # 最活跃贡献者
        author_commits = defaultdict(int)
        for c in all_commits:
            author_commits[c['author']] += 1

        if author_commits:
            top = max(author_commits.items(), key=lambda x: x[1])
            lines.append(f"- 🏆 **TOP 贡献者**: {top[0]} ({top[1]} 次提交)")

        if message_quality >= 80:
            lines.append(f"- ✅ **提交信息质量优秀**: {message_quality:.0f}%")

        if late_night + weekend < 5:
            lines.append("- 🌟 **工作时间健康**: 深夜/周末提交少")

        lines.append("")

        return '\n'.join(lines)
