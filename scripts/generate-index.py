#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成报告中心索引页面
动态扫描所有日报和周报，按月份分组显示
"""

import os
import glob
from datetime import datetime
from collections import defaultdict

def generate_index():
    """生成报告中心索引页面"""

    # 获取报告目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(os.path.dirname(script_dir), 'reports')
    daily_dir = os.path.join(reports_dir, 'daily')
    weekly_dir = os.path.join(reports_dir, 'weekly')

    # 获取所有日报（动态扫描所有年月）
    daily_files = glob.glob(os.path.join(daily_dir, '*.md'))
    daily_by_month = defaultdict(list)  # 按月份分组

    for f in sorted(daily_files, reverse=True):  # 按日期倒序
        filename = os.path.basename(f)
        if filename.startswith('example'):  # 跳过示例文件
            continue
        date_str = filename.replace('.md', '')
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            year_month = date_str[:7]  # 2026-01
            daily_by_month[year_month].append(date_str)
        except ValueError:
            continue

    # 获取所有周报
    weekly_files = glob.glob(os.path.join(weekly_dir, '*.md'))
    weekly_reports = []
    for f in sorted(weekly_files, reverse=True):
        filename = os.path.basename(f)
        if filename.startswith('example'):
            continue
        week_str = filename.replace('.md', '')
        weekly_reports.append(week_str)

    total_daily = sum(len(dates) for dates in daily_by_month.values())
    total_weekly = len(weekly_reports)

    # 生成周报链接HTML
    weekly_links_html = ""
    for week in weekly_reports:
        weekly_links_html += f'<a href="/reports/weekly/{week}.html" class="report-link week-link">📑 {week}</a>\n'

    # 生成日报区块HTML（按月份分组）
    daily_sections_html = ""
    for year_month in sorted(daily_by_month.keys(), reverse=True):
        dates = sorted(daily_by_month[year_month], reverse=True)
        year, month = year_month.split('-')
        month_name = f"{year}年{int(month)}月"

        daily_links = ""
        for date_str in dates:
            display = date_str[5:]  # MM-DD
            daily_links += f'<a href="/reports/daily/{date_str}.html" class="report-link">{display}</a>\n'

        daily_sections_html += f'''
        <div class="section">
            <h2>📆 日报 ({month_name}，共{len(dates)}天)</h2>
            <div class="report-grid">
                {daily_links}
            </div>
        </div>
'''

    # 获取统计周期
    all_months = sorted(daily_by_month.keys())
    if all_months:
        period = f"{all_months[0]} 至 {all_months[-1]}"
    else:
        period = "暂无数据"

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码健康监控 - 报告中心</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{ color: #333; font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ color: #666; font-size: 14px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card .label {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
        .stat-card .value {{ color: #667eea; font-size: 32px; font-weight: bold; }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #333;
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .report-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
        }}
        .report-link {{
            display: block;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            text-decoration: none;
            color: #333;
            text-align: center;
            transition: all 0.2s;
        }}
        .report-link:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }}
        .week-link {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: bold;
        }}
        .week-link:hover {{
            transform: scale(1.05);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
        }}
        .dashboard-btn {{
            display: inline-block;
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
            margin-top: 10px;
        }}
        .dashboard-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
        }}
        .footer {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 代码健康监控 - 报告中心</h1>
            <div class="meta">统计周期: {period} | 系统: 代码健康监控平台</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">日报总数</div>
                <div class="value">{total_daily}</div>
            </div>
            <div class="stat-card">
                <div class="label">周报总数</div>
                <div class="value">{total_weekly}</div>
            </div>
            <div class="stat-card">
                <div class="label">统计月份</div>
                <div class="value">{len(daily_by_month)}</div>
            </div>
        </div>

        <div class="section">
            <h2>📈 可视化仪表盘</h2>
            <p style="margin-bottom: 15px; color: #666;">查看代码健康趋势、提交量分析、开发者贡献等可视化数据</p>
            <a href="/dashboard/index.html" class="dashboard-btn">🎯 打开可视化仪表盘</a>
        </div>

        <div class="section">
            <h2>📅 周报 (共{total_weekly}周)</h2>
            <div class="report-grid">
                {weekly_links_html}
            </div>
        </div>

        {daily_sections_html}

        <div class="footer">
            由代码健康监控系统自动生成 | 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</body>
</html>'''

    # 保存index.html
    index_file = os.path.join(reports_dir, 'index.html')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 索引页面已生成: {index_file}")
    print(f"   包含 {total_daily} 天的日报, {total_weekly} 周的周报")


if __name__ == "__main__":
    generate_index()
