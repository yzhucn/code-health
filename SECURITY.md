# 安全配置指南

**中文** | [English](SECURITY_EN.md)

## ⚠️ 重要提醒

**切勿将以下敏感信息提交到 Git 仓库**：

1. ❌ 钉钉/飞书 Webhook 和 Secret
2. ❌ Git 仓库访问 Token
3. ❌ 服务器 IP 地址
4. ❌ 私有仓库 URL
5. ❌ 团队成员真实邮箱
6. ❌ 任何密码、密钥、凭证

## 📋 配置清单

### 1. 创建本地配置文件

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑配置文件
vim config.yaml
```

### 2. 配置 Git 凭证

#### 方式一：环境变量（推荐）

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export GIT_TOKEN="your_git_access_token_here"

# 或在运行时指定
GIT_TOKEN="your_token" ./scripts/daily-job.sh
```

#### 方式二：Git 凭证存储

```bash
# 配置 Git 凭证助手
git config --global credential.helper store

# 首次克隆时输入用户名和 token
git clone https://yourname:YOUR_TOKEN@git.example.com/repo.git
```

#### 方式三：SSH 密钥（最安全）

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加公钥到 Git 服务器
cat ~/.ssh/id_ed25519.pub

# 使用 SSH URL 克隆仓库
git clone git@git.example.com:yourname/repo.git
```

### 3. 配置钉钉/飞书通知

**config.yaml** 中配置：

```yaml
notification:
  dingtalk:
    enabled: true
    webhook: https://oapi.dingtalk.com/robot/send?access_token=YOUR_REAL_TOKEN
    secret: YOUR_REAL_SECRET

  feishu:
    enabled: false
    webhook: https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_REAL_WEBHOOK
```

**获取钉钉凭证**：

1. 登录钉钉管理后台
2. 进入「智能群助手」→「自定义机器人」
3. 创建机器人，选择「加签」安全设置
4. 复制 Webhook URL 和 Secret

### 4. 配置仓库路径

在 **config.yaml** 中配置你的实际仓库：

```yaml
repositories:
  # 本地仓库（绝对路径）
  - path: /Users/yourname/code/project1
    name: project1
    type: java
    main_branch: main

  # 远程仓库（需要先克隆到本地）
  - path: /opt/repos/project2
    name: project2
    type: python
    main_branch: dev
```

## 🔒 ECS 服务器部署安全配置

### 1. 在 ECS 上配置环境变量

```bash
# SSH 登录 ECS
ssh root@YOUR_ECS_IP

# 编辑环境变量
vim ~/.bashrc

# 添加以下内容
export GIT_TOKEN="your_git_access_token"
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=XXX"
export DINGTALK_SECRET="YOUR_SECRET"

# 使配置生效
source ~/.bashrc
```

### 2. 使用 AWS Secrets Manager（可选）

如果使用云服务，建议使用密钥管理服务：

```bash
# 安装 AWS CLI
pip3 install awscli

# 配置凭证
aws configure

# 从 Secrets Manager 读取密钥
aws secretsmanager get-secret-value --secret-id prod/code-health/dingtalk --query SecretString --output text
```

### 3. 限制文件权限

```bash
# 确保配置文件只有所有者可读
chmod 600 config.yaml

# 检查权限
ls -la config.yaml
# 应该显示: -rw------- 1 root root
```

## 🛡️ 安全检查清单

在推送代码前，务必检查：

- [ ] `config.yaml` 已在 `.gitignore` 中
- [ ] `config.example.yaml` 中无真实凭证
- [ ] 文档中无真实 IP、Token、Secret
- [ ] 脚本中无硬编码密码、Token
- [ ] `.git/config` 中无明文凭证
- [ ] 运行 `git status` 确认敏感文件未被追踪

### 快速检查命令

```bash
# 检查是否有敏感信息
grep -r "access_token" . --exclude-dir=.git
grep -r "SECRET" . --exclude-dir=.git
grep -r "password" . --exclude-dir=.git

# 检查 git 状态
git status

# 查看将要提交的内容
git diff --cached
```

## 🚨 如果不小心泄露了敏感信息

### 1. 立即撤销凭证

- 钉钉：删除并重新创建机器人
- Git Token：立即撤销并生成新 token
- SSH 密钥：删除公钥并重新生成

### 2. 从 Git 历史中移除

```bash
# 使用 git-filter-repo 清理历史
pip3 install git-filter-repo

# 移除敏感文件
git filter-repo --path config.yaml --invert-paths

# 强制推送（危险操作，仅在私有仓库且无协作者时使用）
git push origin --force --all
```

### 3. 修改所有暴露的凭证

- 更换所有密钥、Token、密码
- 审查访问日志，查看是否被滥用
- 通知团队成员

## 📚 参考资源

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [钉钉开放平台: 自定义机器人](https://open.dingtalk.com/document/robots/custom-robot-access)
- [Git Credential Storage](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage)

## ✅ 最佳实践

1. **使用环境变量**：所有敏感配置通过环境变量传递
2. **最小权限原则**：Token 只授予必要的权限
3. **定期轮换**：每 3-6 个月更换一次密钥
4. **审计日志**：定期检查访问日志
5. **团队培训**：确保所有成员了解安全规范

---

**记住：安全无小事，预防胜于补救！**
