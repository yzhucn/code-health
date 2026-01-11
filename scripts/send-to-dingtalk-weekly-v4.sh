#!/bin/bash
# 钉钉周报推送脚本（v4 - 仓库名+语言双显示，多仓库换行）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

# 支持指定周期参数
if [ -n "$1" ] && [ -n "$2" ]; then
    WEEK="${1}-W${2}"
elif [ -n "$1" ]; then
    WEEK="$1"
else
    TODAY_WEEKDAY=$(date +%u 2>/dev/null || date +%w)
    if [ "$TODAY_WEEKDAY" = "6" ]; then
        WEEK=$(date +%Y-W%V)
    else
        WEEK=$(date -d "last saturday" +%Y-W%V 2>/dev/null || date -v-sat +%Y-W%V)
    fi
fi

REPORT_FILE="$SCRIPT_DIR/../reports/weekly/$WEEK.md"

# 读取配置
WEBHOOK=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "webhook:" | awk '{print $2}' | tr -d '"')
SECRET=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "secret:" | awk '{print $2}' | tr -d '"')
BASE_URL=$(grep -A 3 "web:" $CONFIG_FILE | grep "base_url:" | awk '{print $2}' | tr -d '"')
PROJECT_NAME=$(grep -A 2 "project:" $CONFIG_FILE | grep "name:" | awk -F': ' '{print $2}' | tr -d '"' || echo "代码健康监控平台")

if [ ! -f "$REPORT_FILE" ]; then
    echo "⚠️  报告文件不存在: $REPORT_FILE"
    exit 1
fi

