"""
Git Provider 抽象基类
定义统一的 Git 数据访问接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class FileChange:
    """文件变更信息"""
    path: str
    added: int = 0
    deleted: int = 0

    @property
    def net(self) -> int:
        return self.added - self.deleted


@dataclass
class CommitInfo:
    """统一的提交信息结构"""
    hash: str
    author: str
    email: str
    date: str  # ISO format: YYYY-MM-DD HH:MM:SS
    message: str
    files: List[FileChange] = field(default_factory=list)

    @property
    def lines_added(self) -> int:
        return sum(f.added for f in self.files)

    @property
    def lines_deleted(self) -> int:
        return sum(f.deleted for f in self.files)

    @property
    def lines_net(self) -> int:
        return self.lines_added - self.lines_deleted

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def datetime(self) -> datetime:
        """解析日期字符串为 datetime 对象"""
        # 支持多种格式
        for fmt in [
            '%Y-%m-%d %H:%M:%S %z',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
        ]:
            try:
                return datetime.strptime(self.date, fmt)
            except ValueError:
                continue
        # 回退：尝试解析前19个字符
        return datetime.strptime(self.date[:19], '%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> Dict:
        """转换为字典格式（兼容旧接口）"""
        return {
            'hash': self.hash,
            'author': self.author,
            'email': self.email,
            'date': self.date,
            'message': self.message,
            'files': [{'path': f.path, 'added': f.added, 'deleted': f.deleted} for f in self.files],
            'lines_added': self.lines_added,
            'lines_deleted': self.lines_deleted,
        }


@dataclass
class RepoInfo:
    """仓库信息"""
    id: str           # 唯一标识符（如 owner/repo 或 URL）
    name: str         # 仓库名称
    url: str          # Git URL
    default_branch: str = 'main'
    type: str = 'unknown'  # java, python, vue, flutter, etc.
    archived: bool = False

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'default_branch': self.default_branch,
            'type': self.type,
            'archived': self.archived,
        }


class GitProvider(ABC):
    """
    Git 数据提供者抽象基类

    所有 Git 平台（GitHub、GitLab、Codeup、通用Git）都需要实现这个接口
    """

    @abstractmethod
    def get_commits(
        self,
        repo_id: str,
        since: str,
        until: Optional[str] = None,
        branch: str = "all"
    ) -> List[CommitInfo]:
        """
        获取提交记录

        Args:
            repo_id: 仓库标识符
            since: 开始日期 (ISO格式 YYYY-MM-DD 或相对时间如 "7 days ago")
            until: 结束日期 (可选)
            branch: 分支名称，"all" 表示所有分支

        Returns:
            提交信息列表
        """
        pass

    @abstractmethod
    def list_repositories(self) -> List[RepoInfo]:
        """
        列出所有可访问的仓库

        Returns:
            仓库信息列表
        """
        pass

    @abstractmethod
    def get_file_content(
        self,
        repo_id: str,
        filepath: str,
        ref: str = "HEAD"
    ) -> Optional[str]:
        """
        获取文件内容

        Args:
            repo_id: 仓库标识符
            filepath: 文件路径
            ref: Git 引用（分支名、tag、commit hash）

        Returns:
            文件内容，不存在返回 None
        """
        pass

    def get_file_line_count(
        self,
        repo_id: str,
        filepath: str,
        ref: str = "HEAD"
    ) -> int:
        """
        获取文件行数

        Args:
            repo_id: 仓库标识符
            filepath: 文件路径
            ref: Git 引用

        Returns:
            文件行数，不存在返回 0
        """
        content = self.get_file_content(repo_id, filepath, ref)
        if content is None:
            return 0
        return len(content.splitlines())

    def get_file_history(
        self,
        repo_id: str,
        filepath: str,
        since: str,
        until: Optional[str] = None
    ) -> List[CommitInfo]:
        """
        获取文件的修改历史

        默认实现：从所有提交中过滤出修改了该文件的提交
        子类可以覆盖此方法以提供更高效的实现

        Args:
            repo_id: 仓库标识符
            filepath: 文件路径
            since: 开始日期
            until: 结束日期

        Returns:
            修改了该文件的提交列表
        """
        commits = self.get_commits(repo_id, since, until)
        return [
            c for c in commits
            if any(f.path == filepath for f in c.files)
        ]

    def cleanup(self) -> None:
        """
        清理资源（如临时克隆的仓库）

        子类可以覆盖此方法以实现清理逻辑
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False
