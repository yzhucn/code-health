#!/bin/bash
# 钉钉日报推送脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

# 支持指定日期参数，默认为昨天
if [ -n "$1" ]; then
    REPORT_DATE="$1"
else
    REPORT_DATE=$(date -d "yesterday" +%Y-%m-%d)
fi

REPORT_FILE="$SCRIPT_DIR/../reports/daily/$REPORT_DATE.md"

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
COMMITS=$(grep "| 提交次数" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([0-9]+)\*\*.*/\1/' || echo "0")
DEVELOPERS=$(grep "| 活跃开发者" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([0-9]+)\*\*.*/\1/' || echo "0")
LINES=$(grep "| \*\*净增行数\*\*" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([+-][0-9,]+)\*\*.*/\1/' | tr -d ',' || echo "+0")
SCORE=$(grep "综合评分:" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+\.[0-9]+) .*/\1/' | head -1 || echo "0")

# 提取风险信息
CHURN_RATE=$(grep "震荡率\*\*:" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+\.[0-9]+).*/\1/' || echo "0")
REWORK_RATE=$(grep "返工率\*\*:" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+\.[0-9]+).*/\1/' || echo "0")
# 精确匹配包含数字的加班提交行，避免匹配到说明文字
OVERTIME=$(grep -E "加班提交: [0-9]+ 次" "$REPORT_FILE" | sed -E 's/.*: ([0-9]+) 次.*/\1/' | head -1)
[ -z "$OVERTIME" ] && OVERTIME="0"

# 评分等级
if (( $(echo "$SCORE >= 90" | bc -l) )); then
    SCORE_LEVEL="🟢 优秀"
elif (( $(echo "$SCORE >= 80" | bc -l) )); then
    SCORE_LEVEL="🟡 良好"
elif (( $(echo "$SCORE >= 60" | bc -l) )); then
    SCORE_LEVEL="🟠 中等"
else
    SCORE_LEVEL="🔴 需改进"
fi

# 报告链接 (HTML格式)
REPORT_URL="$BASE_URL/reports/daily/$REPORT_DATE.html"
DASHBOARD_URL="$BASE_URL/dashboard/index.html"

# 生成签名（如果配置了secret）
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
        "title": "代码管理日报",
        "text": "## 📊 代码管理 - 每日健康监控\n\n**日期**: $REPORT_DATE\n**系统**: $PROJECT_NAME\n\n---\n\n### 📈 核心指标\n\n- **提交次数**: $COMMITS 次\n- **活跃开发者**: $DEVELOPERS 人\n- **代码净增**: $LINES 行\n- **健康评分**: $SCORE 分 $SCORE_LEVEL\n\n---\n\n### 🚨 风险指标\n\n- **震荡率**: $CHURN_RATE%\n- **返工率**: $REWORK_RATE%\n- **加班提交**: $OVERTIME 次\n\n---\n\n### 🔗 快速链接\n\n- [📄 查看完整日报]($REPORT_URL)\n- [📊 查看可视化仪表盘]($DASHBOARD_URL)\n\n---\n\n> 💡 代码管理系统提示：点击链接查看详细数据分析"
    }
}
EOF
)

# 发送到钉钉
if [ -n "$SECRET" ] && [ "$SECRET" != "YOUR_DINGTALK_SECRET" ]; then
    # 使用加签
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
        echo "✅ 日报已推送到钉钉"
    else
        echo "❌ 推送失败: $RESPONSE"
    fi
else
    echo "⚠️  钉钉webhook未配置，跳过推送"
fi
