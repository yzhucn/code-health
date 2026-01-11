#!/bin/bash
# 发送前验证数据非空

REPORT_FILE="$1"
REPORT_TYPE="$2"  # weekly or daily

# 检查文件存在
if [ ! -f "$REPORT_FILE" ]; then
    echo "错误：报告文件不存在: $REPORT_FILE"
    exit 1
fi

# 提取关键数据验证
if [ "$REPORT_TYPE" = "weekly" ]; then
    COMMITS=$(grep "| 总提交数" "$REPORT_FILE" | head -1 | sed -E 's/[^0-9]*([0-9]+).*/\1/' || echo "0")
    DEVELOPERS=$(grep "| 活跃开发者" "$REPORT_FILE" | head -1 | sed -E 's/[^0-9]*([0-9]+).*/\1/' || echo "0")
else
    COMMITS=$(grep "| 提交次数" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([0-9]+)\*\*.*/\1/' || echo "0")
    DEVELOPERS=$(grep "| 活跃开发者" "$REPORT_FILE" | head -1 | sed -E 's/.*\*\*([0-9]+)\*\*.*/\1/' || echo "0")
fi

if [ -z "$COMMITS" ] || [ "$COMMITS" = "0" ]; then
    echo "错误：提交数为空或为0"
    exit 1
fi

if [ -z "$DEVELOPERS" ] || [ "$DEVELOPERS" = "0" ]; then
    echo "错误：开发者数为空或为0"
    exit 1
fi

echo "验证通过：提交${COMMITS}次，${DEVELOPERS}位开发者"
exit 0
