#!/bin/bash
# 每日数据准备任务：克隆 -> 生成报告 -> 转HTML -> 更新仪表盘 -> 清理
# 执行时间：每天7:45，为8:00的钉钉推送准备数据

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/reports/daily-prepare.log"
# 加载环境变量
[ -f /etc/environment ] && source /etc/environment

echo "======================================" | tee -a $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始数据准备任务" | tee -a $LOG_FILE

# 1. 克隆代码 (允许部分失败)
echo "1️⃣ 克隆代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/auto-clone-repos.sh || echo "   ⚠️  部分仓库克隆失败，继续执行" | tee -a $LOG_FILE

# 2. 生成日报 (MD格式)
echo "2️⃣ 生成日报..." | tee -a $LOG_FILE
cd $SCRIPT_DIR
./run.sh daily >> $LOG_FILE 2>&1

# 3. 转换为HTML格式
echo "3️⃣ 转换为HTML..." | tee -a $LOG_FILE
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
MD_FILE="$PROJECT_ROOT/reports/daily/$YESTERDAY.md"
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
python3 dashboard-generator-range.py all >> $LOG_FILE 2>&1
chmod 644 "$PROJECT_ROOT"/dashboard/*.html >> $LOG_FILE 2>&1
echo "   ✅ 仪表盘已更新（6个时间范围 + 全周期）" | tee -a $LOG_FILE

# 5. 清理代码（安全第一）
echo "5️⃣ 清理代码仓库..." | tee -a $LOG_FILE
$SCRIPT_DIR/cleanup-repos.sh
echo "   ✅ 代码已清理，保证安全" | tee -a $LOG_FILE

echo "$(date '+%Y-%m-%d %H:%M:%S') - 数据准备完成，等待8:00推送钉钉" | tee -a $LOG_FILE
echo "======================================" | tee -a $LOG_FILE
