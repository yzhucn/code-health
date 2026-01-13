# V2 Source - CLAUDE.md

V2 版本使用 Python 模块架构，支持 Docker 部署和多平台 API。

## 目录结构

```
src/
├── CLAUDE.md                 # 本文件
├── __init__.py
├── main.py                   # 主入口 (CLI)
├── config.py                 # 配置管理
│
├── providers/                # Git 数据提供者
│   ├── __init__.py
│   ├── base.py               # 基类定义 (GitProvider, CommitInfo, RepoInfo)
│   ├── codeup.py             # 阿里云 Codeup API
│   ├── github.py             # GitHub API
│   ├── gitlab.py             # GitLab API
│   └── generic_git.py        # 通用 Git (本地克隆)
│
├── reporters/                # 报告生成器
│   ├── __init__.py
│   ├── base.py               # 基类定义
│   ├── daily.py              # 日报生成
│   ├── weekly.py             # 周报生成
│   └── monthly.py            # 月报生成
│
├── analyzers/                # 数据分析器
│   ├── __init__.py
│   ├── git_analyzer.py       # Git 提交分析
│   ├── health_score.py       # 健康评分计算
│   ├── churn.py              # 代码震荡分析
│   ├── rework.py             # 返工率分析
│   └── hotspot.py            # 热点文件分析
│
├── notifiers/                # 通知器
│   ├── __init__.py
│   ├── base.py               # 基类定义
│   ├── dingtalk.py           # 钉钉通知
│   └── feishu.py             # 飞书通知
│
└── utils/                    # 工具类
    ├── __init__.py
    ├── helpers.py            # 通用工具函数
    ├── html_generator.py     # Markdown 转 HTML
    ├── index_generator.py    # 索引页面生成
    └── dashboard_generator.py # 可视化仪表盘
```

---

## 核心组件

### 1. Providers (数据提供者)

Provider 负责获取 Git 仓库数据，支持多种平台。

#### base.py 定义的接口

```python
class GitProvider(ABC):
    def list_repositories() -> List[RepoInfo]
    def get_commits(repo_id, since, until, branch) -> List[CommitInfo]
    def list_branches(repo_id) -> List[str]
    def get_file_content(repo_id, filepath, ref) -> str
```

#### codeup.py (重点)

阿里云 Codeup API Provider。

**配置**:
```python
# 环境变量
CODEUP_TOKEN      # 云效个人访问令牌
CODEUP_ORG_ID     # 云效企业 ID
CODEUP_PROJECT    # 项目命名空间 (如 "my-project")
```

**特性**:
- 使用 `x-yunxiao-token` 认证
- 自动按项目命名空间过滤仓库
- 支持指定仓库列表过滤
- 自动推断仓库类型 (java/python/vue/android)

**仓库获取逻辑**:
1. 获取组织下所有仓库 `_fetch_all_repositories()`
2. 按项目过滤 `_filter_by_project()` - 匹配路径 `/{project}/`
3. 或按配置列表过滤 `_filter_by_config()`

### 2. Reporters (报告生成器)

#### daily.py
日报生成器。

**输入**: 指定日期的提交数据
**输出**: Markdown 格式日报

**内容**:
- 今日概况 (提交/开发者/仓库/文件数)
- 代码变更统计 (新增/删除/净增)
- 各仓库变更详情
- 风险预警 (加班/深夜/周末提交)
- 健康评分
- 提交详情 (按开发者分组)

#### weekly.py
周报生成器。

**内容**:
- 贡献排行榜 (按净增代码排序)
- 团队总产出
- 仓库分布
- 代码质量 (大提交/微小提交/提交信息质量)
- 工作时间分布 (ASCII 热力图)
- 健康评分
- 改进建议

#### monthly.py
月报生成器。

**内容**:
- 月度总览 (核心指标)
- 贡献排行榜
- 仓库贡献统计
- 每周趋势
- 健康评分
- 工作时间分布
- 提交粒度分析
- 文件修改热点
- 下月建议

### 3. Analyzers (分析器)

#### health_score.py
健康评分计算。

**扣分项**:
- 大提交 (>500行): -5分/次
- 深夜提交 (22:00-06:00): -2分/次
- 周末提交: -1分/次

**评分等级**:
- 80-100: 优秀
- 60-79: 良好
- 40-59: 警告
- 0-39: 危险

### 4. Notifiers (通知器)

#### dingtalk.py
钉钉通知器。

**特性**:
- Webhook 推送
- HMAC-SHA256 加签验证
- Markdown 消息格式
- 日报/周报/月报专用格式

**消息格式**:
- `_format_daily_message()` - 日报格式
- `_format_weekly_message()` - 周报格式
- `_format_monthly_message()` - 月报格式

### 5. Utils (工具类)

#### html_generator.py
Markdown 转 HTML。

**功能**:
- 单文件转换 `convert_md_to_html()`
- 批量转换 `convert_all_reports()`
- 自动添加 CSS 样式和 ECharts 图表

#### index_generator.py
生成报告索引页面。

**功能**:
- 扫描日报/周报/月报
- 按时间分组显示
- 生成仪表盘入口
- 生成历史报告入口

#### dashboard_generator.py
可视化仪表盘生成。

**功能**:
- 提交趋势图
- 代码量趋势图
- 活跃人数趋势图
- 时间分布热力图
- 仓库分布饼图
- 开发者排行
- 项目生命周期

**时间范围**:
- 7/14/30/60/90 天可选

