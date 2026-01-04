#!/bin/bash
# 钉钉周报推送脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

# 支持指定周期参数，默认为上周
if [ -n "$1" ] && [ -n "$2" ]; then
    WEEK="${1}-W${2}"
elif [ -n "$1" ]; then
    # 如果只有一个参数，假设是完整的YYYY-WXX格式
    WEEK="$1"
else
    WEEK=$(date -d "last saturday" +%Y-W%V)
fi

REPORT_FILE="$SCRIPT_DIR/../reports/weekly/$WEEK.md"

# 从config.yaml读取钉钉配置
WEBHOOK=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "webhook:" | awk '{print $2}' | tr -d '"')
SECRET=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "secret:" | awk '{print $2}' | tr -d '"')
BASE_URL=$(grep -A 3 "web:" $CONFIG_FILE | grep "base_url:" | awk '{print $2}' | tr -d '"')
PROJECT_NAME=$(grep -A 2 "project:" $CONFIG_FILE | grep "name:" | sed 's/.*name: *"\?\([^"]*\)"\?.*/\1/' || echo "代码健康监控平台")

if [ ! -f "$REPORT_FILE" ]; then
    echo "⚠️  报告文件不存在: $REPORT_FILE"
    exit 1
fi

# 提取关键数据
TOTAL_COMMITS=$(grep "| 总提交数" "$REPORT_FILE" | head -1 | grep -oP '\d+' | head -1 || echo "0")
TOTAL_LINES=$(grep "| \*\*总净增行数\*\*" "$REPORT_FILE" | head -1 | grep -oP '[+-]?\d+' | head -1 || echo "0")
DEVELOPERS=$(grep "| 活跃开发者" "$REPORT_FILE" | head -1 | grep -oP '\d+' || echo "0")

# 提取TOP1贡献者
TOP1=$(grep -A 1 "提交量排行榜" "$REPORT_FILE" | grep "| 1 |" | awk -F'|' '{print $3}' | tr -d ' ' || echo "未知")
TOP1_LINES=$(grep -A 1 "提交量排行榜" "$REPORT_FILE" | grep "| 1 |" | awk -F'|' '{print $7}' | tr -d ' *+' || echo "0")

# 提取风险信息
HIGH_RISK_FILES=$(grep "🔴 严重" "$REPORT_FILE" | grep -oP '\d+' | head -1 || echo "0")
CHURN_RATE=$(grep "本周震荡率\*\*:" "$REPORT_FILE" | grep -oP '\d+\.\d+' || echo "0")

# 报告链接 (HTML格式)
REPORT_URL="$BASE_URL/reports/weekly/$WEEK.html"
DASHBOARD_URL="$BASE_URL/dashboard/index.html"

# 生成签名
function generate_sign() {
    local timestamp=$(date +%s)000  # 毫秒时间戳
    local string_to_sign="${timestamp}"$'\n'"${SECRET}"
    local sign=$(echo -ne "$string_to_sign" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
    local encoded_sign=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$sign', safe=''))")
    echo "timestamp=${timestamp}&sign=${encoded_sign}"
}

# 构建消息
MESSAGE=$(cat <<EOF
{
    "msgtype": "markdown",
    "markdown": {
        "title": "代码管理周报",
        "text": "## 📈 代码管理 - 每周健康监控\n\n**报告周期**: $WEEK\n**系统**: $PROJECT_NAME\n\n---\n\n### 🎯 团队产出\n\n- **总提交数**: $TOTAL_COMMITS 次\n- **总净增代码**: $TOTAL_LINES 行\n- **活跃开发者**: $DEVELOPERS 人\n\n---\n\n### 🏆 TOP 1 贡献者\n\n- **姓名**: $TOP1\n- **贡献**: $TOP1_LINES 行\n\n---\n\n### 🚨 风险监控\n\n- **高危文件**: $HIGH_RISK_FILES 个\n- **震荡率**: $CHURN_RATE%\n\n---\n\n### 🔗 快速链接\n\n- [📄 查看完整周报]($REPORT_URL)\n- [📊 查看可视化仪表盘]($DASHBOARD_URL)\n\n---\n\n> 💡 代码管理系统提示：点击链接查看详细团队分析和改进建议"
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
        echo "✅ 周报已推送到钉钉"
    else
        echo "❌ 推送失败: $RESPONSE"
    fi
else
    echo "⚠️  钉钉webhook未配置，跳过推送"
fi
