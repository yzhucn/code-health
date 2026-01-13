"""
Git 分析器
基于 Provider 模式，兼容多种 Git 平台
"""

from typing import List, Dict, Optional, Set
from datetime import datetime

from ..providers.base import GitProvider, CommitInfo


class GitAnalyzer:
    """
    Git 仓库分析器

    使用 Provider 模式获取数据，支持：
    - GitHub API
    - GitLab API
    - 云效 Codeup API
    - 通用 Git（浅 clone）
    """

    def __init__(self, provider: GitProvider, repo_id: str):
        """
        初始化 Git 分析器

        Args:
            provider: Git 数据提供者
            repo_id: 仓库标识符
        """
        self.provider = provider
        self.repo_id = repo_id
        self.repo_name = repo_id  # 兼容旧接口

    def get_commits(
        self,
        since: str = "1 day ago",
        until: Optional[str] = None,
        branch: str = "all"
    ) -> List[CommitInfo]:
        """
        获取提交记录

        Args:
            since: 开始时间（如 "1 day ago", "7 days ago", "2024-01-01"）
            until: 结束时间（可选）
            branch: 分支名称，"all" 表示所有分支

        Returns:
            提交信息列表
        """
        return self.provider.get_commits(self.repo_id, since, until, branch)

    def get_commits_as_dict(
        self,
        since: str = "1 day ago",
        until: Optional[str] = None,
        branch: str = "all"
    ) -> List[Dict]:
        """
        获取提交记录（字典格式，兼容旧接口）

        Returns:
            提交信息列表（字典格式）
        """
        commits = self.get_commits(since, until, branch)
        return [c.to_dict() for c in commits]

    def get_file_history(
        self,
        filepath: str,
        since: str = "7 days ago"
    ) -> List[Dict]:
        """
        获取文件修改历史

        Args:
            filepath: 文件路径
            since: 开始时间

        Returns:
            修改历史列表
        """
        commits = self.provider.get_file_history(self.repo_id, filepath, since)
        return [
            {
                'hash': c.hash,
                'author': c.author,
                'date': c.date
            }
            for c in commits
        ]

    def get_all_modified_files(self, since: str = "1 day ago") -> List[str]:
        """
        获取所有修改过的文件

        Args:
            since: 开始时间

        Returns:
            文件路径列表
        """
        commits = self.get_commits(since)
        files = set()
        for commit in commits:
            for f in commit.files:
                files.add(f.path)
        return list(files)

    def get_file_size(self, filepath: str) -> int:
        """
        获取文件行数

        Args:
            filepath: 文件路径

        Returns:
            文件行数
        """
        return self.provider.get_file_line_count(self.repo_id, filepath)

    def get_file_authors(self, filepath: str, since: str = "7 days ago") -> Set[str]:
        """
        获取文件的作者列表

        Args:
            filepath: 文件路径
            since: 开始时间

        Returns:
            作者集合
        """
        history = self.get_file_history(filepath, since)
        return set(h['author'] for h in history)


class MultiRepoAnalyzer:
    """
    多仓库分析器

    批量分析多个仓库
    """

    def __init__(self, provider: GitProvider):
        """
        初始化多仓库分析器

        Args:
            provider: Git 数据提供者
        """
        self.provider = provider

    def get_all_repos(self) -> List[str]:
        """获取所有仓库 ID"""
        repos = self.provider.list_repositories()
        return [r.id for r in repos]

    def get_analyzer(self, repo_id: str) -> GitAnalyzer:
        """获取单个仓库的分析器"""
        return GitAnalyzer(self.provider, repo_id)

    def analyze_all(
        self,
        since: str = "1 day ago",
        until: Optional[str] = None
    ) -> Dict[str, List[CommitInfo]]:
        """
        分析所有仓库

        Args:
            since: 开始时间
            until: 结束时间

        Returns:
            {repo_id: [commits]}
        """
        results = {}
        for repo_id in self.get_all_repos():
            analyzer = self.get_analyzer(repo_id)
            results[repo_id] = analyzer.get_commits(since, until)
        return results
