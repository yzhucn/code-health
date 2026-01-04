#!/bin/bash
# 批量生成历史日报和周报（优化版）
# 1. 跳过零提交的日报
# 2. 同时生成MD和HTML格式

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 批量生成12月日报和周报 ==="
echo ""
echo "📅 时间范围: 2025-12-01 至 2025-12-30"
echo ""

# 1. 生成所有日报 (12-01 到 12-30)
echo "1️⃣ 开始生成日报..."
echo ""

success_count=0
skipped_count=0
failed_count=0

for day in {1..30}; do
    date_str=$(printf '2025-12-%02d' $day)
    echo -n "  [$((day))/30] 生成 $date_str 日报... "

    # 生成MD格式
    if python3 daily-report.py $date_str > /tmp/daily_report_$day.log 2>&1; then
        # 检查是否有提交
        md_file="$(dirname $SCRIPT_DIR)/reports/daily/$date_str.md"
        commits=$(grep '| 提交次数' "$md_file" | head -1 | grep -oP '\*\*\d+\*\*' | tr -d '*' || echo "0")

        if [ "$commits" = "0" ]; then
            # 删除零提交的报告
            rm -f "$md_file"
            skipped_count=$((skipped_count + 1))
            echo "⏭️  (0次提交，已跳过)"
        else
            # 生成HTML格式
            python3 md2html.py "$md_file" > /dev/null 2>&1
            success_count=$((success_count + 1))
            echo "✅ ($commits 次提交)"
        fi
    else
        failed_count=$((failed_count + 1))
        echo "❌"
    fi
done

echo ""
echo "✅ 日报生成完成: 成功 $success_count 个, 跳过 $skipped_count 个 (0提交), 失败 $failed_count 个"
echo ""

# 2. 生成周报
echo "2️⃣ 开始生成周报..."
echo ""

# 12月的ISO周数
weeks=(
    "2025-W49"  # 12-01 (周一) 至 12-07 (周日)
    "2025-W50"  # 12-08 (周一) 至 12-14 (周日)
    "2025-W51"  # 12-15 (周一) 至 12-21 (周日)
    "2025-W52"  # 12-22 (周一) 至 12-28 (周日)
)

week_success=0
week_failed=0

for week in "${weeks[@]}"; do
    echo -n "  生成 $week 周报... "

    if python3 weekly-report.py $week > /dev/null 2>&1; then
        # 生成HTML格式
        md_file="$(dirname $SCRIPT_DIR)/reports/weekly/$week.md"
        python3 md2html.py "$md_file" > /dev/null 2>&1
        week_success=$((week_success + 1))
        echo "✅"
    else
        week_failed=$((week_failed + 1))
        echo "❌"
    fi
done

echo ""
echo "✅ 周报生成完成: 成功 $week_success 个, 失败 $week_failed 个"
echo ""

# 3. 生成仪表盘
echo "3️⃣ 生成可视化仪表盘..."
python3 dashboard-generator-range.py 30 > /dev/null 2>&1
echo "✅ 仪表盘已生成"
echo ""

# 4. 设置文件权限
echo "4️⃣ 设置文件权限..."
chmod -R 755 $(dirname $SCRIPT_DIR)/reports/
chmod -R 644 $(dirname $SCRIPT_DIR)/reports/daily/*.md 2>/dev/null || true
chmod -R 644 $(dirname $SCRIPT_DIR)/reports/daily/*.html 2>/dev/null || true
chmod -R 644 $(dirname $SCRIPT_DIR)/reports/weekly/*.md 2>/dev/null || true
chmod -R 644 $(dirname $SCRIPT_DIR)/reports/weekly/*.html 2>/dev/null || true
chmod -R 755 $(dirname $SCRIPT_DIR)/dashboard/
chmod 644 $(dirname $SCRIPT_DIR)/dashboard/*.html 2>/dev/null || true
echo "✅ 权限设置完成"
echo ""

# 5. 总结
echo "=== 生成完成 ==="
echo "日报: $success_count/$((success_count + skipped_count + failed_count)) (跳过 $skipped_count 个零提交)"
echo "周报: $week_success/$((week_success + week_failed))"
echo ""
echo "📁 报告目录:"
echo "  - 日报: $(dirname $SCRIPT_DIR)/reports/daily/"
echo "  - 周报: $(dirname $SCRIPT_DIR)/reports/weekly/"
echo "  - 仪表盘: $(dirname $SCRIPT_DIR)/dashboard/"
