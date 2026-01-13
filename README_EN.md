# Code Health Monitor

> Git-based automated code quality and team productivity monitoring platform

[中文文档](README.md) | **English**

> 📢 **v2.0 Released**: Docker deployment, multi-platform support, Provider architecture refactoring

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![GitHub stars](https://img.shields.io/github/stars/yzhucn/code-health?style=social)](https://github.com/yzhucn/code-health/stargazers)

## Introduction

Code Health Monitor is a lightweight code quality and team productivity monitoring tool. It analyzes Git commit history to automatically generate daily, weekly, and monthly reports, and pushes them to collaboration platforms like DingTalk/Feishu.

**v2.0 New Features:**
- Docker one-click deployment, ready to use out of the box
- Supports remote repository auto shallow clone (no local repos needed)
- Provider architecture, supporting multiple Git platforms (GitHub/GitLab/Codeup)
- Modular Python code structure

Helps project managers and tech leads:
- 🎯 Real-time code health monitoring
- 📊 Quantified team productivity metrics
- 🚨 Early detection of technical risks
- 💡 Data-driven improvement decisions

## Features Preview

### 📱 DingTalk Daily Report

The system automatically pushes daily health monitoring reports to DingTalk group chat:

```
📊 Code Management - Daily Health Monitor

Date: 2026-01-04
System: Code Health Monitor

━━━━━━━━━━━━━━━━━━━

📈 Core Metrics
• Commits: 23
• Active Developers: 5
• Net Code Change: +1,245 lines
• Health Score: 85.5 🟢 Excellent

━━━━━━━━━━━━━━━━━━━

🚨 Risk Indicators
• Churn Rate: 12.3%
• Rework Rate: 8.7%
• Overtime Commits: 3

━━━━━━━━━━━━━━━━━━━

🔗 Quick Links
📄 View Full Report
📊 View Dashboard
```

### 📊 Visualization Dashboard

Access via web interface to view:
- **Health Score Trends**: Score changes across multiple time ranges (7/14/30/60/90 days)
- **Code Change Heatmap**: Visual representation of code activity distribution
- **Risk Indicator Statistics**: Charts displaying key metrics like churn rate and rework rate

### 📄 Markdown Report Example

<details>
<summary><b>Click to view full report example</b></summary>

```markdown
# Code Health Daily Report

**Date**: 2026-01-04
**Reporting Period**: 2026-01-04 00:00:00 to 2026-01-04 23:59:59

---

## 📊 Overview

| Metric | Value |
|--------|-------|
| Total Commits | **23** |
| Active Developers | **5** |
| Active Repositories | **3** |
| **Lines Added** | **2,134** |
| **Lines Deleted** | **889** |
| **Net Change** | **+1,245** |
| Files Changed | **87** |

---

## 🚨 Risk Alerts

### Code Churn Detection
- **Churn Rate**: 12.3%
- **Churning Files**: 8

**Churning Files List**:
1. `backend/service/UserService.java` - 7 modifications
2. `frontend/components/Header.vue` - 6 modifications
...

### Rework Rate Analysis
- **Rework Rate**: 8.7%
- **Rework Code**: 186 lines

---

## 📈 Health Score

**Overall Score**: 85.5 🟢 **Excellent**

Score Breakdown:
- Good commit quality
- Churn rate within normal range
- Low rework rate
- Reasonable working hours distribution
```

</details>

## Core Features

### 1. Automated Reporting

- **Daily Reports**: Auto-generated at 8:00 AM, covering commit stats, code changes, risk alerts, and health scores
- **Weekly Reports**: Auto-generated every Friday, including productivity rankings, high-risk files, team health, and quality trends
- **Monthly Reports**: Auto-generated monthly with comprehensive team analytics
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

## Quick Start (v2 Docker Deployment)

See [QUICK_START.md](QUICK_START.md) for the complete guide.

### 1. Configure Environment Variables

```bash
cp .env.example .env
vi .env
```

```bash
# Required configuration
GIT_TOKEN=your_git_token_here
PROJECT_NAME=My Project

# Repository configuration
REPOSITORIES=backend|https://github.com/org/backend.git|java|main,frontend|https://github.com/org/frontend.git|vue|main

# DingTalk notification (optional)
DINGTALK_ENABLED=true
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx
```

### 2. Start Services

```bash
# Build and start
docker-compose up -d

# Manually generate daily report
docker-compose run --rm code-health daily

# View reports
open http://localhost:8080
```

### 3. CLI Usage

```bash
# Generate daily/weekly/monthly reports
python -m src.main daily
python -m src.main weekly
python -m src.main monthly --month 2025-01

# Send notifications
python -m src.main notify daily
python -m src.main notify weekly --week 2025-W02
```

## Project Structure (v2)

```
.code-health/
├── src/                         # v2 core code
│   ├── main.py                  # Main entry point
│   ├── config.py                # Configuration management
│   ├── providers/               # Git data providers
│   │   ├── base.py              # Provider abstract base class
│   │   ├── generic_git.py       # Generic Git Provider (shallow clone)
│   │   ├── github.py            # GitHub API Provider
│   │   ├── gitlab.py            # GitLab API Provider
│   │   └── codeup.py            # Alibaba Cloud Codeup Provider
│   ├── analyzers/               # Analyzers
│   │   ├── git_analyzer.py      # Git commit analysis
│   │   ├── churn.py             # Code churn analysis
│   │   ├── rework.py            # Rework rate analysis
│   │   ├── hotspot.py           # Hotspot file analysis
│   │   └── health_score.py      # Health score calculation
│   ├── reporters/               # Report generators
│   │   ├── base.py              # Report base class
│   │   ├── daily.py             # Daily report generation
│   │   ├── weekly.py            # Weekly report generation
│   │   └── monthly.py           # Monthly report generation
│   ├── notifiers/               # Notification modules
│   │   ├── base.py              # Notifier base class
│   │   ├── dingtalk.py          # DingTalk notification
│   │   └── feishu.py            # Feishu notification
│   └── utils/                   # Utility functions
│       └── helpers.py
├── config/
│   └── config.yaml              # Configuration file
├── scripts/                     # v1 scripts (kept for compatibility)
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── nginx.conf
├── README.md
└── QUICK_START.md
```

## Configuration

### Risk Threshold Configuration

```yaml
thresholds:
  large_commit: 500              # Large commit threshold (lines)
  tiny_commit: 10                # Tiny commit threshold (lines)

  churn_days: 3                  # Churn detection days
  churn_count: 5                 # Churn detection count

  rework_add_days: 7             # Rework detection: within N days after code added
  rework_delete_days: 3          # Rework detection: deleted is considered rework

  hotspot_days: 7                # Hotspot file statistics days
  hotspot_count: 10              # Hotspot modification count threshold
  large_file: 1000               # Large file line threshold
```

### Working Hours Configuration

```yaml
working_hours:
  normal_start: "09:00"          # Normal work start time
  normal_end: "18:00"            # Normal work end time
  overtime_start: "18:00"        # Overtime start time
  overtime_end: "21:00"          # Overtime end time
  late_night_start: "22:00"      # Late night start time
  late_night_end: "06:00"        # Late night end time
```

See [config.example.yaml](config.example.yaml) for detailed configuration.

## Usage Examples

### Manual Report Generation

```bash
cd scripts

# Generate today's daily report
python3 daily-report.py

# Generate report for specific date
python3 daily-report.py 2026-01-01

# Generate this week's weekly report
python3 weekly-report.py

# Generate report for specific week (ISO week format)
python3 weekly-report.py 2026-W01
```

### Convert to HTML

```bash
# Convert daily report
python3 md2html.py ../reports/daily/2026-01-04.md

# Batch convert
for file in ../reports/daily/*.md; do
    python3 md2html.py "$file"
done
```

### Generate Dashboard

```bash
# Generate 7-day dashboard
python3 dashboard-generator-range.py 7

# Generate 30-day dashboard
python3 dashboard-generator-range.py 30
```

### Push to DingTalk

```bash
# Push yesterday's daily report
./send-to-dingtalk.sh

# Push specific date's daily report
./send-to-dingtalk.sh 2026-01-04
```

## Metrics Documentation

See [METRICS.md](METRICS.md) for detailed metrics system, calculation methods, and risk assessment rules.

Key metrics include:
- **Code Churn Rate**: File stability indicator
- **Rework Rate**: Wasted effort indicator
- **Health Score**: Comprehensive code quality score (0-100)
- **High-Risk Files**: Files with risk score > 60
- **Working Hours Anomaly**: Overtime, late-night, weekend commit statistics

## Tech Stack

- **Data Collection**: Git CLI
- **Data Processing**: Python 3.8+
- **Script Orchestration**: Bash Shell
- **Report Generation**: Markdown + Python-Markdown
- **Visualization**: ECharts + HTML/CSS/JS
- **Notifications**: DingTalk Webhook API
- **Web Service**: Nginx
- **Scheduling**: Crontab

## Version History

### v2.0.0 (2026-01)

Major update with new architecture:

- ✅ Docker one-click deployment
- ✅ Provider architecture (GitHub/GitLab/Codeup support)
- ✅ Remote repository auto shallow clone
- ✅ Modular Python code structure
- ✅ Monthly report generation
- ✅ Enhanced security (no hardcoded tokens)

### v1.0.0 (2026-01-01)

Initial release with core features:

- ✅ Daily report auto-generation and push
- ✅ Weekly report auto-generation and push
- ✅ Code churn detection
- ✅ Rework rate analysis
- ✅ High-risk file identification
- ✅ Working hours anomaly detection
- ✅ Health score system
- ✅ Visualization dashboard (5 time ranges)
- ✅ DingTalk auto-push
- ✅ ECS one-click deployment
- ✅ Web access support

## Documentation

- [METRICS.md](METRICS.md) - Detailed metrics documentation
- [SECURITY.md](SECURITY.md) - Security best practices
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guide
- [config.example.yaml](config.example.yaml) - Configuration template

## FAQ

### 1. Report generation failed

Check if the repository path is correct and Git history is accessible:

```bash
cd /path/to/your/repo
git log --oneline -10
```

### 2. DingTalk push failed

- Check if webhook and secret are correctly configured
- Verify network connection
- Check DingTalk robot keyword settings

### 3. Web access 404

Check Nginx configuration and file permissions:

```bash
# Check Nginx config
nginx -t

# Check file permissions
ls -la /opt/your-project/.code-health/reports/
```

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
- [ ] Support custom report templates
- [ ] Add real-time monitoring alerts

## License

[MIT License](LICENSE)

## Author

- **yzhucn** - [GitHub](https://github.com/yzhucn)

---

**📊 Let data drive R&D efficiency improvement!**
