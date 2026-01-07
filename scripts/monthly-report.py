#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - 月报生成器
Author: DevOps Team
Created: 2026-01-06

Usage:
    python monthly-report.py [year-month]

Examples:
    python monthly-report.py              # 生成上个月的月报
    python monthly-report.py 2025-12      # 生成指定月的月报
"""

import os
import sys
import glob
import re
from datetime import datetime, timedelta
from collections import defaultdict
from calendar import monthrange

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils import (
    GitAnalyzer, ChurnAnalyzer, ReworkAnalyzer, HotspotAnalyzer,
    HealthScoreCalculator, load_config, format_number,
    is_late_night, is_weekend, calculate_message_quality,
    parse_iso_datetime
)


class MonthlyReportGenerator:
    """月报生成器"""

    def __init__(self, config_path: str, month_str: str = None):
        self.config = load_config(config_path)

        # 解析月份
        if month_str:
            # 格式: 2025-12
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

        # 计算月份的起始和结束时间
        _, last_day = monthrange(self.year, self.month)
        self.month_start = datetime(self.year, self.month, 1)
        self.month_end = datetime(self.year, self.month, last_day, 23, 59, 59)

        self.since_time = self.month_start.strftime("%Y-%m-%d 00:00:00")
        self.until_time = self.month_end.strftime("%Y-%m-%d 23:59:59")

        # 计算工作日数量
        self.work_days = self._count_work_days()

        self.analyzers = self._init_analyzers()

        # 加载本月的周报数据
        self.weekly_reports = self._load_weekly_reports()

    def _count_work_days(self) -> int:
        """计算当月工作日数量（周一到周五）"""
        work_days = 0
        current = self.month_start
        while current <= self.month_end:
            if current.weekday() < 5:  # 0-4 是周一到周五
                work_days += 1
            current += timedelta(days=1)
        return work_days

    def _init_analyzers(self) -> list:
        """初始化所有仓库的分析器"""
        analyzers = []
        missing_repos = []
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
            else:
                missing_repos.append(f"{repo['name']} ({repo['path']})")

        if missing_repos:
            print(f"⚠️  警告: 以下仓库路径不存在，将跳过统计:")
            for repo in missing_repos:
                print(f"   - {repo}")

        print(f"✅ 成功加载 {len(analyzers)}/{len(self.config['repositories'])} 个仓库")
        return analyzers

    def _load_weekly_reports(self) -> list:
        """加载本月的所有周报"""
        project_root = os.path.dirname(script_dir)
        weekly_dir = os.path.join(project_root, 'reports', 'weekly')

        weekly_reports = []
        if not os.path.exists(weekly_dir):
            return weekly_reports

        # 查找本月的周报文件
        pattern = os.path.join(weekly_dir, f"{self.year}-W*.md")
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            # 提取周数
            match = re.match(r'(\d{4})-W(\d{2})\.md', filename)
            if match:
                weekly_reports.append({
                    'filename': filename,
                    'path': filepath,
                    'week': int(match.group(2))
                })

        # 按周数排序
        weekly_reports.sort(key=lambda x: x['week'])
        return weekly_reports

    def generate(self) -> str:
        """生成月报"""
        report = []

        # 标题
        report.append(self._generate_header())

        # 一、月度总览
        report.append("## 一、月度总览 📊")
        report.append(self._generate_overview())

        # 二、团队表现
        report.append("## 二、团队表现 👥")
        report.append(self._generate_team_performance())

        # 三、趋势分析
        report.append("## 三、趋势分析 📈")
        report.append(self._generate_trends())

        # 四、健康指标
        report.append("## 四、健康指标 ❤️")
        report.append(self._generate_health_metrics())

        # 五、风险分析
        report.append("## 五、风险分析 ⚠️")
        report.append(self._generate_risk_analysis())

        # 六、代码质量
        report.append("## 六、代码质量 💎")
        report.append(self._generate_quality_metrics())

        # 七、下月计划建议
        report.append("## 七、下月计划建议 💡")
        report.append(self._generate_recommendations())

        # 底部
        report.append(self._generate_footer())

        return '\n\n'.join(report)

    def _generate_header(self) -> str:
        """生成报告头部"""
        month_names = {
            1: '一月', 2: '二月', 3: '三月', 4: '四月',
            5: '五月', 6: '六月', 7: '七月', 8: '八月',
            9: '九月', 10: '十月', 11: '十一月', 12: '十二月'
        }

        lines = [
            f"# {self.year}年{month_names[self.month]} 代码健康月报",
            "",
            f"**报告周期**: {self.month_start.strftime('%Y-%m-%d')} ~ {self.month_end.strftime('%Y-%m-%d')}",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**工作日数**: {self.work_days} 天",
            "",
            "---"
        ]
        return '\n'.join(lines)

    def _generate_overview(self) -> str:
        """生成月度总览"""
        lines = []

        # 收集本月所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        # 统计数据
        total_commits = len(all_commits)
        total_added = sum(c['lines_added'] for c in all_commits)
        total_deleted = sum(c['lines_deleted'] for c in all_commits)
        total_net = total_added - total_deleted

        # 统计活跃开发者
        active_authors = set(c['author'] for c in all_commits)

        # 统计涉及仓库
        active_repos = set(c['repo'] for c in all_commits)

        # 按日统计
        daily_commits = defaultdict(int)
        for commit in all_commits:
            date = commit['commit_date'][:10]  # YYYY-MM-DD
            daily_commits[date] += 1

        # 最活跃的一天
        if daily_commits:
            most_active_day = max(daily_commits.items(), key=lambda x: x[1])
        else:
            most_active_day = ("N/A", 0)

        lines.append("### 📌 核心指标")
        lines.append("")
        lines.append("| 指标 | 数值 | 说明 |")
        lines.append("|------|------|------|")
        lines.append(f"| 总提交次数 | **{format_number(total_commits)}** | 本月全部代码提交 |")
        lines.append(f"| 代码新增 | **{format_number(total_added)}** 行 | 新增代码行数 |")
        lines.append(f"| 代码删除 | **{format_number(total_deleted)}** 行 | 删除代码行数 |")
        lines.append(f"| 代码净增 | **{format_number(total_net)}** 行 | 新增减去删除 |")
        lines.append(f"| 活跃开发者 | **{len(active_authors)}** 人 | 有代码提交的开发者 |")
        lines.append(f"| 活跃仓库 | **{len(active_repos)}** 个 | 有代码变更的仓库 |")
        lines.append(f"| 日均提交量 | **{total_commits / max(1, self.work_days):.1f}** 次 | 工作日平均 |")
        lines.append(f"| 最活跃日 | {most_active_day[0]} | {most_active_day[1]} 次提交 |")

        return '\n'.join(lines)

    def _generate_team_performance(self) -> str:
        """生成团队表现"""
        lines = []

        # 收集本月所有提交
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
            'net': 0,
            'files': 0,
            'repos': set()
        })

        for commit in all_commits:
            author = commit['author']
            author_stats[author]['commits'] += 1
            author_stats[author]['added'] += commit['lines_added']
            author_stats[author]['deleted'] += commit['lines_deleted']
            author_stats[author]['net'] += (commit['lines_added'] - commit['lines_deleted'])
            author_stats[author]['files'] += len(commit['files'])
            author_stats[author]['repos'].add(commit['repo'])

        # 贡献排行榜
        lines.append("### 🏆 贡献排行榜")
        lines.append("")
        lines.append("| 排名 | 开发者 | 提交次数 | 新增行数 | 删除行数 | 净增行数 | 文件数 | 涉及仓库 |")
        lines.append("|------|--------|---------|---------|---------|---------|--------|----------|")

        # 按提交次数排序
        sorted_authors = sorted(author_stats.items(), key=lambda x: x[1]['commits'], reverse=True)
        for rank, (author, stats) in enumerate(sorted_authors[:10], 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            lines.append(
                f"| {medal} | {author} | {stats['commits']} | "
                f"{format_number(stats['added'])} | {format_number(stats['deleted'])} | "
                f"{format_number(stats['net'])} | {stats['files']} | {len(stats['repos'])} |"
            )

        # 协作统计
        lines.append("")
        lines.append("### 🤝 协作统计")
        lines.append("")

        # 统计多人协作的仓库
        repo_authors = defaultdict(set)
        for commit in all_commits:
            repo_authors[commit['repo']].add(commit['author'])

        lines.append("| 仓库 | 贡献人数 | 提交次数 |")
        lines.append("|------|---------|---------|")

        repo_commits = defaultdict(int)
        for commit in all_commits:
            repo_commits[commit['repo']] += 1

        for repo in sorted(repo_authors.keys()):
            authors_count = len(repo_authors[repo])
            commits_count = repo_commits[repo]
            lines.append(f"| {repo} | {authors_count} | {commits_count} |")

        return '\n'.join(lines)

    def _generate_trends(self) -> str:
        """生成趋势分析"""
        lines = []

        # 收集本月所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        # 按周统计
        weekly_stats = defaultdict(lambda: {
            'commits': 0,
            'added': 0,
            'deleted': 0,
            'authors': set()
        })

        for commit in all_commits:
            commit_date = datetime.strptime(commit['commit_date'][:10], '%Y-%m-%d')
            week_num = commit_date.isocalendar()[1]
            week_key = f"{commit_date.year}-W{week_num:02d}"

            weekly_stats[week_key]['commits'] += 1
            weekly_stats[week_key]['added'] += commit['lines_added']
            weekly_stats[week_key]['deleted'] += commit['lines_deleted']
            weekly_stats[week_key]['authors'].add(commit['author'])

        lines.append("### 📊 每周趋势对比")
        lines.append("")
        lines.append("| 周 | 提交次数 | 代码新增 | 代码删除 | 净增 | 活跃人数 |")
        lines.append("|----|---------|---------|---------|------|---------|")

        for week in sorted(weekly_stats.keys()):
            stats = weekly_stats[week]
            net = stats['added'] - stats['deleted']
            lines.append(
                f"| {week} | {stats['commits']} | "
                f"{format_number(stats['added'])} | {format_number(stats['deleted'])} | "
                f"{format_number(net)} | {len(stats['authors'])} |"
            )

        # 找出最活跃的周
        if weekly_stats:
            most_active_week = max(weekly_stats.items(), key=lambda x: x[1]['commits'])
            lines.append("")
            lines.append(f"**最活跃的周**: {most_active_week[0]} ({most_active_week[1]['commits']} 次提交)")

        return '\n'.join(lines)

    def _generate_health_metrics(self) -> str:
        """生成健康指标"""
        lines = []

        # 收集本月所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        # 计算月度健康评分
        if all_commits:
            # 使用每日的健康评分计算月度平均值
            daily_scores = []
            current = self.month_start
            while current <= self.month_end:
                date_str = current.strftime("%Y-%m-%d")
                next_day = current + timedelta(days=1)
                next_date_str = next_day.strftime("%Y-%m-%d")

                day_commits = [
                    c for c in all_commits
                    if date_str <= c['commit_date'][:10] < next_date_str
                ]

                if day_commits:
                    calculator = HealthScoreCalculator(self.config['thresholds'])
                    score = calculator.calculate(day_commits)
                    daily_scores.append(score)

                current = next_day

            avg_score = sum(daily_scores) / len(daily_scores) if daily_scores else 0
        else:
            avg_score = 0

        # 评级
        if avg_score >= 80:
            rating = "🟢 优秀"
        elif avg_score >= 60:
            rating = "🟡 良好"
        else:
            rating = "🔴 需改进"

        lines.append("### 💯 月度健康评分")
        lines.append("")
        lines.append(f"**平均健康分**: {avg_score:.1f} / 100 ({rating})")
        lines.append("")

        # 工作时间分布
        normal_hours = 0
        overtime_hours = 0
        late_night_hours = 0
        weekend_hours = 0

        for commit in all_commits:
            commit_dt = parse_iso_datetime(commit['commit_date'])
            if is_weekend(commit_dt):
                weekend_hours += 1
            elif is_late_night(commit_dt):
                late_night_hours += 1
            elif commit_dt.hour >= 18:
                overtime_hours += 1
            else:
                normal_hours += 1

        total = len(all_commits)
        if total > 0:
            lines.append("### ⏰ 工作时间分布")
            lines.append("")
            lines.append("| 时段 | 提交次数 | 占比 |")
            lines.append("|------|---------|------|")
            lines.append(f"| 正常工作时间 (9-18点) | {normal_hours} | {normal_hours/total*100:.1f}% |")
            lines.append(f"| 加班时间 (18-22点) | {overtime_hours} | {overtime_hours/total*100:.1f}% |")
            lines.append(f"| 深夜时间 (22-6点) | {late_night_hours} | {late_night_hours/total*100:.1f}% |")
            lines.append(f"| 周末时间 | {weekend_hours} | {weekend_hours/total*100:.1f}% |")

        return '\n'.join(lines)

    def _generate_risk_analysis(self) -> str:
        """生成风险分析"""
        lines = []

        # 收集本月所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        # 统计风险提交
        late_night_commits = []
        weekend_commits = []
        large_commits = []

        for commit in all_commits:
            commit_dt = parse_iso_datetime(commit['commit_date'])

            if is_late_night(commit_dt):
                late_night_commits.append(commit)

            if is_weekend(commit_dt):
                weekend_commits.append(commit)

            if commit['lines_added'] + commit['lines_deleted'] > 500:
                large_commits.append(commit)

        lines.append("### ⚠️ 风险提交统计")
        lines.append("")
        lines.append("| 风险类型 | 数量 | 占比 | 说明 |")
        lines.append("|---------|------|------|------|")

        total = len(all_commits) if all_commits else 1
        lines.append(f"| 深夜提交 (22:00-06:00) | {len(late_night_commits)} | {len(late_night_commits)/total*100:.1f}% | 可能影响代码质量 |")
        lines.append(f"| 周末提交 | {len(weekend_commits)} | {len(weekend_commits)/total*100:.1f}% | 工作生活平衡问题 |")
        lines.append(f"| 大型提交 (>500行) | {len(large_commits)} | {len(large_commits)/total*100:.1f}% | 难以审查 |")

        # 建议
        lines.append("")
        lines.append("### 💡 风险缓解建议")
        lines.append("")

        if len(late_night_commits) / total > 0.1:
            lines.append("- ⚠️ **深夜提交占比较高**: 建议调整工作节奏，避免疲劳编码")

        if len(weekend_commits) / total > 0.15:
            lines.append("- ⚠️ **周末提交占比较高**: 建议关注团队工作负荷，避免过度加班")

        if len(large_commits) / total > 0.2:
            lines.append("- ⚠️ **大型提交较多**: 建议拆分提交，提高代码审查效率")

        return '\n'.join(lines)

    def _generate_quality_metrics(self) -> str:
        """生成代码质量指标"""
        lines = []

        # 收集本月所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        # 提交粒度分析
        commit_sizes = [c['lines_added'] + c['lines_deleted'] for c in all_commits]

        if commit_sizes:
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

        # 文件修改热点
        file_changes = defaultdict(int)
        for commit in all_commits:
            for file_info in commit['files']:
                file_changes[file_info['path']] += 1

        if file_changes:
            lines.append("")
            lines.append("### 🔥 文件修改热点 (TOP 10)")
            lines.append("")
            lines.append("| 文件路径 | 修改次数 |")
            lines.append("|---------|---------|")

            sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)
            for filepath, count in sorted_files[:10]:
                lines.append(f"| `{filepath}` | {count} |")

        return '\n'.join(lines)

    def _generate_recommendations(self) -> str:
        """生成下月计划建议"""
        lines = []

        # 收集本月所有提交
        all_commits = []
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        lines.append("基于本月数据分析，建议下月重点关注：")
        lines.append("")

        # 计算一些关键指标
        total = len(all_commits)
        if total > 0:
            late_night = len([c for c in all_commits if is_late_night(parse_iso_datetime(c['commit_date']))])
            weekend = len([c for c in all_commits if is_weekend(parse_iso_datetime(c['commit_date']))])
            large = len([c for c in all_commits if c['lines_added'] + c['lines_deleted'] > 500])

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

    def _generate_footer(self) -> str:
        """生成报告底部"""
        lines = [
            "---",
            "",
            "*本报告由 EcoMind 代码健康监控系统自动生成*",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        return '\n'.join(lines)

    def save(self, output_dir: str):
        """保存报告到文件"""
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{self.month_str}.md"
        filepath = os.path.join(output_dir, filename)

        report_content = self.generate()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"✅ 月报已生成: {filepath}")
        return filepath


def main():
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'config.yaml')
    output_dir = os.path.join(project_root, 'reports', 'monthly')

    # 解析命令行参数
    month_str = sys.argv[1] if len(sys.argv) > 1 else None

    # 生成月报
    print(f"📊 开始生成月报...")
    if month_str:
        print(f"   指定月份: {month_str}")
    else:
        print(f"   使用上个月")

    generator = MonthlyReportGenerator(config_path, month_str)
    filepath = generator.save(output_dir)

    print(f"✅ 月报生成完成!")
    print(f"   文件路径: {filepath}")


if __name__ == '__main__':
    main()
