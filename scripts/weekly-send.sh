#!/bin/bash
# 每周钉钉推送任务：推送上周周报到钉钉
# 执行时间：每周六8:00准时

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/reports/weekly-send.log"

echo "======================================" | tee -a $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始推送周报到钉钉" | tee -a $LOG_FILE

# 获取本周周报文件（2026-W01格式）
CURRENT_YEAR=$(date '+%Y')
WEEK_NUM=$(date '+%U')  # 获取周数
REPORT_FILE="$PROJECT_ROOT/reports/weekly/${CURRENT_YEAR}-W$(printf '%02d' $WEEK_NUM).md"

# 发送前验证数据
if [ -f "$SCRIPT_DIR/validate-before-send.sh" ] && [ -f "$REPORT_FILE" ]; then
    echo "   🔍 验证周报数据..." | tee -a $LOG_FILE
    if $SCRIPT_DIR/validate-before-send.sh "$REPORT_FILE" "weekly" >> $LOG_FILE 2>&1; then
        echo "   ✅ 数据验证通过" | tee -a $LOG_FILE
    else
        echo "   ❌ 数据验证失败，跳过发送" | tee -a $LOG_FILE
        exit 1
    fi
fi

# 推送到钉钉 - 使用v4版本脚本
if [ -f "$SCRIPT_DIR/send-to-dingtalk-weekly-v4.sh" ]; then
    $SCRIPT_DIR/send-to-dingtalk-weekly-v4.sh >> $LOG_FILE 2>&1
    echo "   ✅ 周报已发送到钉钉 (使用v4脚本)" | tee -a $LOG_FILE
else
    echo "   ⚠️  钉钉周报v4脚本不存在" | tee -a $LOG_FILE
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 周报推送完成" | tee -a $LOG_FILE
echo "======================================" | tee -a $LOG_FILE
