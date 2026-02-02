"""
配置管理模块
支持从 YAML 文件和环境变量加载配置
"""

import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

import yaml


# 默认配置
DEFAULT_CONFIG = {
    'project': {
        'name': '代码健康监控',
    },
    'git': {
        'platform': 'git',  # github, gitlab, codeup, git
        'token': '',
        'org': '',
        'base_url': '',
    },
    'thresholds': {
        'large_commit': 500,
        'tiny_commit': 10,
        'churn_days': 3,
        'churn_count': 5,
        'churn_rate_warning': 10,
        'churn_rate_danger': 30,
        'rework_add_days': 7,
        'rework_delete_days': 3,
        'rework_rate_warning': 15,
        'rework_rate_danger': 30,
        'hotspot_days': 7,
        'hotspot_count': 10,
        'large_file': 1000,
        'multi_author_count': 3,
        'health_score_excellent': 80,
        'health_score_good': 60,
        'health_score_warning': 40,
    },
    'working_hours': {
        'normal_start': '09:00',
        'normal_end': '18:00',
        'overtime_start': '18:00',
        'overtime_end': '21:00',
        'late_night_start': '22:00',
        'late_night_end': '06:00',
        'weekend_work_warning': True,
    },
    'notification': {
        'dingtalk': {
            'enabled': False,
            'webhook': '',
            'secret': '',
        },
        'feishu': {
            'enabled': False,
            'webhook': '',
        },
        'email': {
            'enabled': False,
            'smtp_server': '',
            'smtp_port': 587,
            'smtp_user': '',
            'smtp_password': '',
            'from': '',
            'to': [],
        },
    },
    'analysis': {
        'all_branches': True,
        'exclude_patterns': [
            '*.md', '*.txt', '*.json', '*.xml', '*.yaml', '*.yml',
            'package-lock.json', 'pom.xml', '.gitignore', 'LICENSE'
        ],
        'exclude_dirs': [
            'node_modules', '.git', '.idea', '__pycache__',
            'target', 'build', 'dist', 'venv', '.venv'
        ],
    },
    'web': {
        'base_url': 'http://localhost:8080',
    },
    'repositories': [],
}


# 环境变量映射
ENV_MAPPING = {
    # Git 配置
    'GIT_PLATFORM': 'git.platform',
    'GIT_TOKEN': 'git.token',
    'GIT_ORG': 'git.org',
    'GIT_BASE_URL': 'git.base_url',
    'CODEUP_ORG_ID': 'git.codeup_org_id',

    # 项目配置
    'PROJECT_NAME': 'project.name',

    # 通知配置
    'DINGTALK_ENABLED': 'notification.dingtalk.enabled',
    'DINGTALK_WEBHOOK': 'notification.dingtalk.webhook',
    'DINGTALK_SECRET': 'notification.dingtalk.secret',
    'DINGTALK_AT_MOBILES': 'notification.dingtalk.at_mobiles',
    'DINGTALK_AT_USERIDS': 'notification.dingtalk.at_userids',
    'FEISHU_ENABLED': 'notification.feishu.enabled',
    'FEISHU_WEBHOOK': 'notification.feishu.webhook',

    # Web 配置
    'WEB_BASE_URL': 'web.base_url',

    # 阈值配置
    'THRESHOLD_LARGE_COMMIT': 'thresholds.large_commit',
    'THRESHOLD_CHURN_DAYS': 'thresholds.churn_days',
    'THRESHOLD_CHURN_COUNT': 'thresholds.churn_count',
    'THRESHOLD_REWORK_ADD_DAYS': 'thresholds.rework_add_days',
    'THRESHOLD_REWORK_DELETE_DAYS': 'thresholds.rework_delete_days',
}


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并两个字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _set_nested_value(config: Dict, path: str, value: Any) -> None:
    """设置嵌套字典的值"""
    keys = path.split('.')
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    final_key = keys[-1]
    if isinstance(current.get(final_key), bool):
        value = str(value).lower() in ('true', '1', 'yes')
    elif isinstance(current.get(final_key), int):
        try:
            value = int(value)
        except ValueError:
            pass

    current[final_key] = value


