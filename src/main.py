"""
Code Health Monitor - 主入口
代码健康监控系统

用法:
    python -m src.main daily      # 生成日报
    python -m src.main weekly     # 生成周报
    python -m src.main monthly    # 生成月报
    python -m src.main notify     # 发送通知
    python -m src.main html       # 生成所有 HTML
    python -m src.main dashboard  # 生成可视化仪表盘
"""

import os
import argparse
from datetime import datetime

from .config import Config
from .providers.generic_git import GenericGitProvider
from .providers.github import GitHubProvider
from .providers.gitlab import GitLabProvider
from .providers.codeup import CodeupProvider
from .reporters import DailyReporter, WeeklyReporter, MonthlyReporter
from .notifiers import DingtalkNotifier, FeishuNotifier
from .utils.html_generator import convert_md_to_html, convert_all_reports
from .utils.index_generator import generate_index
from .utils.dashboard_generator import generate_dashboard


def create_provider(config: Config):
    """
    根据配置创建 Git Provider

    Args:
        config: 配置对象

    Returns:
        GitProvider 实例
    """
    platform = config.git_platform.lower()

    # GitHub API Provider
    if platform == 'github':
        org = config.git_org
        repos = [r.get('name') or r.get('url', '').split('/')[-1].replace('.git', '')
                 for r in config.repositories]
        # 如果配置了完整仓库名 (owner/repo)，直接使用
        if repos and '/' in repos[0]:
            return GitHubProvider(
                token=config.git_token,
                repos=repos,
            )
        return GitHubProvider(
            token=config.git_token,
            org=org,
            repos=[f"{org}/{r}" for r in repos] if org else repos,
        )

    # GitLab API Provider
    if platform == 'gitlab':
        base_url = config.get('git.base_url', 'https://gitlab.com')
        group = config.git_org
        projects = [r.get('name') for r in config.repositories]
        return GitLabProvider(
            token=config.git_token,
            base_url=base_url,
            group=group,
            projects=projects if projects else None,
        )

    # Codeup API Provider
    if platform == 'codeup':
        # 优先从环境变量获取，其次从配置文件
        org_id = os.environ.get('CODEUP_ORG_ID', '') or config.get('git.codeup_org_id', '')
        token = os.environ.get('CODEUP_TOKEN', '') or config.git_token
        project = os.environ.get('CODEUP_PROJECT', '') or config.get('git.codeup_project', '')

        if not org_id:
            print("警告: 未配置 Codeup 企业 ID (CODEUP_ORG_ID 环境变量或 git.codeup_org_id)")
            return None

        if not token:
            print("警告: 未配置云效访问令牌 (CODEUP_TOKEN 环境变量)")
            return None

        # 如果配置了具体仓库列表，使用列表过滤
        # 否则使用 project 参数按命名空间过滤
        repositories = None
        if config.repositories:
            repositories = [{'id': r.get('id'), 'name': r.get('name'), 'type': r.get('type')}
                           for r in config.repositories]

        return CodeupProvider(
            token=token,
            organization_id=org_id,
            project=project,
            repositories=repositories,
        )

    # 默认: 通用 Git Provider (浅克隆)
    repositories = config.repositories

    if not repositories:
        print("警告: 未配置任何仓库，请在 config.yaml 或环境变量中配置")
        return None

    return GenericGitProvider(
        repositories=repositories,
        token=config.git_token,
        clone_depth=1000,
        auto_cleanup=True
    )


def run_daily(config: Config, date: str = None, output_dir: str = None):
    """
    生成日报

    Args:
        config: 配置对象
        date: 报告日期 (YYYY-MM-DD)
        output_dir: 输出目录
    """
    print(f"{'='*50}")
    print(f"  代码健康日报 - {config.project_name}")
    print(f"{'='*50}")
    print()

    provider = create_provider(config)
    if not provider:
        return

    with provider:
        reporter = DailyReporter(provider, config, date)
        report = reporter.generate()

        # 输出到文件
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            report_date = date or datetime.now().strftime("%Y-%m-%d")
            filepath = os.path.join(output_dir, f"{report_date}.md")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存: {filepath}")

            # 生成 HTML
            convert_md_to_html(filepath)

            # 更新索引
            reports_base = os.path.dirname(output_dir)
            generate_index(reports_base, config.project_name)
            print()

        # 输出到控制台
        print(report)

    print()
    print("✅ 日报生成完成")


