# Code Health Monitor 项目发布公告

## 📢 GitHub Discussion 版本（推荐）

### 中文版

---

# 🎉 Code Health Monitor v1.0.0 正式发布！

大家好！

我很高兴地宣布 **Code Health Monitor** 正式开源发布！这是一个基于 Git 的自动化代码质量与团队效能监控平台。

## 💡 项目背景

在日常的团队协作开发中，我们经常面临这些问题：
- 🤔 代码质量如何？有哪些潜在风险？
- 📊 团队的开发效能如何量化？
- 🚨 如何及时发现技术债务和不稳定代码？
- 💬 如何让团队成员了解项目的健康状况？

为了解决这些问题，我开发了 Code Health Monitor，它可以：
- 自动分析 Git 提交历史
- 生成每日/周报
- 自动推送到钉钉/飞书
- 提供可视化仪表盘

## ✨ 核心功能

### 📈 自动化报告
- **日报**：每天早上 8:00 自动生成，涵盖提交统计、代码变更、风险预警、健康评分
- **周报**：每周五自动生成，包含效能排行、高风险文件、团队健康度、质量趋势
- **钉钉/飞书推送**：自动推送到团队协作平台

### 🔍 代码质量监控
- **代码震荡检测**：识别频繁修改的不稳定文件
- **返工率分析**：统计无效工作量，发现需求/设计问题
- **高风险文件识别**：综合评估文件的修改频率、复杂度、协作冲突风险
- **提交质量评估**：检测大提交、微小提交、提交信息规范性

### 👥 团队效能分析
- **效能排行**：提交量、代码行数、文件修改统计
- **工作时间分析**：加班、深夜、周末工作检测
- **协作热力图**：识别高频协作关系和潜在冲突
- **技能地图**：按技术栈分析团队能力分布

### 📊 可视化仪表盘
- 支持多时间范围：7天、14天、30天、60天、90天
- 健康评分趋势图
- 代码变更热力图
- HTML 报告查看

## 🎯 适用场景

- **技术 Leader**：实时掌握团队开发效能和代码健康度
- **项目经理**：通过数据了解项目进展和风险
- **开发团队**：自动化的代码质量反馈
- **DevOps 工程师**：集成到 CI/CD 流程中

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/yzhucn/code-health.git
cd code-health

# 安装依赖
pip3 install -r requirements.txt

# 配置
cp config.example.yaml config.yaml
vim config.yaml  # 配置你的仓库路径和钉钉webhook

