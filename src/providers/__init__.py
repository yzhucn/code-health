"""
Git Provider 模块
提供统一的 Git 数据访问接口，支持多种 Git 平台
"""

from .base import GitProvider, CommitInfo, FileChange, RepoInfo
from .generic_git import GenericGitProvider
from .github import GitHubProvider
from .gitlab import GitLabProvider
from .codeup import CodeupProvider

__all__ = [
    'GitProvider',
    'CommitInfo',
    'FileChange',
    'RepoInfo',
    'GenericGitProvider',
    'GitHubProvider',
    'GitLabProvider',
    'CodeupProvider',
]
