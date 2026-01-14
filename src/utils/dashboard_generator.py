"""
Dashboard 生成器 - 生成可视化仪表盘
移植自 V1 scripts/dashboard-generator-range.py
"""

import os
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from .helpers import parse_iso_datetime, format_number


def generate_redirect_html(target_url: str, days: int, project_days: int) -> str:
    """生成重定向页面HTML

    当请求的天数超过项目实际天数时，重定向到全周期页面
    """
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={target_url}">
    <title>重定向中...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }}
        .message {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .message h2 {{ color: #333; margin-bottom: 15px; }}
        .message p {{ color: #666; margin-bottom: 20px; }}
        .message a {{ color: #667eea; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="message">
        <h2>正在跳转...</h2>
        <p>项目运行仅 {project_days} 天，不足 {days} 天</p>
        <p>正在跳转到 <a href="{target_url}">项目全周期仪表盘</a></p>
    </div>
</body>
</html>'''


def get_date_range(start_date_str=None, end_date_str=None, days=None):
    """获取日期范围

    Args:
        start_date_str: 起始日期 YYYY-MM-DD
        end_date_str: 结束日期 YYYY-MM-DD
        days: 最近N天（如果start_date和end_date未指定）

    Returns:
        (start_datetime, end_datetime, days_count)
    """
    if start_date_str and end_date_str:
        start = datetime.strptime(start_date_str, '%Y-%m-%d')
        end = datetime.strptime(end_date_str, '%Y-%m-%d')
        days_count = (end - start).days + 1
        return start, end, days_count
    elif days:
        end = datetime.now()
        start = end - timedelta(days=days - 1)
        return start, end, days
    else:
        end = datetime.now()
        start = end - timedelta(days=6)
        return start, end, 7


def collect_dashboard_data(provider, start_date, end_date):
    """收集仪表盘数据

    Args:
        provider: Git Provider 实例
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        统计数据字典
    """
    data = {
        'dates': [],
        'commits_by_date': defaultdict(int),
        'lines_by_date': defaultdict(lambda: {'added': 0, 'deleted': 0}),
        'authors': defaultdict(lambda: {'commits': 0, 'added': 0, 'deleted': 0}),
        'repos': defaultdict(lambda: {'commits': 0, 'added': 0, 'deleted': 0}),
        'time_distribution': defaultdict(int),
        'all_commits': []
    }

    # 生成日期列表
    current_date = start_date
    while current_date <= end_date:
        data['dates'].append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    # 收集提交数据
    since_time = start_date.strftime('%Y-%m-%d 00:00:00')
    until_time = (end_date + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')

    # 获取所有仓库并收集提交
    all_commits = []
    repos = provider.list_repositories()
    for repo in repos:
        repo_commits = provider.get_commits(repo.id, since_time, until_time)
        # 将 CommitInfo 对象转换为 dict 并添加仓库名称
        for commit in repo_commits:
            commit_dict = {
                'hash': commit.hash,
                'author': commit.author,
                'email': commit.email,
                'date': commit.date,
                'message': commit.message,
                'lines_added': commit.lines_added,
                'lines_deleted': commit.lines_deleted,
                'repo': repo.name
            }
            all_commits.append(commit_dict)

    for commit in all_commits:
        try:
            commit_date = parse_iso_datetime(commit['date'])
            date_str = commit_date.strftime('%Y-%m-%d')
            hour = commit_date.hour

            # 按日期统计
            data['commits_by_date'][date_str] += 1
            data['lines_by_date'][date_str]['added'] += commit.get('lines_added', 0)
            data['lines_by_date'][date_str]['deleted'] += commit.get('lines_deleted', 0)

            # 按作者统计
            author = commit['author']
            data['authors'][author]['commits'] += 1
            data['authors'][author]['added'] += commit.get('lines_added', 0)
            data['authors'][author]['deleted'] += commit.get('lines_deleted', 0)

            # 按仓库统计
            repo_name = commit.get('repo', 'unknown')
            data['repos'][repo_name]['commits'] += 1
            data['repos'][repo_name]['added'] += commit.get('lines_added', 0)
            data['repos'][repo_name]['deleted'] += commit.get('lines_deleted', 0)

            # 时间分布
            data['time_distribution'][hour] += 1

            # 保存完整提交
            data['all_commits'].append({
                **commit,
                'date_str': date_str,
                'hour': hour
            })
        except Exception as e:
            print(f"处理提交时出错: {e}")

    return data


def generate_dashboard_html(data, start_date, end_date, days_count,
                           project_start_date=None, project_days=None,
                           output_filename=None, reports_dir=None):
    """生成仪表盘HTML

    Args:
        data: 统计数据
        start_date: 统计开始日期
        end_date: 统计结束日期
        days_count: 统计天数
        project_start_date: 项目最早提交日期
        project_days: 项目运行总天数
        output_filename: 输出文件名
        reports_dir: 报告目录路径
    """
    # 提取数据
    commits_trend_data = [data['commits_by_date'].get(date, 0) for date in data['dates']]
    lines_added_data = [data['lines_by_date'][date]['added'] for date in data['dates']]
    lines_deleted_data = [data['lines_by_date'][date]['deleted'] for date in data['dates']]

    # 开发者贡献（TOP 10）
    top_authors = sorted(
        data['authors'].items(),
        key=lambda x: x[1]['added'] - x[1]['deleted'],
        reverse=True
    )[:10]

    author_names = [author for author, _ in top_authors]
    author_commits = [stats['commits'] for _, stats in top_authors]
    author_lines = [stats['added'] - stats['deleted'] for _, stats in top_authors]

    # 仓库分布
    repo_names = list(data['repos'].keys())
    repo_commits = [stats['commits'] for stats in data['repos'].values()]

    # 时间分布（24小时）
    hours = list(range(24))
    hour_commits = [data['time_distribution'].get(hour, 0) for hour in hours]

    # 计算健康分数
    health_scores = []
    for date in data['dates']:
        commits = data['commits_by_date'].get(date, 0)
        added = data['lines_by_date'][date]['added']
        deleted = data['lines_by_date'][date]['deleted']

        score = 80.0
        if commits == 0:
            score = 70.0
        elif commits > 20:
            score -= 5.0

        if added > 0:
            rework_rate = (deleted / added * 100)
            if rework_rate > 50:
                score -= 15.0
            elif rework_rate > 30:
                score -= 10.0

        health_scores.append(max(0, min(100, score)))

    date_range_str = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

    # 构建时间范围选项
    range_options = []
    range_options.append({
        'value': '/reports/index.html',
        'label': '🏠 返回报告中心',
        'selected': False
    })

    preset_ranges = [7, 14, 30, 60, 90]
    for days in preset_ranges:
        url = 'index.html' if days == 7 else f'index-{days}d.html'
        is_current = (output_filename == url) if output_filename else False

        if project_days and days > project_days:
            label = f'最近{days}天 (实际{project_days}天)'
        else:
            label = f'最近{days}天'

        range_options.append({
            'value': url,
            'label': label,
            'selected': is_current
        })

    if project_days and project_start_date:
        is_all = (project_days == days_count and
                  start_date.date() == project_start_date)
        range_options.append({
            'value': 'index-all.html',
            'label': f'📅 项目全周期 (自{project_start_date.strftime("%m/%d")}起，{project_days}天)',
            'selected': is_all
        })

    select_options_html = ""
    for opt in range_options:
        selected_attr = 'selected' if opt['selected'] else ''
        select_options_html += f'<option value="{opt["value"]}" {selected_attr}>{opt["label"]}</option>\n'

    # 查找最新报告
    daily_link = '<span class="report-btn daily disabled">📅 暂无日报</span>'
    weekly_link = '<span class="report-btn weekly disabled">📊 暂无周报</span>'
    monthly_link = '<span class="report-btn monthly disabled">📈 暂无月报</span>'

    if reports_dir:
        reports_path = Path(reports_dir)

        # 最新日报
        daily_files = sorted([f for f in (reports_path / 'daily').glob('*.html')
                             if not f.name.startswith('example')])
        if daily_files:
            latest_daily = daily_files[-1].stem
            daily_link = f'<a href="/reports/daily/{latest_daily}.html" class="report-btn daily">📅 最新日报 ({latest_daily})</a>'

        # 最新周报
        weekly_files = sorted([f for f in (reports_path / 'weekly').glob('*.html')
                              if not f.name.startswith('example')])
        if weekly_files:
            latest_weekly = weekly_files[-1].stem
            weekly_link = f'<a href="/reports/weekly/{latest_weekly}.html" class="report-btn weekly">📊 最新周报 ({latest_weekly})</a>'

        # 最新月报
        monthly_files = sorted([f for f in (reports_path / 'monthly').glob('*.html')
                               if not f.name.startswith('example')])
        if monthly_files:
            latest_monthly = monthly_files[-1].stem
            monthly_link = f'<a href="/reports/monthly/{latest_monthly}.html" class="report-btn monthly">📈 最新月报 ({latest_monthly})</a>'

    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码健康监控仪表盘</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px; min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: white; border-radius: 12px; padding: 30px;
            margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{ color: #333; font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ color: #666; font-size: 14px; margin-top: 15px; }}
        .date-selector {{
            margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 8px;
        }}
        .date-selector h3 {{ color: #333; font-size: 16px; margin-bottom: 15px; }}
        .date-selector select {{
            width: 100%; max-width: 400px; padding: 12px 16px; font-size: 15px;
            border: 2px solid #667eea; border-radius: 8px; background: white;
            color: #333; cursor: pointer; transition: all 0.2s;
        }}
        .date-selector select:hover {{ border-color: #5568d3; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2); }}
        .date-selector select:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }}
        .stats-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 20px;
        }}
        .stat-card {{
            background: white; border-radius: 12px; padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-card .label {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
        .stat-card .value {{ color: #333; font-size: 32px; font-weight: bold; }}
        .stat-card .trend {{ color: #10b981; font-size: 12px; margin-top: 8px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
        .chart-card {{
            background: white; border-radius: 12px; padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .chart-card.full-width {{ grid-column: 1 / -1; }}
        .chart-card h2 {{
            color: #333; font-size: 18px; margin-bottom: 15px;
            padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;
        }}
        .chart-container {{ width: 100%; height: 350px; }}
        .chart-container.large {{ height: 450px; }}
        .quick-access {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 20px; }}
        .quick-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .quick-card h3 {{ color: #333; font-size: 16px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }}
        .report-links, .nav-links {{ display: flex; gap: 10px; flex-wrap: wrap; }}
        .report-btn, .nav-btn {{
            display: inline-block; padding: 12px 20px; border-radius: 8px;
            text-decoration: none; font-weight: bold; transition: all 0.2s;
        }}
        .report-btn.daily {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .report-btn.weekly {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }}
        .report-btn.monthly {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }}
        .nav-btn {{ background: #f8f9fa; color: #333; border: 1px solid #e0e0e0; }}
        .report-btn:hover, .nav-btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .report-btn.disabled, .nav-btn.disabled {{ background: #e5e7eb; color: #9ca3af; cursor: not-allowed; pointer-events: none; }}
        .footer {{
            background: white; border-radius: 12px; padding: 20px; margin-top: 20px;
            text-align: center; color: #666; font-size: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        @media (max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 代码健康监控仪表盘</h1>
            <div class="meta">
                统计周期: {date_range_str} ({days_count}天) |
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            <div class="date-selector">
                <h3>📅 切换时间范围</h3>
                <select onchange="handleRangeChange(this.value)">
                    {select_options_html}
                </select>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">总提交数</div>
                <div class="value">{len(data['all_commits'])}</div>
                <div class="trend">📈 统计周期内</div>
            </div>
            <div class="stat-card">
                <div class="label">活跃开发者</div>
                <div class="value">{len(data['authors'])}</div>
                <div class="trend">👥 参与贡献</div>
            </div>
            <div class="stat-card">
                <div class="label">代码净增</div>
                <div class="value">{format_number(sum(s['added'] - s['deleted'] for s in data['authors'].values()))}</div>
                <div class="trend">💻 行</div>
            </div>
            <div class="stat-card">
                <div class="label">平均健康分</div>
                <div class="value">{sum(health_scores) / len(health_scores) if health_scores else 0:.0f}</div>
                <div class="trend">🟢 优秀</div>
            </div>
        </div>

        <div class="quick-access">
            <div class="quick-card">
                <h3>📄 最新报告</h3>
                <div class="report-links">
                    {daily_link}
                    {weekly_link}
                    {monthly_link}
                </div>
            </div>
            <div class="quick-card">
                <h3>🔗 快速导航</h3>
                <div class="nav-links">
                    <a href="/reports/index.html" class="nav-btn">📋 报告中心</a>
                    <a href="/dashboard/history.html" class="nav-btn">📜 历史查询</a>
                </div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card full-width">
                <h2>健康分数趋势</h2>
                <div id="healthChart" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <h2>提交量趋势</h2>
                <div id="commitsChart" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <h2>代码变更趋势</h2>
                <div id="linesChart" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <h2>开发者提交量 TOP 10</h2>
                <div id="authorCommitsChart" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <h2>开发者代码净增 TOP 10</h2>
                <div id="authorLinesChart" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <h2>仓库提交分布</h2>
                <div id="repoChart" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <h2>提交时间分布（24小时）</h2>
                <div id="timeChart" class="chart-container"></div>
            </div>
        </div>

        <div class="footer">
            由代码健康监控系统自动生成 |
            <a href="/reports/index.html">返回报告中心</a>
        </div>
    </div>

    <script>
        const healthChart = echarts.init(document.getElementById('healthChart'));
        healthChart.setOption({{
            title: {{ text: '健康分数走势', left: 'center', textStyle: {{ fontSize: 14, color: '#666' }} }},
            tooltip: {{ trigger: 'axis', formatter: function(params) {{ return params[0].name + '<br/>健康分: ' + params[0].value.toFixed(0) + ' 分'; }} }},
            xAxis: {{ type: 'category', data: {json.dumps(data['dates'])}, axisLabel: {{ rotate: 45 }} }},
            yAxis: {{ type: 'value', min: 0, max: 100, name: '分数' }},
            series: [{{
                name: '健康分', type: 'line', data: {json.dumps(health_scores)}, smooth: true,
                itemStyle: {{ color: '#10b981' }},
                areaStyle: {{ color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    {{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }},
                    {{ offset: 1, color: 'rgba(16, 185, 129, 0.05)' }}
                ]) }},
                markLine: {{ data: [
                    {{ yAxis: 80, lineStyle: {{ color: '#10b981' }}, label: {{ formatter: '优秀线' }} }},
                    {{ yAxis: 60, lineStyle: {{ color: '#f59e0b' }}, label: {{ formatter: '良好线' }} }},
                    {{ yAxis: 40, lineStyle: {{ color: '#ef4444' }}, label: {{ formatter: '警告线' }} }}
                ] }}
            }}]
        }});

        const commitsChart = echarts.init(document.getElementById('commitsChart'));
        commitsChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: {json.dumps(data['dates'])}, axisLabel: {{ rotate: 45 }} }},
            yAxis: {{ type: 'value', name: '提交数' }},
            series: [{{ name: '提交数', type: 'bar', data: {json.dumps(commits_trend_data)}, itemStyle: {{ color: '#667eea' }} }}]
        }});

        const linesChart = echarts.init(document.getElementById('linesChart'));
        linesChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            legend: {{ data: ['新增', '删除'], bottom: 0 }},
            xAxis: {{ type: 'category', data: {json.dumps(data['dates'])}, axisLabel: {{ rotate: 45 }} }},
            yAxis: {{ type: 'value', name: '行数' }},
            series: [
                {{ name: '新增', type: 'line', data: {json.dumps(lines_added_data)}, itemStyle: {{ color: '#10b981' }}, areaStyle: {{ opacity: 0.3 }} }},
                {{ name: '删除', type: 'line', data: {json.dumps(lines_deleted_data)}, itemStyle: {{ color: '#ef4444' }}, areaStyle: {{ opacity: 0.3 }} }}
            ]
        }});

        const authorCommitsChart = echarts.init(document.getElementById('authorCommitsChart'));
        authorCommitsChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            xAxis: {{ type: 'value', name: '提交数' }},
            yAxis: {{ type: 'category', data: {json.dumps(author_names[::-1])}, axisLabel: {{ interval: 0 }} }},
            series: [{{ name: '提交数', type: 'bar', data: {json.dumps(author_commits[::-1])}, itemStyle: {{ color: '#764ba2' }}, label: {{ show: true, position: 'right' }} }}]
        }});

        const authorLinesChart = echarts.init(document.getElementById('authorLinesChart'));
        authorLinesChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            xAxis: {{ type: 'value', name: '净增行数' }},
            yAxis: {{ type: 'category', data: {json.dumps(author_names[::-1])}, axisLabel: {{ interval: 0 }} }},
            series: [{{ name: '净增行数', type: 'bar', data: {json.dumps(author_lines[::-1])}, itemStyle: {{ color: '#667eea' }}, label: {{ show: true, position: 'right' }} }}]
        }});

        const repoChart = echarts.init(document.getElementById('repoChart'));
        repoChart.setOption({{
            tooltip: {{ trigger: 'item' }},
            legend: {{ bottom: 0, type: 'scroll' }},
            series: [{{
                name: '提交数', type: 'pie', radius: '60%',
                data: {json.dumps([{'name': name, 'value': commits} for name, commits in zip(repo_names, repo_commits)])},
                emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }} }},
                label: {{ formatter: '{{b}}: {{c}} ({{d}}%)' }}
            }}]
        }});

        const timeChart = echarts.init(document.getElementById('timeChart'));
        timeChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            xAxis: {{ type: 'category', data: {json.dumps(hours)}, name: '小时' }},
            yAxis: {{ type: 'value', name: '提交数' }},
            series: [{{
                name: '提交数', type: 'bar', data: {json.dumps(hour_commits)},
                itemStyle: {{ color: function(params) {{
                    const hour = params.dataIndex;
                    if (hour >= 22 || hour < 6) return '#ef4444';
                    if (hour >= 9 && hour < 18) return '#10b981';
                    return '#f59e0b';
                }} }},
                markArea: {{ data: [[{{ xAxis: 9 }}, {{ xAxis: 18 }}]], itemStyle: {{ color: 'rgba(16, 185, 129, 0.1)' }}, label: {{ formatter: '工作时间' }} }}
            }}]
        }});

        window.addEventListener('resize', function() {{
            healthChart.resize(); commitsChart.resize(); linesChart.resize();
            authorCommitsChart.resize(); authorLinesChart.resize();
            repoChart.resize(); timeChart.resize();
        }});

        function handleRangeChange(value) {{ window.location.href = value; }}
    </script>
</body>
</html>'''

    return html


def generate_dashboard(provider, output_dir: str, reports_dir: str = None,
                      days: int = None, start_date: str = None, end_date: str = None,
                      generate_all_ranges: bool = True):
    """生成仪表盘

    Args:
        provider: Git Provider 实例
        output_dir: 输出目录
        reports_dir: 报告目录（用于查找最新报告链接）
        days: 生成指定天数的仪表盘
        start_date: 起始日期
        end_date: 结束日期
        generate_all_ranges: 是否生成所有预设时间范围

    Returns:
        生成的文件列表
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    # 计算项目起始日期（基于第一份日报）
    project_start_date = None
    project_days = None

    if reports_dir:
        reports_path = Path(reports_dir)
        daily_dir = reports_path / 'daily'
        if daily_dir.exists():
            daily_files = sorted([f for f in daily_dir.glob('*.md')
                                 if not f.name.startswith('example')])
            if daily_files:
                first_report = daily_files[0].stem
                try:
                    project_start_date = datetime.strptime(first_report, '%Y-%m-%d').date()
                    project_days = (datetime.now().date() - project_start_date).days + 1
                    print(f"   项目起始日期: {project_start_date} ({project_days}天)")
                except ValueError:
                    pass

    if generate_all_ranges:
        # 生成多个时间范围的仪表盘
        ranges_to_generate = [
            (7, 'index.html'),
            (14, 'index-14d.html'),
            (30, 'index-30d.html'),
            (60, 'index-60d.html'),
            (90, 'index-90d.html'),
        ]

        for range_days, filename in ranges_to_generate:
            print(f"   生成 {filename} ({range_days}天)...")

            # 对于60/90天，如果项目天数不足，生成重定向页面
            if range_days >= 60 and project_days and project_days < range_days:
                print(f"   → 项目仅 {project_days} 天，重定向到全周期页面")
                html = generate_redirect_html('index-all.html', range_days, project_days)
                output_file = os.path.join(output_dir, filename)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                generated_files.append(output_file)
                continue

            # 计算实际日期范围（考虑项目起始日期）
            range_start, range_end, actual_days = get_date_range(days=range_days)

            if project_start_date and range_start.date() < project_start_date:
                range_start = datetime.combine(project_start_date, datetime.min.time())
                actual_days = (range_end.date() - range_start.date()).days + 1

            # 收集数据并生成HTML
            data = collect_dashboard_data(provider, range_start, range_end)
            html = generate_dashboard_html(
                data, range_start, range_end, actual_days,
                project_start_date, project_days, filename, reports_dir
            )

            output_file = os.path.join(output_dir, filename)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            generated_files.append(output_file)
            print(f"   ✓ {filename}: {len(data['all_commits'])} 提交, {len(data['authors'])} 开发者")

        # 生成全周期仪表盘
        if project_start_date:
            print(f"   生成 index-all.html (全周期)...")
            range_start = datetime.combine(project_start_date, datetime.min.time())
            range_end = datetime.now()
            actual_days = (range_end.date() - range_start.date()).days + 1

            data = collect_dashboard_data(provider, range_start, range_end)
            html = generate_dashboard_html(
                data, range_start, range_end, actual_days,
                project_start_date, project_days, 'index-all.html', reports_dir
            )

            output_file = os.path.join(output_dir, 'index-all.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            generated_files.append(output_file)
            print(f"   ✓ index-all.html: {len(data['all_commits'])} 提交")

    elif days:
        # 只生成指定天数
        filename = 'index.html' if days == 7 else f'index-{days}d.html'
        range_start, range_end, actual_days = get_date_range(days=days)

        if project_start_date and range_start.date() < project_start_date:
            range_start = datetime.combine(project_start_date, datetime.min.time())
            actual_days = (range_end.date() - range_start.date()).days + 1

        data = collect_dashboard_data(provider, range_start, range_end)
        html = generate_dashboard_html(
            data, range_start, range_end, actual_days,
            project_start_date, project_days, filename, reports_dir
        )

        output_file = os.path.join(output_dir, filename)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        generated_files.append(output_file)

    elif start_date and end_date:
        # 指定日期范围
        range_start, range_end, actual_days = get_date_range(start_date, end_date)
        filename = f'index-{start_date}-to-{end_date}.html'

        data = collect_dashboard_data(provider, range_start, range_end)
        html = generate_dashboard_html(
            data, range_start, range_end, actual_days,
            project_start_date, project_days, filename, reports_dir
        )

        output_file = os.path.join(output_dir, filename)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        generated_files.append(output_file)

    return generated_files
