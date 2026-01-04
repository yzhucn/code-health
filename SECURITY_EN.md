# Security Configuration Guide

[中文版](SECURITY.md) | **English**

## ⚠️ Important Warning

**Never commit the following sensitive information to Git repository**:

1. ❌ DingTalk/Feishu Webhook and Secret
2. ❌ Git repository access Token
3. ❌ Server IP addresses
4. ❌ Private repository URLs
5. ❌ Team members' real email addresses
6. ❌ Any passwords, keys, or credentials

## 📋 Configuration Checklist

### 1. Create Local Configuration File

```bash
# Copy configuration template
cp config.example.yaml config.yaml

# Edit configuration file
vim config.yaml
```

### 2. Configure Git Credentials

#### Method 1: Environment Variables (Recommended)

```bash
# Add to ~/.bashrc or ~/.zshrc
export GIT_TOKEN="your_git_access_token_here"

# Or specify at runtime
GIT_TOKEN="your_token" ./scripts/daily-job.sh
```

#### Method 2: Git Credential Storage

```bash
# Configure Git credential helper
git config --global credential.helper store

# Enter username and token when cloning for the first time
git clone https://yourname:YOUR_TOKEN@git.example.com/repo.git
```

#### Method 3: SSH Keys (Most Secure)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add public key to Git server
cat ~/.ssh/id_ed25519.pub

# Clone repository using SSH URL
git clone git@git.example.com:yourname/repo.git
```

### 3. Configure DingTalk/Feishu Notifications

In **config.yaml**:

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

**Getting DingTalk Credentials**:

1. Log in to DingTalk admin console
2. Go to "Smart Group Assistant" → "Custom Robot"
3. Create robot, choose "Signature" security setting
4. Copy Webhook URL and Secret

### 4. Configure Repository Paths

In **config.yaml**, configure your actual repositories:

```yaml
repositories:
  # Local repository (absolute path)
  - path: /Users/yourname/code/project1
    name: project1
    type: java
    main_branch: main

  # Remote repository (needs to be cloned locally first)
  - path: /opt/repos/project2
    name: project2
    type: python
    main_branch: dev
```

## 🔒 ECS Server Deployment Security Configuration

### 1. Configure Environment Variables on ECS

```bash
# SSH login to ECS
ssh root@YOUR_ECS_IP

# Edit environment variables
vim ~/.bashrc

# Add the following content
export GIT_TOKEN="your_git_access_token"
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=XXX"
export DINGTALK_SECRET="YOUR_SECRET"

# Apply configuration
source ~/.bashrc
```

### 2. Use AWS Secrets Manager (Optional)

If using cloud services, it's recommended to use secrets management service:

```bash
# Install AWS CLI
pip3 install awscli

# Configure credentials
aws configure

# Read secrets from Secrets Manager
aws secretsmanager get-secret-value --secret-id prod/code-health/dingtalk --query SecretString --output text
```

### 3. Limit File Permissions

```bash
# Ensure configuration file is only readable by owner
chmod 600 config.yaml

# Check permissions
ls -la config.yaml
# Should display: -rw------- 1 root root
```

## 🛡️ Security Checklist

Before pushing code, always check:

- [ ] `config.yaml` is in `.gitignore`
- [ ] `config.example.yaml` contains no real credentials
- [ ] Documentation contains no real IP, Token, or Secret
- [ ] Scripts contain no hardcoded passwords or Tokens
- [ ] `.git/config` contains no plaintext credentials
- [ ] Run `git status` to confirm sensitive files are not tracked

### Quick Check Commands

```bash
# Check for sensitive information
grep -r "access_token" . --exclude-dir=.git
grep -r "SECRET" . --exclude-dir=.git
grep -r "password" . --exclude-dir=.git

# Check git status
git status

# View content to be committed
git diff --cached
```

## 🚨 If You Accidentally Leaked Sensitive Information

### 1. Immediately Revoke Credentials

- DingTalk: Delete and recreate the robot
- Git Token: Immediately revoke and generate new token
- SSH Key: Delete public key and regenerate

### 2. Remove from Git History

```bash
# Use git-filter-repo to clean history
pip3 install git-filter-repo

# Remove sensitive files
git filter-repo --path config.yaml --invert-paths

# Force push (dangerous operation, only use in private repos without collaborators)
git push origin --force --all
```

### 3. Change All Exposed Credentials

- Replace all keys, Tokens, passwords
- Review access logs to check for abuse
- Notify team members

## 📚 Reference Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [DingTalk Open Platform: Custom Robot](https://open.dingtalk.com/document/robots/custom-robot-access)
- [Git Credential Storage](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage)

## ✅ Best Practices

1. **Use Environment Variables**: Pass all sensitive configurations through environment variables
2. **Principle of Least Privilege**: Grant only necessary permissions to Tokens
3. **Regular Rotation**: Replace keys every 3-6 months
4. **Audit Logs**: Regularly check access logs
5. **Team Training**: Ensure all members understand security standards

---

**Remember: Security is no small matter, prevention is better than cure!**
