# Code Health Monitor

> 基于 Git 的自动化代码质量与团队效能监控平台
> Git-based automated code quality and team productivity monitoring platform

**中文** | [English](README_EN.md)

> 📢 **v2.0 发布**: Docker 化部署、多平台支持、Provider 架构重构

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![GitHub stars](https://img.shields.io/github/stars/yzhucn/code-health?style=social)](https://github.com/yzhucn/code-health/stargazers)

## 简介

Code Health Monitor 是一个轻量级的代码质量和团队效能自动化监控工具，通过分析 Git 提交历史，自动生成日报、周报、月报，并推送到钉钉/飞书等协作平台。

**v2.0 新特性：**
- Docker 一键部署，开箱即用
- 支持远程仓库自动浅克隆（无需本地仓库）
- Provider 架构，支持多 Git 平台 (GitHub/GitLab/Codeup)
- 模块化 Python 代码结构

帮助项目管理者和技术 Leader：
- 🎯 实时掌握代码健康状况
- 📊 量化团队开发效能
- 🚨 及时发现技术风险
- 💡 数据驱动改进决策

## 效果展示

### 📱 钉钉日报推送效果

系统会自动将每日健康监控报告推送到钉钉群聊，格式如下：

```
📊 代码管理 - 每日健康监控

日期: 2026-01-04
系统: 代码管理平台

━━━━━━━━━━━━━━━━━━━

📈 核心指标
• 提交次数: 23 次
• 活跃开发者: 5 人
• 代码净增: +1,245 行
• 健康评分: 85.5 分 🟢 优秀

━━━━━━━━━━━━━━━━━━━

🚨 风险指标
• 震荡率: 12.3%
• 返工率: 8.7%
• 加班提交: 3 次

━━━━━━━━━━━━━━━━━━━

🔗 快速链接
📄 查看完整日报
📊 查看可视化仪表盘
```

### 📊 可视化仪表盘

通过 Web 界面可以查看：
- **健康评分趋势**：多时间范围（7/14/30/60/90天）的评分变化
- **代码变更热力图**：直观展示代码活跃度分布
- **风险指标统计**：震荡率、返工率等关键指标的图表展示

### 📄 Markdown 日报示例

<details>
<summary><b>点击查看完整日报示例</b></summary>

```markdown
# 代码健康监控日报

**日期**: 2026-01-04
**报告周期**: 2026-01-04 00:00:00 至 2026-01-04 23:59:59

---

## 📊 基础数据总览

| 指标 | 数值 |
|------|------|
| 提交次数 | **23** 次 |
| 活跃开发者 | **5** 人 |
| 活跃仓库 | **3** 个 |
| **新增行数** | **2,134** 行 |
| **删除行数** | **889** 行 |
| **净增行数** | **+1,245** 行 |
| 变更文件数 | **87** 个 |

---

## 🚨 风险预警

### 代码震荡检测
- **震荡率**: 12.3%
- **震荡文件数**: 8 个

**震荡文件列表**:
1. `backend/service/UserService.java` - 7次修改
2. `frontend/components/Header.vue` - 6次修改
...

### 返工率分析
- **返工率**: 8.7%
- **返工代码**: 186 行

---

## 📈 健康评分

**综合评分**: 85.5 分 🟢 **优秀**

评分说明：
- 提交质量良好
- 震荡率控制在正常范围
- 返工率较低
- 工作时间分布合理
```

</details>

## 核心功能

### 1. 自动化报告

- **日报**：每日 8:00 自动生成，涵盖提交统计、代码变更、风险预警、健康评分
- **周报**：每周五自动生成，包含生产力排行、高危文件、团队健康度、质量趋势
- **钉钉/飞书推送**：报告自动推送到团队协作平台

### 2. 代码质量监控

- **代码震荡检测**：识别频繁修改的不稳定文件
- **返工率分析**：统计无效工作量，发现需求/设计问题
- **高危文件识别**：综合评估文件的修改频率、复杂度、协作冲突风险
- **提交质量评估**：检测大提交、微小提交、提交信息规范性

### 3. 团队效能分析

- **生产力排行**：提交量、代码行数、文件修改统计
- **工作时间分析**：加班、深夜、周末工作检测
- **协作热力图**：识别高频协作关系和潜在冲突
- **技能地图**：按技术栈分析团队能力分布

### 4. 可视化仪表盘

- 支持多时间范围：7天、14天、30天、60天、90天
- 健康评分趋势图
- 代码变更热力图
- HTML 报告查看

## 快速开始 (v2 Docker 部署)

详见 [QUICK_START.md](QUICK_START.md) 获取完整指南。

### 1. 配置环境变量

```bash
cp .env.example .env
vi .env
```

```bash
# 必需配置
GIT_TOKEN=your_git_token_here
PROJECT_NAME=我的项目

# 仓库配置
REPOSITORIES=backend|https://github.com/org/backend.git|java|main,frontend|https://github.com/org/frontend.git|vue|main

# 钉钉通知（可选）
DINGTALK_ENABLED=true
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx
```

### 2. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 手动生成日报
docker-compose run --rm code-health daily

# 查看报告
open http://localhost:8080
```

### 3. 命令行使用

```bash
# 生成日报/周报/月报
python -m src.main daily
python -m src.main weekly
python -m src.main monthly --month 2025-01

# 发送通知
python -m src.main notify daily
python -m src.main notify weekly --week 2025-W02
```

## 项目结构 (v2)

```
.code-health/
├── src/                         # v2 核心代码
│   ├── main.py                  # 主入口
│   ├── config.py                # 配置管理
│   ├── providers/               # Git 数据提供者
│   │   ├── base.py              # Provider 抽象基类
│   │   ├── generic_git.py       # 通用 Git Provider (浅克隆)
│   │   ├── github.py            # GitHub API Provider
│   │   ├── gitlab.py            # GitLab API Provider
│   │   └── codeup.py            # 阿里云 Codeup Provider
│   ├── analyzers/               # 分析器
│   │   ├── git_analyzer.py      # Git 提交分析
│   │   ├── churn.py             # 代码震荡分析
│   │   ├── rework.py            # 返工率分析
│   │   ├── hotspot.py           # 热点文件分析
│   │   └── health_score.py      # 健康评分计算
│   ├── reporters/               # 报告生成器
│   │   ├── base.py              # 报告基类
│   │   ├── daily.py             # 日报生成
│   │   ├── weekly.py            # 周报生成
│   │   └── monthly.py           # 月报生成
│   ├── notifiers/               # 通知模块
│   │   ├── base.py              # 通知器基类
│   │   ├── dingtalk.py          # 钉钉通知
│   │   └── feishu.py            # 飞书通知
│   └── utils/                   # 工具函数
│       └── helpers.py
├── config/
│   └── config.yaml              # 配置文件
├── scripts/                     # v1 脚本 (兼容保留)
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── nginx.conf
├── README.md
└── QUICK_START.md
```

## 配置说明

### 风险阈值配置

```yaml
thresholds:
  large_commit: 500              # 大提交阈值（行）
  tiny_commit: 10                # 微小提交阈值（行）

  churn_days: 3                  # 震荡检测天数
  churn_count: 5                 # 震荡检测次数

  rework_add_days: 7             # 返工检测：代码新增后N天内
  rework_delete_days: 3          # 返工检测：被删除视为返工

  hotspot_days: 7                # 热点文件统计天数
  hotspot_count: 10              # 热点修改次数阈值
  large_file: 1000               # 大文件行数阈值
```

### 工作时间配置

```yaml
working_hours:
  normal_start: "09:00"          # 正常工作开始时间
  normal_end: "18:00"            # 正常工作结束时间
  overtime_start: "18:00"        # 加班开始时间
  overtime_end: "21:00"          # 加班结束时间
  late_night_start: "22:00"      # 深夜开始时间
  late_night_end: "06:00"        # 深夜结束时间
```

详细配置说明请查看 [配置文件示例](config.yaml)。

## 使用示例

### 手动生成报告

```bash
cd scripts

# 生成今天的日报
python3 daily-report.py

# 生成指定日期的日报
python3 daily-report.py 2026-01-01

# 生成本周周报
python3 weekly-report.py

# 生成指定周的周报（ISO周格式）
python3 weekly-report.py 2026-W01
```

### 转换为 HTML

```bash
# 转换日报
python3 md2html.py ../reports/daily/2026-01-04.md

# 批量转换
for file in ../reports/daily/*.md; do
    python3 md2html.py "$file"
done
```

### 生成仪表盘

```bash
# 生成7天仪表盘
python3 dashboard-generator-range.py 7

# 生成30天仪表盘
python3 dashboard-generator-range.py 30
```

### 推送到钉钉

```bash
# 推送昨天的日报
./send-to-dingtalk.sh

# 推送指定日期的日报
./send-to-dingtalk.sh 2026-01-04
```

## 监控指标说明

详细的监控指标体系、计算方法、风险评估规则等，请查看 [METRICS.md](METRICS.md)。

主要指标包括：
- **代码震荡率**：文件稳定性指标
- **返工率**：无效工作量指标
- **健康评分**：综合代码质量评分（0-100分）
- **高危文件**：风险评分 > 60 的文件
- **工作时间异常**：加班、深夜、周末提交统计

## 技术栈

- **数据采集**：Git CLI
- **数据处理**：Python 3.8+
- **脚本编排**：Bash Shell
- **报告生成**：Markdown + Python-Markdown
- **可视化**：ECharts + HTML/CSS/JS
- **通知推送**：钉钉 Webhook API
- **Web 服务**：Nginx
- **定时任务**：Crontab

## 版本历史

### v1.0.0 (2026-01-01)

初始版本，核心功能：

- ✅ 日报自动生成与推送
- ✅ 周报自动生成与推送
- ✅ 代码震荡检测
- ✅ 返工率分析
- ✅ 高危文件识别
- ✅ 工作时间异常检测
- ✅ 健康评分系统
- ✅ 可视化仪表盘（5个时间范围）
- ✅ 钉钉自动推送
- ✅ ECS 一键部署
- ✅ Web 访问支持

## 文档索引

- [METRICS.md](METRICS.md) - 详细指标体系说明
- [SECURITY.md](SECURITY.md) - 安全配置指南
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- [config.example.yaml](config.example.yaml) - 配置文件模板

## 常见问题

### 1. 报告生成失败

检查仓库路径是否正确，Git 历史是否可访问：

```bash
cd /path/to/your/repo
git log --oneline -10
```

### 2. 钉钉推送失败

- 检查 webhook 和 secret 是否正确配置
- 验证网络连接是否正常
- 查看钉钉机器人关键词设置

### 3. Web 访问 404

检查 Nginx 配置和文件权限：

```bash
# 检查 Nginx 配置
nginx -t

# 检查文件权限
ls -la /opt/your-project/.code-health/reports/
```

## 贡献指南

欢迎贡献代码、提出问题或建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 路线图

- [ ] 支持更多通知渠道（企业微信、Slack）
- [ ] 集成代码覆盖率数据
- [ ] 集成 SonarQube 质量门禁
- [ ] 增加月报功能
- [ ] 支持自定义报告模板
- [ ] 提供 Docker 部署方案
- [ ] 增加实时监控告警

## 许可证

[MIT License](LICENSE)

## 作者

- **yzhucn** - [GitHub](https://github.com/yzhucn)

---

**📊 让数据驱动研发效能提升！**
