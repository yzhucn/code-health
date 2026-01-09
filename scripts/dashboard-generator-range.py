#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - 可视化仪表盘生成器（日期范围版本）
支持指定起止日期生成仪表盘
"""

import os
import sys
import json
import glob
from datetime import datetime, timedelta
from collections import defaultdict

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils import GitAnalyzer, load_config, format_number, parse_iso_datetime


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
        # 指定了起止日期
        start = datetime.strptime(start_date_str, '%Y-%m-%d')
        end = datetime.strptime(end_date_str, '%Y-%m-%d')
        days_count = (end - start).days + 1
        return start, end, days_count
    elif days:
        # 最近N天
        end = datetime.now()
        start = end - timedelta(days=days - 1)
        return start, end, days
    else:
        # 默认最近30天
        end = datetime.now()
        start = end - timedelta(days=29)
        return start, end, 30


def generate_dashboard_html(data, start_date, end_date, days_count, project_start_date=None, project_days=None):
    """生成仪表盘HTML

    Args:
        data: 统计数据
        start_date: 统计开始日期
        end_date: 统计结束日期
        days_count: 统计天数
        project_start_date: 项目最早提交日期
        project_days: 项目运行总天数
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

    # 添加返回报告中心选项
    range_options.append({
        'value': '/reports/index.html',
        'label': '🏠 返回报告中心',
        'selected': False
    })

    # 预设时间范围（始终显示所有选项）
    preset_ranges = [7, 14, 30, 60, 90]
    for days in preset_ranges:
        is_current = (days_count == days)
        url = 'index.html' if days == 7 else f'index-{days}d.html'
        range_options.append({
            'value': url,
            'label': f'最近{days}天',
            'selected': is_current
        })

    # 添加项目全周期选项
    if project_days and project_start_date:
        # 判断是否是全周期（从第一份日报到今天）
        is_all = (project_days == days_count and
                  start_date.date() == project_start_date)
        range_options.append({
            'value': 'index-all.html',
            'label': f'📅 项目全周期 (自{project_start_date.strftime("%m/%d")}起，{project_days}天)',
            'selected': is_all
        })

    # 生成下拉菜单选项HTML
    select_options_html = ""
    for opt in range_options:
        selected_attr = 'selected' if opt['selected'] else ''
        select_options_html += f'<option value="{opt["value"]}" {selected_attr}>{opt["label"]}</option>\n'

    # 动态查找最新的报告文件
    reports_dir = os.path.join(os.path.dirname(script_dir), 'reports')

    # 查找最新日报
    daily_files = glob.glob(os.path.join(reports_dir, 'daily', '*.html'))
    daily_files = [f for f in daily_files if not os.path.basename(f).startswith('example')]
    if daily_files:
        latest_daily = os.path.basename(sorted(daily_files)[-1]).replace('.html', '')
    else:
        latest_daily = None

    # 查找最新周报
    weekly_files = glob.glob(os.path.join(reports_dir, 'weekly', '*.html'))
    weekly_files = [f for f in weekly_files if not os.path.basename(f).startswith('example')]
    if weekly_files:
        latest_weekly = os.path.basename(sorted(weekly_files)[-1]).replace('.html', '')
    else:
        latest_weekly = None

    # 查找最新月报
    monthly_files = glob.glob(os.path.join(reports_dir, 'monthly', '*.html'))
    monthly_files = [f for f in monthly_files if not os.path.basename(f).startswith('example')]
    if monthly_files:
        latest_monthly = os.path.basename(sorted(monthly_files)[-1]).replace('.html', '')
    else:
        latest_monthly = None

    # 生成报告链接 HTML
    if latest_daily:
        daily_link = f'<a href="/reports/daily/{latest_daily}.html" class="report-btn daily">📅 最新日报 ({latest_daily})</a>'
    else:
        daily_link = '<span class="report-btn daily disabled">📅 暂无日报</span>'

    if latest_weekly:
        weekly_link = f'<a href="/reports/weekly/{latest_weekly}.html" class="report-btn weekly">📊 最新周报 ({latest_weekly})</a>'
    else:
        weekly_link = '<span class="report-btn weekly disabled">📊 暂无周报</span>'

    if latest_monthly:
        monthly_link = f'<a href="/reports/monthly/{latest_monthly}.html" class="report-btn monthly">📈 最新月报 ({latest_monthly})</a>'
    else:
        monthly_link = '<span class="report-btn monthly disabled">📈 暂无月报</span>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码健康监控仪表盘</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header .meta {{
            color: #666;
            font-size: 14px;
            margin-top: 15px;
        }}

        .date-selector {{
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}

        .date-selector h3 {{
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
        }}

        .date-selector select {{
            width: 100%;
            max-width: 400px;
            padding: 12px 16px;
            font-size: 15px;
            border: 2px solid #667eea;
            border-radius: 8px;
            background: white;
            color: #333;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .date-selector select:hover {{
            border-color: #5568d3;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }}

        .date-selector select:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card .label {{
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }}

        .stat-card .value {{
            color: #333;
            font-size: 32px;
            font-weight: bold;
        }}

        .stat-card .trend {{
            color: #10b981;
            font-size: 12px;
            margin-top: 8px;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}

        .chart-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .chart-card.full-width {{
            grid-column: 1 / -1;
        }}

        .chart-card h2 {{
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .chart-container {{
            width: 100%;
            height: 350px;
        }}

        .chart-container.large {{
            height: 450px;
        }}

        .quick-access {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }}

        .quick-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .quick-card h3 {{
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .report-links, .nav-links {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .report-btn, .nav-btn {{
            display: inline-block;
            padding: 12px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.2s;
        }}

        .report-btn.daily {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .report-btn.weekly {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}

        .report-btn.monthly {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}

        .nav-btn {{
            background: #f8f9fa;
            color: #333;
            border: 1px solid #e0e0e0;
        }}

        .report-btn:hover, .nav-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        .report-btn.disabled, .nav-btn.disabled {{
            background: #e5e7eb;
            color: #9ca3af;
            cursor: not-allowed;
            pointer-events: none;
        }}

        .footer {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>📊 代码健康监控仪表盘</h1>
            <div class="meta">
                统计周期: {date_range_str} ({days_count}天) |
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>

            <!-- 时间范围切换 -->
            <div class="date-selector">
                <h3>📅 切换时间范围</h3>
                <select onchange="handleRangeChange(this.value)">
                    {select_options_html}
                </select>
            </div>
        </div>

        <!-- 统计卡片 -->
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

        <!-- 快速入口区域 -->
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
                </div>
            </div>
        </div>

        <!-- 图表区域 -->
        <div class="charts-grid">
            <!-- 健康分数趋势 -->
            <div class="chart-card full-width">
                <h2>健康分数趋势</h2>
                <div id="healthChart" class="chart-container"></div>
            </div>

            <!-- 提交量趋势 -->
            <div class="chart-card">
                <h2>提交量趋势</h2>
                <div id="commitsChart" class="chart-container"></div>
            </div>

            <!-- 代码变更趋势 -->
            <div class="chart-card">
                <h2>代码变更趋势</h2>
                <div id="linesChart" class="chart-container"></div>
            </div>

            <!-- 开发者贡献对比 -->
            <div class="chart-card">
                <h2>开发者提交量 TOP 10</h2>
                <div id="authorCommitsChart" class="chart-container"></div>
            </div>

            <!-- 开发者代码贡献 -->
            <div class="chart-card">
                <h2>开发者代码净增 TOP 10</h2>
                <div id="authorLinesChart" class="chart-container"></div>
            </div>

            <!-- 仓库分布 -->
            <div class="chart-card">
                <h2>仓库提交分布</h2>
                <div id="repoChart" class="chart-container"></div>
            </div>

            <!-- 时间分布热力图 -->
            <div class="chart-card">
                <h2>提交时间分布（24小时）</h2>
                <div id="timeChart" class="chart-container"></div>
            </div>
        </div>

        <!-- 底部 -->
        <div class="footer">
            由代码健康监控系统自动生成 |
            <a href="/reports/index.html">返回报告中心</a>
        </div>
    </div>

    <script>
        // 健康分数趋势
        const healthChart = echarts.init(document.getElementById('healthChart'));
        healthChart.setOption({{
            title: {{
                text: '健康分数走势',
                left: 'center',
                textStyle: {{ fontSize: 14, color: '#666' }}
            }},
            tooltip: {{
                trigger: 'axis',
                formatter: function(params) {{
                    return params[0].name + '<br/>' +
                           '健康分: ' + params[0].value.toFixed(0) + ' 分';
                }}
            }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(data['dates'])},
                axisLabel: {{ rotate: 45 }}
            }},
            yAxis: {{
                type: 'value',
                min: 0,
                max: 100,
                name: '分数'
            }},
            series: [{{
                name: '健康分',
                type: 'line',
                data: {json.dumps(health_scores)},
                smooth: true,
                itemStyle: {{ color: '#10b981' }},
                areaStyle: {{
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }},
                        {{ offset: 1, color: 'rgba(16, 185, 129, 0.05)' }}
                    ])
                }},
                markLine: {{
                    data: [
                        {{ yAxis: 80, lineStyle: {{ color: '#10b981' }}, label: {{ formatter: '优秀线' }} }},
                        {{ yAxis: 60, lineStyle: {{ color: '#f59e0b' }}, label: {{ formatter: '良好线' }} }},
                        {{ yAxis: 40, lineStyle: {{ color: '#ef4444' }}, label: {{ formatter: '警告线' }} }}
                    ]
                }}
            }}]
        }});

        // 提交量趋势
        const commitsChart = echarts.init(document.getElementById('commitsChart'));
        commitsChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(data['dates'])},
                axisLabel: {{ rotate: 45 }}
            }},
            yAxis: {{ type: 'value', name: '提交数' }},
            series: [{{
                name: '提交数',
                type: 'bar',
                data: {json.dumps(commits_trend_data)},
                itemStyle: {{ color: '#667eea' }}
            }}]
        }});

        // 代码变更趋势
        const linesChart = echarts.init(document.getElementById('linesChart'));
        linesChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            legend: {{ data: ['新增', '删除'], bottom: 0 }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(data['dates'])},
                axisLabel: {{ rotate: 45 }}
            }},
            yAxis: {{ type: 'value', name: '行数' }},
            series: [
                {{
                    name: '新增',
                    type: 'line',
                    data: {json.dumps(lines_added_data)},
                    itemStyle: {{ color: '#10b981' }},
                    areaStyle: {{ opacity: 0.3 }}
                }},
                {{
                    name: '删除',
                    type: 'line',
                    data: {json.dumps(lines_deleted_data)},
                    itemStyle: {{ color: '#ef4444' }},
                    areaStyle: {{ opacity: 0.3 }}
                }}
            ]
        }});

        // 开发者提交量
        const authorCommitsChart = echarts.init(document.getElementById('authorCommitsChart'));
        authorCommitsChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            xAxis: {{ type: 'value', name: '提交数' }},
            yAxis: {{
                type: 'category',
                data: {json.dumps(author_names[::-1])},
                axisLabel: {{ interval: 0 }}
            }},
            series: [{{
                name: '提交数',
                type: 'bar',
                data: {json.dumps(author_commits[::-1])},
                itemStyle: {{ color: '#764ba2' }},
                label: {{ show: true, position: 'right' }}
            }}]
        }});

        // 开发者代码贡献
        const authorLinesChart = echarts.init(document.getElementById('authorLinesChart'));
        authorLinesChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            xAxis: {{ type: 'value', name: '净增行数' }},
            yAxis: {{
                type: 'category',
                data: {json.dumps(author_names[::-1])},
                axisLabel: {{ interval: 0 }}
            }},
            series: [{{
                name: '净增行数',
                type: 'bar',
                data: {json.dumps(author_lines[::-1])},
                itemStyle: {{ color: '#667eea' }},
                label: {{ show: true, position: 'right' }}
            }}]
        }});

        // 仓库分布饼图
        const repoChart = echarts.init(document.getElementById('repoChart'));
        repoChart.setOption({{
            tooltip: {{ trigger: 'item' }},
            legend: {{ bottom: 0, type: 'scroll' }},
            series: [{{
                name: '提交数',
                type: 'pie',
                radius: '60%',
                data: {json.dumps([{'name': name, 'value': commits} for name, commits in zip(repo_names, repo_commits)])},
                emphasis: {{
                    itemStyle: {{
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }}
                }},
                label: {{ formatter: '{{b}}: {{c}} ({{d}}%)' }}
            }}]
        }});

        // 时间分布热力图
        const timeChart = echarts.init(document.getElementById('timeChart'));
        timeChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(hours)},
                name: '小时'
            }},
            yAxis: {{ type: 'value', name: '提交数' }},
            series: [{{
                name: '提交数',
                type: 'bar',
                data: {json.dumps(hour_commits)},
                itemStyle: {{
                    color: function(params) {{
                        const hour = params.dataIndex;
                        if (hour >= 22 || hour < 6) return '#ef4444';  // 深夜
                        if (hour >= 9 && hour < 18) return '#10b981';  // 正常工作时间
                        return '#f59e0b';  // 其他时间
                    }}
                }},
                markArea: {{
                    data: [
                        [{{ xAxis: 9 }}, {{ xAxis: 18 }}],  // 正常工作时间
                    ],
                    itemStyle: {{ color: 'rgba(16, 185, 129, 0.1)' }},
                    label: {{ formatter: '工作时间' }}
                }}
            }}]
        }});

        // 响应式调整
        window.addEventListener('resize', function() {{
            healthChart.resize();
            commitsChart.resize();
            linesChart.resize();
            authorCommitsChart.resize();
            authorLinesChart.resize();
            repoChart.resize();
            timeChart.resize();
        }});

        // 时间范围切换功能
        function handleRangeChange(value) {{
            window.location.href = value;
        }}
    </script>