# 提取基础数据
TOTAL_COMMITS=$(grep "| 总提交数" "$REPORT_FILE" | head -1 | sed -E 's/[^0-9]*([0-9]+).*/\1/' || echo "0")
TOTAL_LINES=$(grep "| \*\*总净增行数\*\*" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([+-]?[0-9,]+)\*\*.*/\1/' | tr -d ',' || echo "0")
# 添加千分号（递归处理所有位数）
if [ "$TOTAL_LINES" != "0" ]; then
    TOTAL_LINES=$(echo "$TOTAL_LINES" | sed ':a;s/\([0-9]\)\([0-9]\{3\}\)\($\|,\)/\1,\2\3/;ta')
fi
DEVELOPERS=$(grep "| 活跃开发者" "$REPORT_FILE" | head -1 | sed -E 's/[^0-9]*([0-9]+).*/\1/' || echo "0")

# 提取TOP 5贡献者详细信息（从LOC统计部分提取语言和仓库）
export REPORT_FILE_PATH="$REPORT_FILE"
python3 << 'EOPY' > /tmp/top5_full_detail.txt
import re
import os

report_file = os.environ['REPORT_FILE_PATH']

with open(report_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 先从排行榜获取TOP 5名单和基础数据
contributors = []
lines = content.split('\n')
in_table = False

for line in lines:
    if "提交量排行榜" in line:
        in_table = True
        continue
    if in_table and line.startswith("| ") and not line.startswith("| 排名"):
        if line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 7 and parts[1].isdigit():
            rank = parts[1]
            name = parts[2]
            commits = parts[3]
            net_lines = parts[6].replace("**", "").replace("+", "").replace(",", "")
            contributors.append({
                'rank': rank,
                'name': name,
                'commits': commits,
                'net_lines': net_lines,
                'languages': [],
                'repos': []
            })
            if len(contributors) >= 5:
                break

# 然后从LOC统计表格提取语言和仓库信息
for contributor in contributors:
    name = contributor['name']

    # 在LOC统计表格中查找该开发者的行
    # 格式: | **开发者名** | +新增 | -删除 | **+净增** | 率 | 语言<br>语言 | 仓库<br>仓库 |
    pattern = rf'\|\s*\*\*{re.escape(name)}\*\*\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
    match = re.search(pattern, content)

    if match:
        lang_part = match.group(1).strip()
        repo_part = match.group(2).strip()

        # 提取主要语言（格式: Java: 1,034,056 行 (100%)<br>Vue/JS: 537 行 (0%)）
        lang_lines = re.split(r'<br>|<br/>|<BR>', lang_part)
        for lang_line in lang_lines[:2]:  # 最多取前2个语言
            m = re.match(r'([^:]+):\s*[\d,]+\s*行', lang_line.strip())
            if m:
                contributor['languages'].append(m.group(1).strip())

        # 提取涉及仓库（格式: ecomind-backend<br>ecomind-etl）
        repo_items = [r.strip() for r in re.split(r'<br>|<br/>|\n', repo_part) if r.strip()]
        contributor['repos'] = repo_items[:3]  # 最多取前3个仓库

# 输出结果
for c in contributors:
    langs = ', '.join(c['languages']) if c['languages'] else 'N/A'
    repos = '|'.join(c['repos']) if c['repos'] else 'N/A'  # 用|分隔，后续替换为<br/>
    print(f"{c['rank']}\t{c['name']}\t{c['commits']}\t{c['net_lines']}\t{langs}\t{repos}")
EOPY

# 构建LOC统计表格
LOC_TABLE=""
while IFS=$'\t' read -r rank name commits net_lines langs repos; do
    # 格式化行数（添加千分号）- 修复：递归添加所有千分号
    formatted_lines=$(echo "$net_lines" | sed ':a;s/\([0-9]\)\([0-9]\{3\}\)\($\|,\)/\1,\2\3/;ta')

    # 处理技术栈（每个语言单独一行，手机查看更友好）
    if [ "$langs" != "N/A" ]; then
        langs_display=$(echo "$langs" | sed 's/, /<br\/>💻 /g')
        langs_display="💻 ${langs_display}"
    else
        langs_display="N/A"
    fi

    # 处理仓库名（每个仓库单独一行，手机查看更友好）
    if [ "$repos" != "N/A" ]; then
        repo_count=$(echo "$repos" | grep -o "|" | wc -l)
        repo_count=$((repo_count + 1))

        if [ $repo_count -gt 3 ]; then
            # 仓库太多，只显示前3个
            first_repos=$(echo "$repos" | cut -d'|' -f1-3 | sed 's/|/<br\/>📦 /g')
            repos_display="📦 ${first_repos}<br/>📦 ...等${repo_count}个"
        else
            repos_display=$(echo "$repos" | sed 's/|/<br\/>📦 /g')
            repos_display="📦 ${repos_display}"
        fi
    else
        repos_display="N/A"
    fi

    # 构建技术栈和仓库信息（垂直布局，避免使用|以免破坏表格）
    if [ "$langs_display" != "N/A" ] && [ "$repos_display" != "N/A" ]; then
        detail="${langs_display}<br/>${repos_display}"
    elif [ "$langs_display" != "N/A" ]; then
        detail="$langs_display"
    elif [ "$repos_display" != "N/A" ]; then
        detail="$repos_display"
    else
        detail="N/A"
    fi

    LOC_TABLE="${LOC_TABLE}| ${name} | ${commits}次 | +${formatted_lines}行 | ${detail} |\n"
done < /tmp/top5_full_detail.txt

# 提取风险信息
HIGH_RISK_FILES=$(grep "发现高危文件" "$REPORT_FILE" | grep -oE '[0-9]+' | head -1 || echo "0")
CHURN_RATE=$(grep "本周震荡率" "$REPORT_FILE" | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo "0.0")

# 检查特别说明
SPECIAL_NOTE=""
if grep -q "特别说明" "$REPORT_FILE"; then
    if grep -q "实际新开发代码" "$REPORT_FILE"; then
        REAL_CODE=$(grep "实际新开发代码" "$REPORT_FILE" | sed -E 's/.*约 ([0-9]+)万行.*/\1/' || echo "未知")
        SPECIAL_NOTE="\\n\\n### ⚠️ 特别提示\\n\\n本周包含大规模代码迁移，实际新开发代码约 **${REAL_CODE}万行**"
    elif grep -q "初始提交" "$REPORT_FILE"; then
        SPECIAL_NOTE="\\n\\n### ⚠️ 特别提示\\n\\n本周包含仓库初始提交，代码量统计包含历史代码迁移"
    fi
fi

# 报告链接
REPORT_URL="$BASE_URL/reports/weekly/$WEEK.html"
DASHBOARD_URL="$BASE_URL/dashboard/index.html"

# 生成签名
function generate_sign() {
    local timestamp=$(date +%s)000
    local string_to_sign="${timestamp}"$'\n'"${SECRET}"
    local sign=$(echo -ne "$string_to_sign" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
    local encoded_sign=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$sign', safe=''))")
    echo "timestamp=${timestamp}&sign=${encoded_sign}"
}

# 构建增强消息
MESSAGE=$(cat <<EOF
{
    "msgtype": "markdown",
    "markdown": {
        "title": "代码健康周报",
        "text": "## 📈 代码健康周报\\n\\n**周期**: $WEEK | **系统**: $PROJECT_NAME\\n\\n---\\n\\n### 📊 团队产出\\n\\n| 指标 | 数值 |\\n|------|------|\\n| 总提交数 | $TOTAL_COMMITS 次 |\\n| 净增代码 | $TOTAL_LINES 行 |\\n| 活跃开发者 | $DEVELOPERS 人 |\\n\\n---\\n\\n### 🏆 TOP 5 代码贡献\\n\\n| 开发者 | 提交 | 净增代码 | 技术栈/仓库 |\\n|--------|------|---------|-----------|\\n${LOC_TABLE}\\n---\\n\\n### 🚨 风险监控\\n\\n- 高危文件: **$HIGH_RISK_FILES** 个\\n- 代码震荡率: **$CHURN_RATE%**$SPECIAL_NOTE\\n\\n---\\n\\n### 🔗 详细报告\\n\\n[📄 完整周报]($REPORT_URL) | [📊 可视化仪表盘]($DASHBOARD_URL)\\n\\n---\\n\\n> 🤖 由代码健康监控系统自动生成"
    }
}
EOF
)

# 发送到钉钉
if [ -n "$SECRET" ] && [ "$SECRET" != "YOUR_DINGTALK_SECRET" ]; then
    SIGN_PARAMS=$(generate_sign)
    FULL_WEBHOOK="$WEBHOOK&$SIGN_PARAMS"
else
    FULL_WEBHOOK="$WEBHOOK"
fi

if [ "$WEBHOOK" != "YOUR_DINGTALK_WEBHOOK" ]; then
    RESPONSE=$(curl -s -X POST "$FULL_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "$MESSAGE")

    if echo "$RESPONSE" | grep -q '"errcode":0'; then
        echo "✅ 周报已推送到钉钉（v4完整版）"
        echo "   总提交: $TOTAL_COMMITS 次 | 开发者: $DEVELOPERS 人"
    else
        echo "❌ 推送失败: $RESPONSE"
    fi
else
    echo "⚠️  钉钉webhook未配置，跳过推送"
fi

# 清理临时文件
rm -f /tmp/top5_full_detail.txt
