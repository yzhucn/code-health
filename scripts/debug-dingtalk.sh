#!/bin/bash

CONFIG_FILE="../config.yaml"
WEBHOOK=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "webhook:" | awk '{print $2}' | tr -d '"')
SECRET=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "secret:" | awk '{print $2}' | tr -d '"')

echo "=== 钉钉推送调试 ==="
echo ""
echo "Webhook: ${WEBHOOK:0:50}..."
echo "Secret: ${SECRET:0:15}..."
echo ""

# 方法1: 当前实现
echo "【方法1】当前实现:"
timestamp=$(date +%s%3N)
string_to_sign="${timestamp}\n${SECRET}"
sign=$(printf "%s" "$string_to_sign" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
encoded_sign=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$sign', safe=''))")
echo "时间戳: $timestamp"
echo "签名: $sign"
echo "URL编码: $encoded_sign"
FULL_URL="$WEBHOOK&timestamp=${timestamp}&sign=${encoded_sign}"

# 测试消息
MESSAGE='{"msgtype":"text","text":{"content":"代码管理 - 测试消息"}}'
RESPONSE=$(curl -s -X POST "$FULL_URL" -H 'Content-Type: application/json' -d "$MESSAGE")
echo "响应: $RESPONSE"
echo ""

# 方法2: 尝试不同的签名方式
echo "【方法2】尝试修复:"
timestamp=$(date +%s)000  # 毫秒
string_to_sign="${timestamp}"$'\n'"${SECRET}"
sign=$(echo -ne "$string_to_sign" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
encoded_sign=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$sign', safe=''))")
echo "时间戳: $timestamp"
echo "签名: $sign"
echo "URL编码: $encoded_sign"
FULL_URL="$WEBHOOK&timestamp=${timestamp}&sign=${encoded_sign}"

RESPONSE=$(curl -s -X POST "$FULL_URL" -H 'Content-Type: application/json' -d "$MESSAGE")
echo "响应: $RESPONSE"

