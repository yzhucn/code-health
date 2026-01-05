#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - 日报生成器
Author: DevOps Team
Created: 2025-12-30

Usage:
    python daily-report.py [date]

Examples:
    python daily-report.py                  # 生成今天的日报
    python daily-report.py 2025-12-29       # 生成指定日期的日报
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
    is_late_night, is_weekend, is_overtime, calculate_message_quality,
    parse_iso_datetime
)


class DailyReportGenerator:
    """日报生成器"""

    def __init__(self, config_path: str, report_date: str = None):
        self.config = load_config(config_path)
        self.report_date = report_date or datetime.now().strftime("%Y-%m-%d")

        # 计算查询的时间范围
        date_obj = datetime.strptime(self.report_date, "%Y-%m-%d")
        self.since_time = date_obj.strftime("%Y-%m-%d 00:00:00")
        self.until_time = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

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
        """生成日报"""
        report = []

        # 标题
        report.append(self._generate_header())

        # 一、基础数据
        report.append("## 一、今日概况")
        report.append(self._generate_basic_metrics())

        # 二、代码变更
        report.append("## 二、代码变更统计")
        report.append(self._generate_code_changes())

        # 三、风险预警
        report.append("## 三、风险预警 🚨")
        report.append(self._generate_risk_alerts())

        # 四、健康评分
        report.append("## 四、今日健康评分")
        report.append(self._generate_health_score())

        # 五、提交详情
        report.append("## 五、提交详情")
        report.append(self._generate_commit_details())

        # 底部
        report.append(self._generate_footer())

        return '\n\n'.join(report)

    def _generate_header(self) -> str:
        """生成报告头部"""
        lines = [
            f"# 代码健康日报",
            "",
            f"**日期**: {self.report_date}",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---"
        ]
        return '\n'.join(lines)

    def _generate_basic_metrics(self) -> str:
        """生成基础指标"""
        total_commits = 0
        total_files = 0
        active_repos = 0
        active_authors = set()
        author_commit_counts = defaultdict(int)

        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            if commits:
                total_commits += len(commits)
                active_repos += 1
                for commit in commits:
                    active_authors.add(commit['author'])
                    author_commit_counts[commit['author']] += 1
                    total_files += len(commit['files'])

        lines = [
            "### 📊 基本数据",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 提交次数 | **{total_commits}** 次 |",
            f"| 活跃开发者 | **{len(active_authors)}** 人 |",
            f"| 涉及仓库 | **{active_repos}** 个 |",
            f"| 修改文件数 | **{total_files}** 个 |",
            ""
        ]

        if active_authors:
            lines.append(f"**活跃开发者详情**:")
            lines.append("")
            # 按提交次数排序
            sorted_authors = sorted(author_commit_counts.items(), key=lambda x: x[1], reverse=True)
            for author, count in sorted_authors:
                lines.append(f"- {author} ({count} commits)")
            lines.append("")

        return '\n'.join(lines)

    def _generate_code_changes(self) -> str:
        """生成代码变更统计"""
        total_added = 0
        total_deleted = 0
        large_commits = 0
        tiny_commits = 0
        repo_stats = []

        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            repo_added = sum(c['lines_added'] for c in commits)
            repo_deleted = sum(c['lines_deleted'] for c in commits)

            if commits:
                repo_stats.append({
                    'name': analyzer['name'],
                    'commits': len(commits),
                    'added': repo_added,
                    'deleted': repo_deleted,
                    'net': repo_added - repo_deleted
                })

                # 统计大提交和微小提交
                for commit in commits:
                    total_change = commit['lines_added'] + commit['lines_deleted']
                    if total_change > self.config['thresholds']['large_commit']:
                        large_commits += 1
                    elif total_change < self.config['thresholds']['tiny_commit']:
                        tiny_commits += 1

            total_added += repo_added
            total_deleted += repo_deleted

        net_lines = total_added - total_deleted

        lines = [
            "### 📈 代码变更量",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 新增行数 | +{format_number(total_added)} 行 |",
            f"| 删除行数 | -{format_number(total_deleted)} 行 |",
            f"| **净增行数** | **{'+' if net_lines >= 0 else ''}{format_number(net_lines)}** 行 |",
            ""
        ]

        # 提交质量分析
        lines.extend([
            "### 📝 提交质量",
            "",
            "| 指标 | 数值 | 状态 |",
            "|------|------|------|",
            f"| 大提交 (>{self.config['thresholds']['large_commit']}行) | {large_commits} 次 | "
            f"{'🔴 警告' if large_commits > 3 else '🟢 正常'} |",
            f"| 微小提交 (<{self.config['thresholds']['tiny_commit']}行) | {tiny_commits} 次 | "
            f"{'🟡 关注' if tiny_commits > 5 else '🟢 正常'} |",
            ""
        ])

        # 按仓库统计
        if repo_stats:
            lines.extend([
                "### 📦 各仓库变更",
                "",
                "| 仓库 | 提交 | 新增 | 删除 | 净增 |",
                "|------|------|------|------|------|"
            ])

            repo_stats.sort(key=lambda x: x['net'], reverse=True)
            for stat in repo_stats:
                lines.append(
                    f"| {stat['name']} | {stat['commits']} | "
                    f"+{format_number(stat['added'])} | "
                    f"-{format_number(stat['deleted'])} | "
                    f"**{'+' if stat['net'] >= 0 else ''}{format_number(stat['net'])}** |"
                )
            lines.append("")

        return '\n'.join(lines)

    def _generate_risk_alerts(self) -> str:
        """生成风险预警"""
        lines = []

        # 1. 代码震荡检测
        lines.append("### 1️⃣ 代码震荡检测")
        lines.append("")

        all_churn_files = []
        total_churn_rate = 0
        repo_count = 0

        for analyzer in self.analyzers:
            churn_files, churn_rate = analyzer['churn'].analyze()
            if churn_files or churn_rate > 0:
                all_churn_files.extend([{**f, 'repo': analyzer['name']} for f in churn_files])
                total_churn_rate += churn_rate
                repo_count += 1

        avg_churn_rate = total_churn_rate / repo_count if repo_count > 0 else 0

        # 震荡率评级
        if avg_churn_rate >= 30:
            churn_status = "🔴 **高风险**"
        elif avg_churn_rate >= 10:
            churn_status = "🟡 **中风险**"
        else:
            churn_status = "🟢 **低风险**"

        lines.append(f"**震荡率**: {avg_churn_rate:.1f}% | 状态: {churn_status}")
        lines.append("")

        if all_churn_files:
            lines.append(f"**震荡文件 TOP 5** (最近{self.config['thresholds']['churn_days']}天内修改≥{self.config['thresholds']['churn_count']}次):")
            lines.append("")
            lines.append("| 仓库 | 文件 | 修改次数 | 涉及开发者 |")
            lines.append("|------|------|---------|-----------|")

            all_churn_files.sort(key=lambda x: x['count'], reverse=True)
            for f in all_churn_files[:5]:
                authors = ', '.join(f['authors'][:3])
                if len(f['authors']) > 3:
                    authors += f" 等{len(f['authors'])}人"
                lines.append(f"| {f['repo']} | `{f['file']}` | {f['count']} | {authors} |")
            lines.append("")
        else:
            lines.append("✅ 未发现震荡文件")
            lines.append("")

        # 2. 返工率检测
        lines.append("### 2️⃣ 返工率检测")
        lines.append("")

        total_rework = 0
        total_added_for_rework = 0

        for analyzer in self.analyzers:
            rework_lines, added_lines, rework_rate = analyzer['rework'].analyze()
            total_rework += rework_lines
            total_added_for_rework += added_lines

        overall_rework_rate = (total_rework / total_added_for_rework * 100) if total_added_for_rework > 0 else 0

        # 返工率评级
        if overall_rework_rate >= 30:
            rework_status = "🔴 **高风险**"
        elif overall_rework_rate >= 15:
            rework_status = "🟡 **中风险**"
        else:
            rework_status = "🟢 **低风险**"

        lines.append(f"**返工率**: {overall_rework_rate:.1f}% | 状态: {rework_status}")
        lines.append(f"**返工代码**: {format_number(total_rework)} 行 (最近7天新增中有{self.config['thresholds']['rework_delete_days']}天内被删除)")
        lines.append("")

        # 3. 高危文件预警
        lines.append("### 3️⃣ 高危文件预警")
        lines.append("")

        all_hotspots = []
        for analyzer in self.analyzers:
            hotspots = analyzer['hotspot'].analyze()
            all_hotspots.extend([{**h, 'repo': analyzer['name']} for h in hotspots])

        all_hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        high_risk_count = len([h for h in all_hotspots if h['risk_score'] >= 80])

        if all_hotspots:
            lines.append(f"**发现高危文件**: {len(all_hotspots)} 个 (严重: {high_risk_count})")
            lines.append("")
            lines.append("**TOP 5 高危文件**:")
            lines.append("")
            lines.append("| 仓库 | 文件 | 风险分 | 修改次数 | 大小 | 开发者 | 标签 |")
            lines.append("|------|------|--------|---------|------|--------|------|")

            for h in all_hotspots[:5]:
                risk_emoji = "🔴" if h['risk_score'] >= 80 else "🟠" if h['risk_score'] >= 60 else "🟡"
                tags = ', '.join(h['tags']) if h['tags'] else "-"
                authors_display = f"{h['author_count']}人"

                lines.append(
                    f"| {h['repo']} | `{h['file']}` | {risk_emoji} {h['risk_score']:.0f} | "
                    f"{h['modify_count']} | {h['file_size']} 行 | {authors_display} | {tags} |"
                )
            lines.append("")
        else:
            lines.append("✅ 未发现高危文件")
            lines.append("")

        # 4. 工作时间异常
        lines.append("### 4️⃣ 工作时间异常")
        lines.append("")

        late_night_commits = []
        weekend_commits_list = []
        overtime_commits = []

        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                if is_late_night(commit['date'], self.config):
                    late_night_commits.append({
                        'author': commit['author'],
                        'time': commit['date'],
                        'repo': analyzer['name']
                    })
                if is_weekend(commit['date']):
                    weekend_commits_list.append({
                        'author': commit['author'],
                        'time': commit['date'],
                        'repo': analyzer['name']
                    })
                if is_overtime(commit['date'], self.config):
                    overtime_commits.append({
                        'author': commit['author'],
                        'time': commit['date'],
                        'repo': analyzer['name']
                    })

        if late_night_commits or weekend_commits_list or overtime_commits:
            # 风险指标说明
            lines.append("**风险指标说明**:")
            lines.append("- ⏰ 加班提交: 18:00-21:00提交，可能排期紧张")
            lines.append("- 🌙 深夜提交: 22:00-06:00提交，影响健康和代码质量")
            lines.append("- 📅 周末工作: 周六/周日提交，工作生活失衡")
            lines.append("")

            # 加班提交统计
            if overtime_commits:
                lines.append(f"#### ⏰ 加班提交: {len(overtime_commits)} 次")
                lines.append("")
                lines.append("**时段**: 18:00-21:00 (晚餐时间后)")
                lines.append("**影响**: 可能排期较紧，需关注项目进度")
                lines.append("")
                author_counts = defaultdict(int)
                for c in overtime_commits:
                    author_counts[c['author']] += 1
                top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
                lines.append(f"**涉及人员**: {', '.join([f'{a}({c}次)' for a, c in top_authors[:3]])}")
                lines.append("")
                lines.append("**建议**:")
                lines.append("- 评估排期是否合理，是否需要调整")
                lines.append("- 关注团队工作负荷，避免持续加班")
                lines.append("- 优化任务分配，提高开发效率")
                lines.append("")

            # 深夜提交统计
            if late_night_commits:
                lines.append(f"#### 🌙 深夜提交: {len(late_night_commits)} 次")
                lines.append("")
                lines.append("**时段**: 22:00-06:00 (应该休息的时间)")
                lines.append("**影响**: 严重影响健康和睡眠，可能导致代码质量下降")
                lines.append("")
                author_counts = defaultdict(int)
                for c in late_night_commits:
                    author_counts[c['author']] += 1
                top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
                lines.append(f"**高频人员**: {', '.join([f'{a}({c}次)' for a, c in top_authors[:3]])}")
                lines.append("")
                lines.append("**健康提醒**:")
                lines.append("- 🚨 **强烈建议**: 保证充足睡眠，避免深夜工作")
                lines.append("- 深夜工作容易出现bug，建议第二天review")
                lines.append("- 如果是紧急修复，需要后续补充测试")
                lines.append("- 持续深夜工作请及时与管理层沟通")
                lines.append("")

            # 周末工作统计
            if weekend_commits_list:
                lines.append(f"#### 📅 周末工作: {len(weekend_commits_list)} 次")
                lines.append("")
                lines.append("**时段**: 周六/周日")
                lines.append("**影响**: 工作生活失衡，长期影响团队士气")
                lines.append("")
                author_counts = defaultdict(int)
                for c in weekend_commits_list:
                    author_counts[c['author']] += 1
                top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
                lines.append(f"**参与人员**: {', '.join([f'{a}({c}次)' for a, c in top_authors[:3]])}")
                lines.append("")
                lines.append("**建议**:")
                lines.append("- 合理安排工作，避免周末加班成为常态")
                lines.append("- 如有紧急情况，建议后续调休")
                lines.append("- 评估是否需要增加人力或延长排期")
                lines.append("")

            # 整体建议
            lines.append("**整体建议**: 关注团队工作压力，评估排期合理性，保持工作生活平衡")
        else:
            lines.append("✅ 工作时间正常，无加班/深夜/周末提交")

        lines.append("")

        return '\n'.join(lines)

    def _generate_health_score(self) -> str:
        """生成健康评分"""
        # 收集所有指标
        total_commits = 0
        large_commits = 0
        all_commits = []
        late_night = 0
        weekend = 0

        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            all_commits.extend(commits)
            total_commits += len(commits)

            for commit in commits:
                total_change = commit['lines_added'] + commit['lines_deleted']
                if total_change > self.config['thresholds']['large_commit']:
                    large_commits += 1
                if is_late_night(commit['date'], self.config):
                    late_night += 1
                if is_weekend(commit['date']):
                    weekend += 1

        # 计算震荡率和返工率
        total_churn_rate = 0
        total_rework_rate = 0
        repo_count = 0

        all_hotspots = []

        for analyzer in self.analyzers:
            churn_files, churn_rate = analyzer['churn'].analyze()
            rework_lines, added_lines, rework_rate = analyzer['rework'].analyze()
            hotspots = analyzer['hotspot'].analyze()

            total_churn_rate += churn_rate
            total_rework_rate += rework_rate
            all_hotspots.extend(hotspots)
            repo_count += 1

        avg_churn_rate = total_churn_rate / repo_count if repo_count > 0 else 0
        avg_rework_rate = total_rework_rate / repo_count if repo_count > 0 else 0

        message_quality = calculate_message_quality(all_commits)
        high_risk_files = len([h for h in all_hotspots if h['risk_score'] >= 60])

        # 构建指标字典
        metrics = {
            'large_commits': large_commits,
            'churn_rate': avg_churn_rate,
            'rework_rate': avg_rework_rate,
            'message_quality': message_quality,
            'late_night_commits': late_night,
            'weekend_commits': weekend,
            'high_risk_files': high_risk_files
        }

        # 计算健康分
        calculator = HealthScoreCalculator(self.config['thresholds'])
        score, deductions = calculator.calculate(metrics)
        emoji, level = calculator.get_level(score)

        lines = [
            f"### {emoji} 综合评分: {score} 分 ({level})",
            ""
        ]

        # 评分说明
        lines.append("**评分说明**:")
        lines.append("- 🟢 优秀 (≥80分): 代码质量高，工作时间健康")
        lines.append("- 🟡 良好 (60-79分): 有改进空间，建议关注扣分项")
        lines.append("- 🟠 警告 (40-59分): 存在明显问题，需及时改进")
        lines.append("- 🔴 危险 (<40分): 严重问题，需要立即处理")
        lines.append("")

        # 评分构成表格
        lines.append("**评分构成**:")
        lines.append("")
        lines.append("| 评分维度 | 当前状态 | 影响 | 说明 |")
        lines.append("|---------|---------|------|------|")

        # 大提交
        if large_commits > 0:
            lines.append(f"| 大提交次数 | {large_commits}次 | -{large_commits * 5}分 | 单次变更>500行，建议拆分 |")
        else:
            lines.append(f"| 大提交次数 | 0次 | +0分 | ✅ 提交粒度适中 |")

        # 震荡率
        if avg_churn_rate > 30:
            lines.append(f"| 代码震荡率 | {avg_churn_rate:.1f}% | -20分 | 频繁修改同一文件，代码不稳定 |")
        elif avg_churn_rate > 10:
            lines.append(f"| 代码震荡率 | {avg_churn_rate:.1f}% | -10分 | 有一定震荡，建议优化设计 |")
        else:
            lines.append(f"| 代码震荡率 | {avg_churn_rate:.1f}% | +0分 | ✅ 代码稳定 |")

        # 返工率
        if avg_rework_rate > 30:
            lines.append(f"| 代码返工率 | {avg_rework_rate:.1f}% | -15分 | 大量返工，需求或设计有问题 |")
        elif avg_rework_rate > 15:
            lines.append(f"| 代码返工率 | {avg_rework_rate:.1f}% | -8分 | 有返工现象，建议评审机制 |")
        else:
            lines.append(f"| 代码返工率 | {avg_rework_rate:.1f}% | +0分 | ✅ 返工率低 |")

        # 提交信息质量
        if message_quality < 60:
            lines.append(f"| 提交信息质量 | {message_quality:.0f}% | -10分 | 提交信息不规范 |")
        else:
            lines.append(f"| 提交信息质量 | {message_quality:.0f}% | +0分 | ✅ 提交信息良好 |")

        # 工作时间
        abnormal_commits = late_night + weekend
        if abnormal_commits > 0:
            lines.append(f"| 工作时间健康 | {abnormal_commits}次异常 | -{abnormal_commits * 2}分 | 深夜/周末工作，注意休息 |")
        else:
            lines.append(f"| 工作时间健康 | 正常 | +0分 | ✅ 工作时间健康 |")

        # 高危文件
        if high_risk_files > 0:
            deduction_hr = min(high_risk_files * 3, 15)
            lines.append(f"| 高危文件数量 | {high_risk_files}个 | -{deduction_hr}分 | 存在高复杂度/高修改频次文件 |")
        else:
            lines.append(f"| 高危文件数量 | 0个 | +0分 | ✅ 无高危文件 |")

        lines.append("")

        # 如果有扣分，显示改进建议
        if score < 100:
            lines.append("**改进建议**:")
            lines.append("")
            if large_commits > 0:
                lines.append("- 📦 **减少大提交**: 将大型变更拆分为多个小提交，每次只做一件事")
            if avg_churn_rate > 10:
                lines.append("- 🔄 **降低震荡率**: 优化代码设计，减少频繁修改同一文件")
            if avg_rework_rate > 15:
                lines.append("- ⚙️ **减少返工**: 加强需求评审和设计评审，降低返工率")
            if message_quality < 60:
                lines.append("- 📝 **规范提交信息**: 使用有意义的提交信息，说明修改原因")
            if abnormal_commits > 0:
                lines.append("- 😴 **注意工作时间**: 避免深夜和周末工作，保持工作生活平衡")
            if high_risk_files > 0:
                lines.append("- 🚨 **重构高危文件**: 优先处理高复杂度或高修改频次的文件")
            lines.append("")

        # 趋势对比（简化版：与昨天对比）
        lines.append("**趋势**: 需要积累历史数据")
        lines.append("")

        return '\n'.join(lines)

    def _generate_commit_details(self) -> str:
        """生成提交详情"""
        all_commits = []

        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(self.since_time, self.until_time)
            for commit in commits:
                all_commits.append({
                    **commit,
                    'repo': analyzer['name']
                })

        if not all_commits:
            return "今日无提交记录"

        # 按作者分组
        author_commits = defaultdict(list)
        for commit in all_commits:
            author_commits[commit['author']].append(commit)

        lines = []

        for author, commits in sorted(author_commits.items()):
            author_added = sum(c['lines_added'] for c in commits)
            author_deleted = sum(c['lines_deleted'] for c in commits)
            author_net = author_added - author_deleted

            lines.append(f"### 👤 {author}")
            lines.append(f"提交: {len(commits)} 次 | 新增: +{format_number(author_added)} | 删除: -{format_number(author_deleted)} | 净增: {'+' if author_net >= 0 else ''}{format_number(author_net)}")
            lines.append("")

            for commit in commits:
                time = parse_iso_datetime(commit['date'])
                time_str = time.strftime("%H:%M")
                net = commit['lines_added'] - commit['lines_deleted']

                lines.append(
                    f"- [{commit['repo']}] {time_str} | "
                    f"+{commit['lines_added']}/-{commit['lines_deleted']} ({'+' if net >= 0 else ''}{net}) | "
                    f"{commit['message'][:60]}"
                )

            lines.append("")

        return '\n'.join(lines)

    def _generate_footer(self) -> str:
        """生成报告底部"""
        lines = [
            "---",
            "",
            "**📌 说明**:",
            "- 数据来源: Git 提交历史",
            f"- 统计范围: {self.report_date} 00:00 - 23:59",
            "- 更新频率: 每日自动生成",
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

    # 获取日期参数
    report_date = sys.argv[1] if len(sys.argv) > 1 else None

    # 生成报告
    generator = DailyReportGenerator(config_path, report_date)
    report = generator.generate()

    # 输出到文件
    report_date_str = report_date or datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(project_root, 'reports', 'daily')
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f'{report_date_str}.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 日报已生成: {output_file}")

    # 同时输出到控制台
    print("\n" + "=" * 80 + "\n")
    print(report)


if __name__ == "__main__":
    main()
