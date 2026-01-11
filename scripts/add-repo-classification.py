#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓库分类脚本 - 优化周报中的仓库LOC分布
按项目类型将仓库分为 EcoMind 和 External 两类
"""

import re
import sys
from pathlib import Path


def parse_repo_table(table_content):
    """解析仓库表格，返回仓库数据列表"""
    repos = []
    lines = table_content.strip().split('\n')
    
    for line in lines[2:]:  # 跳过表头和分隔线
        line = line.strip()
        if not line or line.startswith('|---'):
            continue
            
        # 解析表格行
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            continue
            
        repo_name = parts[1]
        commits = parts[2]
        additions = parts[3]
        deletions = parts[4]
        net_change = parts[5]
        percentage = parts[6]
        
        repos.append({
            'name': repo_name,
            'commits': commits,
            'additions': additions,
            'deletions': deletions,
            'net_change': net_change,
            'percentage': percentage
        })
    
    return repos


def classify_repos(repos):
    """将仓库分类为 EcoMind 和 External"""
    ecomind_repos = []
    external_repos = []
    
    for repo in repos:
        if repo['name'].lower().startswith('ecomind'):
            ecomind_repos.append(repo)
        else:
            external_repos.append(repo)
    
    return ecomind_repos, external_repos


def parse_number(value_str):
    """解析数字字符串，处理 +/- 符号和逗号"""
    if not value_str or value_str == '-':
        return 0
    
    # 移除 +, -, **, 逗号等符号
    clean_str = value_str.replace('**', '').replace('+', '').replace(',', '').strip()
    
    # 处理负数
    is_negative = '-' in value_str
    clean_str = clean_str.replace('-', '')
    
    try:
        num = int(clean_str)
        return -num if is_negative else num
    except ValueError:
        return 0


def calculate_subtotal(repos):
    """计算小计数据"""
    total_commits = 0
    total_additions = 0
    total_deletions = 0
    total_net = 0
    
    for repo in repos:
        total_commits += parse_number(repo['commits'])
        total_additions += parse_number(repo['additions'])
        total_deletions += parse_number(repo['deletions'])
        total_net += parse_number(repo['net_change'])
    
    return {
        'commits': total_commits,
        'additions': total_additions,
        'deletions': total_deletions,
        'net': total_net
    }


def format_number(num):
    """格式化数字，添加千位分隔符和正负号"""
    if num == 0:
        return "0"
    
    abs_num = abs(num)
    formatted = f"{abs_num:,}"
    
    if num > 0:
        return f"+{formatted}"
    else:
        return f"-{formatted}"


def generate_classified_table(ecomind_repos, external_repos):
    """生成分类后的表格内容"""
    output = []
    
    output.append("### 4️⃣ 仓库 LOC 分布\n")
    
    # EcoMind 项目表格
    if ecomind_repos:
        output.append(f"#### 📦 EcoMind 项目 ({len(ecomind_repos)}个仓库)\n")
        output.append("| 仓库 | 提交 | 新增 | 删除 | 净增 | 占比 |")
        output.append("|------|------|------|------|------|------|")
        
        for repo in ecomind_repos:
            output.append(f"| {repo['name']} | {repo['commits']} | {repo['additions']} | "
                        f"{repo['deletions']} | {repo['net_change']} | {repo['percentage']} |")
        
        # 添加小计
        subtotal = calculate_subtotal(ecomind_repos)
        output.append(f"\n**小计**: 提交{subtotal['commits']}次，新增{format_number(subtotal['additions'])}行，"
                     f"删除{format_number(subtotal['deletions'])}行，净增{format_number(subtotal['net'])}行\n")
    
    # External 项目表格
    if external_repos:
        output.append(f"#### 🔌 External 项目 ({len(external_repos)}个仓库)\n")
        output.append("| 仓库 | 提交 | 新增 | 删除 | 净增 | 占比 |")
        output.append("|------|------|------|------|------|------|")
        
        for repo in external_repos:
            output.append(f"| {repo['name']} | {repo['commits']} | {repo['additions']} | "
                        f"{repo['deletions']} | {repo['net_change']} | {repo['percentage']} |")
        
        # 添加小计
        subtotal = calculate_subtotal(external_repos)
        output.append(f"\n**小计**: 提交{subtotal['commits']}次，新增{format_number(subtotal['additions'])}行，"
                     f"删除{format_number(subtotal['deletions'])}行，净增{format_number(subtotal['net'])}行\n")
    
    return '\n'.join(output)


def process_weekly_report(file_path):
    """处理周报文件，优化仓库LOC分布"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"错误: 文件不存在 - {file_path}")
        return False
    
    # 读取原文件
    content = file_path.read_text(encoding='utf-8')
    
    # 查找仓库LOC分布章节
    pattern = r'(### 4️⃣ 仓库 LOC 分布\n\n)(.*?)(\n\n## 二、高危文件深度分析)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("警告: 未找到'仓库 LOC 分布'章节")
        return False
    
    table_content = match.group(2).strip()
    
    # 检查表格是否为空
    if not table_content or '| ecomind' not in table_content.lower():
        print("警告: 仓库LOC分布表格为空或无数据，无法进行分类")
        print("\n建议: 请先确保周报中有仓库数据")
        return False
    
    # 解析表格
    repos = parse_repo_table(table_content)
    
    if not repos:
        print("警告: 未能解析到任何仓库数据")
        return False
    
    print(f"\n解析到 {len(repos)} 个仓库")
    
    # 分类仓库
    ecomind_repos, external_repos = classify_repos(repos)
    
    print(f"  - EcoMind 项目: {len(ecomind_repos)} 个仓库")
    print(f"  - External 项目: {len(external_repos)} 个仓库")
    
    # 生成新表格
    new_section = generate_classified_table(ecomind_repos, external_repos)
    
    # 替换内容
    new_content = content[:match.start()] + new_section + match.group(3) + content[match.end():]
    
    # 备份原文件
    backup_path = file_path.with_suffix('.md.bak')
    file_path.rename(backup_path)
    print(f"\n备份原文件到: {backup_path}")
    
    # 写入新文件
    file_path.write_text(new_content, encoding='utf-8')
    print(f"已更新文件: {file_path}")
    
    # 输出统计信息
    print("\n" + "="*60)
    print("统计信息:")
    print("="*60)
    
    if ecomind_repos:
        ecomind_subtotal = calculate_subtotal(ecomind_repos)
        print(f"\n📦 EcoMind 项目 ({len(ecomind_repos)}个仓库):")
        print(f"   提交: {ecomind_subtotal['commits']} 次")
        print(f"   新增: {format_number(ecomind_subtotal['additions'])} 行")
        print(f"   删除: {format_number(ecomind_subtotal['deletions'])} 行")
        print(f"   净增: {format_number(ecomind_subtotal['net'])} 行")
    
    if external_repos:
        external_subtotal = calculate_subtotal(external_repos)
        print(f"\n🔌 External 项目 ({len(external_repos)}个仓库):")
        print(f"   提交: {external_subtotal['commits']} 次")
        print(f"   新增: {format_number(external_subtotal['additions'])} 行")
        print(f"   删除: {format_number(external_subtotal['deletions'])} 行")
        print(f"   净增: {format_number(external_subtotal['net'])} 行")
    
    print("\n" + "="*60)
    
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python add-repo-classification.py <周报文件路径>")
        print("示例: python add-repo-classification.py reports/weekly/2026-W02.md")
        sys.exit(1)
    
    report_file = sys.argv[1]
    
    print(f"正在处理周报: {report_file}")
    success = process_weekly_report(report_file)
    
    if success:
        print("\n✅ 周报优化完成!")
    else:
        print("\n❌ 周报优化失败")
        sys.exit(1)
