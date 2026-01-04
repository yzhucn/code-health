# Code Health Monitor

> Git-based automated code quality and team productivity monitoring platform

[中文文档](README.md) | **English**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Bash](https://img.shields.io/badge/shell-bash-green.svg)](https://www.gnu.org/software/bash/)
[![GitHub stars](https://img.shields.io/github/stars/yzhucn/code-health?style=social)](https://github.com/yzhucn/code-health/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yzhucn/code-health?style=social)](https://github.com/yzhucn/code-health/network/members)
[![GitHub issues](https://img.shields.io/github/issues/yzhucn/code-health)](https://github.com/yzhucn/code-health/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/yzhucn/code-health)](https://github.com/yzhucn/code-health/commits/main)

## Introduction

Code Health Monitor is a lightweight code quality and team productivity monitoring tool. It analyzes Git commit history to automatically generate daily and weekly reports, and pushes them to collaboration platforms like DingTalk/Feishu.

Helps project managers and tech leads:
- 🎯 Real-time code health monitoring
- 📊 Quantified team productivity metrics
- 🚨 Early detection of technical risks
- 💡 Data-driven improvement decisions

## Core Features

### 1. Automated Reporting

- **Daily Reports**: Auto-generated at 8:00 AM, covering commit stats, code changes, risk alerts, and health scores
- **Weekly Reports**: Auto-generated every Friday, including productivity rankings, high-risk files, team health, and quality trends
- **Platform Integration**: Auto-push to DingTalk/Feishu

### 2. Code Quality Monitoring

- **Code Churn Detection**: Identifies frequently modified unstable files
- **Rework Rate Analysis**: Tracks wasted effort, reveals requirement/design issues
- **High-Risk File Identification**: Comprehensive assessment of file modification frequency, complexity, and collaboration conflicts
- **Commit Quality Evaluation**: Detects large commits, tiny commits, and commit message quality

### 3. Team Productivity Analysis

- **Productivity Rankings**: Commit volume, lines of code, file modification statistics
- **Working Hours Analysis**: Overtime, late-night, and weekend work detection
- **Collaboration Heatmap**: Identifies high-frequency collaboration and potential conflicts
- **Skill Map**: Team capability distribution by tech stack

### 4. Visualization Dashboard

- Multiple time ranges: 7, 14, 30, 60, 90 days
- Health score trends
- Code change heatmap
- HTML report viewing

## Quick Start

### Prerequisites

- Python 3.8+
- Git 2.0+
- Bash shell
- (Optional) Nginx for web access

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yzhucn/code-health.git
cd code-health
```

#### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

#### 3. Configure Repositories

**Copy configuration template:**

```bash
cp config.example.yaml config.yaml
```

**Edit `config.yaml`** and add repositories to monitor:

```yaml
# Project configuration
project:
  name: "Code Health Monitor"  # Customize your project name

# Repository configuration
repositories:
  - path: /path/to/your/repo1
    name: your-repo-name
    type: java                  # Supported: java, python, vue, flutter
    main_branch: main

notification:
  dingtalk:
    enabled: true
    webhook: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
    secret: YOUR_SECRET
```

#### 4. Generate Reports

```bash
cd scripts

# Generate today's daily report
./run.sh daily

# Generate this week's weekly report
./run.sh weekly
```

## Configuration Guide

For detailed configuration instructions, see the [中文 README](README.md#快速开始).

Key configurations:
- **Repository paths**: Absolute paths to Git repositories
- **DingTalk/Feishu webhooks**: For notification delivery
- **Risk thresholds**: Customize detection rules
- **Working hours**: Define overtime and late-night work periods

## Project Structure

```
code-health/
├── README.md                # Chinese documentation
├── README_EN.md            # English documentation (this file)
├── METRICS.md              # Detailed metrics documentation
├── config.example.yaml     # Configuration template
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
│
├── scripts/               # Core scripts
│   ├── daily-report.py    # Daily report generator
│   ├── weekly-report.py   # Weekly report generator
│   ├── utils.py           # Common utilities
│   └── ...
│
├── reports/               # Report archives
│   ├── daily/            # Daily reports (MD + HTML)
│   └── weekly/           # Weekly reports (MD + HTML)
│
└── dashboard/            # Visualization dashboards
    └── index.html        # Main dashboard
```

## Tech Stack

- **Data Collection**: Git CLI
- **Data Processing**: Python 3.8+
- **Script Orchestration**: Bash Shell
- **Report Generation**: Markdown + Python-Markdown
- **Visualization**: ECharts + HTML/CSS/JS
- **Notifications**: DingTalk Webhook API
- **Web Service**: Nginx
- **Scheduling**: Crontab

## Documentation

- [METRICS.md](METRICS.md) - Detailed metrics documentation
- [SECURITY.md](SECURITY.md) - Security best practices
- [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) - Security checklist
- [config.example.yaml](config.example.yaml) - Configuration template

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Roadmap

- [ ] Support more notification channels (WeChat Work, Slack)
- [ ] Integrate code coverage data
- [ ] Integrate SonarQube quality gates
- [ ] Add monthly reports
- [ ] Support custom report templates
- [ ] Provide Docker deployment
- [ ] Add real-time monitoring alerts

## License

[MIT License](LICENSE)

## Author

- **yzhucn** - [GitHub](https://github.com/yzhucn)

---

**📊 Let data drive R&D efficiency improvement!**
