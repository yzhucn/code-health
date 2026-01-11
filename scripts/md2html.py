#!/usr/bin/env python3
"""
Markdown to HTML converter with beautiful styling
Fixed: HTML escape for commit messages and other content
"""
import sys
import markdown
import re
import html
from pathlib import Path

def escape_html_in_content(md_content):
    """转义markdown内容中的HTML特殊字符，但保留markdown语法
    
    主要处理：
    1. commit message中的<>符号
    2. 表格单元格中的<>符号
    3. 其他非markdown语法的<>符号
    """
    
    # 策略：先保护markdown语法标记，转义其他HTML字符，再恢复markdown标记
    
    # 1. 保护代码块（```代码块```）
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"
    
    md_content = re.sub(r'```[\s\S]*?```', save_code_block, md_content)
    
    # 2. 保护行内代码（`代码`）
    inline_codes = []
    def save_inline_code(match):
        inline_codes.append(match.group(0))
        return f"___INLINE_CODE_{len(inline_codes)-1}___"
    
    md_content = re.sub(r'`[^`]+`', save_inline_code, md_content)
    
    # 3. 保护markdown链接 [text](url)
    md_links = []
    def save_md_link(match):
        md_links.append(match.group(0))
        return f"___MD_LINK_{len(md_links)-1}___"
    
    md_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', save_md_link, md_content)
    
    # 4. 保护HTML注释
    html_comments = []
    def save_html_comment(match):
        html_comments.append(match.group(0))
        return f"___HTML_COMMENT_{len(html_comments)-1}___"
    
    md_content = re.sub(r'<!--[\s\S]*?-->', save_html_comment, md_content)
    
    # 5. 现在转义剩余的HTML特殊字符
    # 只转义 < 和 >，因为这是最常见的问题
    md_content = md_content.replace('<', '&lt;').replace('>', '&gt;')
    
    # 6. 恢复保护的内容
    for i, comment in enumerate(html_comments):
        md_content = md_content.replace(f"___HTML_COMMENT_{i}___", comment)
    
    for i, link in enumerate(md_links):
        md_content = md_content.replace(f"___MD_LINK_{i}___", link)
    
    for i, code in enumerate(inline_codes):
        md_content = md_content.replace(f"___INLINE_CODE_{i}___", code)
    
    for i, code in enumerate(code_blocks):
        md_content = md_content.replace(f"___CODE_BLOCK_{i}___", code)
    
    return md_content

def convert_md_to_html(md_file, html_file=None):
    """Convert markdown file to HTML with CSS styling"""
    
    md_path = Path(md_file)
    if not md_path.exists():
        print(f"Error: File {md_file} not found")
        return False
    
    if html_file is None:
        html_file = md_path.with_suffix('.html')
    
    # Read markdown content
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Escape HTML special characters in content (but preserve markdown syntax)
    md_content = escape_html_in_content(md_content)
    
    # Convert markdown to HTML
    md_converter = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br'])
    html_body = md_converter.convert(md_content)
    
    # Get title from first heading or filename
    title = md_path.stem.replace('-', ' ').title()
    if md_content.startswith('# '):
        title = md_content.split('\n')[0].replace('# ', '')
    
    # Create full HTML with styling
    html_template = f"""<!DOCTYPE html>
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            line-height: 1.6;
            color: #24292e;
            background: #f6f8fa;
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
            font-size: 2.5em;
            margin-bottom: 0.5em;
            color: #0366d6;
            border-bottom: 3px solid #0366d6;
            padding-bottom: 0.3em;
        }}
        
        h2 {{
            font-size: 2em;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #24292e;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 0.3em;
        }}
        
        h3 {{
            font-size: 1.5em;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            color: #24292e;
        }}
        
        h4 {{
            font-size: 1.25em;
            margin-top: 1em;
            margin-bottom: 0.5em;
            color: #586069;
        }}
        
        p {{
            margin-bottom: 1em;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 10px 12px;
            border: 1px solid #e1e4e8;
        }}
        
        tr:nth-child(even) {{
            background-color: #f6f8fa;
        }}
        
        tr:hover {{
            background-color: #e8f0fe;
        }}
        
        code {{
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.9em;
            color: #d73a49;
        }}
        
        pre {{
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 1em 0;
        }}
        
        pre code {{
            background: none;
            color: #24292e;
            padding: 0;
        }}
        
        ul, ol {{
            margin-left: 2em;
            margin-bottom: 1em;
        }}
        
        li {{
            margin-bottom: 0.5em;
        }}
        
        blockquote {{
            border-left: 4px solid #dfe2e5;
            padding-left: 1em;
            margin: 1em 0;
            color: #6a737d;
        }}
        
        strong {{
            color: #d73a49;
            font-weight: 600;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #e1e4e8;
            margin: 2em 0;
        }}
        
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .emoji {{
            font-size: 1.2em;
        }}
        
        /* Status badges */
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #28a745;
            color: white;
        }}
        
        .badge-warning {{
            background: #ffc107;
            color: #333;
        }}
        
        .badge-danger {{
            background: #dc3545;
            color: white;
        }}
        
        /* Print styles */
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                padding: 0;
            }}
        }}
        
        /* Meta info */
        .meta-info {{
            color: #586069;
            font-size: 0.9em;
            margin-bottom: 2em;
            padding: 10px;
            background: #f1f8ff;
            border-left: 4px solid #0366d6;
            border-radius: 3px;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
            
            table {{
                font-size: 0.9em;
            }}
        }}
    </style>
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
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✅ Successfully converted: {md_file}")
    print(f"   Output: {html_file}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 md2html.py <markdown_file> [output_html_file]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    html_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = convert_md_to_html(md_file, html_file)
    sys.exit(0 if success else 1)
