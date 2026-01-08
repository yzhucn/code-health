#!/bin/bash
# 自动克隆仓库脚本
# 用于 ECS 上不留存代码的模式：每次任务前克隆，任务后删除
#
# 使用方法：
# 1. 在 config.yaml 中配置仓库路径（如果仓库在本地已存在）
# 2. 如需自动克隆远程仓库，请创建 repos-list.txt 文件
# 3. 设置环境变量：export GIT_TOKEN="your_token" (可选)

set -e

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/config.yaml"

# repos-list.txt 格式示例：
# repo-name|https://git.example.com/org/repo-name.git
# another-repo|https://git.example.com/org/another-repo.git
REPOS_LIST_FILE="$PROJECT_ROOT/repos-list.txt"

# 仓库克隆目标目录
REPOS_DIR="${REPOS_DIR:-$PROJECT_ROOT/../repos}"
LOG_FILE="$PROJECT_ROOT/reports/clone.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "=== 仓库自动克隆脚本 ===" | tee -a "$LOG_FILE"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "目标目录: $REPOS_DIR" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 检查是否有仓库列表文件
if [ ! -f "$REPOS_LIST_FILE" ]; then
    echo "⚠️  未找到 repos-list.txt 文件" | tee -a "$LOG_FILE"
    echo "说明：此脚本用于自动克隆远程仓库到临时目录" | tee -a "$LOG_FILE"
    echo "如果你的仓库已在本地，请在 config.yaml 中配置路径即可" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "如需使用自动克隆功能，请创建 repos-list.txt 文件：" | tee -a "$LOG_FILE"
    echo "格式：repo-name|https://git.example.com/org/repo.git" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "示例 repos-list.txt 内容：" | tee -a "$LOG_FILE"
    cat > "$PROJECT_ROOT/repos-list.example.txt" << 'EOF'
# 仓库列表配置文件
# 格式：仓库名|仓库URL
# 注意：
# 1. 每行一个仓库
# 2. 使用 | 分隔仓库名和URL
# 3. # 开头的行为注释

# 示例（请修改为你的实际仓库）
my-backend|https://github.com/yourname/my-backend.git
my-frontend|https://github.com/yourname/my-frontend.git

# 如果仓库是私有的，需要配置 Git 凭证：
# 方式1：使用环境变量
#   export GIT_TOKEN="your_token"
#   仓库URL格式: https://${USERNAME}:${GIT_TOKEN}@github.com/org/repo.git
#
# 方式2：使用 git credential helper
#   git config --global credential.helper store
#
# 方式3：使用 SSH (推荐)
#   仓库URL格式: git@github.com:org/repo.git
EOF
    echo "  已创建示例文件: repos-list.example.txt" | tee -a "$LOG_FILE"
    exit 0
fi

# 读取 Git Token（如果需要）
if [ -n "$GIT_TOKEN" ]; then
    echo "✅ 检测到 GIT_TOKEN 环境变量" | tee -a "$LOG_FILE"
else
    echo "ℹ️  未设置 GIT_TOKEN，将使用 git 默认凭证" | tee -a "$LOG_FILE"
fi

# 创建目标目录
mkdir -p "$REPOS_DIR"
cd "$REPOS_DIR"

# 统计变量
SUCCESS_COUNT=0
FAILED_COUNT=0
FAILED_REPOS=()

# 读取并克隆仓库
while IFS='|' read -r repo_name repo_url || [ -n "$repo_name" ]; do
    # 跳过注释和空行
    if [[ "$repo_name" =~ ^#.* ]] || [ -z "$repo_name" ]; then
        continue
    fi

    # 去除前后空格
    repo_name=$(echo "$repo_name" | xargs)
    repo_url=$(echo "$repo_url" | xargs)

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
    echo "📦 克隆仓库: $repo_name" | tee -a "$LOG_FILE"

    # 如果目录已存在，先删除
    if [ -d "$repo_name" ]; then
        echo "  目录已存在，删除旧版本..." | tee -a "$LOG_FILE"
        rm -rf "$repo_name"
    fi

    # 如果配置了 Token，插入到 URL 中
    if [ -n "$GIT_TOKEN" ] && [[ "$repo_url" == https://* ]]; then
        # 提取域名和路径
        domain=$(echo "$repo_url" | sed -E 's|https://([^/]+)/.*|\1|')
        path=$(echo "$repo_url" | sed -E 's|https://[^/]+/(.*)|\1|')
        auth_url="https://token:${GIT_TOKEN}@${domain}/${path}"
        echo "  使用 Token 认证..." | tee -a "$LOG_FILE"
    else
        auth_url="$repo_url"
    fi

    # 克隆仓库（所有分支）
    if git clone --mirror "$auth_url" "$repo_name/.git" >> "$LOG_FILE" 2>&1; then
        cd "$repo_name"
        git config --bool core.bare false >> "$LOG_FILE" 2>&1
        git checkout >> "$LOG_FILE" 2>&1 || true
        cd ..

        echo "  ✅ 克隆成功" | tee -a "$LOG_FILE"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "  ❌ 克隆失败" | tee -a "$LOG_FILE"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FAILED_REPOS+=("$repo_name")
    fi
done < "$REPOS_LIST_FILE"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📊 克隆统计:" | tee -a "$LOG_FILE"
echo "  成功: $SUCCESS_COUNT 个" | tee -a "$LOG_FILE"
echo "  失败: $FAILED_COUNT 个" | tee -a "$LOG_FILE"

if [ $FAILED_COUNT -gt 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "❌ 失败的仓库:" | tee -a "$LOG_FILE"
    for repo in "${FAILED_REPOS[@]}"; do
        echo "  - $repo" | tee -a "$LOG_FILE"
    done
fi

echo "" | tee -a "$LOG_FILE"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"

# 如果有失败，以非0状态退出（但允许部分失败）
if [ $SUCCESS_COUNT -eq 0 ] && [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi

exit 0
