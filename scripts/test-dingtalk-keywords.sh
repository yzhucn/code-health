#!/bin/bash
# 钉钉机器人关键词测试脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

# 从config.yaml读取钉钉配置
WEBHOOK=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "webhook:" | awk '{print $2}' | tr -d '"')
SECRET=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "secret:" | awk '{print $2}' | tr -d '"')

# 生成签名
function generate_sign() {
    local timestamp=$(($(date +%s%3N)))
    local string_to_sign="$timestamp\n$SECRET"
    local sign=$(echo -n "$string_to_sign" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
    echo "timestamp=$timestamp&sign=$(echo $sign | sed 's/+/%2B/g' | sed 's/\//%2F/g' | sed 's/=/%3D/g')"
}

# 测试不同关键词
KEYWORDS=("监控" "日报" "周报" "报告" "代码" "健康" "通知" "提醒" "测试")

echo "=== 钉钉机器人关键词测试 ==="
echo "Webhook: ${WEBHOOK:0:50}..."
echo ""

for keyword in "${KEYWORDS[@]}"; do
    echo "测试关键词: $keyword"

    MESSAGE="{\"msgtype\":\"text\",\"text\":{\"content\":\"$keyword - 这是一条测试消息\"}}"

    if [ -n "$SECRET" ] && [ "$SECRET" != "YOUR_DINGTALK_SECRET" ]; then
        SIGN_PARAMS=$(generate_sign)
        FULL_WEBHOOK="$WEBHOOK&$SIGN_PARAMS"
    else
        FULL_WEBHOOK="$WEBHOOK"
    fi

    RESPONSE=$(curl -s -X POST "$FULL_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "$MESSAGE")

    if echo "$RESPONSE" | grep -q '"errcode":0'; then
        echo "✅ 成功！关键词是: $keyword"
        echo ""
        echo "请在推送脚本中使用此关键词。"
        exit 0
    else
        ERROR=$(echo "$RESPONSE" | grep -oP '"errmsg":"[^"]+' | cut -d'"' -f4)
        echo "❌ 失败: ${ERROR:0:30}..."
    fi

    sleep 1  # 避免频率限制
done

echo ""
echo "=== 所有常见关键词测试失败 ==="
echo ""
echo "请检查钉钉机器人设置："
echo "1. 打开钉钉群设置 → 智能群助手 → 找到您的机器人"
echo "2. 查看机器人设置中的【自定义关键词】"
echo "3. 将关键词告诉我，我会更新推送脚本"
echo ""
echo "或者："
echo "- 如果机器人设置为【自定义关键词】，请将关键词改为：监控"
echo "- 或者将机器人改为【加签】模式（已配置secret）"
