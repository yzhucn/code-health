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
    monthly_dir = os.path.join(reports_dir, 'monthly')

    # 确定当前年月和上月
    now = datetime.now()
    current_year_month = now.strftime('%Y-%m')  # 2026-01
    if now.month == 1:
        last_month_year = now.year - 1
        last_month = 12
    else:
        last_month_year = now.year
        last_month = now.month - 1
    last_year_month = f"{last_month_year}-{last_month:02d}"  # 2025-12

    # 获取当月日报
    daily_files = glob.glob(os.path.join(daily_dir, '*.md'))
    current_month_daily = []

    for f in sorted(daily_files, reverse=True):  # 按日期倒序
        filename = os.path.basename(f)
        if filename.startswith('example'):  # 跳过示例文件
            continue
        date_str = filename.replace('.md', '')
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            year_month = date_str[:7]  # 2026-01
            if year_month == current_year_month:
                current_month_daily.append(date_str)
        except ValueError:
            continue

    # 获取当月周报（当年的所有周报）
    weekly_files = glob.glob(os.path.join(weekly_dir, '*.md'))
    current_year_weekly = []
    for f in sorted(weekly_files, reverse=True):
        filename = os.path.basename(f)
        if filename.startswith('example'):
            continue
        week_str = filename.replace('.md', '')
        # 只显示当年的周报
        if week_str.startswith(str(now.year)):
            current_year_weekly.append(week_str)

    # 获取上月月报
    last_month_report = None
    monthly_file = os.path.join(monthly_dir, f"{last_year_month}.md")
    if os.path.exists(monthly_file):
        last_month_report = last_year_month

    total_daily = len(current_month_daily)
    total_weekly = len(current_year_weekly)

    # 生成周报链接HTML
    weekly_links_html = ""
    for week in current_year_weekly:
        weekly_links_html += f'<a href="/reports/weekly/{week}.html" class="report-link week-link">📑 {week}</a>\n'

    # 生成当月日报HTML
    year, month = current_year_month.split('-')
    month_name = f"{year}年{int(month)}月"

    daily_links = ""
    for date_str in current_month_daily:
        display = date_str[5:]  # MM-DD
        daily_links += f'<a href="/reports/daily/{date_str}.html" class="report-link">{display}</a>\n'

    # 生成上月月报HTML
    monthly_section_html = ""
    if last_month_report:
        last_year, last_mon = last_year_month.split('-')
        last_month_name = f"{last_year}年{int(last_mon)}月"
        monthly_section_html = f'''
        <div class="section">
            <h2>📊 月报 ({last_month_name})</h2>
            <div class="report-grid">
                <a href="/reports/monthly/{last_year_month}.html" class="report-link month-link">📄 {last_year_month} 月报</a>
            </div>
        </div>
'''

    # 获取统计周期
    period = f"{current_year_month} (当月)"

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
        .month-link {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            font-weight: bold;
        }}
        .month-link:hover {{
            transform: scale(1.05);
            box-shadow: 0 6px 12px rgba(245, 87, 108, 0.4);
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
                <div class="label">当月日报</div>
                <div class="value">{total_daily}</div>
            </div>
            <div class="stat-card">
                <div class="label">本年周报</div>
                <div class="value">{total_weekly}</div>
            </div>
            <div class="stat-card">
                <div class="label">统计月份</div>
                <div class="value">{month_name}</div>
            </div>
        </div>

        <div class="section">
            <h2>📈 可视化仪表盘</h2>
            <p style="margin-bottom: 15px; color: #666;">查看代码健康趋势、提交量分析、开发者贡献等可视化数据</p>
            <a href="/dashboard/index.html" class="dashboard-btn">🎯 打开可视化仪表盘</a>
            <a href="/dashboard/history.html" class="dashboard-btn" style="margin-left: 10px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">📚 查看历史报告</a>
        </div>

        {monthly_section_html}

        <div class="section">
            <h2>📅 周报 ({year}年，共{total_weekly}周)</h2>
            <div class="report-grid">
                {weekly_links_html}
            </div>
        </div>

        <div class="section">
            <h2>📆 日报 ({month_name}，共{total_daily}天)</h2>
            <div class="report-grid">
                {daily_links}
            </div>
        </div>

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