def run_weekly(config: Config, week: str = None, output_dir: str = None):
    """
    生成周报

    Args:
        config: 配置对象
        week: 周标识 (YYYY-Wxx 或 YYYY-MM-DD)
        output_dir: 输出目录
    """
    print(f"{'='*50}")
    print(f"  代码健康周报 - {config.project_name}")
    print(f"{'='*50}")
    print()

    provider = create_provider(config)
    if not provider:
        return

    with provider:
        reporter = WeeklyReporter(provider, config, week)
        report = reporter.generate()

        # 输出到文件
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f"{reporter.week_str}.md")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存: {filepath}")

            # 生成 HTML
            convert_md_to_html(filepath)

            # 更新索引
            reports_base = os.path.dirname(output_dir)
            generate_index(reports_base, config.project_name)
            print()

        # 输出到控制台
        print(report)

    print()
    print("✅ 周报生成完成")


def run_monthly(config: Config, month: str = None, output_dir: str = None):
    """
    生成月报

    Args:
        config: 配置对象
        month: 月份标识 (YYYY-MM)
        output_dir: 输出目录
    """
    print(f"{'='*50}")
    print(f"  代码健康月报 - {config.project_name}")
    print(f"{'='*50}")
    print()

    provider = create_provider(config)
    if not provider:
        return

    with provider:
        reporter = MonthlyReporter(provider, config, month)
        report = reporter.generate()

        # 输出到文件
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f"{reporter.month_str}.md")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存: {filepath}")

            # 生成 HTML
            convert_md_to_html(filepath)

            # 更新索引
            reports_base = os.path.dirname(output_dir)
            generate_index(reports_base, config.project_name)
            print()

        # 输出到控制台
        print(report)

    print()
    print("月报生成完成")


def run_notify(config: Config, report_type: str, report_path: str = None,
               date: str = None, week: str = None, month: str = None):
    """
    发送通知

    Args:
        config: 配置对象
        report_type: 报告类型 (daily/weekly/monthly)
        report_path: 报告文件路径 (可选)
        date: 日报日期 (YYYY-MM-DD)
        week: 周报周标识 (YYYY-Wxx)
        month: 月报月份 (YYYY-MM)
    """
    print(f"{'='*50}")
    print(f"  发送通知 - {config.project_name}")
    print(f"{'='*50}")
    print()

    # 确定报告文件路径
    if not report_path:
        base_dir = os.environ.get('CODE_HEALTH_OUTPUT', 'reports')
        if report_type == 'daily':
            date_str = date or datetime.now().strftime("%Y-%m-%d")
            report_path = os.path.join(base_dir, 'daily', f"{date_str}.md")
        elif report_type == 'weekly':
            week_str = week or datetime.now().strftime("%Y-W%V")
            report_path = os.path.join(base_dir, 'weekly', f"{week_str}.md")
        elif report_type == 'monthly':
            month_str = month or datetime.now().strftime("%Y-%m")
            report_path = os.path.join(base_dir, 'monthly', f"{month_str}.md")

    # 读取报告内容
    if not os.path.exists(report_path):
        print(f"报告文件不存在: {report_path}")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()

    print(f"报告文件: {report_path}")
    print()

    # 初始化通知器
    notifiers = []

    dingtalk = DingtalkNotifier(config)
    if dingtalk.is_enabled():
        notifiers.append(('钉钉', dingtalk))

    feishu = FeishuNotifier(config)
    if feishu.is_enabled():
        notifiers.append(('飞书', feishu))

    if not notifiers:
        print("未配置任何通知渠道")
        return

    # 发送通知
    for name, notifier in notifiers:
        print(f"发送到 {name}...")
        if report_type == 'daily':
            date_str = date or datetime.now().strftime("%Y-%m-%d")
            success = notifier.send_daily_report(date_str, report_content)
        elif report_type == 'weekly':
            week_str = week or datetime.now().strftime("%Y-W%V")
            success = notifier.send_weekly_report(week_str, report_content)
        elif report_type == 'monthly':
            month_str = month or datetime.now().strftime("%Y-%m")
            success = notifier.send_monthly_report(month_str, report_content)

        if success:
            print(f"  {name} 发送成功")
        else:
            print(f"  {name} 发送失败")

    print()
    print("通知发送完成")


def run_html(config: Config, output_dir: str = None):
    """
    生成所有 HTML 文件

    Args:
        config: 配置对象
        output_dir: 报告目录
    """
    print(f"{'='*50}")
    print(f"  生成 HTML - {config.project_name}")
    print(f"{'='*50}")
    print()

    reports_dir = output_dir or os.environ.get('CODE_HEALTH_OUTPUT', 'reports')

    # 转换所有 Markdown 报告为 HTML
    result = convert_all_reports(reports_dir)
    print(f"转换完成: 成功 {result['success']} 个, 失败 {result['failed']} 个")

    # 生成索引页面
    generate_index(reports_dir, config.project_name)

    print()
    print("✅ HTML 生成完成")


