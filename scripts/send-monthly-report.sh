#!/bin/bash
# 钉钉月报推送脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

# 支持指定月份参数，默认为上个月
if [ -n "$1" ]; then
    MONTH="$1"
else
    # 获取上个月
    MONTH=$(date -d "last month" +%Y-%m)
fi

REPORT_FILE="$SCRIPT_DIR/../reports/monthly/$MONTH.md"

# 从config.yaml读取钉钉配置
WEBHOOK=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "webhook:" | awk '{print $2}' | tr -d '"')
SECRET=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "secret:" | awk '{print $2}' | tr -d '"')
BASE_URL=$(grep -A 3 "web:" $CONFIG_FILE | grep "base_url:" | awk '{print $2}' | tr -d '"')
PROJECT_NAME=$(grep -A 2 "project:" $CONFIG_FILE | grep "name:" | sed 's/.*name: *"\?\([^"]*\)"\?.*/\1/' || echo "代码健康监控平台")

if [ ! -f "$REPORT_FILE" ]; then
    echo "⚠️  报告文件不存在: $REPORT_FILE"
    exit 1
fi

# 提取关键数据 (兼容 macOS 和 Linux)
TOTAL_COMMITS=$(grep "| 总提交次数" "$REPORT_FILE" | head -1 | sed 's/.*\*\*\([0-9]*\)\*\*.*/\1/' || echo "0")
TOTAL_NET=$(grep "| 代码净增" "$REPORT_FILE" | head -1 | sed 's/.*\*\*\([+-]*[0-9]*\)\*\*.*/\1/' || echo "0")
DEVELOPERS=$(grep "| 活跃开发者" "$REPORT_FILE" | head -1 | sed 's/.*\*\*\([0-9]*\)\*\*.*/\1/' || echo "0")
WORK_DAYS=$(grep "工作日数" "$REPORT_FILE" | head -1 | sed 's/.*: *\([0-9]*\).*/\1/' || echo "0")

# 提取TOP1贡献者
TOP1=$(grep "| 🥇" "$REPORT_FILE" | head -1 | awk -F'|' '{print $3}' | tr -d ' ' || echo "未知")
TOP1_COMMITS=$(grep "| 🥇" "$REPORT_FILE" | head -1 | awk -F'|' '{print $4}' | tr -d ' ' || echo "0")

# 提取健康评分
HEALTH_SCORE=$(grep "平均健康分" "$REPORT_FILE" | sed 's/.*: *\([0-9.]*\).*/\1/' || echo "0")

# 提取风险信息
LATE_NIGHT=$(grep "| 深夜提交" "$REPORT_FILE" | head -1 | awk -F'|' '{print $3}' | tr -d ' ' || echo "0")
WEEKEND=$(grep "| 周末提交" "$REPORT_FILE" | head -1 | awk -F'|' '{print $3}' | tr -d ' ' || echo "0")

# 报告链接 (HTML格式，如果有的话)
REPORT_URL="$BASE_URL/reports/monthly/$MONTH.html"
DASHBOARD_URL="$BASE_URL/dashboard/index.html"

# 生成签名
function generate_sign() {
    local timestamp=$(date +%s)000  # 毫秒时间戳
    local string_to_sign="${timestamp}"$'\n'"${SECRET}"
    local sign=$(echo -ne "$string_to_sign" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
    local encoded_sign=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$sign', safe=''))")
    echo "timestamp=${timestamp}&sign=${encoded_sign}"
}

# 提取月份名称
YEAR=$(echo $MONTH | cut -d'-' -f1)
MONTH_NUM=$(echo $MONTH | cut -d'-' -f2)
MONTH_NAMES=("" "一月" "二月" "三月" "四月" "五月" "六月" "七月" "八月" "九月" "十月" "十一月" "十二月")
MONTH_NAME=${MONTH_NAMES[10#$MONTH_NUM]}

# 构建消息
MESSAGE=$(cat <<EOF
{
    "msgtype": "markdown",
    "markdown": {
        "title": "代码管理月报",
        "text": "## 📊 代码管理 - ${YEAR}年${MONTH_NAME}月报\n\n**报告周期**: $MONTH\n**系统**: $PROJECT_NAME\n\n---\n\n### 📈 月度总览\n\n- **总提交数**: $TOTAL_COMMITS 次\n- **代码净增**: $TOTAL_NET 行\n- **活跃开发者**: $DEVELOPERS 人\n- **工作日数**: $WORK_DAYS 天\n\n---\n\n### 🏆 本月MVP\n\n- **姓名**: $TOP1\n- **提交数**: $TOP1_COMMITS 次\n\n---\n\n### ❤️ 健康评分\n\n- **月度平均分**: $HEALTH_SCORE 分\n\n---\n\n### ⚠️ 风险提示\n\n- **深夜提交**: $LATE_NIGHT 次\n- **周末提交**: $WEEKEND 次\n\n---\n\n### 🔗 快速链接\n\n- [📊 查看可视化仪表盘]($DASHBOARD_URL)\n\n---\n\n> 💡 代码管理系统提示：关注团队健康度，保持可持续发展"
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
        echo "✅ 月报已推送到钉钉"
    else
        echo "❌ 推送失败: $RESPONSE"
    fi
else
    echo "⚠️  钉钉webhook未配置，跳过推送"
fi
