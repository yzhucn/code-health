#!/bin/bash
# 每周任务：克隆 -> 生成周报 -> 转HTML -> 更新仪表盘 -> 清理 -> 推送钉钉

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/reports/weekly-job.log"

echo "======================================" | tee -a $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始周报任务" | tee -a $LOG_FILE

# 1. 克隆代码 (允许部分失败)
echo "1️⃣ 克隆代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/auto-clone-repos.sh || echo "   ⚠️  部分仓库克隆失败，继续执行" | tee -a $LOG_FILE

# 2. 生成周报 (MD格式)
echo "2️⃣ 生成周报..." | tee -a $LOG_FILE
cd $SCRIPT_DIR
./run.sh weekly >> $LOG_FILE 2>&1

# 3. 转换为HTML格式
echo "3️⃣ 转换为HTML..." | tee -a $LOG_FILE
# 计算上周的ISO周数
LAST_WEEK=$(date -d "last saturday" +%G-W%V)
MD_FILE="$PROJECT_ROOT/reports/weekly/$LAST_WEEK.md"
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

# 5. 清理代码
echo "5️⃣ 清理代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/cleanup-repos.sh

# 6. 推送到钉钉
echo "6️⃣ 推送到钉钉..." | tee -a $LOG_FILE
if [ -f "$SCRIPT_DIR/send-to-dingtalk-weekly.sh" ]; then
    $SCRIPT_DIR/send-to-dingtalk-weekly.sh >> $LOG_FILE 2>&1
    echo "   ✅ 钉钉消息已发送" | tee -a $LOG_FILE
else
    echo "   ⚠️  钉钉脚本不存在" | tee -a $LOG_FILE
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 周报任务完成" | tee -a $LOG_FILE
echo "======================================" | tee -a $LOG_FILE