def run_dashboard(config: Config, output_dir: str = None, reports_dir: str = None,
                 days: int = None):
    """
    生成可视化仪表盘

    Args:
        config: 配置对象
        output_dir: 仪表盘输出目录
        reports_dir: 报告目录（用于查找最新报告链接）
        days: 生成指定天数的仪表盘（默认生成所有预设范围）
    """
    print(f"{'='*50}")
    print(f"  生成仪表盘 - {config.project_name}")
    print(f"{'='*50}")
    print()

    provider = create_provider(config)
    if not provider:
        return

    dashboard_dir = output_dir or os.path.join(
        os.environ.get('CODE_HEALTH_OUTPUT', 'reports'),
        '../dashboard'
    )
    reports_base = reports_dir or os.environ.get('CODE_HEALTH_OUTPUT', 'reports')

    print(f"📊 正在生成仪表盘...")

    with provider:
        if days:
            # 只生成指定天数
            files = generate_dashboard(
                provider, dashboard_dir, reports_base,
                days=days, generate_all_ranges=False
            )
        else:
            # 生成所有预设时间范围
            files = generate_dashboard(
                provider, dashboard_dir, reports_base,
                generate_all_ranges=True
            )

    print()
    print(f"✅ 仪表盘生成完成，共 {len(files)} 个文件")
    for f in files:
        print(f"   - {os.path.basename(f)}")


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description='Code Health Monitor - 代码健康监控系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.main daily                    # 生成今天的日报
  python -m src.main daily --date 2025-01-10  # 生成指定日期的日报
  python -m src.main weekly                   # 生成上周的周报
  python -m src.main weekly --week 2025-W02   # 生成指定周的周报
  python -m src.main monthly                  # 生成上月的月报
  python -m src.main monthly --month 2024-12  # 生成指定月的月报
  python -m src.main notify daily             # 发送日报通知
  python -m src.main html                     # 生成所有 HTML 文件
  python -m src.main dashboard                # 生成可视化仪表盘
  python -m src.main dashboard --days 30      # 只生成最近30天仪表盘
"""
    )

    parser.add_argument(
        'command',
        choices=['daily', 'weekly', 'monthly', 'notify', 'html', 'dashboard'],
        help='命令: daily(日报), weekly(周报), monthly(月报), notify(通知), html(生成HTML), dashboard(仪表盘)'
    )
    parser.add_argument(
        'subcommand',
        nargs='?',
        choices=['daily', 'weekly', 'monthly'],
        help='通知类型 (仅用于 notify 命令)'
    )
    parser.add_argument(
        '--config', '-c',
        help='配置文件路径',
        default=None
    )
    parser.add_argument(
        '--output', '-o',
        help='报告输出目录',
        default=None
    )
    parser.add_argument(
        '--date',
        help='日报日期 (YYYY-MM-DD)',
        default=None
    )
    parser.add_argument(
        '--week',
        help='周报周期 (YYYY-Wxx 或 YYYY-MM-DD)',
        default=None
    )
    parser.add_argument(
        '--month',
        help='月报月份 (YYYY-MM)',
        default=None
    )
    parser.add_argument(
        '--report-file',
        help='报告文件路径 (用于 notify 命令)',
        default=None
    )
    parser.add_argument(
        '--days',
        type=int,
        help='仪表盘天数 (用于 dashboard 命令)',
        default=None
    )

    args = parser.parse_args()

    # 加载配置
    config = Config(args.config)

    # 确定输出目录
    output_dir = args.output
    if output_dir is None and os.environ.get('CODE_HEALTH_OUTPUT'):
        output_dir = os.environ.get('CODE_HEALTH_OUTPUT')

    # 执行对应命令
    if args.command == 'daily':
        daily_output = os.path.join(output_dir, 'daily') if output_dir else None
        run_daily(config, args.date, daily_output)
    elif args.command == 'weekly':
        weekly_output = os.path.join(output_dir, 'weekly') if output_dir else None
        run_weekly(config, args.week, weekly_output)
    elif args.command == 'monthly':
        monthly_output = os.path.join(output_dir, 'monthly') if output_dir else None
        run_monthly(config, args.month, monthly_output)
    elif args.command == 'notify':
        if not args.subcommand:
            print("错误: notify 命令需要指定报告类型 (daily/weekly/monthly)")
            print("示例: python -m src.main notify daily")
            return
        run_notify(
            config,
            report_type=args.subcommand,
            report_path=args.report_file,
            date=args.date,
            week=args.week,
            month=args.month
        )
    elif args.command == 'html':
        run_html(config, output_dir)
    elif args.command == 'dashboard':
        dashboard_output = os.path.join(output_dir, '../dashboard') if output_dir else None
        run_dashboard(config, dashboard_output, output_dir, args.days)


if __name__ == '__main__':
    main()
