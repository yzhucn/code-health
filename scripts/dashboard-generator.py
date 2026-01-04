#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - 可视化仪表盘生成器
Author: DevOps Team
Created: 2025-12-30

Usage:
    python dashboard-generator.py [days]

Examples:
    python dashboard-generator.py           # 生成最近7天的仪表盘
    python dashboard-generator.py 30        # 生成最近30天的仪表盘
"""

import os
import sys
import json
from datetime import datetime, timedelta
from collections import defaultdict

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils import GitAnalyzer, load_config, format_number


class DashboardGenerator:
    """仪表盘生成器"""

    def __init__(self, config_path: str, days: int = 7):
        self.config = load_config(config_path)
        self.days = days
        self.analyzers = self._init_analyzers()
        self.data = self._collect_data()

    def _init_analyzers(self) -> list:
        """初始化所有仓库的分析器"""
        analyzers = []
        for repo in self.config['repositories']:
            if os.path.exists(repo['path']):
                git_analyzer = GitAnalyzer(repo['path'])
                analyzers.append({
                    'name': repo['name'],
                    'type': repo['type'],
                    'git': git_analyzer
                })
        return analyzers

    def _collect_data(self) -> dict:
        """收集历史数据"""
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
        end_date = datetime.now()
        for i in range(self.days - 1, -1, -1):
            date = end_date - timedelta(days=i)
            data['dates'].append(date.strftime('%Y-%m-%d'))

        # 收集所有提交
        for analyzer in self.analyzers:
            commits = analyzer['git'].get_commits(f"{self.days} days ago")

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
                    repo = analyzer['name']
                    data['repos'][repo]['commits'] += 1
                    data['repos'][repo]['added'] += commit['lines_added']
                    data['repos'][repo]['deleted'] += commit['lines_deleted']

                    # 时间分布
                    data['time_distribution'][hour] += 1

                    # 保存完整提交
                    data['all_commits'].append({
                        **commit,
                        'repo': analyzer['name'],
                        'date_str': date_str,
                        'hour': hour
                    })

                except Exception as e:
                    print(f"Error processing commit: {e}")

        return data

    def generate_html(self) -> str:
        """生成HTML仪表盘"""
        # 准备图表数据
        commits_trend_data = [self.data['commits_by_date'].get(date, 0) for date in self.data['dates']]
        lines_added_data = [self.data['lines_by_date'][date]['added'] for date in self.data['dates']]
        lines_deleted_data = [self.data['lines_by_date'][date]['deleted'] for date in self.data['dates']]

        # 开发者贡献（TOP 10）
        top_authors = sorted(
            self.data['authors'].items(),
            key=lambda x: x[1]['added'] - x[1]['deleted'],
            reverse=True
        )[:10]

        author_names = [author for author, _ in top_authors]
        author_commits = [stats['commits'] for _, stats in top_authors]
        author_lines = [stats['added'] - stats['deleted'] for _, stats in top_authors]

        # 仓库分布
        repo_names = list(self.data['repos'].keys())
        repo_commits = [stats['commits'] for stats in self.data['repos'].values()]

        # 时间分布（24小时）
        hours = list(range(24))
        hour_commits = [self.data['time_distribution'].get(hour, 0) for hour in hours]

        # 计算健康分数（简化版）
        health_scores = []
        for date in self.data['dates']:
            # 简化的健康分计算：基于提交量和代码质量
            commits = self.data['commits_by_date'].get(date, 0)
            added = self.data['lines_by_date'][date]['added']
            deleted = self.data['lines_by_date'][date]['deleted']

            # 基础分
            score = 80.0

            # 根据提交量调整
            if commits == 0:
                score = 70.0
            elif commits > 20:
                score -= 5.0  # 提交过多可能是震荡

            # 根据返工率调整（简化）
            if added > 0:
                rework_rate = (deleted / added * 100)
                if rework_rate > 50:
                    score -= 15.0
                elif rework_rate > 30:
                    score -= 10.0

            health_scores.append(max(0, min(100, score)))

        # 准备日期选择器数据
        all_dates_json = json.dumps(self.data['dates'])

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
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
        }}

        .date-selector {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}

        .date-selector label {{
            font-weight: 500;
        }}

        .date-selector select {{
            padding: 8px 12px;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            background: white;
        }}

        .date-selector select:hover {{
            background: #f8f9fa;
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
                <div>
                    统计周期: 最近 {self.days} 天 |
                    生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                <div class="date-selector">
                    <label>显示天数:</label>
                    <select id="daysSelector" onchange="changeDays()">
                        <option value="7" {'selected' if self.days == 7 else ''}>最近7天</option>
                        <option value="14" {'selected' if self.days == 14 else ''}>最近14天</option>
                        <option value="30" {'selected' if self.days == 30 else ''}>最近30天</option>
                        <option value="60" {'selected' if self.days == 60 else ''}>最近60天</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">总提交数</div>
                <div class="value">{len(self.data['all_commits'])}</div>
                <div class="trend">📈 最近 {self.days} 天</div>
            </div>
            <div class="stat-card">
                <div class="label">活跃开发者</div>
                <div class="value">{len(self.data['authors'])}</div>
                <div class="trend">👥 参与贡献</div>
            </div>
            <div class="stat-card">
                <div class="label">代码净增</div>
                <div class="value">{format_number(sum(s['added'] - s['deleted'] for s in self.data['authors'].values()))}</div>
                <div class="trend">💻 行</div>
            </div>
            <div class="stat-card">
                <div class="label">平均健康分</div>
                <div class="value">{sum(health_scores) / len(health_scores) if health_scores else 0:.0f}</div>
                <div class="trend">🟢 优秀</div>
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
            <a href="#" onclick="location.reload()">刷新数据</a>
        </div>
    </div>

    <script>
        // 健康分数趋势
        const healthChart = echarts.init(document.getElementById('healthChart'));
        healthChart.setOption({{
            title: {{
                text: '最近 {self.days} 天健康分数走势',
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
                data: {json.dumps(self.data['dates'])},
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
                data: {json.dumps(self.data['dates'])},
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
                data: {json.dumps(self.data['dates'])},
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

        // 日期选择器功能
        function changeDays() {{
            const days = document.getElementById('daysSelector').value;
            // 根据选择的天数跳转到相应的仪表盘
            if (days === '30') {{
                window.location.href = 'index.html';
            }} else {{
                window.location.href = 'index-' + days + 'd.html';
            }}
        }}
    </script>
</body>
</html>
'''
        return html

    def save_dashboard(self, output_path: str):
        """保存仪表盘到文件"""
        html = self.generate_html()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


def main():
    """主函数"""
    # 获取配置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'config.yaml')

    # 获取天数参数
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7

    # 生成仪表盘
    print(f"📊 正在生成最近 {days} 天的仪表盘...")
    generator = DashboardGenerator(config_path, days)

    # 保存HTML
    output_dir = os.path.join(project_root, 'dashboard')
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'index.html')
    generator.save_dashboard(output_file)

    print(f"✅ 仪表盘已生成: {output_file}")
    print(f"\n在浏览器中打开:")
    print(f"  file://{output_file}")
    print(f"\n或运行: open {output_file}")


if __name__ == "__main__":
    main()
