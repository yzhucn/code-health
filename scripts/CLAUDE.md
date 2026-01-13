# V1 Scripts - CLAUDE.md

V1 版本使用 Shell + Python 脚本，数据源为本地克隆的 Git 仓库。

## 目录结构

```
scripts/
├── CLAUDE.md                 # 本文件
│
├── # 核心报告生成
├── daily-report.py           # 日报生成
├── weekly-report.py          # 周报生成
├── monthly-report.py         # 月报生成
├── run.sh                    # 统一入口脚本
│
├── # HTML 和可视化
├── md2html.py                # Markdown 转 HTML
├── generate-index.py         # 生成 index.html 索引页
├── dashboard-generator-range.py  # 可视化仪表盘生成
│
├── # 完整流程脚本 (Cron Job)
├── daily-job.sh              # 每日完整流程
├── weekly-job.sh             # 每周完整流程
├── monthly-job.sh            # 每月完整流程
├── dashboard-job.sh          # 仪表盘更新任务
│
├── # 仓库管理
├── auto-clone-repos.sh       # 自动克隆仓库
├── cleanup-repos.sh          # 清理仓库
├── git-sync.py               # Git 同步
├── sync-repos-list.py        # 同步仓库列表
│
├── # 钉钉通知
├── send-to-dingtalk.sh       # 发送日报到钉钉
├── send-to-dingtalk-weekly.sh    # 发送周报到钉钉
├── send-to-dingtalk-weekly-v4.sh # 周报钉钉格式 V4
├── send-to-dingtalk-daily-v3.sh  # 日报钉钉格式 V3
├── send-monthly-report.sh    # 发送月报到钉钉
│
├── # 验证和调试
├── validate-before-send.sh   # 发送前数据验证
├── debug-dingtalk.sh         # 钉钉调试
├── test-dingtalk-keywords.sh # 测试钉钉关键词
├── test-sign.sh              # 测试签名
├── test-web-access.sh        # 测试 Web 访问
│
├── # 工具脚本
├── utils.py                  # 通用工具函数
├── backfill-reports.py       # 补充历史报告
├── add-repo-classification.py    # 添加仓库分类
├── archive-old-reports.sh    # 归档旧报告
├── batch-generate-reports.sh # 批量生成报告
│
├── # 准备和发送分离脚本
├── daily-prepare.sh          # 日报准备阶段
├── weekly-prepare.sh         # 周报准备阶段
├── daily-send.sh             # 日报发送阶段
└── weekly-send.sh            # 周报发送阶段
```

---

## 核心文件说明

### daily-report.py
日报生成脚本，分析昨日提交数据。

**功能**:
- 统计提交次数、活跃开发者、涉及仓库
- 计算代码变更量 (新增/删除/净增)
- 检测风险提交 (加班/深夜/周末)
- 计算健康评分
- 生成 Markdown 报告

**依赖**:
- `utils.py` - 通用工具
- 本地 Git 仓库 (repos/ 目录)

### weekly-report.py
周报生成脚本，分析过去一周数据。

**功能**:
- 生产力排行榜 (按 LOC)
- 代码贡献详情 (语言/仓库分布)
- 工作时间分布热力图
- 提交节奏分析
- 协作关系矩阵
- 代码质量趋势 (震荡率/返工率)
- 改进建议

### monthly-report.py
月报生成脚本，分析整月数据。

**功能**:
- 月度总览 (核心指标)
- 贡献排行榜
- 每周趋势对比
- 工作时间分布
- 提交粒度分析
- 文件修改热点

### validate-before-send.sh
**重要**: 发送钉钉消息前必须验证数据。

```bash
#!/bin/bash
# 使用方法
./validate-before-send.sh reports/daily/2025-01-10.md daily
./validate-before-send.sh reports/weekly/2025-W02.md weekly
```

**检查项**:
1. 报告文件是否存在
2. 提交次数是否为 0 (为 0 则不发送)
3. 开发者数是否为 0 (为 0 则不发送)

---

## 流程脚本

### daily-job.sh
每日完整流程 (建议 Cron: 每天 9:00):

