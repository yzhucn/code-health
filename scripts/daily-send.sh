#!/bin/bash
# 每日钉钉推送任务：推送昨日日报到钉钉
# 执行时间：每天8:00准时

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/reports/daily-send.log"

echo "======================================" | tee -a $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始推送钉钉消息" | tee -a $LOG_FILE

# 推送到钉钉 - 使用v3版本脚本
if [ -f "$SCRIPT_DIR/send-to-dingtalk-daily-v3.sh" ]; then
    $SCRIPT_DIR/send-to-dingtalk-daily-v3.sh >> $LOG_FILE 2>&1
    echo "   ✅ 钉钉消息已发送 (使用v3脚本)" | tee -a $LOG_FILE
else
    echo "   ⚠️  钉钉日报v3脚本不存在" | tee -a $LOG_FILE
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 钉钉推送完成" | tee -a $LOG_FILE
echo "======================================" | tee -a $LOG_FILE