# 生成报告
cd scripts
./run.sh daily   # 生成日报
./run.sh weekly  # 生成周报
```

详细配置请查看：[README.md](https://github.com/yzhucn/code-health/blob/main/README.md)

## 🌟 项目特色

1. **轻量级**：基于 Git CLI 和 Python，无需安装额外服务
2. **易部署**：支持本地运行和 ECS 服务器部署
3. **自动化**：配合 Crontab 实现完全自动化
4. **可定制**：支持自定义风险阈值、工作时间等
5. **双语文档**：完整的中英文文档支持
6. **开箱即用**：提供完整的配置示例和使用指南

## 📚 技术栈

- Python 3.8+
- Bash Shell
- Git
- Markdown
- ECharts
- DingTalk/Feishu API

## 🤝 如何贡献

我们欢迎任何形式的贡献！

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码

详细贡献指南：[CONTRIBUTING.md](https://github.com/yzhucn/code-health/blob/main/CONTRIBUTING.md)

## 🗺️ 未来规划

- [ ] 支持更多通知渠道（企业微信、Slack）
- [ ] 集成代码覆盖率数据
- [ ] 集成 SonarQube 质量门禁
- [ ] 增加月报功能
- [ ] 支持自定义报告模板
- [ ] 提供 Docker 部署方案
- [ ] 增加实时监控告警

## 📞 联系方式

- **GitHub**: https://github.com/yzhucn/code-health
- **Issues**: https://github.com/yzhucn/code-health/issues
- **Discussions**: https://github.com/yzhucn/code-health/discussions

## 📄 许可证

MIT License - 可以自由使用、修改和分发

---

如果这个项目对你有帮助，欢迎 ⭐ Star 支持！

也欢迎分享给你的团队和朋友！🙏

---

### English Version

# 🎉 Code Health Monitor v1.0.0 Released!

Hi everyone!

I'm excited to announce the official open-source release of **Code Health Monitor** - a Git-based automated code quality and team productivity monitoring platform!

## 💡 Background

During daily team collaboration, we often face these challenges:
- 🤔 How's our code quality? What are the potential risks?
- 📊 How to quantify team productivity?
- 🚨 How to detect technical debt and unstable code early?
- 💬 How to keep the team informed about project health?

To solve these problems, I created Code Health Monitor, which can:
- Automatically analyze Git commit history
- Generate daily/weekly reports
- Auto-push to DingTalk/Feishu
- Provide visualization dashboards

## ✨ Key Features

### 📈 Automated Reporting
- **Daily Reports**: Auto-generated at 8:00 AM with commit stats, code changes, risk alerts, and health scores
- **Weekly Reports**: Auto-generated every Friday with productivity rankings, high-risk files, team health, and quality trends
- **DingTalk/Feishu Integration**: Automatic notifications to collaboration platforms

### 🔍 Code Quality Monitoring
- **Code Churn Detection**: Identifies frequently modified unstable files
- **Rework Rate Analysis**: Tracks wasted effort and reveals requirement/design issues
- **High-Risk File Identification**: Comprehensive assessment of modification frequency, complexity, and collaboration conflicts
- **Commit Quality Evaluation**: Detects large commits, tiny commits, and message quality

### 👥 Team Productivity Analysis
- **Productivity Rankings**: Commit volume, lines of code, file modification statistics
- **Working Hours Analysis**: Overtime, late-night, and weekend work detection
- **Collaboration Heatmap**: Identifies high-frequency collaboration and potential conflicts
- **Skill Mapping**: Team capability distribution by tech stack

### 📊 Visualization Dashboard
- Multiple time ranges: 7, 14, 30, 60, 90 days
- Health score trends
- Code change heatmap
- HTML report viewing

## 🎯 Use Cases

- **Tech Leads**: Real-time monitoring of team productivity and code health
- **Project Managers**: Data-driven insights into project progress and risks
- **Development Teams**: Automated code quality feedback
- **DevOps Engineers**: Integration into CI/CD pipelines

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yzhucn/code-health.git
cd code-health

# Install dependencies
pip3 install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
vim config.yaml  # Configure your repository paths and DingTalk webhook

# Generate reports
cd scripts
./run.sh daily   # Generate daily report
./run.sh weekly  # Generate weekly report
```

