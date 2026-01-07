#!/bin/bash
# 归档老旧报告
# 日报：30天前 -> reports/archive/daily/YYYY/MM/
# 周报：12周前(84天) -> reports/archive/weekly/YYYY/

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ARCHIVE_ROOT="$PROJECT_ROOT/reports/archive"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/archive.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

echo "======================================" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始归档任务" | tee -a "$LOG_FILE"

# 计数器
DAILY_COUNT=0
WEEKLY_COUNT=0

# 归档30天前的日报
echo "1️⃣ 归档30天前的日报..." | tee -a "$LOG_FILE"
if [ -d "$PROJECT_ROOT/reports/daily" ]; then
    find "$PROJECT_ROOT/reports/daily" -name "*.md" -mtime +30 2>/dev/null | while read file; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            date_str=${filename%.md}

            # 从文件名提取年月 (格式: YYYY-MM-DD.md)
            year=${date_str:0:4}
            month=${date_str:5:2}

            # 创建归档目录
            archive_dir="$ARCHIVE_ROOT/daily/$year/$month"
            mkdir -p "$archive_dir"

            # 移动文件
            if mv "$file" "$archive_dir/" 2>/dev/null; then
                echo "   ✅ 已归档: $filename -> daily/$year/$month/" | tee -a "$LOG_FILE"
                DAILY_COUNT=$((DAILY_COUNT + 1))
            else
                echo "   ⚠️  归档失败: $filename" | tee -a "$LOG_FILE"
            fi
        fi
    done
    echo "   📊 日报归档数量: $DAILY_COUNT" | tee -a "$LOG_FILE"
else
    echo "   ⚠️  日报目录不存在" | tee -a "$LOG_FILE"
fi

# 归档12周前的周报
echo "2️⃣ 归档12周前的周报..." | tee -a "$LOG_FILE"
if [ -d "$PROJECT_ROOT/reports/weekly" ]; then
    find "$PROJECT_ROOT/reports/weekly" -name "*.md" -mtime +84 2>/dev/null | while read file; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")

            # 从文件名提取年份 (格式: YYYY-MM-DD.md 或 YYYY-WXX.md)
            year=${filename:0:4}

            # 创建归档目录
            archive_dir="$ARCHIVE_ROOT/weekly/$year"
            mkdir -p "$archive_dir"

            # 移动文件
            if mv "$file" "$archive_dir/" 2>/dev/null; then
                echo "   ✅ 已归档: $filename -> weekly/$year/" | tee -a "$LOG_FILE"
                WEEKLY_COUNT=$((WEEKLY_COUNT + 1))
            else
                echo "   ⚠️  归档失败: $filename" | tee -a "$LOG_FILE"
            fi
        fi
    done
    echo "   📊 周报归档数量: $WEEKLY_COUNT" | tee -a "$LOG_FILE"
else
    echo "   ⚠️  周报目录不存在" | tee -a "$LOG_FILE"
fi

# 总结
echo "✅ 归档任务完成" | tee -a "$LOG_FILE"
echo "   - 日报: $DAILY_COUNT 个文件" | tee -a "$LOG_FILE"
echo "   - 周报: $WEEKLY_COUNT 个文件" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - 归档任务结束" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"
