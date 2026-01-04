#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML converter
Simple converter for code health reports
"""

import re


def markdown_to_html(md_content: str, title: str = "代码健康报告") -> str:
    """将Markdown内容转换为HTML"""

    # 先提取并保护代码块，避免被后续处理影响
    code_blocks = []
    def extract_code_block(match):
        code = match.group(1).strip()
        # 转义HTML字符但保留换行
        code = code.replace('<', '&lt;').replace('>', '&gt;')

        # 给热力图方块字符添加颜色（使用span标签包裹）
        # 实心方块 █ 用深色，空心方块 ░ 用浅色
        code = code.replace('█', '<span style="color: #667eea; font-weight: bold;">█</span>')
        code = code.replace('░', '<span style="color: #c7d2fe;">░</span>')

        placeholder = f'___CODE_BLOCK_{len(code_blocks)}___'
        code_blocks.append(f'<pre><code>{code}</code></pre>')
        return placeholder

    html_content = re.sub(r'```(.*?)```', extract_code_block, md_content, flags=re.DOTALL)

    # 转换标题
    html_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html_content, flags=re.MULTILINE)

    # 转换粗体
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)

    # 转换行内代码
    html_content = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_content)

    # 转换链接
    html_content = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html_content)

    # 转换水平线
    html_content = re.sub(r'^---$', r'<hr>', html_content, flags=re.MULTILINE)

    # 转换表格
    lines = html_content.split('\n')
    in_table = False
    result_lines = []

    for i, line in enumerate(lines):
        if '|' in line and not in_table:
            # 表格开始
            in_table = True
            result_lines.append('<div class="table-wrapper"><table>')
            # 处理表头
            cells = [c.strip() for c in line.split('|') if c.strip()]
            result_lines.append('<thead><tr>')
            for cell in cells:
                result_lines.append(f'<th>{cell}</th>')
            result_lines.append('</tr></thead>')
            result_lines.append('<tbody>')
        elif '|' in line and in_table:
            # 检查是否是分隔行
            if re.match(r'^\|[\s\-:|]+\|$', line):
                continue
            # 表格数据行
            cells = [c.strip() for c in line.split('|') if c.strip()]
            result_lines.append('<tr>')
            for cell in cells:
                result_lines.append(f'<td>{cell}</td>')
            result_lines.append('</tr>')
        elif in_table and '|' not in line:
            # 表格结束
            in_table = False
            result_lines.append('</tbody></table></div>')
            result_lines.append(line)
        else:
            result_lines.append(line)

    if in_table:
        result_lines.append('</tbody></table></div>')

    html_content = '\n'.join(result_lines)

    # 转换段落（简单处理）
    paragraphs = []
    current_para = []

    for line in html_content.split('\n'):
        line = line.strip()

        # 跳过代码块占位符
        if line.startswith('___CODE_BLOCK_'):
            if current_para:
                para_text = ' '.join(current_para)
                paragraphs.append(f'<p>{para_text}</p>')
                current_para = []
            paragraphs.append(line)
            continue

        # 跳过已经是HTML标签的行
        if line.startswith('<') or not line:
            if current_para:
                para_text = ' '.join(current_para)
                if not para_text.startswith('<'):
                    paragraphs.append(f'<p>{para_text}</p>')
                else:
                    paragraphs.append(para_text)
                current_para = []
            if line:
                paragraphs.append(line)
        else:
            # 处理列表
            if line.startswith('- '):
                if current_para:
                    paragraphs.append(f'<p>{" ".join(current_para)}</p>')
                    current_para = []
                paragraphs.append(f'<li>{line[2:]}</li>')
            else:
                current_para.append(line)

    if current_para:
        paragraphs.append(f'<p>{" ".join(current_para)}</p>')

    html_content = '\n'.join(paragraphs)

    # 包装列表项
    html_content = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'</ul>\s*<ul>', '', html_content)

    # 恢复代码块
    for i, code_block in enumerate(code_blocks):
        html_content = html_content.replace(f'___CODE_BLOCK_{i}___', code_block)

    # 优化LOC统计显示（将开发者信息转换为卡片）
    def convert_developer_section(text):
        """将开发者LOC统计转换为紧凑卡片布局"""
        # 匹配 #### 👤 开发者名 ... 到下一个 #### 或其他标题
        pattern = r'<h4>(👤 .*?)</h4>(.*?)(?=<h[234]|$)'

        def format_developer_card(match):
            dev_name = match.group(1)
            content = match.group(2)

            # 提取统计数据
            stats = {}
            if '新增代码:' in content:
                stats['added'] = re.search(r'新增代码:\s*([\d,]+)\s*行', content)
            if '删除代码:' in content:
                stats['deleted'] = re.search(r'删除代码:\s*([\d,]+)\s*行', content)
            if '净贡献:' in content:
                stats['net'] = re.search(r'净贡献:\s*<strong>([+\-\d,]+)</strong>\s*行', content)
            if '有效代码率:' in content:
                stats['efficiency'] = re.search(r'有效代码率:\s*([\d.]+)%', content)

            # 提取语言信息
            languages = re.findall(r'<li>(.*?):\s*([\d,]+)\s*行', content)

            # 提取仓库信息
            repos_match = re.search(r'涉及仓库</strong>:\s*([^<\n]+)', content)
            repos = repos_match.group(1).strip() if repos_match else ''

            # 构建紧凑卡片
            card_html = f'<div class="developer-card">'
            card_html += f'<h4 style="margin: 0 0 10px 0; background: none; padding: 0; border: none;">{dev_name}</h4>'

            # 统计数据网格
            card_html += '<div class="developer-stats">'

            if stats.get('added'):
                added_val = stats['added'].group(1)
                card_html += f'<div class="stat-item"><span class="stat-label">新增</span><strong>+{added_val}</strong> 行</div>'

            if stats.get('deleted'):
                deleted_val = stats['deleted'].group(1)
                card_html += f'<div class="stat-item"><span class="stat-label">删除</span><strong>-{deleted_val}</strong> 行</div>'

            if stats.get('net'):
                net_val = stats['net'].group(1)
                color = '#10b981' if '+' in net_val else '#ef4444'
                card_html += f'<div class="stat-item"><span class="stat-label">净贡献</span><strong style="color: {color};">{net_val}</strong> 行</div>'

            if stats.get('efficiency'):
                eff_val = stats['efficiency'].group(1)
                card_html += f'<div class="stat-item"><span class="stat-label">有效率</span><strong>{eff_val}%</strong></div>'

            card_html += '</div>'

            # 语言和仓库信息（更紧凑）
            if languages or repos:
                card_html += '<div style="margin-top: 10px; font-size: 13px; color: #666;">'
                if languages:
                    lang_text = ' | '.join([f'{lang}: {count}行' for lang, count in languages[:3]])
                    card_html += f'<span>💻 {lang_text}</span>'
                if repos:
                    card_html += f' <span style="margin-left: 10px;">📁 {repos}</span>'
                card_html += '</div>'

            card_html += '</div>'
            return card_html

        result = re.sub(pattern, format_developer_card, text, flags=re.DOTALL)
        return result

    html_content = convert_developer_section(html_content)

    # 生成完整HTML
    full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            font-size: 32px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}

        h2 {{
            color: #34495e;
            font-size: 24px;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #667eea;
        }}

        h3 {{
            color: #555;
            font-size: 20px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}

        h4 {{
            color: #666;
            font-size: 16px;
            margin-top: 15px;
            margin-bottom: 8px;
        }}

        p {{
            margin-bottom: 10px;
            line-height: 1.8;
        }}

        .table-wrapper {{
            overflow-x: auto;
            margin: 20px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #e0e0e0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
            font-size: 0.9em;
            color: #e83e8c;
        }}

        pre {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            overflow-x: auto;
            margin: 20px 0;
            line-height: 1.8;
            font-family: "SFMono-Regular", "Consolas", "Liberation Mono", "Menlo", "Courier", monospace;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
        }}

        pre code {{
            background: none;
            padding: 0;
            color: #555;
            font-size: 14px;
            white-space: pre;
            display: block;
            line-height: 1.8;
        }}

        /* 热力图方块字符样式 */
        pre code::before {{
            content: '';
        }}

        h4 {{
            color: #667eea;
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 12px;
            padding: 10px 15px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}

        /* LOC统计开发者卡片优化 */
        .developer-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.2s;
        }}

        .developer-card:hover {{
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }}

        .developer-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 10px 0;
        }}

        .stat-item {{
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 13px;
        }}

        .stat-item strong {{
            color: #667eea;
            font-size: 16px;
        }}

        .stat-label {{
            color: #666;
            font-size: 12px;
            display: block;
            margin-bottom: 4px;
        }}

        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}

        ul {{
            margin: 10px 0 10px 20px;
        }}

        li {{
            margin-bottom: 5px;
        }}

        a {{
            color: #667eea;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border-radius: 4px;
            text-decoration: none;
        }}

        .back-link:hover {{
            background: #5568d3;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/reports/index.html" class="back-link">← 返回报告中心</a>
        {html_content}
    </div>
</body>
</html>'''

    return full_html


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = markdown_to_html(md_content)

        html_file = md_file.replace('.md', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ 已生成: {html_file}")
