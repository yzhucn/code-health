"""
报告索引生成器 - 生成报告中心首页
移植自 V1 scripts/generate-index.py
"""

import os
import glob
from datetime import datetime
from pathlib import Path


def generate_index(reports_dir: str, project_name: str = "代码健康监控") -> str:
    """生成报告中心索引页面

    Args:
        reports_dir: 报告目录路径
        project_name: 项目名称

    Returns:
        生成的索引文件路径
    """
    reports_path = Path(reports_dir)
    daily_dir = reports_path / 'daily'
    weekly_dir = reports_path / 'weekly'
    monthly_dir = reports_path / 'monthly'

    now = datetime.now()
    current_year_month = now.strftime('%Y-%m')

    # 上月
    if now.month == 1:
        last_year_month = f"{now.year - 1}-12"
    else:
        last_year_month = f"{now.year}-{now.month - 1:02d}"

    # 获取当月日报
    current_month_daily = []
    for f in sorted(daily_dir.glob('*.html'), reverse=True):
        if f.name.startswith('example'):
            continue
        date_str = f.stem
        if date_str[:7] == current_year_month:
            current_month_daily.append(date_str)

    # 获取当年周报
    current_year_weekly = []
    for f in sorted(weekly_dir.glob('*.html'), reverse=True):
        if f.name.startswith('example'):
            continue
        week_str = f.stem
        if week_str.startswith(str(now.year)):
            current_year_weekly.append(week_str)

    # 获取上月月报
    last_month_report = None
    if (monthly_dir / f"{last_year_month}.html").exists():
        last_month_report = last_year_month

    total_daily = len(current_month_daily)
    total_weekly = len(current_year_weekly)

    # 生成周报链接
    weekly_links = "\n".join([
        f'<a href="/reports/weekly/{w}.html" class="report-link week-link">📑 {w}</a>'
        for w in current_year_weekly
    ])

    # 生成日报链接
    daily_links = "\n".join([
        f'<a href="/reports/daily/{d}.html" class="report-link">{d[5:]}</a>'
        for d in current_month_daily
    ])

    # 月报部分
    year, month = current_year_month.split('-')
    month_name = f"{year}年{int(month)}月"

    monthly_section = ""
    if last_month_report:
        ly, lm = last_year_month.split('-')
        monthly_section = f'''
        <div class="section">
            <h2>📊 月报 ({ly}年{int(lm)}月)</h2>
            <div class="report-grid">
                <a href="/reports/monthly/{last_year_month}.html" class="report-link month-link">📄 {last_year_month} 月报</a>
            </div>
        </div>'''

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - 报告中心</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px; min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: white; border-radius: 12px; padding: 30px;
            margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{ color: #333; font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ color: #666; font-size: 14px; }}
        .stats-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px; margin-bottom: 20px;
        }}
        .stat-card {{
            background: white; border-radius: 12px; padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;
        }}
        .stat-card .label {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
        .stat-card .value {{ color: #667eea; font-size: 32px; font-weight: bold; }}
        .section {{
            background: white; border-radius: 12px; padding: 30px;
            margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #333; font-size: 20px; margin-bottom: 20px;
            padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;
        }}
        .report-grid {{
            display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px;
        }}
        .report-link {{
            display: block; padding: 12px; background: #f8f9fa; border-radius: 8px;
            text-decoration: none; color: #333; text-align: center; transition: all 0.2s;
        }}
        .report-link:hover {{
            background: #667eea; color: white; transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }}
        .week-link {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; font-weight: bold;
        }}
        .week-link:hover {{ transform: scale(1.05); box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4); }}
        .month-link {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white; font-weight: bold;
        }}
        .month-link:hover {{ transform: scale(1.05); box-shadow: 0 6px 12px rgba(245, 87, 108, 0.4); }}
        .dashboard-btn {{
            display: inline-block; padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; text-decoration: none; border-radius: 8px;
            font-size: 16px; font-weight: bold; transition: all 0.3s; margin-top: 10px;
        }}
        .dashboard-btn:hover {{ transform: translateY(-3px); box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4); }}
        .footer {{
            background: white; border-radius: 12px; padding: 20px;
            text-align: center; color: #666; font-size: 14px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {project_name} - 报告中心</h1>
            <div class="meta">统计周期: {current_year_month} (当月) | 系统: {project_name}</div>
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

        {monthly_section}

        <div class="section">
            <h2>📅 周报 ({year}年，共{total_weekly}周)</h2>
            <div class="report-grid">
                {weekly_links}
            </div>
        </div>

        <div class="section">
            <h2>📆 日报 ({month_name}，共{total_daily}天)</h2>
            <div class="report-grid">
                {daily_links}
            </div>
        </div>

        <div class="footer">
            由代码健康监控系统自动生成 | 更新时间: {now.strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</body>
</html>'''

    index_file = reports_path / 'index.html'
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"索引页面已生成: {index_file}")
    print(f"  包含 {total_daily} 天日报, {total_weekly} 周周报")

    return str(index_file)
