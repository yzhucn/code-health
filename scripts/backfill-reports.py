#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - 历史数据补全工具
Author: DevOps Team
Created: 2025-12-30

功能：
1. 自动检测最早提交日期
2. 批量生成历史日报
3. 批量生成历史周报
4. 显示进度和统计

Usage:
    python backfill-reports.py [options]

Examples:
    python backfill-reports.py                    # 补全所有历史数据
    python backfill-reports.py --daily-only       # 只补全日报
    python backfill-reports.py --weekly-only      # 只补全周报
    python backfill-reports.py --from 2025-12-01  # 从指定日期开始
    python backfill-reports.py --dry-run          # 只显示计划，不实际生成
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils import GitAnalyzer, load_config


class BackfillReports:
    """历史报告补全工具"""

    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.analyzers = self._init_analyzers()
        self.earliest_date = None
        self.latest_date = datetime.now()

    def _init_analyzers(self) -> list:
        """初始化所有仓库的分析器"""
        analyzers = []
        for repo in self.config['repositories']:
            if os.path.exists(repo['path']):
                git_analyzer = GitAnalyzer(repo['path'])
                analyzers.append({
                    'name': repo['name'],
                    'path': repo['path'],
                    'git': git_analyzer
                })
        return analyzers

    def find_earliest_commit(self) -> datetime:
        """查找最早的提交日期"""
        print("🔍 正在检测最早的提交日期...")

        earliest = None
        for analyzer in self.analyzers:
            try:
                # 获取该仓库最早的提交
                cmd = ["git", "-C", analyzer['path'], "log", "--all", "--reverse",
                       "--pretty=format:%ad", "--date=short"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                if result.stdout:
                    first_line = result.stdout.split('\n')[0]
                    repo_earliest = datetime.strptime(first_line, '%Y-%m-%d')

                    if earliest is None or repo_earliest < earliest:
                        earliest = repo_earliest

                    print(f"  - {analyzer['name']}: {first_line}")
            except Exception as e:
                print(f"  - {analyzer['name']}: 无法获取 ({e})")

        return earliest

    def generate_date_range(self, start_date: datetime, end_date: datetime) -> list:
        """生成日期范围列表"""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def generate_week_range(self, start_date: datetime, end_date: datetime) -> list:
        """生成周期范围列表"""
        weeks = set()

        # 确保从周一开始
        current = start_date - timedelta(days=start_date.weekday())

        while current <= end_date:
            iso = current.isocalendar()
            week_str = f"{iso[0]}-W{iso[1]:02d}"
            weeks.add(week_str)
            current += timedelta(days=7)

        return sorted(list(weeks))

    def backfill_daily(self, dates: list, dry_run: bool = False):
        """批量生成日报"""
        print(f"\n📅 准备生成 {len(dates)} 个日报...")

        if dry_run:
            print("  （干运行模式：不会实际生成文件）")
            for i, date in enumerate(dates[:5], 1):
                print(f"  {i}. {date.strftime('%Y-%m-%d')}")
            if len(dates) > 5:
                print(f"  ... 还有 {len(dates) - 5} 个日期")
            return

        success_count = 0
        skip_count = 0
        fail_count = 0

        for i, date in enumerate(dates, 1):
            date_str = date.strftime('%Y-%m-%d')

            # 检查文件是否已存在
            output_file = os.path.join(
                os.path.dirname(script_dir),
                'reports', 'daily', f'{date_str}.md'
            )

            if os.path.exists(output_file):
                print(f"  [{i}/{len(dates)}] ⏭️  {date_str} (已存在)")
                skip_count += 1
                continue

            # 生成日报
            try:
                cmd = ["python3", "daily-report.py", date_str]
                result = subprocess.run(
                    cmd,
                    cwd=script_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    print(f"  [{i}/{len(dates)}] ✅ {date_str}")
                    success_count += 1
                else:
                    print(f"  [{i}/{len(dates)}] ❌ {date_str} (错误)")
                    fail_count += 1
            except Exception as e:
                print(f"  [{i}/{len(dates)}] ❌ {date_str} ({e})")
                fail_count += 1

        print(f"\n✅ 日报生成完成:")
        print(f"  - 成功: {success_count}")
        print(f"  - 跳过: {skip_count}")
        print(f"  - 失败: {fail_count}")

    def backfill_weekly(self, weeks: list, dry_run: bool = False):
        """批量生成周报"""
        print(f"\n📈 准备生成 {len(weeks)} 个周报...")

        if dry_run:
            print("  （干运行模式：不会实际生成文件）")
            for i, week in enumerate(weeks[:5], 1):
                print(f"  {i}. {week}")
            if len(weeks) > 5:
                print(f"  ... 还有 {len(weeks) - 5} 个周期")
            return

        success_count = 0
        skip_count = 0
        fail_count = 0

        for i, week in enumerate(weeks, 1):
            # 检查文件是否已存在
            output_file = os.path.join(
                os.path.dirname(script_dir),
                'reports', 'weekly', f'{week}.md'
            )

            if os.path.exists(output_file):
                print(f"  [{i}/{len(weeks)}] ⏭️  {week} (已存在)")
                skip_count += 1
                continue

            # 生成周报
            try:
                cmd = ["python3", "weekly-report.py", week]
                result = subprocess.run(
                    cmd,
                    cwd=script_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    print(f"  [{i}/{len(weeks)}] ✅ {week}")
                    success_count += 1
                else:
                    print(f"  [{i}/{len(weeks)}] ❌ {week} (错误)")
                    fail_count += 1
            except Exception as e:
                print(f"  [{i}/{len(weeks)}] ❌ {week} ({e})")
                fail_count += 1

        print(f"\n✅ 周报生成完成:")
        print(f"  - 成功: {success_count}")
        print(f"  - 跳过: {skip_count}")
        print(f"  - 失败: {fail_count}")

    def run(self, start_date=None, daily_only=False, weekly_only=False, dry_run=False, yes=False):
        """执行历史数据补全"""
        print("=" * 70)
        print("🚀 代码健康监控 - 历史数据补全")
        print("=" * 70)

        # 确定起始日期
        if start_date:
            self.earliest_date = datetime.strptime(start_date, '%Y-%m-%d')
            print(f"\n📅 使用指定起始日期: {start_date}")
        else:
            self.earliest_date = self.find_earliest_commit()
            if self.earliest_date:
                print(f"\n📅 检测到最早提交日期: {self.earliest_date.strftime('%Y-%m-%d')}")
            else:
                print("\n❌ 无法检测到提交历史")
                return

        print(f"📅 结束日期: {self.latest_date.strftime('%Y-%m-%d')}")

        days_count = (self.latest_date - self.earliest_date).days + 1
        print(f"📊 总天数: {days_count} 天")

        # 生成日期和周期列表
        dates = self.generate_date_range(self.earliest_date, self.latest_date)
        weeks = self.generate_week_range(self.earliest_date, self.latest_date)

        print(f"📊 将生成:")
        if not weekly_only:
            print(f"  - 日报: {len(dates)} 个")
        if not daily_only:
            print(f"  - 周报: {len(weeks)} 个")

        # 确认
        if not dry_run and not yes:
            print("\n⚠️  这将需要一些时间...")
            response = input("是否继续? (y/N): ")
            if response.lower() != 'y':
                print("已取消")
                return

        # 生成报告
        if not weekly_only:
            self.backfill_daily(dates, dry_run)

        if not daily_only:
            self.backfill_weekly(weeks, dry_run)

        print("\n" + "=" * 70)
        print("🎉 历史数据补全完成！")
        print("=" * 70)

        if not dry_run:
            print("\n📂 报告位置:")
            print(f"  - 日报: .code-health/reports/daily/")
            print(f"  - 周报: .code-health/reports/weekly/")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='代码健康监控 - 历史数据补全工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--from',
        dest='start_date',
        help='起始日期 (YYYY-MM-DD)，默认自动检测'
    )

    parser.add_argument(
        '--daily-only',
        action='store_true',
        help='只生成日报'
    )

    parser.add_argument(
        '--weekly-only',
        action='store_true',
        help='只生成周报'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式，只显示计划不实际生成'
    )

    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='自动确认，不询问'
    )

    args = parser.parse_args()

    # 获取配置文件路径
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'config.yaml')

    # 执行补全
    backfill = BackfillReports(config_path)
    backfill.run(
        start_date=args.start_date,
        daily_only=args.daily_only,
        weekly_only=args.weekly_only,
        dry_run=args.dry_run,
        yes=args.yes
    )


if __name__ == "__main__":
    main()
