# Code Health Monitor - CLAUDE.md

本文件为 Claude AI 助手提供项目上下文，避免每次都需要读取整个代码库。

## 项目概述

代码健康监控系统，用于分析 Git 仓库的提交活动，生成日报/周报/月报，并通过钉钉等渠道通知团队。

### 版本说明

| 版本 | 目录 | 运行方式 | 数据源 |
|------|------|----------|--------|
| V1 | `scripts/` | Shell + Python 脚本 | 本地克隆仓库 |
| V2 | `src/` | Python 模块 + Docker | API (Codeup/GitHub/GitLab) |

**重要**: V1 和 V2 是并存的，V2 是 V1 的重构版本，支持 Docker 部署和多平台 API。

---

## 目录结构

```
.code-health/
├── CLAUDE.md              # 本文件 - 项目总览
├── scripts/               # V1 脚本版本
│   └── CLAUDE.md          # V1 详细文档
├── src/                   # V2 模块版本
│   └── CLAUDE.md          # V2 详细文档
├── reports/               # 报告输出目录 (已 gitignore)
│   ├── daily/             # 日报 (YYYY-MM-DD.md/.html)
│   ├── weekly/            # 周报 (YYYY-Wxx.md/.html)
│   └── monthly/           # 月报 (YYYY-MM.md/.html)
├── dashboard/             # 可视化仪表盘 (已 gitignore)
├── config.yaml            # 配置文件 (已 gitignore)
├── .env.example           # 环境变量示例
├── docker-compose.yml     # Docker 部署配置
├── Dockerfile             # Docker 镜像定义
├── entrypoint.sh          # Docker 入口脚本
└── nginx.conf             # Nginx 配置 (Web 服务)
```

---

## 安全检查清单

### 敏感信息保护 (必须遵守)

以下文件**绝对不能**提交到 GitHub：

| 文件 | 内容 | 状态 |
|------|------|------|
| `config.yaml` | 包含 Token/Webhook | .gitignore 已排除 |
| `config-ecs.yaml` | ECS 部署配置 | .gitignore 已排除 |
| `.env` | 环境变量 | .gitignore 已排除 |
| `.env.test` | 测试用凭证 | .gitignore 已排除 |
| `repos-list.txt` | 私有仓库 URL | .gitignore 已排除 |
| `reports/` | 包含开发者信息 | .gitignore 已排除 |

### 代码提交前检查

1. **检查 git status**: 确认没有敏感文件被 staged
2. **检查 .gitignore**: 新增配置文件要加入排除列表
3. **检查 Token**: 代码中不能硬编码任何 Token/Secret
4. **检查报告**: 生成的报告不能包含私密信息

```bash
# 提交前运行检查
git status
git diff --staged | grep -i "token\|secret\|password\|key"
```

### 发送钉钉消息前验证

V1 使用 `scripts/validate-before-send.sh` 验证数据：
- 检查报告文件是否存在
- 检查提交次数不为 0
- 检查开发者数不为 0

V2 在 `src/notifiers/dingtalk.py` 中进行验证：
- 检查 Webhook 配置是否有效
- 检查消息格式是否正确

---

## 环境变量

### 必需变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `GIT_PLATFORM` | Git 平台 | `codeup` / `github` / `gitlab` |
| `CODEUP_TOKEN` | 云效访问令牌 | `pt-xxx` |
| `CODEUP_ORG_ID` | 云效企业 ID | `your_org_id` |
| `CODEUP_PROJECT` | 项目命名空间 | `your-project` |

### 可选变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PROJECT_NAME` | 项目名称 | 代码健康监控 |
| `WEB_BASE_URL` | Web 访问地址 | http://localhost:8080 |
| `CODE_HEALTH_OUTPUT` | 报告输出目录 | reports |
| `DINGTALK_ENABLED` | 是否启用钉钉 | false |
| `DINGTALK_WEBHOOK` | 钉钉 Webhook | - |
| `DINGTALK_SECRET` | 钉钉加签密钥 | - |

---

## 常用命令

### V1 (脚本版本)

```bash
cd scripts/

# 生成报告
./run.sh daily              # 日报
./run.sh weekly             # 周报
./run.sh monthly            # 月报

# 完整流程 (克隆 -> 报告 -> HTML -> 钉钉)
./daily-job.sh
./weekly-job.sh
./monthly-job.sh

# 工具脚本
python3 md2html.py reports/daily/2025-01-10.md    # 转 HTML
python3 dashboard-generator-range.py 7            # 仪表盘
python3 generate-index.py                         # 索引页面
./validate-before-send.sh reports/daily/xxx.md daily  # 验证数据
```

### V2 (Docker 版本)

```bash
# 本地运行
source .env.test
python -m src.main daily --date 2025-01-10 --output reports
python -m src.main weekly --week 2025-W02 --output reports
python -m src.main monthly --month 2025-12 --output reports
python -m src.main html --output reports
python -m src.main dashboard --output reports

# Docker 运行
docker-compose run --rm code-health daily
docker-compose run --rm code-health weekly
docker-compose run --rm code-health monthly
docker-compose run --rm code-health notify daily
```

---

## 报告类型说明

### 日报内容
- 提交次数、活跃开发者、涉及仓库
- 代码变更量 (新增/删除/净增)
- 各仓库变更统计
- 风险预警 (加班/深夜/周末提交)
- 健康评分 (0-100)
- TOP 开发者详情

### 周报内容
- 贡献排行榜 (LOC 统计)
- 团队总产出
- 仓库分布
- 工作时间分布 (热力图)
- 提交节奏分析
- 代码质量趋势 (震荡率/返工率)
- 改进建议

### 月报内容
- 月度总览 (核心指标)
- 贡献排行榜
- 每周趋势对比
- 健康指标 (工作时间分布)
- 代码质量 (提交粒度分析)
- 文件修改热点
- 下月计划建议

---

## 故障排查

### 报告数据为空
1. 检查日期范围是否正确
2. 检查 API Token 是否有效
3. 检查仓库是否有该时间段的提交

### 钉钉消息发送失败
1. 检查 DINGTALK_WEBHOOK 配置
2. 检查 DINGTALK_SECRET 加签配置
3. 使用 `scripts/debug-dingtalk.sh` 调试

### Docker 容器无法访问
1. 检查 nginx.conf 配置
2. 检查 docker-compose.yml 端口映射
3. 检查报告目录挂载是否正确

---

## 版本对比

| 功能 | V1 | V2 |
|------|----|----|
| 日报生成 | daily-report.py | src/reporters/daily.py |
| 周报生成 | weekly-report.py | src/reporters/weekly.py |
| 月报生成 | monthly-report.py | src/reporters/monthly.py |
| HTML 生成 | md2html.py | src/utils/html_generator.py |
| 索引页面 | generate-index.py | src/utils/index_generator.py |
| 仪表盘 | dashboard-generator-range.py | src/utils/dashboard_generator.py |
| 钉钉通知 | send-to-dingtalk.sh | src/notifiers/dingtalk.py |
| 数据验证 | validate-before-send.sh | (内置于 reporter) |
| 数据源 | 本地 Git 仓库 | API (Codeup/GitHub/GitLab) |
| 部署方式 | Cron + ECS | Docker Compose |

---

## 更新日志

### 2026-01-13
- 完成 V2 Docker 版本验证
- 添加 .env.test 私密测试配置
- 创建 CLAUDE.md 文档体系

### 2026-01-12
- 移植 dashboard-generator-range.py 到 V2
- 修复 index.html 历史报告入口
- 验证 V1 vs V2 数据一致性
