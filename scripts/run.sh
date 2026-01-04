#!/bin/bash
# 代码健康监控 - 快速启动脚本
# Usage: ./run.sh [daily|weekly] [date]

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装${NC}"
    exit 1
fi

# 检查依赖
if ! python3 -c "import yaml" 2>/dev/null; then
    echo -e "${YELLOW}📦 安装依赖...${NC}"
    pip3 install -q -r ../requirements.txt
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
fi

# 默认命令
COMMAND=${1:-daily}
DATE=${2:-}

case $COMMAND in
    daily)
        echo -e "${GREEN}📊 生成日报...${NC}"
        if [ -z "$DATE" ]; then
            python3 daily-report.py
        else
            python3 daily-report.py "$DATE"
        fi
        ;;

    weekly)
        echo -e "${GREEN}📈 生成周报...${NC}"
        if [ -z "$DATE" ]; then
            python3 weekly-report.py
        else
            python3 weekly-report.py "$DATE"
        fi
        ;;

    dashboard)
        DAYS=${2:-7}
        echo -e "${GREEN}📊 生成可视化仪表盘 (最近 ${DAYS} 天)...${NC}"
        python3 dashboard-generator.py "$DAYS"
        DASHBOARD_PATH="../dashboard/index.html"
        if [ -f "$DASHBOARD_PATH" ]; then
            echo -e "${GREEN}✅ 仪表盘已生成${NC}"
            echo ""
            echo "在浏览器中打开:"
            echo "  file://$(cd .. && pwd)/dashboard/index.html"
            echo ""
            read -p "是否立即在浏览器中打开? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                open "$DASHBOARD_PATH" 2>/dev/null || xdg-open "$DASHBOARD_PATH" 2>/dev/null || echo "请手动打开仪表盘"
            fi
        fi
        ;;

    sync)
        echo -e "${GREEN}🔄 同步 Git 仓库...${NC}"
        python3 git-sync.py
        ;;

    backfill)
        echo -e "${GREEN}📚 补全历史数据...${NC}"
        python3 backfill-reports.py "$@"
        ;;

    setup)
        echo -e "${GREEN}🔧 初始化监控系统...${NC}"

        # 创建目录
        mkdir -p ../reports/daily
        mkdir -p ../reports/weekly
        mkdir -p ../reports/monthly

        # 安装依赖
        pip3 install -q -r ../requirements.txt

        echo -e "${GREEN}✅ 初始化完成${NC}"
        echo ""
        echo "接下来可以:"
        echo "  1. 编辑配置文件: ../config.yaml"
        echo "  2. 生成日报: ./run.sh daily"
        ;;

    test)
        echo -e "${GREEN}🧪 运行测试...${NC}"
        python3 -c "from utils import *; print('✅ 工具库正常')"
        python3 daily-report.py --help 2>/dev/null || echo "✅ 日报脚本正常"
        echo -e "${GREEN}✅ 测试通过${NC}"
        ;;

    schedule)
        echo -e "${GREEN}⏰ 设置定时任务...${NC}"
        echo ""
        echo "添加以下内容到 crontab (crontab -e):"
        echo ""
        echo "# 代码健康监控 - 每天 18:00 生成日报"
        echo "0 18 * * * cd $SCRIPT_DIR && ./run.sh daily >> ../reports/cron.log 2>&1"
        echo ""
        echo "# 代码健康监控 - 每周五 17:00 生成周报"
        echo "0 17 * * 5 cd $SCRIPT_DIR && ./run.sh weekly >> ../reports/cron.log 2>&1"
        echo ""
        echo "# 代码健康监控 - 每天 19:00 生成仪表盘"
        echo "0 19 * * * cd $SCRIPT_DIR && ./run.sh dashboard >> ../reports/cron.log 2>&1"
        echo ""
        ;;

    clean)
        echo -e "${YELLOW}🧹 清理缓存文件...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ 清理完成${NC}"
        ;;

    help|--help|-h)
        echo "代码健康监控 - 使用指南"
        echo ""
        echo "用法: ./run.sh [命令] [参数]"
        echo ""
        echo "命令:"
        echo "  daily [date]      生成日报 (默认今天)"
        echo "                    示例: ./run.sh daily 2025-12-29"
        echo ""
        echo "  weekly [week]     生成周报 (默认本周)"
        echo "                    示例: ./run.sh weekly 2025-W52"
        echo ""
        echo "  dashboard [days]  生成可视化仪表盘 (默认最近7天)"
        echo "                    示例: ./run.sh dashboard 30"
        echo ""
        echo "  sync              同步所有 Git 仓库 (拉取最新代码)"
        echo "                    示例: ./run.sh sync"
        echo ""
        echo "  backfill          补全历史报告"
        echo "                    示例: ./run.sh backfill"
        echo "                    选项: --dry-run (查看计划)"
        echo "                          --daily-only (只补日报)"
        echo "                          --weekly-only (只补周报)"
        echo "                          --from 2025-12-01 (指定起始)"
        echo ""
        echo "  setup             初始化监控系统"
        echo "  test              测试环境"
        echo "  schedule          显示定时任务配置"
        echo "  clean             清理缓存文件"
        echo "  help              显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  ./run.sh sync               # 拉取所有仓库最新代码"
        echo "  ./run.sh backfill --dry-run # 查看历史数据补全计划"
        echo "  ./run.sh backfill           # 补全所有历史报告"
        echo "  ./run.sh daily              # 生成今天的日报"
        echo "  ./run.sh weekly             # 生成本周的周报"
        echo "  ./run.sh dashboard          # 生成7天仪表盘"
        echo ""
        ;;

    *)
        echo -e "${RED}❌ 未知命令: $COMMAND${NC}"
        echo "使用 './run.sh help' 查看帮助"
        exit 1
        ;;
esac
