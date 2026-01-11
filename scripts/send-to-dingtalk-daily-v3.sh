#!/bin/bash
# 钉钉日报推送脚本（v3 - 增加详细开发者信息）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

# 支持指定日期参数，默认为昨天
if [ -n "$1" ]; then
    REPORT_DATE="$1"
else
    REPORT_DATE=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
fi

REPORT_FILE="$SCRIPT_DIR/../reports/daily/$REPORT_DATE.md"

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
COMMITS=$(grep "| 提交次数" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([0-9]+)\*\*.*/\1/' || echo "0")
DEVELOPERS=$(grep "| 活跃开发者" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([0-9]+)\*\*.*/\1/' || echo "0")
LINES=$(grep "| \*\*净增行数\*\*" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([+-][0-9,]+)\*\*.*/\1/' | tr -d ',' || echo "+0")
# 添加千分号（递归处理所有位数）
if [ "$LINES" != "+0" ] && [ "$LINES" != "0" ]; then
    # 分离符号和数字
    sign=$(echo "$LINES" | grep -o '^[+-]')
    number=$(echo "$LINES" | sed 's/^[+-]//')
    formatted_number=$(echo "$number" | sed ':a;s/\([0-9]\)\([0-9]\{3\}\)\($\|,\)/\1,\2\3/;ta')
    LINES="${sign}${formatted_number}"
fi
SCORE=$(grep "综合评分:" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+\.[0-9]+) .*/\1/' | head -1 || echo "0")
REPOS=$(grep "| 涉及仓库" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([0-9]+)\*\*.*/\1/' || echo "0")

# 评分等级
if (( $(echo "$SCORE >= 90" | bc -l 2>/dev/null || echo "0") )); then
    SCORE_LEVEL="🟢 优秀"
elif (( $(echo "$SCORE >= 80" | bc -l 2>/dev/null || echo "0") )); then
    SCORE_LEVEL="🟡 良好"
elif (( $(echo "$SCORE >= 60" | bc -l 2>/dev/null || echo "0") )); then
    SCORE_LEVEL="🟠 警告"
else
    SCORE_LEVEL="🔴 危险"
fi

# 提取TOP 3活跃开发者详细信息（从活跃开发者详情表格）
export REPORT_FILE_PATH="$REPORT_FILE"
python3 << 'EOPY' > /tmp/top3_daily_detail.txt
import re
import os

report_file = os.environ['REPORT_FILE_PATH']

with open(report_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 从活跃开发者详情表格提取TOP 3
developers = []
lines = content.split('\n')
in_table = False

for line in lines:
    if "活跃开发者详情" in line or "## 👥 活跃开发者" in line:
        in_table = True
        continue
    if in_table and line.startswith("| ") and not line.startswith("| 排名"):
        if line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.split("|")]
        # 格式: | 排名 | 开发者 | 提交次数 | 新增行数 | 删除行数 | 净增行数 | 主要语言 | 涉及仓库 |
        if len(parts) > 8 and parts[1].isdigit():
            rank = parts[1]
            name = parts[2]
            commits = parts[3]
            net_lines = parts[6].replace("+", "").replace(",", "")
            languages = parts[7].strip()
            repos = parts[8].strip()

            # 处理语言（可能包含多个，用逗号或<br>分隔）
            lang_list = []
            for lang in re.split(r',|<br>|<br/>', languages):
                lang = lang.strip()
                if lang and lang != 'N/A':
                    lang_list.append(lang)

            # 处理仓库（用逗号或<br>分隔）
            repo_list = []
            for repo in re.split(r',|<br>|<br/>|\s+', repos):
                repo = repo.strip()
                if repo and repo != 'N/A' and not repo.isdigit():
                    repo_list.append(repo)

            langs = ', '.join(lang_list[:2]) if lang_list else 'N/A'
            repo_str = '|'.join(repo_list[:3]) if repo_list else 'N/A'

            # 先检查是否已达到3个
            if len(developers) >= 3:
                break

            print(f"{rank}\t{name}\t{commits}\t{net_lines}\t{langs}\t{repo_str}")
            developers.append(name)

    # 如果遇到新的章节，停止
    if in_table and line.startswith("##") and len(developers) > 0:
        break
EOPY

# 构建TOP 3开发者表格
TOP3_TABLE=""
while IFS=$'\t' read -r rank name commits lines langs repos; do
    # 格式化行数（添加千位分隔符）
    if [ "$lines" != "0" ] && [ "$lines" != "N/A" ]; then
        # 使用sed手动添加千位分隔符
        formatted_lines=$(echo "$lines" | sed -e ':a' -e 's/\([0-9]\)\([0-9]\{3\}\)$/\1,\2/' -e 't a')
        # 检查是否已有+号
        if [[ "$formatted_lines" =~ ^\+ ]]; then
            : # 已有+号，不添加
        else
            formatted_lines="+${formatted_lines}"
        fi
    else
        formatted_lines="+0"
    fi

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

        if [ $repo_count -gt 2 ]; then
            # 仓库太多，只显示前2个
            first_repos=$(echo "$repos" | cut -d'|' -f1-2 | sed 's/|/<br\/>📦 /g')
            repos_display="📦 ${first_repos}<br/>📦 ...等${repo_count}个"
        else
            repos_display=$(echo "$repos" | sed 's/|/<br\/>📦 /g')
            repos_display="📦 ${repos_display}"
        fi
    else
        repos_display="N/A"
    fi

    # 构建详细信息（垂直布局，避免使用|以免破坏表格）
    if [ "$langs_display" != "N/A" ] && [ "$repos_display" != "N/A" ]; then
        detail="${langs_display}<br/>${repos_display}"
    elif [ "$langs_display" != "N/A" ]; then
        detail="$langs_display"
    elif [ "$repos_display" != "N/A" ]; then
        detail="$repos_display"
    else
        detail="N/A"
    fi

    TOP3_TABLE="${TOP3_TABLE}| ${name} | ${commits}次 | ${formatted_lines}行 | ${detail} |\n"
done < /tmp/top3_daily_detail.txt

# 提取风险信息
CHURN_RATE=$(grep "震荡率\*\*:" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+\.[0-9]+).*/\1/' || echo "0")
REWORK_RATE=$(grep "返工率\*\*:" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+\.[0-9]+).*/\1/' || echo "0")
OVERTIME=$(grep -E "加班提交: [0-9]+ 次" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+) 次.*/\1/' | head -1)
[ -z "$OVERTIME" ] && OVERTIME="0"

# 报告链接
REPORT_URL="$BASE_URL/reports/daily/$REPORT_DATE.html"
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
        "title": "代码健康日报",
        "text": "## 📊 代码健康日报\\n\\n**日期**: $REPORT_DATE | **系统**: $PROJECT_NAME\\n\\n---\\n\\n### 📈 核心指标\\n\\n| 指标 | 数值 |\\n|------|------|\\n| 提交次数 | $COMMITS 次 |\\n| 活跃开发者 | $DEVELOPERS 人 |\\n| 涉及仓库 | $REPOS 个 |\\n| 代码净增 | $LINES 行 |\\n| 健康评分 | $SCORE 分 $SCORE_LEVEL |\\n\\n---\\n\\n### 👥 TOP 3 活跃开发者\\n\\n| 开发者 | 提交 | 净增代码 | 技术栈/仓库 |\\n|--------|------|---------|-----------|\\n${TOP3_TABLE}\\n---\\n\\n### 🚨 风险指标\\n\\n- 震荡率: **$CHURN_RATE%**\\n- 返工率: **$REWORK_RATE%**\\n- 加班提交: **$OVERTIME** 次\\n\\n---\\n\\n### 🔗 详细报告\\n\\n[📄 完整日报]($REPORT_URL) | [📊 可视化仪表盘]($DASHBOARD_URL)\\n\\n---\\n\\n> 🤖 由代码健康监控系统自动生成"
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
        echo "✅ 日报已推送到钉钉（v3增强版）"
        echo "   提交: $COMMITS 次 | 开发者: $DEVELOPERS 人 | 评分: $SCORE"
    else
        echo "❌ 推送失败: $RESPONSE"
    fi
else
    echo "⚠️  钉钉webhook未配置，跳过推送"
fi

# 清理临时文件
rm -f /tmp/top3_daily_detail.txt
