# Code Health Monitor

> 基于 Git 的自动化代码质量与团队效能监控平台
> Git-based automated code quality and team productivity monitoring platform

**中文** | [English](README_EN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Bash](https://img.shields.io/badge/shell-bash-green.svg)](https://www.gnu.org/software/bash/)
[![GitHub stars](https://img.shields.io/github/stars/yzhucn/code-health?style=social)](https://github.com/yzhucn/code-health/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yzhucn/code-health?style=social)](https://github.com/yzhucn/code-health/network/members)
[![GitHub issues](https://img.shields.io/github/issues/yzhucn/code-health)](https://github.com/yzhucn/code-health/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/yzhucn/code-health)](https://github.com/yzhucn/code-health/commits/main)

## 简介

Code Health Monitor 是一个轻量级的代码质量和团队效能自动化监控工具，通过分析 Git 提交历史，自动生成日报、周报，并推送到钉钉/飞书等协作平台。

帮助项目管理者和技术 Leader：
- 🎯 实时掌握代码健康状况
- 📊 量化团队开发效能
- 🚨 及时发现技术风险
- 💡 数据驱动改进决策

## 效果展示

### 📱 钉钉日报推送效果

<table>
<tr>
<td width="50%">

**消息预览**

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

</td>
<td width="50%">

**截图示例**

<!--
TODO: 添加钉钉推送截图
建议截图内容：钉钉群聊中的机器人消息
建议尺寸：宽度 400-600px
文件路径：docs/images/dingtalk-daily.png

![钉钉日报推送](docs/images/dingtalk-daily.png)
-->

*💡 待添加实际截图*

</td>
</tr>
</table>

### 📊 可视化仪表盘

<table>
<tr>
<td width="33%">

**健康评分趋势**

<!--
TODO: 添加仪表盘截图
文件路径：docs/images/dashboard-health.png

![健康评分趋势](docs/images/dashboard-health.png)
-->

*💡 待添加实际截图*

</td>
<td width="33%">

**代码变更热力图**

<!--
TODO: 添加仪表盘截图
文件路径：docs/images/dashboard-heatmap.png

![代码变更热力图](docs/images/dashboard-heatmap.png)
-->

*💡 待添加实际截图*

</td>
<td width="33%">

**风险指标统计**

<!--
TODO: 添加仪表盘截图
文件路径：docs/images/dashboard-risks.png

![风险指标](docs/images/dashboard-risks.png)
-->

*💡 待添加实际截图*

</td>
</tr>
</table>

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

### 📸 如何添加截图（可选）

如果你想添加实际的效果截图，请按以下步骤操作：

1. **创建图片目录**：
   ```bash
   mkdir -p docs/images
   ```

2. **截取以下内容**（注意去除敏感信息）：
   - 钉钉群聊中的机器人消息 → `docs/images/dingtalk-daily.png`
   - 浏览器中打开的仪表盘 → `docs/images/dashboard-*.png`
   - Markdown 日报的 HTML 渲染效果 → `docs/images/report-html.png`

3. **去除敏感信息**：
   - 打码或模糊处理：真实仓库名、开发者姓名、IP地址
   - 使用示例数据替换：如将真实仓库名改为"my-backend"

4. **取消注释 README 中的图片引用**：
   - 删除 `<!-- ` 和 ` -->` 标记
   - 删除 `*💡 待添加实际截图*` 占位文本

5. **提交图片**：
   ```bash
   git add docs/images/*.png
   git commit -m "docs: 添加效果展示截图"
   git push
   ```

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

## 快速开始

### 前置要求

- Python 3.8+
- Git 2.0+
- Bash shell
- (可选) Nginx（Web 访问）

### 安装部署

#### 1. 克隆项目

```bash
git clone https://github.com/yzhucn/code-health.git
cd code-health
```

#### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 3. 配置监控仓库

**复制配置模板**：

```bash
cp config.example.yaml config.yaml
```

**编辑 `config.yaml`**，添加需要监控的代码仓库：

```yaml
repositories:
  - path: /path/to/your/repo1  # 仓库的绝对路径
    name: your-repo-name        # 显示名称
    type: java                  # 项目类型：java, python, vue, flutter
    main_branch: main           # 主分支名称

  - path: /path/to/your/repo2
    name: another-repo
    type: python
    main_branch: dev
```

**配置钉钉/飞书通知**（可选）：

```yaml
notification:
  dingtalk:
    enabled: true
    webhook: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
    secret: YOUR_SECRET

  feishu:
    enabled: false
    webhook: https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK
```

**如何获取钉钉 Webhook 和 Secret：**

1. 在钉钉群中，点击「群设置」→「智能群助手」→「添加机器人」
2. 选择「自定义」机器人，输入机器人名称（如：代码健康监控）
3. **安全设置**：选择「加签」方式，复制生成的 **Secret**
4. 完成后，复制 **Webhook 地址**（包含 access_token）
5. 将 Webhook 和 Secret 填入 `config.yaml`

**重要安全提示：**
- ⚠️ `config.yaml` 包含敏感信息，已在 `.gitignore` 中忽略，不会提交到 Git
- ⚠️ 切勿将真实的 webhook 和 secret 提交到公开仓库
- ✅ 只有 `config.example.yaml` 会被提交，它仅包含占位符

**配置 Web 访问 URL**（用于钉钉中的报告链接）：

```yaml
web:
  base_url: "http://localhost:8080"  # 本地开发
  # base_url: "http://YOUR_ECS_IP:8080"  # ECS 部署时修改为服务器地址
```

**高级：使用环境变量管理敏感信息（可选，更安全）：**

除了在 `config.yaml` 中配置，也可以使用环境变量：

```bash
# ~/.bashrc 或 ~/.zshrc
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
export DINGTALK_SECRET="YOUR_SECRET"
export GIT_TOKEN="your_git_token"  # 用于 auto-clone-repos.sh
```

然后修改脚本读取环境变量（或者保持现状，环境变量主要用于 Git Token）。

#### 4. 测试配置

**本地测试（推荐先在本地验证配置正确）：**

```bash
cd scripts

# 测试1：生成日报（不推送）
python3 daily-report.py

# 检查生成的报告
ls -lh ../reports/daily/

# 测试2：转换为 HTML
python3 md2html.py ../reports/daily/$(date +%Y-%m-%d).md

# 测试3：测试钉钉推送（如果配置了钉钉）
./send-to-dingtalk.sh $(date +%Y-%m-%d)
```

**验证checklist：**
- ✅ 日报文件已生成：`reports/daily/YYYY-MM-DD.md`
- ✅ HTML 文件已生成：`reports/daily/YYYY-MM-DD.html`
- ✅ 钉钉消息已收到（如果配置了钉钉）
- ✅ 报告中包含各仓库的提交统计

如果以上测试都通过，说明配置正确，可以继续部署到 ECS 或设置定时任务。

**常见配置场景：**

<details>
<summary><b>场景1：本地开发 + 监控本地仓库</b></summary>

```yaml
repositories:
  - path: /Users/yourname/projects/my-backend
    name: my-backend
    type: java
    main_branch: main

notification:
  dingtalk:
    enabled: false  # 本地测试时可以先禁用

web:
  base_url: "http://localhost:8080"
```

</details>

<details>
<summary><b>场景2：ECS 部署 + 自动克隆远程仓库</b></summary>

1. 创建 `repos-list.txt`：
   ```txt
   backend|https://github.com/yourorg/backend.git
   frontend|https://github.com/yourorg/frontend.git
   ```

2. 设置环境变量（私有仓库需要）：
   ```bash
   export GIT_TOKEN="your_github_personal_access_token"
   ```

3. `config.yaml` 中配置临时克隆目录：
   ```yaml
   repositories:
     - path: /opt/your-project/repos/backend
       name: backend
       type: java
       main_branch: main

   notification:
     dingtalk:
       enabled: true
       webhook: https://oapi.dingtalk.com/robot/send?access_token=YOUR_REAL_TOKEN
       secret: YOUR_REAL_SECRET

   web:
     base_url: "http://YOUR_ECS_IP:8080"
   ```

</details>

<details>
<summary><b>场景3：混合模式（本地仓库 + 远程仓库）</b></summary>

部分仓库已在 ECS 上（如正在运行的服务），部分需要临时克隆：

```yaml
repositories:
  # 本地已存在的仓库
  - path: /opt/services/production-backend
    name: backend-prod
    type: java
    main_branch: master

  # 需要自动克隆的仓库（通过 repos-list.txt）
  - path: /opt/your-project/repos/frontend
    name: frontend
    type: vue
    main_branch: dev
```

然后运行 `scripts/auto-clone-repos.sh` 只克隆 repos-list.txt 中配置的仓库。

</details>

#### 5. 生成报告

```bash
# 生成今天的日报
cd scripts
./run.sh daily

# 生成本周周报
./run.sh weekly
```

## ECS 服务器部署

### 前提条件

1. 在 GitHub 上创建仓库并推送代码（见下文"推送到 GitHub"）
2. ECS 服务器上已安装 Git, Python 3.8+, Nginx

### 一键部署步骤

#### 1. 在 ECS 上克隆代码

```bash
# SSH 登录 ECS
ssh root@YOUR_ECS_IP

# 创建目录并克隆
mkdir -p /opt/your-project
cd /opt/your-project
git clone https://github.com/yzhucn/code-health.git .code-health
cd .code-health
```

#### 2. 配置项目

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑配置文件，填写实际的仓库路径、钉钉webhook等
vim config.yaml
```

#### 3. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 4. 配置定时任务

编辑 crontab：

```bash
crontab -e
```

添加以下内容（注意替换路径）：

```bash
# 每天早上 8:00 生成并推送日报
0 8 * * * /opt/your-project/.code-health/scripts/daily-job.sh

# 每周五下午 17:00 生成并推送周报
0 17 * * 5 /opt/your-project/.code-health/scripts/weekly-job.sh
```

#### 5. 配置 Nginx（可选）

如需 Web 访问，配置 Nginx：

```nginx
server {
    listen 8080;
    server_name YOUR_ECS_IP;

    location / {
        root /opt/your-project/.code-health;
        index index.html;
        autoindex on;
    }

    location /reports/ {
        alias /opt/your-project/.code-health/reports/;
        autoindex on;
    }

    location /dashboard/ {
        alias /opt/your-project/.code-health/dashboard/;
    }
}
```

重启 Nginx：

```bash
nginx -t
systemctl reload nginx
```

### Web 访问

部署后可通过浏览器访问：

- **仪表盘**：http://YOUR_ECS_IP:8080/dashboard/
- **日报列表**：http://YOUR_ECS_IP:8080/reports/
- **具体日报**：http://YOUR_ECS_IP:8080/reports/daily/2026-01-04.html

## 本地开发

### 本地运行

```bash
cd scripts

# 生成今天的日报
python3 daily-report.py

# 生成指定日期的日报
python3 daily-report.py 2026-01-01

# 生成本周周报
python3 weekly-report.py
```

### 本地测试钉钉推送

```bash
# 推送昨天的日报
./send-to-dingtalk.sh

# 推送指定日期的日报
./send-to-dingtalk.sh 2026-01-04
```

## 项目结构

```
.code-health/
├── README.md                    # 项目说明（本文件）
├── METRICS.md                   # 详细指标体系文档
├── config.yaml                  # 主配置文件
├── requirements.txt             # Python 依赖
├── .gitignore                   # Git 忽略文件
│
├── scripts/                     # 核心脚本
│   ├── run.sh                   # 主入口脚本
│   ├── daily-report.py          # 日报生成器
│   ├── weekly-report.py         # 周报生成器
│   ├── utils.py                 # 公共工具函数
│   ├── daily-job.sh             # 日报定时任务
│   ├── weekly-job.sh            # 周报定时任务
│   ├── send-to-dingtalk.sh      # 钉钉推送脚本
│   ├── md2html.py               # Markdown 转 HTML
│   ├── dashboard-generator.py   # 仪表盘生成器
│   └── auto-clone-repos.sh      # 自动克隆仓库
│
├── reports/                     # 报告存档
│   ├── daily/                   # 日报（MD + HTML）
│   │   ├── 2026-01-04.md
│   │   └── 2026-01-04.html
│   └── weekly/                  # 周报（MD + HTML）
│       └── 2026-W01.md
│
├── dashboard/                   # 可视化仪表盘
│   ├── index.html               # 默认仪表盘（7天）
│   ├── index-14d.html           # 14天仪表盘
│   ├── index-30d.html           # 30天仪表盘
│   ├── index-60d.html           # 60天仪表盘
│   └── index-90d.html           # 90天仪表盘
│
└── docs/                        # 文档目录
    ├── ECS_COMPLETE_GUIDE.md    # ECS 部署完整指南
    ├── USER_GUIDE.md            # 用户使用指南
    └── AUTOMATION_STATUS.md     # 自动化状态说明
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
- [ECS_COMPLETE_GUIDE.md](ECS_COMPLETE_GUIDE.md) - ECS 部署完整指南
- [USER_GUIDE.md](USER_GUIDE.md) - 用户使用指南
- [AUTOMATION_STATUS.md](AUTOMATION_STATUS.md) - 自动化配置状态
- [config.yaml](config.yaml) - 配置文件模板

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