---

## 命令行接口

```bash
# 主入口
python -m src.main <command> [options]

# 命令
daily     # 生成日报
weekly    # 生成周报
monthly   # 生成月报
notify    # 发送通知
html      # 生成 HTML
dashboard # 生成仪表盘

# 参数
--config, -c     # 配置文件路径
--output, -o     # 输出目录
--date           # 日期 (YYYY-MM-DD)
--week           # 周 (YYYY-Wxx)
--month          # 月 (YYYY-MM)
--days           # 仪表盘天数
--report-file    # 报告文件路径 (notify)
```

---

## 配置管理

### config.py

配置优先级: 环境变量 > 配置文件 > 默认值

**主要配置项**:
```python
# Git 平台
git_platform     # codeup/github/gitlab/generic
git_token        # 访问令牌
git_org          # 组织/企业

# 项目
project_name     # 项目名称

# 钉钉
dingtalk_enabled # 是否启用
dingtalk_webhook # Webhook URL
dingtalk_secret  # 加签密钥

# 输出
web_base_url     # Web 访问地址
```

---

## Docker 部署

### entrypoint.sh 命令

```bash
daily       # 生成日报 + 通知
weekly      # 生成周报 + 通知
monthly     # 生成月报 + 通知
html        # 生成所有 HTML
dashboard   # 生成仪表盘
notify      # 仅发送通知
serve       # 启动 Nginx 服务
```

### docker-compose.yml

```yaml
services:
  code-health:
    build: .
    environment:
      - CODEUP_TOKEN
      - CODEUP_ORG_ID
      - CODEUP_PROJECT
    volumes:
      - ./reports:/app/reports
      - ./dashboard:/app/dashboard
```

---

## 数据流程

```
1. main.py
   └─> 解析命令行参数
   └─> 加载配置 (config.py)
   └─> 创建 Provider (codeup/github/gitlab)

2. Provider.list_repositories()
   └─> 获取仓库列表
   └─> 过滤指定项目仓库

3. Provider.get_commits()
   └─> 获取所有分支
   └─> 获取每个分支的提交
   └─> 去重合并

4. Reporter.generate()
   └─> 调用 Analyzer 分析数据
   └─> 生成 Markdown 报告

5. html_generator.convert_md_to_html()
   └─> 转换为 HTML
   └─> 添加 ECharts 图表

6. index_generator.generate_index()
   └─> 更新索引页面

7. Notifier.send()
   └─> 格式化消息
   └─> 发送到钉钉/飞书
```

---

## 安全检查

### 敏感信息保护

1. **Token 不能硬编码**: 必须使用环境变量
2. **配置文件排除**: config.yaml 在 .gitignore 中
3. **测试配置隔离**: .env.test 在 .gitignore 中

### 数据验证

V2 在以下位置进行数据验证:

1. **Provider 层**: 检查 Token/Org ID 配置
2. **Reporter 层**: 检查提交数据是否为空
3. **Notifier 层**: 检查 Webhook 配置是否有效

### 发送前检查 (dingtalk.py)

```python
def is_enabled(self) -> bool:
    return (
        self.config.dingtalk_enabled and
        self.webhook and
        self.webhook != 'YOUR_DINGTALK_WEBHOOK'  # 防止发送到示例 URL
    )
```

---

## V1 -> V2 迁移对照

| V1 文件 | V2 文件 | 说明 |
|---------|---------|------|
| daily-report.py | reporters/daily.py | 日报生成 |
| weekly-report.py | reporters/weekly.py | 周报生成 |
| monthly-report.py | reporters/monthly.py | 月报生成 |
| md2html.py | utils/html_generator.py | HTML 生成 |
| generate-index.py | utils/index_generator.py | 索引页面 |
| dashboard-generator-range.py | utils/dashboard_generator.py | 仪表盘 |
| send-to-dingtalk.sh | notifiers/dingtalk.py | 钉钉通知 |
| validate-before-send.sh | (内置验证) | 数据验证 |
| auto-clone-repos.sh | providers/generic_git.py | 仓库克隆 |
| - | providers/codeup.py | Codeup API (新增) |
| - | providers/github.py | GitHub API (新增) |
| - | providers/gitlab.py | GitLab API (新增) |

---

## 测试验证

### 本地测试

```bash
# 加载测试配置
source .env.test

# 测试日报
python -m src.main daily --date 2025-12-04 --output reports_v2_test

# 测试周报
python -m src.main weekly --week 2025-W50 --output reports_v2_test

# 测试月报
python -m src.main monthly --month 2025-12 --output reports_v2_test

# 对比 V1 和 V2
diff reports/daily/2025-12-04.md reports_v2_test/daily/2025-12-04.md
```

### Docker 测试

```bash
docker-compose build
docker-compose run --rm code-health daily
docker-compose run --rm code-health weekly
```

---

## 常见问题

### Q: Provider 返回空仓库列表
A: 检查以下几点:
1. CODEUP_TOKEN 是否有效
2. CODEUP_ORG_ID 是否正确
3. CODEUP_PROJECT 是否匹配仓库路径

### Q: 提交数据比 V1 多
A: 这是预期行为:
- V2 通过 API 获取项目下所有仓库
- V1 只分析配置的本地仓库

### Q: 钉钉消息格式不正确
A: 检查 `dingtalk.py` 中的格式化方法:
- `_format_daily_message()`
- `_format_weekly_message()`
- `_format_monthly_message()`
