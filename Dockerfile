# Code Health Monitor - Docker镜像
# 代码健康监控系统 - 轻量化部署版本

FROM python:3.11-slim

LABEL maintainer="code-health team"
LABEL description="Code Health Monitor - 代码健康监控系统"
LABEL version="2.1.0"

# 使用国内镜像源并安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖 (使用国内镜像)
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY entrypoint.sh .

# 创建必要目录
RUN mkdir -p /app/reports/daily /app/reports/weekly /app/reports/monthly \
    /app/dashboard /app/logs /app/config /tmp/code-health-repos

# 设置权限
RUN chmod +x /app/entrypoint.sh

# 环境变量
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai
ENV CODE_HEALTH_CONFIG=/app/config/config.yaml

# 数据卷
VOLUME ["/app/reports", "/app/dashboard", "/app/logs"]

# 入口点
ENTRYPOINT ["/app/entrypoint.sh"]

# 默认命令
CMD ["--help"]
