"""
HTML 生成器 - 将 Markdown 报告转换为美观的 HTML 页面
移植自 V1 scripts/md2html.py
"""

import re
from pathlib import Path

try:
    import markdown
except ImportError:
    markdown = None


def escape_html_in_content(md_content: str) -> str:
    """转义markdown内容中的HTML特殊字符，但保留markdown语法"""

    # 保护代码块
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"
    md_content = re.sub(r'```[\s\S]*?```', save_code_block, md_content)

    # 保护行内代码
    inline_codes = []
    def save_inline_code(match):
        inline_codes.append(match.group(0))
        return f"___INLINE_CODE_{len(inline_codes)-1}___"
    md_content = re.sub(r'`[^`]+`', save_inline_code, md_content)

    # 保护markdown链接
    md_links = []
    def save_md_link(match):
        md_links.append(match.group(0))
        return f"___MD_LINK_{len(md_links)-1}___"
    md_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', save_md_link, md_content)

    # 转义HTML特殊字符
    md_content = md_content.replace('<', '&lt;').replace('>', '&gt;')

    # 恢复保护的内容
    for i, link in enumerate(md_links):
        md_content = md_content.replace(f"___MD_LINK_{i}___", link)
    for i, code in enumerate(inline_codes):
        md_content = md_content.replace(f"___INLINE_CODE_{i}___", code)
    for i, code in enumerate(code_blocks):
        md_content = md_content.replace(f"___CODE_BLOCK_{i}___", code)

    return md_content


# HTML 模板样式 (V1 风格)
HTML_STYLE = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6; color: #24292e; background: #f6f8fa; padding: 20px;
}
.container {
    max-width: 1200px; margin: 0 auto; background: white;
    padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
h1 { font-size: 2.5em; margin-bottom: 0.5em; color: #0366d6; border-bottom: 3px solid #0366d6; padding-bottom: 0.3em; }
h2 { font-size: 2em; margin-top: 1.5em; margin-bottom: 0.5em; color: #24292e; border-bottom: 2px solid #e1e4e8; padding-bottom: 0.3em; }
h3 { font-size: 1.5em; margin-top: 1.2em; margin-bottom: 0.5em; color: #24292e; }
h4 { font-size: 1.25em; margin-top: 1em; margin-bottom: 0.5em; color: #586069; }
p { margin-bottom: 1em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; text-align: left; font-weight: 600; }
td { padding: 10px 12px; border: 1px solid #e1e4e8; }
tr:nth-child(even) { background-color: #f6f8fa; }
tr:hover { background-color: #e8f0fe; }
code { background: #f6f8fa; padding: 2px 6px; border-radius: 3px; font-family: "SFMono-Regular", Consolas, monospace; font-size: 0.9em; color: #d73a49; }
pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; margin: 1em 0; }
pre code { background: none; color: #24292e; padding: 0; }
ul, ol { margin-left: 2em; margin-bottom: 1em; }
li { margin-bottom: 0.5em; }
blockquote { border-left: 4px solid #dfe2e5; padding-left: 1em; margin: 1em 0; color: #6a737d; }
strong { color: #d73a49; font-weight: 600; }
hr { border: none; border-top: 2px solid #e1e4e8; margin: 2em 0; }
a { color: #0366d6; text-decoration: none; }
a:hover { text-decoration: underline; }
.meta-info { color: #586069; font-size: 0.9em; margin-bottom: 2em; padding: 10px; background: #f1f8ff; border-left: 4px solid #0366d6; border-radius: 3px; }
@media (max-width: 768px) {
    body { padding: 10px; }
    .container { padding: 20px; }
    h1 { font-size: 2em; }
    h2 { font-size: 1.5em; }
    table { font-size: 0.9em; }
}
@media print {
    body { background: white; padding: 0; }
    .container { box-shadow: none; padding: 0; }
}
"""


def convert_md_to_html(md_file: str, html_file: str = None) -> bool:
    """将 Markdown 文件转换为 HTML

    Args:
        md_file: Markdown 文件路径
        html_file: 输出 HTML 文件路径（可选，默认同名 .html）

    Returns:
        是否成功
    """
    if markdown is None:
        print("请安装 markdown 库: pip install markdown")
        return False

    md_path = Path(md_file)
    if not md_path.exists():
        print(f"文件不存在: {md_file}")
        return False

    if html_file is None:
        html_file = md_path.with_suffix('.html')

    # 读取 Markdown 内容
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 转义 HTML 特殊字符
    md_content = escape_html_in_content(md_content)

    # 转换为 HTML
    md_converter = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br'])
    html_body = md_converter.convert(md_content)

    # 提取标题
    title = md_path.stem.replace('-', ' ').title()
    if md_content.startswith('# '):
        title = md_content.split('\n')[0].replace('# ', '')

    # 生成完整 HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{HTML_STYLE}</style>
</head>
<body>
    <div class="container">
        {html_body}
        <hr>
        <div class="meta-info">
            Generated from: {md_path.name} | Report generated by Code Health Monitor
        </div>
    </div>
</body>
</html>
"""

    # 写入 HTML 文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML 生成成功: {html_file}")
    return True


def convert_all_reports(reports_dir: str) -> dict:
    """转换目录下所有 Markdown 报告为 HTML

    Args:
        reports_dir: 报告目录路径

    Returns:
        转换结果统计 {'success': int, 'failed': int}
    """
    reports_path = Path(reports_dir)
    result = {'success': 0, 'failed': 0}

    # 转换日报
    for md_file in (reports_path / 'daily').glob('*.md'):
        if md_file.name.startswith('example'):
            continue
        if convert_md_to_html(str(md_file)):
            result['success'] += 1
        else:
            result['failed'] += 1

    # 转换周报
    for md_file in (reports_path / 'weekly').glob('*.md'):
        if md_file.name.startswith('example'):
            continue
        if convert_md_to_html(str(md_file)):
            result['success'] += 1
        else:
            result['failed'] += 1

    # 转换月报
    for md_file in (reports_path / 'monthly').glob('*.md'):
        if md_file.name.startswith('example'):
            continue
        if convert_md_to_html(str(md_file)):
            result['success'] += 1
        else:
            result['failed'] += 1

    return result
