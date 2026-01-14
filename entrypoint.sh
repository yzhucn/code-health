#!/bin/bash
# Code Health Monitor - Docker 入口脚本
# 用法: ./entrypoint.sh [命令] [选项]
#
# 命令:
#   daily   - 生成日报
#   weekly  - 生成周报
#   monthly - 生成月报
#   --help  - 显示帮助信息

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
╔═══════════════════════════════════════════════════════════════╗
║           Code Health Monitor - 代码健康监控系统              ║
╚═══════════════════════════════════════════════════════════════╝

用法: docker run code-health [命令] [选项]

命令:
  daily       生成日报（昨日代码提交分析）
  weekly      生成周报（本周代码健康分析）
  monthly     生成月报（本月代码健康分析）
  html        重新生成所有 HTML 报告和索引页
  dashboard   生成可视化仪表盘
  --help      显示此帮助信息

环境变量:
  必需:
    GIT_TOKEN         Git 平台访问令牌
    GIT_PLATFORM      Git 平台类型 (github/gitlab/codeup/git)

  可选:
    GIT_ORG           组织/用户名
    GIT_BASE_URL      自托管 Git 服务器地址
    DINGTALK_ENABLED  启用钉钉通知 (true/false)
    DINGTALK_WEBHOOK  钉钉机器人 Webhook
    DINGTALK_SECRET   钉钉机器人签名密钥
    FEISHU_ENABLED    启用飞书通知 (true/false)
    FEISHU_WEBHOOK    飞书机器人 Webhook
    WEB_BASE_URL      报告访问基础 URL

示例:
  # 生成日报
  docker run -e GIT_TOKEN=xxx -e GIT_PLATFORM=github \\
      -v ./reports:/app/reports code-health daily

  # 使用 docker-compose
  docker-compose run code-health daily

配置文件:
  可以挂载 config/config.yaml 覆盖默认配置:
  -v ./config/config.yaml:/app/config/config.yaml:ro

更多信息: https://github.com/your-org/code-health
EOF
}

# 检查必需的环境变量
check_env() {
    local missing=0

    if [ -z "$GIT_TOKEN" ]; then
        log_error "缺少环境变量: GIT_TOKEN"
        missing=1
    fi

    if [ -z "$GIT_PLATFORM" ]; then
        log_warn "未设置 GIT_PLATFORM，使用默认值: git"
        export GIT_PLATFORM="git"
    fi

    if [ $missing -eq 1 ]; then
        echo ""
        log_info "请设置必需的环境变量，或使用 --help 查看帮助"
        exit 1
    fi
}

# 显示配置信息
show_config() {
    log_info "当前配置:"
    echo "  - GIT_PLATFORM: ${GIT_PLATFORM:-git}"
    echo "  - GIT_ORG: ${GIT_ORG:-未设置}"
    echo "  - DINGTALK_ENABLED: ${DINGTALK_ENABLED:-false}"
    echo "  - FEISHU_ENABLED: ${FEISHU_ENABLED:-false}"
    echo "  - WEB_BASE_URL: ${WEB_BASE_URL:-http://localhost:8080}"
    echo ""
}

# 主函数
main() {
    local cmd="${1:-}"
    shift 2>/dev/null || true  # 移除第一个参数，保留剩余参数

    case "$cmd" in
        --help|-h|help)
            show_help
            exit 0
            ;;
        daily)
            check_env
            show_config
            log_info "开始生成日报..."
            export CODE_HEALTH_OUTPUT=/app/reports
            python -m src.main daily --output /app/reports "$@"
            log_success "日报生成完成"
            # 生成仪表盘
            log_info "更新仪表盘..."
            python -m src.main dashboard --output /app/reports --reports-dir /app/reports || log_warn "仪表盘生成失败，继续执行"
            # 如果启用了通知，自动发送（只在不指定日期时发送）
            if [ -z "$1" ] && ([ "$DINGTALK_ENABLED" = "true" ] || [ "$FEISHU_ENABLED" = "true" ]); then
                log_info "发送通知..."
                python -m src.main notify daily
            fi
            ;;
        weekly)
            check_env
            show_config
            log_info "开始生成周报..."
            export CODE_HEALTH_OUTPUT=/app/reports
            python -m src.main weekly --output /app/reports "$@"
            log_success "周报生成完成"
            # 生成仪表盘
            log_info "更新仪表盘..."
            python -m src.main dashboard --output /app/reports --reports-dir /app/reports || log_warn "仪表盘生成失败，继续执行"
            # 如果启用了通知，自动发送（只在不指定周时发送）
            if [ -z "$1" ] && ([ "$DINGTALK_ENABLED" = "true" ] || [ "$FEISHU_ENABLED" = "true" ]); then
                log_info "发送通知..."
                python -m src.main notify weekly
            fi
            ;;
        monthly)
            check_env
            show_config
            log_info "开始生成月报..."
            export CODE_HEALTH_OUTPUT=/app/reports
            python -m src.main monthly --output /app/reports "$@"
            log_success "月报生成完成"
            # 生成仪表盘
            log_info "更新仪表盘..."
            python -m src.main dashboard --output /app/reports --reports-dir /app/reports || log_warn "仪表盘生成失败，继续执行"
            # 如果启用了通知，自动发送（只在不指定月时发送）
            if [ -z "$1" ] && ([ "$DINGTALK_ENABLED" = "true" ] || [ "$FEISHU_ENABLED" = "true" ]); then
                log_info "发送通知..."
                python -m src.main notify monthly
            fi
            ;;
        html)
            log_info "重新生成所有 HTML 报告..."
            export CODE_HEALTH_OUTPUT=/app/reports
            python -m src.main html --output /app/reports
            log_success "HTML 报告生成完成"
            ;;
        dashboard)
            check_env
            show_config
            log_info "生成可视化仪表盘..."
            export CODE_HEALTH_OUTPUT=/app/reports
            python -m src.main dashboard --output /app/reports
            log_success "仪表盘生成完成"
            ;;
        "")
            show_help
            exit 0
            ;;
        *)
            log_error "未知命令: $cmd"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
