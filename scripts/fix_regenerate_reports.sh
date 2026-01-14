#!/bin/bash
# 修复脚本 - 重新生成所有日报
#
# 用法:
#   ./scripts/fix_regenerate_reports.sh
#
# 功能:
#   1. 先运行 API 调试检查
#   2. 重新生成2025年12月的所有日报
#   3. 重新生成2026年1月的所有日报
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Code Health Monitor - 报告修复脚本${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# 检查环境变量
if [ -z "$CODEUP_TOKEN" ]; then
    echo -e "${RED}错误: CODEUP_TOKEN 环境变量未设置${NC}"
    exit 1
fi

if [ -z "$CODEUP_ORG_ID" ]; then
    echo -e "${RED}错误: CODEUP_ORG_ID 环境变量未设置${NC}"
    exit 1
fi

echo -e "${GREEN}环境变量检查通过${NC}"
echo

# 设置输出目录
OUTPUT_DIR="${CODE_HEALTH_OUTPUT:-/opt/code-health/reports}"
echo "输出目录: $OUTPUT_DIR"
echo

# 步骤1: 运行API调试（可选）
echo -e "${YELLOW}步骤1: 运行 API 调试${NC}"
echo "-----------------------------------------"
CODEUP_DEBUG=1 python3 -c "
import os
import sys
sys.path.insert(0, '.')
from src.providers.codeup import CodeupProvider

provider = CodeupProvider()
repos = provider.list_repositories()
print(f'找到 {len(repos)} 个仓库')

if repos:
    # 获取一个提交来测试
    from datetime import datetime, timedelta
    end = datetime.now()
    start = end - timedelta(days=7)
    commits = provider.get_commits(repos[0].id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    print(f'获取到 {len(commits)} 个提交')
    if commits:
        print(f'第一个提交文件数: {len(commits[0].files)}')
        for f in commits[0].files[:3]:
            print(f'  - {f.path}')
" 2>&1 || echo -e "${RED}调试失败，继续执行...${NC}"
echo

# 步骤2: 生成2025年12月日报
echo -e "${YELLOW}步骤2: 重新生成2025年12月日报${NC}"
echo "-----------------------------------------"

for day in $(seq -w 4 31); do
    date="2025-12-$day"
    echo -n "生成 $date... "
    python3 -m src.main daily --date "$date" --output "$OUTPUT_DIR" > /dev/null 2>&1 && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"
done
echo

# 步骤3: 生成2026年1月日报
echo -e "${YELLOW}步骤3: 重新生成2026年1月日报${NC}"
echo "-----------------------------------------"

for day in $(seq -w 1 14); do
    date="2026-01-$day"
    echo -n "生成 $date... "
    python3 -m src.main daily --date "$date" --output "$OUTPUT_DIR" > /dev/null 2>&1 && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"
done
echo

# 步骤4: 生成HTML
echo -e "${YELLOW}步骤4: 生成 HTML 文件${NC}"
echo "-----------------------------------------"
python3 -m src.main html --output "$OUTPUT_DIR"
echo

# 步骤5: 更新仪表盘
echo -e "${YELLOW}步骤5: 更新仪表盘${NC}"
echo "-----------------------------------------"
DASHBOARD_DIR="${OUTPUT_DIR}/../dashboard"
python3 -m src.main dashboard --output "$DASHBOARD_DIR" --reports-dir "$OUTPUT_DIR"
echo

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}  修复完成!${NC}"
echo -e "${BLUE}================================================${NC}"
