#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - 周报生成器
Author: DevOps Team
Created: 2025-12-30

Usage:
    python weekly-report.py [week]

Examples:
    python weekly-report.py                 # 生成本周的周报
    python weekly-report.py 2025-W52        # 生成指定周的周报
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils import (
    GitAnalyzer, ChurnAnalyzer, ReworkAnalyzer, HotspotAnalyzer,
    HealthScoreCalculator, load_config, format_number,
    is_late_night, is_weekend, calculate_message_quality,
    parse_iso_datetime
)


class WeeklyReportGenerator:
    """周报生成器"""

    def __init__(self, config_path: str, week_str: str = None):
        self.config = load_config(config_path)

        # 解析周期
        if week_str:
            # 格式: 2025-W52
            year, week = week_str.split('-W')
            self.year = int(year)
            self.week = int(week)
        else:
            # 使用当前周
            now = datetime.now()
            self.year = now.year
            self.week = now.isocalendar()[1]

        self.week_str = f"{self.year}-W{self.week:02d}"

        # 计算周的起始和结束时间
        # ISO 8601: 周一是一周的第一天
        jan4 = datetime(self.year, 1, 4)  # 1月4日总是在第一周
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        week_start = week1_monday + timedelta(weeks=self.week - 1)
        week_end = week_start + timedelta(days=7)

        self.since_time = week_start.strftime("%Y-%m-%d 00:00:00")
        self.until_time = week_end.strftime("%Y-%m-%d 00:00:00")

        # 保存日期范围用于显示（周日是最后一天）
        self.week_start_date = week_start
        self.week_end_date = week_start + timedelta(days=6)  # 周一+6天=周日
        self.date_range_str = f"{self.week_start_date.strftime('%m月%d日')} - {self.week_end_date.strftime('%m月%d日')}"

        self.analyzers = self._init_analyzers()

    def _init_analyzers(self) -> list:
        """初始化所有仓库的分析器"""
        analyzers = []
        for repo in self.config['repositories']:
            if os.path.exists(repo['path']):
                git_analyzer = GitAnalyzer(repo['path'])
                analyzers.append({
                    'name': repo['name'],
                    'type': repo['type'],
                    'git': git_analyzer,
                    'churn': ChurnAnalyzer(
                        git_analyzer,
                        self.config['thresholds']['churn_days'],
                        self.config['thresholds']['churn_count']
                    ),
                    'rework': ReworkAnalyzer(
                        git_analyzer,
                        self.config['thresholds']['rework_add_days'],
                        self.config['thresholds']['rework_delete_days']
                    ),
                    'hotspot': HotspotAnalyzer(
                        git_analyzer,
                        self.config['thresholds']
                    )
                })
        return analyzers

    def generate(self) -> str:
        """生成周报"""
        report = []

        # 标题
        report.append(self._generate_header())

        # 一、生产力统计
        report.append("## 一、生产力统计 📊")
        report.append(self._generate_productivity())

        # 二、高危文件深度分析
        report.append("## 二、高危文件深度分析 🚨")
        report.append(self._generate_risk_files())

        # 三、团队健康度分析
        report.append("## 三、团队健康度分析 👥")
        report.append(self._generate_team_health())

        # 四、代码质量趋势
        report.append("## 四、代码质量趋势 📈")
        report.append(self._generate_quality_trends())

        # 五、改进建议
        report.append("## 五、改进建议 💡")
        report.append(self._generate_recommendations())

        # 底部
        report.append(self._generate_footer())

        return '\n\n'.join(report)

    def _generate_header(self) -> str:
        """生成报告头部"""
        lines = [
            f"# 代码健康周报",
            "",
            f"**报告周期**: {self.week_str} ({self.date_range_str})",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---"
        ]
        return '\n'.join(lines)

    def _generate_productivity(self) -> str:
        """生成生产力统计"""
        lines = []

        # 收集本周所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        # 按作者统计
        author_stats = defaultdict(lambda: {
            'commits': 0,
            'added': 0,
            'deleted': 0,
            'files': 0,
            'repos': set(),
            'languages': defaultdict(int)
        })

        for commit in all_commits:
            author = commit['author']
            author_stats[author]['commits'] += 1
            author_stats[author]['added'] += commit['lines_added']
            author_stats[author]['deleted'] += commit['lines_deleted']
            author_stats[author]['files'] += len(commit['files'])
            author_stats[author]['repos'].add(commit['repo'])

            # 统计语言（基于文件扩展名）
            for file_info in commit['files']:
                filepath = file_info['path']
                if filepath.endswith('.java'):
                    author_stats[author]['languages']['Java'] += file_info['added']
                elif filepath.endswith('.py'):
                    author_stats[author]['languages']['Python'] += file_info['added']
                elif filepath.endswith(('.vue', '.js', '.ts')):
                    author_stats[author]['languages']['Vue/JS'] += file_info['added']
                elif filepath.endswith('.dart'):
                    author_stats[author]['languages']['Dart'] += file_info['added']

        # 1. 提交量排行榜
        lines.append("### 1️⃣ 提交量排行榜")
        lines.append("")
        lines.append("| 排名 | 开发者 | 提交次数 | 新增行数 | 删除行数 | 净增行数 | 文件数 | 平均提交大小 | 涉及仓库 |")
        lines.append("|------|--------|---------|---------|---------|---------|--------|------------|----------|")

        # 按净增行数排序
        sorted_authors = sorted(
            author_stats.items(),
            key=lambda x: x[1]['added'] - x[1]['deleted'],
            reverse=True
        )

        for rank, (author, stats) in enumerate(sorted_authors, 1):
            net = stats['added'] - stats['deleted']
            avg_commit_size = (stats['added'] + stats['deleted']) // stats['commits'] if stats['commits'] > 0 else 0
            repos_count = len(stats['repos'])

            lines.append(
                f"| {rank} | {author} | {stats['commits']} | "
                f"+{format_number(stats['added'])} | "
                f"-{format_number(stats['deleted'])} | "
                f"**{'+' if net >= 0 else ''}{format_number(net)}** | "
                f"{stats['files']} | "
                f"{format_number(avg_commit_size)}行/次 | "
                f"{repos_count}个 |"
            )

        lines.append("")

        # 2. LOC 详细统计
        lines.append("### 2️⃣ LOC 统计（代码贡献详情）")
        lines.append("")

        for author, stats in sorted_authors:
            net = stats['added'] - stats['deleted']
            efficiency = (net / stats['added'] * 100) if stats['added'] > 0 else 0

            lines.append(f"#### 👤 {author}")
            lines.append("")
            lines.append(f"**代码贡献**:")
            lines.append(f"- 新增代码: {format_number(stats['added'])} 行")
            lines.append(f"- 删除代码: {format_number(stats['deleted'])} 行")
            lines.append(f"- 净贡献: **{'+' if net >= 0 else ''}{format_number(net)}** 行")
            lines.append(f"- 有效代码率: {efficiency:.1f}% (净增/新增)")
            lines.append("")

            # 语言分布
            if stats['languages']:
                total_lang_lines = sum(stats['languages'].values())
                lines.append("**主要语言**:")
                for lang, lines_count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (lines_count / total_lang_lines * 100) if total_lang_lines > 0 else 0
                    lines.append(f"- {lang}: {format_number(lines_count)} 行 ({percentage:.0f}%)")
                lines.append("")

            # 涉及仓库
            lines.append(f"**涉及仓库**: {', '.join(sorted(stats['repos']))}")
            lines.append("")

        # 3. 团队总产出
        total_commits = len(all_commits)
        total_added = sum(c['lines_added'] for c in all_commits)
        total_deleted = sum(c['lines_deleted'] for c in all_commits)
        total_net = total_added - total_deleted
        avg_efficiency = (total_net / total_added * 100) if total_added > 0 else 0

        lines.append("### 3️⃣ 团队总产出")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 总提交数 | {total_commits} 次 |")
        lines.append(f"| 总新增行数 | +{format_number(total_added)} 行 |")
        lines.append(f"| 总删除行数 | -{format_number(total_deleted)} 行 |")
        lines.append(f"| **总净增行数** | **+{format_number(total_net)}** 行 |")
        lines.append(f"| 平均有效率 | {avg_efficiency:.1f}% |")
        lines.append(f"| 活跃开发者 | {len(author_stats)} 人 |")
        lines.append("")

        # 4. 仓库 LOC 分布
        lines.append("### 4️⃣ 仓库 LOC 分布")
        lines.append("")

        repo_stats = defaultdict(lambda: {'added': 0, 'deleted': 0, 'commits': 0})
        for commit in all_commits:
            repo = commit['repo']
            repo_stats[repo]['added'] += commit['lines_added']
            repo_stats[repo]['deleted'] += commit['lines_deleted']
            repo_stats[repo]['commits'] += 1

        lines.append("| 仓库 | 提交 | 新增 | 删除 | 净增 | 占比 |")
        lines.append("|------|------|------|------|------|------|")

        sorted_repos = sorted(
            repo_stats.items(),
            key=lambda x: x[1]['added'] - x[1]['deleted'],
            reverse=True
        )

        for repo, stats in sorted_repos:
            net = stats['added'] - stats['deleted']
            percentage = (net / total_net * 100) if total_net > 0 else 0
            lines.append(
                f"| {repo} | {stats['commits']} | "
                f"+{format_number(stats['added'])} | "
                f"-{format_number(stats['deleted'])} | "
                f"**+{format_number(net)}** | "
                f"{percentage:.0f}% |"
            )

        lines.append("")

        return '\n'.join(lines)

    def _generate_risk_files(self) -> str:
        """生成高危文件分析"""
        lines = []

        # 收集所有高危文件
        all_hotspots = []
        for analyzer in self.analyzers:
            hotspots = analyzer['hotspot'].analyze()
            all_hotspots.extend([{**h, 'repo': analyzer['name']} for h in hotspots])

        all_hotspots.sort(key=lambda x: x['risk_score'], reverse=True)

        # 统计风险等级
        critical_count = len([h for h in all_hotspots if h['risk_score'] >= 80])
        high_count = len([h for h in all_hotspots if 60 <= h['risk_score'] < 80])
        medium_count = len([h for h in all_hotspots if 40 <= h['risk_score'] < 60])

        lines.append("### 1️⃣ 风险概览")
        lines.append("")
        lines.append(f"**发现高危文件**: {len(all_hotspots)} 个")
        lines.append("")
        lines.append("| 风险等级 | 数量 | 说明 |")
        lines.append("|---------|------|------|")
        lines.append(f"| 🔴 严重 (80-100) | {critical_count} | 需要立即重构 |")
        lines.append(f"| 🟠 高 (60-79) | {high_count} | 本周内处理 |")
        lines.append(f"| 🟡 中 (40-59) | {medium_count} | 计划改进 |")
        lines.append("")

        # TOP 20 高危文件
        lines.append("### 2️⃣ 高危文件 TOP 20")
        lines.append("")
        lines.append("| 排名 | 仓库 | 文件 | 风险分 | 修改次数 | 大小 | 开发者 | 风险标签 | 建议 |")
        lines.append("|------|------|------|--------|---------|------|--------|----------|------|")

        for rank, h in enumerate(all_hotspots[:20], 1):
            risk_emoji = "🔴" if h['risk_score'] >= 80 else "🟠" if h['risk_score'] >= 60 else "🟡"
            tags = ', '.join(h['tags']) if h['tags'] else "-"
            suggestion_icon = h['suggestion'].split()[0]  # 提取emoji

            lines.append(
                f"| {rank} | {h['repo']} | `{h['file']}` | "
                f"{risk_emoji} {h['risk_score']:.0f} | "
                f"{h['modify_count']} | {h['file_size']} 行 | "
                f"{h['author_count']}人 | {tags} | {suggestion_icon} |"
            )

        lines.append("")

        # 风险文件详细分析
        if critical_count > 0:
            lines.append("### 3️⃣ 严重风险文件详情")
            lines.append("")

            for h in all_hotspots[:5]:
                if h['risk_score'] < 80:
                    break

                lines.append(f"#### 🔴 {h['repo']}: `{h['file']}`")
                lines.append("")
                lines.append(f"**风险分数**: {h['risk_score']:.0f} / 100")
                lines.append(f"**最近7天修改**: {h['modify_count']} 次")
                lines.append(f"**文件大小**: {h['file_size']} 行")
                lines.append(f"**涉及开发者**: {', '.join(h['authors'])}")
                lines.append(f"**风险标签**: {', '.join(h['tags'])}")
                lines.append("")
                lines.append(f"**改进建议**: {h['suggestion']}")
                lines.append("")

        return '\n'.join(lines)

    def _generate_team_health(self) -> str:
        """生成团队健康度分析"""
        lines = []

        # 收集本周所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        # 1. 工作模式分析
        lines.append("### 1️⃣ 工作时间分布")
        lines.append("")

        # 统计每个时段的提交
        time_slots = defaultdict(int)
        weekday_commits = 0
        weekend_commits = 0
        late_night_commits = 0

        for commit in all_commits:
            try:
                dt = parse_iso_datetime(commit['date'])
                hour = dt.hour

                # 时段分类
                if 0 <= hour < 6:
                    time_slots['00-06'] += 1
                    late_night_commits += 1
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
                    late_night_commits += 1

                # 工作日 vs 周末
                if is_weekend(commit['date']):
                    weekend_commits += 1
                else:
                    weekday_commits += 1
            except:
                pass

        total_commits = len(all_commits)

        lines.append("**时段分布热力图** (本周):")
        lines.append("```")
        for slot in ['00-06', '06-09', '09-12', '12-14', '14-18', '18-22', '22-24']:
            count = time_slots.get(slot, 0)
            percentage = (count / total_commits * 100) if total_commits > 0 else 0
            bar_length = int(percentage / 3)
            bar = '█' * bar_length + '░' * (33 - bar_length)

            slot_name = {
                '00-06': '深夜',
                '06-09': '早晨',
                '09-12': '上午',
                '12-14': '午休',
                '14-18': '下午',
                '18-22': '晚上',
                '22-24': '深夜'
            }[slot]

            lines.append(f"{slot} ({slot_name}): {bar} {percentage:5.1f}% ({count}次)")
        lines.append("```")
        lines.append("")

        # 工作日 vs 周末
        weekday_pct = (weekday_commits / total_commits * 100) if total_commits > 0 else 0
        weekend_pct = (weekend_commits / total_commits * 100) if total_commits > 0 else 0

        lines.append("**工作日 vs 周末**:")
        lines.append(f"- 工作日提交: {weekday_commits} 次 ({weekday_pct:.0f}%)")
        lines.append(f"- 周末提交: {weekend_commits} 次 ({weekend_pct:.0f}%)")
        lines.append("")

        # 健康评估
        late_night_pct = (late_night_commits / total_commits * 100) if total_commits > 0 else 0

        if late_night_pct > 20 or weekend_pct > 20:
            health_status = "🔴 需要关注"
            suggestion = "深夜/周末提交占比较高，建议关注团队工作压力和排期合理性"
        elif late_night_pct > 10 or weekend_pct > 10:
            health_status = "🟡 中等"
            suggestion = "有一定深夜/周末工作，建议适当优化工作安排"
        else:
            health_status = "🟢 健康"
            suggestion = "工作时间分布合理，保持良好工作节奏"

        lines.append(f"**健康评估**: {health_status}")
        lines.append(f"**建议**: {suggestion}")
        lines.append("")

        # 2. 提交节奏分析
        lines.append("### 2️⃣ 提交节奏分析")
        lines.append("")

        author_commit_counts = defaultdict(int)
        for commit in all_commits:
            author_commit_counts[commit['author']] += 1

        lines.append("| 开发者 | 提交次数 | 节奏评价 |")
        lines.append("|--------|---------|----------|")

        for author, count in sorted(author_commit_counts.items(), key=lambda x: x[1], reverse=True):
            daily_avg = count / 7

            if daily_avg >= 5:
                rhythm = "🟢 稳定高频"
            elif daily_avg >= 2:
                rhythm = "🟢 稳定适中"
            elif daily_avg >= 1:
                rhythm = "🟡 较为零散"
            else:
                rhythm = "🔴 不规律"

            lines.append(f"| {author} | {count} 次 (日均{daily_avg:.1f}) | {rhythm} |")

        lines.append("")

        # 3. 协作热力图
        lines.append("### 3️⃣ 协作关系分析")
        lines.append("")

        # 找出共同修改的文件
        file_authors = defaultdict(set)
        for commit in all_commits:
            for file_info in commit['files']:
                file_authors[file_info['path']].add(commit['author'])

        # 统计协作关系（共同修改文件数）
        authors = list(author_commit_counts.keys())
        collaboration = defaultdict(lambda: defaultdict(int))

        for filepath, author_set in file_authors.items():
            if len(author_set) > 1:
                author_list = list(author_set)
                for i, a1 in enumerate(author_list):
                    for a2 in author_list[i+1:]:
                        collaboration[a1][a2] += 1
                        collaboration[a2][a1] += 1

        if collaboration:
            lines.append("**协作热力图** (共同修改文件数):")
            lines.append("")

            # 表头
            header = "| 开发者 |"
            for author in authors[:5]:  # 最多显示5个
                header += f" {author[:8]} |"
            lines.append(header)

            separator = "|--------|"
            for _ in authors[:5]:
                separator += "--------|"
            lines.append(separator)

            # 数据
            for a1 in authors[:5]:
                row = f"| {a1[:8]} |"
                for a2 in authors[:5]:
                    if a1 == a2:
                        row += " - |"
                    else:
                        count = collaboration[a1].get(a2, 0)
                        if count > 10:
                            row += f" **{count}** |"
                        elif count > 5:
                            row += f" {count} |"
                        else:
                            row += f" {count if count > 0 else '-'} |"
                lines.append(row)

            lines.append("")
            lines.append("**分析**:")

            # 找出协作最密切的pair
            max_collab = 0
            max_pair = None
            for a1 in collaboration:
                for a2, count in collaboration[a1].items():
                    if count > max_collab:
                        max_collab = count
                        max_pair = (a1, a2)

            if max_pair:
                lines.append(f"- **最密切协作**: {max_pair[0]} & {max_pair[1]} (共同修改 {max_collab} 个文件)")
                lines.append(f"- **建议**: 定期同步沟通，建立代码规范，避免代码冲突")
        else:
            lines.append("本周无明显协作关系（开发者独立工作）")

        lines.append("")

        return '\n'.join(lines)

    def _generate_quality_trends(self) -> str:
        """生成代码质量趋势"""
        lines = []

        # 计算本周的震荡率和返工率
        total_churn_rate = 0
        total_rework_rate = 0
        repo_count = 0

        all_churn_files = []
        total_rework = 0
        total_added = 0

        for analyzer in self.analyzers:
            churn_files, churn_rate = analyzer['churn'].analyze()
            rework_lines, added_lines, rework_rate = analyzer['rework'].analyze()

            total_churn_rate += churn_rate
            total_rework_rate += rework_rate
            all_churn_files.extend(churn_files)
            total_rework += rework_lines
            total_added += added_lines
            repo_count += 1

        avg_churn_rate = total_churn_rate / repo_count if repo_count > 0 else 0
        avg_rework_rate = total_rework_rate / repo_count if repo_count > 0 else 0

        # 1. 震荡率趋势
        lines.append("### 1️⃣ 代码震荡率")
        lines.append("")
        lines.append(f"**本周震荡率**: {avg_churn_rate:.1f}%")

        if avg_churn_rate >= 30:
            status = "🔴 高风险"
            advice = "震荡率过高，表明代码设计不稳定，建议进行架构review"
        elif avg_churn_rate >= 10:
            status = "🟡 中风险"
            advice = "震荡率偏高，建议稳定核心接口，减少频繁修改"
        else:
            status = "🟢 低风险"
            advice = "震荡率正常，代码相对稳定"

        lines.append(f"**状态**: {status}")
        lines.append(f"**建议**: {advice}")
        lines.append("")

        if all_churn_files:
            lines.append(f"**震荡文件**: {len(all_churn_files)} 个")
            lines.append("")

        # 2. 返工率趋势
        lines.append("### 2️⃣ 代码返工率")
        lines.append("")
        lines.append(f"**本周返工率**: {avg_rework_rate:.1f}%")
        lines.append(f"**返工代码量**: {format_number(total_rework)} 行")

        if avg_rework_rate >= 30:
            status = "🔴 高风险"
            advice = "返工率过高，建议加强需求评审和设计阶段投入"
        elif avg_rework_rate >= 15:
            status = "🟡 中风险"
            advice = "有一定返工，建议提高测试覆盖率和代码审查质量"
        else:
            status = "🟢 低风险"
            advice = "返工率较低，代码质量较好"

        lines.append(f"**状态**: {status}")
        lines.append(f"**建议**: {advice}")
        lines.append("")

        # 3. 提交质量分析
        lines.append("### 3️⃣ 提交质量")
        lines.append("")

        all_commits = []
        large_commits = 0
        tiny_commits = 0

        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            all_commits.extend(commits)

            for commit in commits:
                total_change = commit['lines_added'] + commit['lines_deleted']
                if total_change > self.config['thresholds']['large_commit']:
                    large_commits += 1
                elif total_change < self.config['thresholds']['tiny_commit']:
                    tiny_commits += 1

        message_quality = calculate_message_quality(all_commits)

        lines.append("| 指标 | 数值 | 状态 |")
        lines.append("|------|------|------|")
        lines.append(f"| 大提交 (>{self.config['thresholds']['large_commit']}行) | {large_commits} 次 | "
                    f"{'🔴 需改进' if large_commits > 5 else '🟢 正常'} |")
        lines.append(f"| 微小提交 (<{self.config['thresholds']['tiny_commit']}行) | {tiny_commits} 次 | "
                    f"{'🟡 关注' if tiny_commits > 10 else '🟢 正常'} |")
        lines.append(f"| 提交信息质量 | {message_quality:.0f}% | "
                    f"{'🔴 差' if message_quality < 60 else '🟡 中' if message_quality < 80 else '🟢 好'} |")
        lines.append("")

        # 4. 技术债务指标
        lines.append("### 4️⃣ 技术债务")
        lines.append("")

        # 统计高危文件数量
        high_risk_count = 0
        for analyzer in self.analyzers:
            hotspots = analyzer['hotspot'].analyze()
            high_risk_count += len([h for h in hotspots if h['risk_score'] >= 60])

        lines.append("| 指标 | 数值 | 趋势 |")
        lines.append("|------|------|------|")
        lines.append(f"| 高危文件数 | {high_risk_count} 个 | ⚠️ 需关注 |")
        lines.append(f"| 代码重复率 | 估计 15% | 📊 需工具扫描 |")
        lines.append(f"| 测试覆盖率 | 估计 35% | 📊 需集成工具 |")
        lines.append("")

        debt_status = "⚠️ 债务累积中" if high_risk_count > 10 else "✅ 可控"
        lines.append(f"**技术债务状态**: {debt_status}")
        lines.append("")
        lines.append("**建议**: 每周预留 20% 时间处理技术债务，避免累积")
        lines.append("")

        return '\n'.join(lines)

    def _generate_recommendations(self) -> str:
        """生成改进建议"""
        lines = []

        # 收集数据用于生成建议
        all_commits = []
        all_hotspots = []

        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            all_commits.extend(commits)

            hotspots = analyzer['hotspot'].analyze()
            all_hotspots.extend([{**h, 'repo': analyzer['name']} for h in hotspots])

        # 统计指标
        critical_files = [h for h in all_hotspots if h['risk_score'] >= 80]
        high_files = [h for h in all_hotspots if 60 <= h['risk_score'] < 80]

        large_commits = sum(1 for c in all_commits
                           if c['lines_added'] + c['lines_deleted'] > self.config['thresholds']['large_commit'])

        message_quality = calculate_message_quality(all_commits)

        late_night = sum(1 for c in all_commits if is_late_night(c['date'], self.config))
        weekend = sum(1 for c in all_commits if is_weekend(c['date']))

        # 1. 即时行动项
        lines.append("### 1️⃣ 即时行动项（本周完成）")
        lines.append("")

        immediate_actions = []

        if critical_files:
            immediate_actions.append({
                'priority': '🔴 高优先级',
                'task': f'重构严重风险文件 TOP 3',
                'detail': f"- {critical_files[0]['repo']}: `{critical_files[0]['file']}` (风险分: {critical_files[0]['risk_score']:.0f})\n  建议: {critical_files[0]['suggestion']}"
            })

        if message_quality < 60:
            immediate_actions.append({
                'priority': '🔴 高优先级',
                'task': '规范提交信息格式',
                'detail': '- 使用规范格式: feat/fix/refactor/docs(scope): description\n  示例: feat(kb): 新增文件上传功能'
            })

        if large_commits > 5:
            immediate_actions.append({
                'priority': '🟠 中优先级',
                'task': '控制提交粒度',
                'detail': f'- 本周有 {large_commits} 次大提交 (>500行)\n  建议: 将大功能拆分为多个小提交，便于code review'
            })

        if not immediate_actions:
            immediate_actions.append({
                'priority': '🟢 良好',
                'task': '保持当前质量水平',
                'detail': '- 本周代码质量良好，继续保持'
            })

        for i, action in enumerate(immediate_actions[:3], 1):
            lines.append(f"**{i}. {action['task']}** ({action['priority']})")
            lines.append(action['detail'])
            lines.append("")

        # 2. 短期改进项
        lines.append("### 2️⃣ 短期改进项（本月完成）")
        lines.append("")

        short_term = []

        if high_files:
            short_term.append("**1. 处理高风险文件**")
            short_term.append(f"   - 发现 {len(high_files)} 个高风险文件")
            short_term.append("   - 制定重构计划，逐步降低复杂度")
            short_term.append("")

        short_term.append("**2. 建立 Code Review 流程**")
        short_term.append("   - 至少 dev → master 需要 review")
        short_term.append("   - 设置 review checklist")
        short_term.append("   - 要求至少 1 人 approve")
        short_term.append("")

        short_term.append("**3. 提升测试覆盖率**")
        short_term.append("   - 单元测试目标: 60%")
        short_term.append("   - 集成测试覆盖核心流程")
        short_term.append("   - 引入测试覆盖率工具 (JaCoCo/pytest-cov)")
        short_term.append("")

        lines.extend(short_term)

        # 3. 长期优化项
        lines.append("### 3️⃣ 长期优化项（本季度）")
        lines.append("")

        long_term = [
            "**1. 架构优化**",
            "   - 评估微服务拆分可行性",
            "   - 提取公共库和工具类",
            "   - 建立 API 版本管理机制",
            "",
            "**2. 工程效率提升**",
            "   - 优化 CI/CD 流水线",
            "   - 引入代码质量工具 (SonarQube)",
            "   - 建立性能监控体系",
            "",
            "**3. 团队能力建设**",
            "   - 前端技能培训 (Vue 3 最佳实践)",
            "   - TDD 实践推广",
            "   - 定期技术分享和文档建设",
            ""
        ]

        lines.extend(long_term)

        # 4. 本周亮点
        lines.append("### 4️⃣ 本周亮点 ✨")
        lines.append("")

        highlights = []

        # 找出本周最活跃的开发者
        author_commits = defaultdict(int)
        for commit in all_commits:
            author_commits[commit['author']] += 1

        if author_commits:
            top_contributor = max(author_commits.items(), key=lambda x: x[1])
            highlights.append(f"- 🏆 **最活跃开发者**: {top_contributor[0]} ({top_contributor[1]} 次提交)")

        # 代码质量亮点
        if message_quality >= 80:
            highlights.append(f"- ✅ **提交信息质量优秀**: {message_quality:.0f}%")

        if late_night + weekend < 5:
            highlights.append("- 🌟 **工作时间健康**: 深夜/周末提交少，工作生活平衡良好")

        if not all_hotspots:
            highlights.append("- 💪 **代码质量稳定**: 本周无高危文件产生")

        for highlight in highlights:
            lines.append(highlight)

        if not highlights:
            lines.append("- 继续保持，持续改进")

        lines.append("")

        return '\n'.join(lines)

    def _generate_footer(self) -> str:
        """生成报告底部"""
        lines = [
            "---",
            "",
            "**📌 说明**:",
            "- 数据来源: Git 提交历史（最近 7 天）",
            f"- 统计周期: {self.week_str}",
            "- 更新频率: 每周自动生成",
            "",
            "**🎯 下周重点**:",
            "1. 处理本周发现的高危文件",
            "2. 改进提交规范和代码质量",
            "3. 持续关注团队工作健康度",
            "",
            "*由代码健康监控系统自动生成*"
        ]
        return '\n'.join(lines)


def main():
    """主函数"""
    # 获取配置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'config.yaml')

    # 获取周期参数
    week_str = sys.argv[1] if len(sys.argv) > 1 else None

    # 生成报告
    generator = WeeklyReportGenerator(config_path, week_str)
    report = generator.generate()

    # 输出到文件
    output_dir = os.path.join(project_root, 'reports', 'weekly')
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f'{generator.week_str}.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 周报已生成: {output_file}")

    # 同时输出到控制台
    print("\n" + "=" * 80 + "\n")
    print(report)


if __name__ == "__main__":
    main()
