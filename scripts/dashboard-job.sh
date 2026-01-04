#!/bin/bash
# 仪表盘任务：克隆 -> 生成仪表盘 -> 清理

set -e

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/reports/dashboard-job.log"

echo "======================================" | tee -a $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始仪表盘任务" | tee -a $LOG_FILE

# 1. 克隆代码
echo "1️⃣ 克隆代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/auto-clone-repos.sh

# 2. 生成仪表盘
echo "2️⃣ 生成仪表盘..." | tee -a $LOG_FILE
cd $SCRIPT_DIR
./run.sh dashboard >> $LOG_FILE 2>&1

# 3. 清理代码
echo "3️⃣ 清理代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/cleanup-repos.sh

echo "$(date '+%Y-%m-%d %H:%M:%S') - 仪表盘任务完成" | tee -a $LOG_FILE
echo "======================================" | tee -a $LOG_FILE
