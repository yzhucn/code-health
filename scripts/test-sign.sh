#!/bin/bash

CONFIG_FILE="../config.yaml"
SECRET=$(grep -A 5 "dingtalk:" $CONFIG_FILE | grep "secret:" | awk '{print $2}' | tr -d '"')

echo "Secret前10位: ${SECRET:0:10}..."

# 测试时间戳
timestamp=$(date +%s%3N)
echo "时间戳: $timestamp"

# 测试签名
string_to_sign="${timestamp}\n${SECRET}"
echo "待签名字符串: ${string_to_sign:0:30}..."

# 使用printf确保正确处理\n
sign=$(printf "%s" "${timestamp}\n${SECRET}" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
echo "签名: ${sign:0:20}..."

# URL编码
encoded_sign=$(echo -n "$sign" | python3 -c "import sys; from urllib.parse import quote; print(quote(sys.stdin.read().strip()))")
echo "URL编码后: ${encoded_sign:0:30}..."
