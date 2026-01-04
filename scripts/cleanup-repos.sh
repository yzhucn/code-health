#!/bin/bash
# 删除代码仓库，不留痕迹

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPOS_DIR="${REPOS_DIR:-$(dirname "$PROJECT_ROOT")/repos}"
LOG_FILE="$PROJECT_ROOT/reports/cleanup.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始清理代码仓库..." | tee -a $LOG_FILE

if [ -d "$REPOS_DIR" ]; then
    # 获取目录大小
    SIZE=$(du -sh $REPOS_DIR | cut -f1)
    echo "清理前大小: $SIZE" | tee -a $LOG_FILE

    # 删除所有代码
    rm -rf $REPOS_DIR/*

    echo "✅ 代码仓库已清理" | tee -a $LOG_FILE
else
    echo "⚠️  代码目录不存在，无需清理" | tee -a $LOG_FILE
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 清理完成" | tee -a $LOG_FILE
