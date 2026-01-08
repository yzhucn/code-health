#!/bin/bash
# 每月任务：克隆 -> 生成月报 -> 转HTML -> 更新仪表盘 -> 清理 -> 推送钉钉

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/reports/monthly-job.log"

echo "======================================" | tee -a $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始月报任务" | tee -a $LOG_FILE

# 支持指定月份参数，默认为上个月
if [ -n "$1" ]; then
    MONTH="$1"
else
    # 获取上个月
    MONTH=$(date -d "last month" +%Y-%m 2>/dev/null || date -v-1m +%Y-%m)
fi
echo "   📅 目标月份: $MONTH" | tee -a $LOG_FILE

# 1. 克隆代码 (允许部分失败)
echo "1️⃣ 克隆代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/auto-clone-repos.sh || echo "   ⚠️  部分仓库克隆失败，继续执行" | tee -a $LOG_FILE

# 2. 生成月报 (MD格式)
echo "2️⃣ 生成月报..." | tee -a $LOG_FILE
cd $SCRIPT_DIR
python3 monthly-report.py "$MONTH" >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 月报已生成" | tee -a $LOG_FILE
else
    echo "   ❌ 月报生成失败" | tee -a $LOG_FILE
fi

# 3. 转换为HTML格式
echo "3️⃣ 转换为HTML..." | tee -a $LOG_FILE
MD_FILE="$PROJECT_ROOT/reports/monthly/$MONTH.md"
if [ -f "$MD_FILE" ]; then
    python3 md2html.py "$MD_FILE" >> $LOG_FILE 2>&1
    echo "   ✅ HTML已生成" | tee -a $LOG_FILE
else
    echo "   ⚠️  MD文件不存在: $MD_FILE" | tee -a $LOG_FILE
fi

# 4. 更新仪表盘 (所有时间范围)
echo "4️⃣ 更新仪表盘..." | tee -a $LOG_FILE
cd $SCRIPT_DIR
python3 dashboard-generator-range.py 7 >> $LOG_FILE 2>&1
python3 dashboard-generator-range.py 14 >> $LOG_FILE 2>&1
python3 dashboard-generator-range.py 30 >> $LOG_FILE 2>&1
python3 dashboard-generator-range.py 60 >> $LOG_FILE 2>&1
python3 dashboard-generator-range.py 90 >> $LOG_FILE 2>&1
chmod 644 $PROJECT_ROOT/dashboard/*.html >> $LOG_FILE 2>&1
echo "   ✅ 仪表盘已更新（5个时间范围）" | tee -a $LOG_FILE

# 5. 设置报告文件权限
echo "5️⃣ 设置文件权限..." | tee -a $LOG_FILE
chmod 644 $PROJECT_ROOT/reports/monthly/*.html 2>/dev/null || true
chmod 644 $PROJECT_ROOT/reports/monthly/*.md 2>/dev/null || true
echo "   ✅ 权限已设置" | tee -a $LOG_FILE

# 6. 清理代码
echo "6️⃣ 清理代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/cleanup-repos.sh

# 7. 推送到钉钉
echo "7️⃣ 推送到钉钉..." | tee -a $LOG_FILE
if [ -f "$SCRIPT_DIR/send-monthly-report.sh" ]; then
    $SCRIPT_DIR/send-monthly-report.sh "$MONTH" >> $LOG_FILE 2>&1
    echo "   ✅ 钉钉消息已发送" | tee -a $LOG_FILE
else
    echo "   ⚠️  钉钉脚本不存在" | tee -a $LOG_FILE
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 月报任务完成" | tee -a $LOG_FILE
echo "======================================" | tee -a $LOG_FILE