def _get_nested_value(config: Dict, path: str, default: Any = None) -> Any:
    """获取嵌套字典的值"""
    keys = path.split('.')
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def _expand_env_vars(value: str) -> str:
    """展开字符串中的环境变量 ${VAR} 或 ${VAR:-default}"""
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'

    def replace(match):
        var_name = match.group(1)
        default = match.group(2) or ''
        return os.environ.get(var_name, default)

    return re.sub(pattern, replace, value)


def _process_config_values(config: Dict) -> Dict:
    """处理配置中的环境变量引用"""
    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[key] = _process_config_values(value)
        elif isinstance(value, str):
            result[key] = _expand_env_vars(value)
        elif isinstance(value, list):
            result[key] = [
                _expand_env_vars(v) if isinstance(v, str) else v
                for v in value
            ]
        else:
            result[key] = value
    return result


def load_config(config_path: Optional[str] = None, use_env: bool = True) -> Dict:
    """
    加载配置

    优先级（从低到高）:
    1. 默认配置
    2. YAML 配置文件
    3. 环境变量
    """
    config = DEFAULT_CONFIG.copy()

    if config_path is None:
        config_path = os.environ.get('CODE_HEALTH_CONFIG', '')

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f) or {}
            yaml_config = _process_config_values(yaml_config)
            config = _deep_merge(config, yaml_config)

    if use_env:
        for env_var, config_path_key in ENV_MAPPING.items():
            value = os.environ.get(env_var)
            if value is not None:
                _set_nested_value(config, config_path_key, value)

    return config


def get_repositories(config: Dict) -> List[Dict]:
    """获取仓库列表"""
    repositories = config.get('repositories', [])

    if not repositories:
        repos_env = os.environ.get('REPOSITORIES')
        if repos_env:
            for repo_str in repos_env.split(','):
                parts = repo_str.strip().split('|')
                if len(parts) >= 2:
                    repositories.append({
                        'name': parts[0],
                        'url': parts[1],
                        'type': parts[2] if len(parts) > 2 else 'unknown',
                        'main_branch': parts[3] if len(parts) > 3 else 'main',
                    })

    return repositories


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        self._config = load_config(config_path)

    def get(self, path: str, default: Any = None) -> Any:
        return _get_nested_value(self._config, path, default)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        return key in self._config

    @property
    def project_name(self) -> str:
        return self.get('project.name', '代码健康监控')

    @property
    def git_platform(self) -> str:
        return self.get('git.platform', 'git')

    @property
    def git_token(self) -> str:
        return self.get('git.token', '')

    @property
    def git_org(self) -> str:
        return self.get('git.org', '')

    @property
    def repositories(self) -> List[Dict]:
        return get_repositories(self._config)

    @property
    def thresholds(self) -> Dict:
        return self._config.get('thresholds', {})

    @property
    def dingtalk_enabled(self) -> bool:
        return self.get('notification.dingtalk.enabled', False)

    @property
    def dingtalk_webhook(self) -> str:
        return self.get('notification.dingtalk.webhook', '')

    @property
    def dingtalk_secret(self) -> str:
        return self.get('notification.dingtalk.secret', '')

    @property
    def dingtalk_at_mobiles(self) -> List[str]:
        """获取钉钉 @ 人手机号列表"""
        mobiles = self.get('notification.dingtalk.at_mobiles', '')
        if isinstance(mobiles, str) and mobiles:
            return [m.strip() for m in mobiles.split(',') if m.strip()]
        elif isinstance(mobiles, list):
            return mobiles
        return []

    @property
    def dingtalk_at_userids(self) -> List[str]:
        """获取钉钉 @ 人 userId 列表"""
        userids = self.get('notification.dingtalk.at_userids', '')
        if isinstance(userids, str) and userids:
            return [u.strip() for u in userids.split(',') if u.strip()]
        elif isinstance(userids, list):
            return userids
        return []

    @property
    def web_base_url(self) -> str:
        return self.get('web.base_url', 'http://localhost:8080')

    @property
    def feishu_enabled(self) -> bool:
        return self.get('notification.feishu.enabled', False)

    @property
    def feishu_webhook(self) -> str:
        return self.get('notification.feishu.webhook', '')

    def to_dict(self) -> Dict:
        return self._config.copy()