</body>
</html>'''

    return html


def main():
    """主函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'config.yaml')

    # 解析参数
    if len(sys.argv) >= 3:
        # 指定起止日期模式
        start_date_str = sys.argv[1]
        end_date_str = sys.argv[2]
        start_date, end_date, days_count = get_date_range(start_date_str, end_date_str)
        output_filename = f"index-{start_date_str}-to-{end_date_str}.html"
    elif len(sys.argv) >= 2:
        param = sys.argv[1]
        if param == 'all':
            # 项目全周期模式：从第一份日报到今天
            reports_dir = os.path.join(project_root, 'reports', 'daily')
            daily_files = sorted([f for f in glob.glob(os.path.join(reports_dir, '*.md'))
                                 if not os.path.basename(f).startswith('example')])
            if daily_files:
                first_report_date = os.path.basename(daily_files[0]).replace('.md', '')
                start_date = datetime.strptime(first_report_date, '%Y-%m-%d')
                end_date = datetime.now()
                days_count = (end_date.date() - start_date.date()).days + 1
                output_filename = "index-all.html"
            else:
                print("⚠️  未找到日报，无法生成全周期dashboard")
                return
        else:
            # 最近N天模式
            days = int(param)
            start_date, end_date, days_count = get_date_range(days=days)
            output_filename = f"index.html" if days == 7 else f"index-{days}d.html"
    else:
        # 默认最近7天
        start_date, end_date, days_count = get_date_range(days=7)
        output_filename = "index.html"

    print(f"📊 正在生成仪表盘...")
    print(f"   起始日期: {start_date.strftime('%Y-%m-%d')}")
    print(f"   结束日期: {end_date.strftime('%Y-%m-%d')}")
    print(f"   统计天数: {days_count}天")

    # 加载配置
    config = load_config(config_path)

    # 收集数据
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

    # 计算项目最早日期和运行天数（基于第一份日报）
    project_start_date = None
    project_days = None
    print(f"📅 正在计算项目运行天数...")

    # 查找第一份日报的日期
    reports_dir = os.path.join(os.path.dirname(script_dir), 'reports', 'daily')
    if os.path.exists(reports_dir):
        daily_files = sorted([f for f in glob.glob(os.path.join(reports_dir, '*.md'))
                             if not os.path.basename(f).startswith('example')])
        if daily_files:
            first_report = os.path.basename(daily_files[0]).replace('.md', '')
            try:
                project_start_date = datetime.strptime(first_report, '%Y-%m-%d').date()
                project_days = (datetime.now().date() - project_start_date).days + 1
                print(f"   第一份日报: {project_start_date}")
                print(f"   项目运行天数: {project_days}天（基于日报）")
            except ValueError:
                print(f"   ⚠️  无法解析日报日期: {first_report}")

    if not project_start_date:
        print(f"   ⚠️  未找到日报，使用默认值")

    # 收集所有仓库的提交（当前时间范围）
    since_time = start_date.strftime('%Y-%m-%d 00:00:00')
    until_time = (end_date + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')

    for repo in config['repositories']:
        if not os.path.exists(repo['path']):
            continue

        git_analyzer = GitAnalyzer(repo['path'])
        commits = git_analyzer.get_commits(since_time, until_time, branch="all")

        for commit in commits:
            try:
                commit_date = parse_iso_datetime(commit['date'])
                date_str = commit_date.strftime('%Y-%m-%d')
                hour = commit_date.hour

                # 按日期统计
                data['commits_by_date'][date_str] += 1
                data['lines_by_date'][date_str]['added'] += commit['lines_added']
                data['lines_by_date'][date_str]['deleted'] += commit['lines_deleted']

                # 按作者统计
                author = commit['author']
                data['authors'][author]['commits'] += 1
                data['authors'][author]['added'] += commit['lines_added']
                data['authors'][author]['deleted'] += commit['lines_deleted']

                # 按仓库统计
                data['repos'][repo['name']]['commits'] += 1
                data['repos'][repo['name']]['added'] += commit['lines_added']
                data['repos'][repo['name']]['deleted'] += commit['lines_deleted']

                # 时间分布
                data['time_distribution'][hour] += 1

                # 保存完整提交
                data['all_commits'].append({
                    **commit,
                    'repo': repo['name'],
                    'date_str': date_str,
                    'hour': hour
                })
            except Exception as e:
                print(f"Error processing commit: {e}")

    # 生成HTML
    html = generate_dashboard_html(data, start_date, end_date, days_count, project_start_date, project_days)

    # 保存文件
    output_dir = os.path.join(project_root, 'dashboard')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, output_filename)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 仪表盘已生成: {output_file}")
    print(f"   总提交数: {len(data['all_commits'])}")
    print(f"   活跃开发者: {len(data['authors'])}")


if __name__ == "__main__":
    main()
