# 故障排查指南 (Troubleshooting Guide)

> 本文档记录 Code Health Monitor 常见问题及解决方案

## 目录

- [1. 钉钉/飞书消息数据为空](#1-钉钉飞书消息数据为空)
- [2. Git 克隆失败](#2-git-克隆失败)
- [3. 脚本执行异常退出](#3-脚本执行异常退出)
- [4. 云效 API 调用问题](#4-云效-api-调用问题)
- [5. Cron 任务不执行](#5-cron-任务不执行)
- [6. 月报脚本数据统计错误](#6-月报脚本数据统计错误)

---

## 1. 钉钉/飞书消息数据为空

### 现象
收到的钉钉消息显示所有数据为 0，如：
```
今日提交: 0 次
代码变更: +0 / -0
```

### 可能原因

| 原因 | 排查方法 |
|------|----------|
| `repos-list.txt` 丢失 | 检查文件是否存在 |
| 仓库路径错误 | 检查 `config.yaml` 中的路径配置 |
| Git 克隆失败 | 查看 `reports/clone.log` |
| 报告生成失败 | 查看 `reports/daily-prepare.log` |

### 解决方案

```bash
# 1. 检查仓库列表文件
ls -la /opt/ecomind/.code-health/repos-list.txt

# 2. 检查克隆日志
tail -50 /opt/ecomind/.code-health/reports/clone.log

# 3. 手动运行克隆测试
cd /opt/ecomind/.code-health/scripts
source /etc/environment  # 加载环境变量
bash auto-clone-repos.sh

# 4. 检查仓库目录
ls -la /opt/ecomind/repos/
```

---

## 2. Git 克隆失败

### 现象
克隆日志显示错误：
```
fatal: could not read Username for 'https://...': No such device or address
```

### 原因分析
Git 无法获取认证凭证，可能是：
1. `GIT_TOKEN` 环境变量未设置
2. Cron 任务未加载环境变量
3. Token 已过期

### 解决方案

```bash
# 1. 检查环境变量
grep GIT_TOKEN /etc/environment

# 2. 如果未设置，添加 Token
echo 'GIT_TOKEN="your_token_here"' >> /etc/environment

# 3. 确保脚本加载环境变量
# 在 daily-prepare.sh 开头添加：
[ -f /etc/environment ] && source /etc/environment

# 4. 测试克隆
export GIT_TOKEN="your_token"
bash auto-clone-repos.sh
```

---

## 3. 脚本执行异常退出

### 经典问题: `set -e` 与 `(())` 的陷阱

#### 现象
脚本在第一个循环迭代后就退出，只处理了一个仓库。

#### 原因
```bash
set -e  # 遇到非零退出码时终止脚本

SUCCESS_COUNT=0
# ...
((SUCCESS_COUNT++))  # 当 SUCCESS_COUNT=0 时，0++ 结果为 0
                      # 在算术上 0 被视为 false，返回退出码 1
                      # 触发 set -e 终止脚本！
```

#### 解决方案

```bash
# 方案1: 使用前缀自增（推荐）
((++SUCCESS_COUNT))  # 先加再返回，结果为 1，退出码为 0

# 方案2: 使用算术扩展
SUCCESS_COUNT=$((SUCCESS_COUNT + 1))

# 方案3: 添加 || true（不推荐，隐藏了问题）
((SUCCESS_COUNT++)) || true
```

> **教训**: 在 `set -e` 环境下，避免使用后缀自增 `((var++))`，改用 `var=$((var + 1))`

---

## 4. 云效 API 调用问题

### 正确的服务接入点

云效 Codeup API 的正确 domain 是：

```
openapi-rdc.aliyuncs.com
```

**不是**：
- ~~codeup.aliyun.com~~ (Web 界面)
- ~~codeup.cn-hangzhou.aliyuncs.com~~ (SDK 专用)
- ~~devops.cn-hangzhou.aliyuncs.com~~ (其他服务)

### 正确的 API 调用方式

```bash
# 使用个人访问令牌调用 ListRepositories API
curl -s "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/${ORG_ID}/repositories?page=1&perPage=100" \
  -H "Content-Type: application/json" \
  -H "x-yunxiao-token: ${TOKEN}"
```

### 认证方式对比

| 认证方式 | 适用场景 | Header |
|----------|----------|--------|
| 个人访问令牌 | API 调用、Git 克隆 | `x-yunxiao-token` |
| AK&SK | SDK 调用（需关联云效账号） | 签名认证 |

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| 302 重定向到登录页 | domain 错误 | 使用 `openapi-rdc.aliyuncs.com` |
| `SYSTEM_NOT_FOUND_ERROR` | AK 未关联云效 | 使用个人访问令牌 |
| `InvalidAction.NotFound` | API 路径错误 | 检查 URL 格式 |

---

## 5. Cron 任务不执行

### 排查步骤

```bash
# 1. 检查 crontab 配置
crontab -l

# 2. 检查 cron 日志
grep CRON /var/log/syslog | tail -20

# 3. 检查脚本权限
ls -la /opt/ecomind/.code-health/scripts/*.sh

# 4. 手动测试脚本
cd /opt/ecomind/.code-health/scripts
bash daily-prepare.sh
```

### 环境变量问题

Cron 任务运行在最小化环境中，不会自动加载 `/etc/environment`。

**解决方案**: 在脚本开头添加：

```bash
# 加载环境变量
[ -f /etc/environment ] && source /etc/environment
```

---

## 最佳实践

### 日志检查清单

```bash
# 克隆日志
tail -f /opt/ecomind/.code-health/reports/clone.log

# 日报准备日志
tail -f /opt/ecomind/.code-health/reports/daily-prepare.log

# Cron 日志
tail -f /opt/ecomind/.code-health/reports/cron.log

# 归档日志
tail -f /opt/ecomind/.code-health/logs/archive.log
```

### 快速恢复脚本

```bash
#!/bin/bash
# quick-fix.sh - 快速恢复服务

# 1. 加载环境变量
source /etc/environment

# 2. 重新克隆仓库
cd /opt/ecomind/.code-health/scripts
bash auto-clone-repos.sh

# 3. 重新生成今日报告
bash daily-prepare.sh

# 4. 检查结果
ls -la ../reports/daily/$(date +%Y-%m-%d).md
```

---

## 6. 月报脚本数据统计错误

### 现象
月报中深夜/周末提交统计数据不准确，或统计结果全为 0。

### 原因分析
函数调用时传入了错误的参数类型：

```python
# ❌ 错误用法（传入 datetime 对象）
is_late_night(parse_iso_datetime(c['date']), self.config)
is_weekend(parse_iso_datetime(c['date']))

# ✅ 正确用法（传入字符串）
is_late_night(c['date'], self.config)
is_weekend(c['date'])
```

`is_late_night()` 和 `is_weekend()` 函数期望字符串参数，会在内部调用 `parse_iso_datetime()` 进行解析。

### 解决方案

检查 `monthly-report.py` 中的函数调用，确保传入字符串而非 datetime 对象：

```python
# 参考 daily-report.py 和 weekly-report.py 的正确用法
late_night = len([c for c in all_commits if is_late_night(c['date'], self.config)])
weekend = len([c for c in all_commits if is_weekend(c['date'])])
```

> **教训**: 调用函数前检查参数类型是否符合函数签名，参考其他调用点保持一致性。

---

**更新时间**: 2026-01-09