For detailed configuration: [README_EN.md](https://github.com/yzhucn/code-health/blob/main/README_EN.md)

## 🌟 Project Highlights

1. **Lightweight**: Based on Git CLI and Python, no additional services required
2. **Easy Deployment**: Supports both local and ECS server deployment
3. **Automated**: Fully automated with Crontab
4. **Customizable**: Configurable risk thresholds, working hours, etc.
5. **Bilingual Documentation**: Complete Chinese and English documentation
6. **Ready to Use**: Complete configuration examples and usage guides

## 📚 Tech Stack

- Python 3.8+
- Bash Shell
- Git
- Markdown
- ECharts
- DingTalk/Feishu API

## 🤝 Contributing

We welcome all kinds of contributions!

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit code

Contribution guide: [CONTRIBUTING_EN.md](https://github.com/yzhucn/code-health/blob/main/CONTRIBUTING_EN.md)

## 🗺️ Roadmap

- [ ] Support more notification channels (WeChat Work, Slack)
- [ ] Integrate code coverage data
- [ ] Integrate SonarQube quality gates
- [ ] Add monthly reports
- [ ] Support custom report templates
- [ ] Provide Docker deployment
- [ ] Add real-time monitoring alerts

## 📞 Contact

- **GitHub**: https://github.com/yzhucn/code-health
- **Issues**: https://github.com/yzhucn/code-health/issues
- **Discussions**: https://github.com/yzhucn/code-health/discussions

## 📄 License

MIT License - Free to use, modify, and distribute

---

If this project helps you, please ⭐ Star to support!

Feel free to share with your team and friends! 🙏

---

## 🐦 Twitter/X 版本（中文）

🎉 开源项目发布！Code Health Monitor v1.0.0

基于 Git 的自动化代码质量监控平台：
✅ 自动生成日报/周报
✅ 钉钉/飞书自动推送
✅ 代码健康评分
✅ 团队效能分析
✅ 可视化仪表盘

轻量级 | 易部署 | 开箱即用
完整双语文档 | MIT 开源

🔗 https://github.com/yzhucn/code-health

#开源 #DevOps #代码质量 #团队协作 #Python

---

## 🐦 Twitter/X Version (English)

🎉 Open Source Release! Code Health Monitor v1.0.0

Git-based automated code quality monitoring platform:
✅ Auto daily/weekly reports
✅ DingTalk/Feishu integration
✅ Code health scoring
✅ Team productivity analytics
✅ Visualization dashboard

Lightweight | Easy deployment | Ready to use
Bilingual docs | MIT license

🔗 https://github.com/yzhucn/code-health

#OpenSource #DevOps #CodeQuality #TeamCollaboration #Python

---

## 💬 技术社区版本（V2EX/掘金/思否）

### 标题
Code Health Monitor - 基于 Git 的自动化代码质量监控平台（开源）

### 正文

各位好，

今天给大家分享一个刚开源的项目：**Code Health Monitor**

## 起因

在团队开发中，我们经常需要了解：
- 代码质量如何？
- 团队效能怎样？
- 有哪些技术风险？

但手工统计太费时，现有工具又太重。于是我开发了这个轻量级的监控工具。

## 它能做什么

**自动化监控**
- 每天早上 8 点自动生成日报
- 每周五生成周报
- 自动推送到钉钉群

**代码质量分析**
- 检测频繁修改的不稳定文件
- 计算代码返工率
- 识别高风险文件
- 评估提交质量

**团队效能分析**
- 开发者效能排行
- 加班/深夜工作统计
- 协作热力图

**可视化展示**
- 健康评分趋势
- 代码变更热力图
- 支持 7/14/30/60/90 天多时间范围

## 技术实现

- 基于 Git CLI 分析提交历史
- Python 处理数据
- Bash 脚本编排
- Markdown 生成报告
- ECharts 可视化
- 钉钉 Webhook 推送

无需额外服务，部署简单。

## 使用方法

```bash
git clone https://github.com/yzhucn/code-health.git
cd code-health
pip3 install -r requirements.txt
cp config.example.yaml config.yaml
# 配置仓库路径和钉钉 webhook
./scripts/run.sh daily  # 生成日报
```

## 特点

- ✅ 轻量级（无需安装额外服务）
- ✅ 开箱即用（提供完整配置示例）
- ✅ 高度可定制（风险阈值、工作时间等）
- ✅ 完整双语文档（中英文）
- ✅ MIT 开源协议

## 项目地址

https://github.com/yzhucn/code-health

欢迎 Star、Fork 和提 Issue！

---

## 📧 邮件列表/Newsletter 版本

**Subject**: [New Release] Code Health Monitor v1.0.0 - Automated Git-based Code Quality Monitoring

**Body**:

Hello,

I'm pleased to announce the release of Code Health Monitor v1.0.0, an open-source automated code quality and team productivity monitoring platform.

**What is it?**

Code Health Monitor analyzes Git commit history to automatically generate daily and weekly reports, providing insights into code quality, team productivity, and potential risks.

**Key Features:**
• Automated daily/weekly report generation
• DingTalk/Feishu integration for notifications
• Code churn and rework rate analysis
• Team productivity rankings
• Visualization dashboards
• Customizable risk thresholds

**Why use it?**
• Lightweight - no additional services required
• Easy deployment - works locally or on servers
• Fully automated - set it and forget it
• Bilingual documentation (Chinese & English)
• MIT licensed

**Get Started:**
GitHub: https://github.com/yzhucn/code-health
Documentation: https://github.com/yzhucn/code-health#readme
Release: https://github.com/yzhucn/code-health/releases/tag/v1.0.0

**Tech Stack:**
Python 3.8+, Bash, Git, Markdown, ECharts

**Contributing:**
We welcome contributions! Check out our contributing guide:
https://github.com/yzhucn/code-health/blob/main/CONTRIBUTING.md

Best regards,
yzhucn

---

## 🎬 YouTube/B站 视频脚本

### 标题
Code Health Monitor - 自动化代码质量监控工具开源了！

### 视频脚本

**[开场 - 0:00-0:15]**
大家好，今天给大家分享一个我刚开源的项目：Code Health Monitor，一个基于 Git 的自动化代码质量监控平台。

**[问题场景 - 0:15-0:45]**
在团队开发中，你是否遇到过这些问题：
- 代码质量如何？有没有潜在风险？
- 团队效能怎样？谁提交的最多？
- 哪些文件频繁修改？返工率高不高？

手工统计很费时，现有工具又太重。所以我开发了这个工具。

**[演示 - 0:45-2:00]**
看一下效果：
1. 每天早上 8 点自动生成日报
2. 自动推送到钉钉群
3. 包含：提交统计、健康评分、风险预警
4. 可视化仪表盘，一目了然
5. 周报自动汇总一周数据

**[技术实现 - 2:00-2:30]**
实现很简单：
- 基于 Git CLI 分析提交历史
- Python 处理数据
- Bash 脚本自动化
- 无需额外服务

**[如何使用 - 2:30-3:00]**
使用也很简单：
1. Clone 项目
2. 安装依赖
3. 配置仓库路径
4. 配置钉钉 webhook
5. 运行脚本

**[结尾 - 3:00-3:30]**
项目完全开源，MIT 协议，有完整的中英文文档。

GitHub 地址在视频描述里，欢迎 Star 和贡献！

如果觉得有用，别忘了点赞、投币、收藏！我们下期见！

**视频描述：**
GitHub: https://github.com/yzhucn/code-health
中文文档: https://github.com/yzhucn/code-health/blob/main/README.md
English Docs: https://github.com/yzhucn/code-health/blob/main/README_EN.md

时间轴：
0:00 开场
0:15 问题场景
0:45 功能演示
2:00 技术实现
2:30 使用教程
3:00 总结

---

## 📱 微信公众号版本

### 标题
Code Health Monitor：让数据驱动你的代码质量提升

### 正文

大家好，

今天给大家介绍一个刚开源的项目：**Code Health Monitor**——一个基于 Git 的自动化代码质量监控平台。

#### 📌 为什么做这个项目？

在团队协作开发中，我们经常面临：

❓ 代码质量如何评估？
❓ 团队效能如何量化？
❓ 技术债务如何及时发现？

手工统计太费时，而现有的质量平台往往过于复杂。于是我开发了这个轻量级的监控工具。

#### ✨ 核心功能

**1️⃣ 自动化报告**
• 每日 8:00 自动生成日报
• 每周五自动生成周报
• 自动推送到钉钉/飞书

**2️⃣ 代码质量监控**
• 代码震荡检测
• 返工率分析
• 高风险文件识别
• 提交质量评估

**3️⃣ 团队效能分析**
• 效能排行榜
• 工作时间分析
• 协作热力图
• 技能地图

**4️⃣ 可视化仪表盘**
• 健康评分趋势
• 代码变更热力图
• 多时间范围支持

#### 🎯 适用场景

✅ 技术 Leader 监控团队效能
✅ 项目经理了解项目进展
✅ DevOps 集成 CI/CD 流程
✅ 开发团队自动化质量反馈

#### 🚀 技术特点

• **轻量级**：基于 Git，无需额外服务
• **易部署**：支持本地和服务器部署
• **自动化**：配合定时任务完全自动化
• **可定制**：灵活的配置选项
• **双语文档**：完整中英文文档

#### 📚 快速开始

```bash
# 克隆项目
git clone https://github.com/yzhucn/code-health.git

# 安装依赖
pip3 install -r requirements.txt

# 配置并运行
cp config.example.yaml config.yaml
./scripts/run.sh daily
```

#### 🔗 项目链接

**GitHub**: https://github.com/yzhucn/code-health

完整文档请访问 GitHub 仓库。

#### 🤝 参与贡献

项目采用 MIT 开源协议，欢迎：
• 提交 Bug 报告
• 提出功能建议
• 改进文档
• 贡献代码

---

如果这个项目对你有帮助，欢迎 Star ⭐ 支持！

也欢迎转发给你的技术朋友！

---

## 🎨 使用建议

**不同平台选择：**

1. **GitHub Discussion** - 使用完整版，包含中英文
2. **Twitter/X** - 使用精简版，突出亮点
3. **技术社区**（V2EX/掘金/思否）- 使用社区版，更接地气
4. **邮件列表** - 使用正式版
5. **视频平台** - 使用视频脚本
6. **微信公众号** - 使用公众号版本，格式友好

**发布时机：**

1. **立即发布**：GitHub Discussion、Twitter/X
2. **工作日上午**：技术社区（V2EX 早上 9-10 点，掘金/思否 10-11 点）
3. **周末**：微信公众号、视频平台

**标签建议：**

中文：#开源项目 #代码质量 #DevOps #团队协作 #自动化
English: #OpenSource #CodeQuality #DevOps #GitAnalysis #Monitoring
