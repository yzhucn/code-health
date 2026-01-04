#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成报告中心索引页面
"""

import os
import glob

def generate_index():
    """生成报告中心索引页面"""

    # 获取报告目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(os.path.dirname(script_dir), 'reports')
    daily_dir = os.path.join(reports_dir, 'daily')

    # 获取所有日报的日期
    daily_files = glob.glob(os.path.join(daily_dir, '2025-12-*.md'))
    valid_dates = []
    for f in sorted(daily_files):
        date_str = os.path.basename(f).replace('.md', '')
        day = date_str.split('-')[2]
        valid_dates.append((date_str, day))

    # 生成日报链接HTML
    daily_links = []
    for date_str, day in valid_dates:
        daily_links.append(f'<a href="/reports/daily/{date_str}.html" class="report-link">{date_str[5:]}</a>')

    daily_links_html = '\n                '.join(daily_links)

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码健康监控 - 报告中心</title>
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
            max-width: 1200px;
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
        }}

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

        .stat-card .label {{
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }}

        .stat-card .value {{
            color: #667eea;
            font-size: 32px;
            font-weight: bold;
        }}

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
            border: 2px solid transparent;
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
        <!-- 头部 -->
        <div class="header">
            <h1>📊 代码健康监控 - 报告中心</h1>
            <div class="meta">
                统计周期: 2025年12月 | 系统: 代码健康监控平台
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">日报总数</div>
                <div class="value">{len(valid_dates)}</div>
            </div>
            <div class="stat-card">
                <div class="label">周报总数</div>
                <div class="value">4</div>
            </div>
            <div class="stat-card">
                <div class="label">统计周数</div>
                <div class="value">4</div>
            </div>
            <div class="stat-card">
                <div class="label">活跃仓库</div>
                <div class="value">9</div>
            </div>
        </div>

        <!-- 可视化仪表盘 -->
        <div class="section">
            <h2>📈 可视化仪表盘</h2>
            <p style="margin-bottom: 15px; color: #666;">查看最近30天的代码健康趋势、提交量分析、开发者贡献等可视化数据。支持选择不同的时间范围（7天/14天/30天/60天）</p>
            <a href="/dashboard/index.html" class="dashboard-btn">🎯 打开可视化仪表盘</a>
        </div>

        <!-- 周报 -->
        <div class="section">
            <h2>📅 周报 (共4周)</h2>
            <div class="report-grid">
                <a href="/reports/weekly/2025-W49.html" class="report-link week-link">📑 第49周<br><small>12-01 至 12-07</small></a>
                <a href="/reports/weekly/2025-W50.html" class="report-link week-link">📑 第50周<br><small>12-08 至 12-14</small></a>
                <a href="/reports/weekly/2025-W51.html" class="report-link week-link">📑 第51周<br><small>12-15 至 12-21</small></a>
                <a href="/reports/weekly/2025-W52.html" class="report-link week-link">📑 第52周<br><small>12-22 至 12-28</small></a>
            </div>
        </div>

        <!-- 日报 -->
        <div class="section">
            <h2>📆 日报 (12月，共{len(valid_dates)}天有提交)</h2>
            <p style="margin-bottom: 15px; color: #999; font-size: 13px;">已自动过滤无提交日期</p>
            <div class="report-grid">
                {daily_links_html}
            </div>
        </div>

        <!-- 底部 -->
        <div class="footer">
            由代码健康监控系统自动生成 |
            <a href="#" onclick="location.reload()">刷新页面</a>
        </div>
    </div>
</body>
</html>'''

    # 保存index.html
    index_file = os.path.join(reports_dir, 'index.html')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 索引页面已生成: {index_file}")
    print(f"   包含 {len(valid_dates)} 天的日报")


if __name__ == "__main__":
    generate_index()