```
1. 克隆代码仓库 (auto-clone-repos.sh)
2. 生成日报 (run.sh daily)
3. 转换为 HTML (md2html.py)
4. 更新仪表盘 (dashboard-generator-range.py)
5. 清理代码仓库 (cleanup-repos.sh)
6. 推送到钉钉 (send-to-dingtalk.sh)
```

### weekly-job.sh
每周完整流程 (建议 Cron: 每周一 9:00):

```
1. 克隆代码仓库
2. 生成周报 (run.sh weekly)
3. 转换为 HTML
4. 更新仪表盘 (5个时间范围)
5. 清理代码仓库
6. 推送到钉钉
```

### monthly-job.sh
每月完整流程 (建议 Cron: 每月 1 日 9:00):

```
1. 生成月报 (run.sh monthly)
2. 推送到钉钉
```

---

## 配置文件

### repos-list.txt (敏感)
仓库列表配置，每行一个仓库:

```
https://codeup.aliyun.com/xxx/your-backend.git
https://codeup.aliyun.com/xxx/your-frontend.git
```

**注意**: 此文件包含私有仓库 URL，已在 .gitignore 中排除。

### 环境变量
脚本依赖以下环境变量 (在 config.yaml 或 .env 中设置):

| 变量 | 说明 |
|------|------|
| `DINGTALK_WEBHOOK` | 钉钉 Webhook URL |
| `DINGTALK_SECRET` | 钉钉加签密钥 |
| `WEB_BASE_URL` | Web 访问地址 |
| `PROJECT_NAME` | 项目名称 |

---

## 数据流程

```
1. auto-clone-repos.sh
   └─> repos/ (克隆到本地)

2. daily-report.py / weekly-report.py / monthly-report.py
   └─> 读取 repos/ 中的 Git 历史
   └─> 生成 reports/daily/YYYY-MM-DD.md

3. md2html.py
   └─> 读取 .md 文件
   └─> 生成 .html 文件

4. generate-index.py
   └─> 扫描 reports/ 目录
   └─> 生成 reports/index.html

5. dashboard-generator-range.py
   └─> 读取 repos/ 中的 Git 历史
   └─> 生成 dashboard/index.html (ECharts 图表)

6. validate-before-send.sh
   └─> 检查报告数据是否有效

7. send-to-dingtalk.sh
   └─> 发送 Markdown 消息到钉钉群
```

---

## 安全检查

### 提交前检查
```bash
# 确保敏感文件没有被追踪
git status
git diff --staged | grep -i "webhook\|token\|secret"
```

### 发送前验证
```bash
# 必须通过验证才能发送
./validate-before-send.sh $REPORT_FILE $REPORT_TYPE || exit 1
./send-to-dingtalk.sh
```

### 敏感文件清单
以下文件不能提交到 Git:
- `repos-list.txt` - 私有仓库 URL
- `config.yaml` - 包含 Token
- 任何包含 `DINGTALK_WEBHOOK` 的脚本变量

---

## 常见问题

### Q: 报告显示 0 提交
A: 检查以下几点:
1. repos/ 目录是否有克隆的仓库
2. 仓库是否有指定日期的提交
3. 日期参数是否正确

### Q: 钉钉消息发送失败
A: 使用调试脚本:
```bash
./debug-dingtalk.sh
./test-sign.sh
```

### Q: HTML 页面无法访问
A: 检查以下几点:
1. nginx.conf 配置是否正确
2. 文件权限是否为 644
3. 使用 `./test-web-access.sh` 测试

---

## Cron 配置示例

```cron
# 每天早上 9:00 生成日报
0 9 * * * /path/to/scripts/daily-job.sh >> /var/log/code-health/daily.log 2>&1

# 每周一早上 9:00 生成周报
0 9 * * 1 /path/to/scripts/weekly-job.sh >> /var/log/code-health/weekly.log 2>&1

# 每月 1 日早上 9:00 生成月报
0 9 1 * * /path/to/scripts/monthly-job.sh >> /var/log/code-health/monthly.log 2>&1
```
