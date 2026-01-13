"""
通用 Git Provider
使用浅 clone 获取 Git 数据，兼容所有 Git 平台
"""

import os
import re
import shutil
import subprocess
import tempfile
from typing import List, Dict, Optional
from urllib.parse import urlparse, urlunparse

from .base import GitProvider, CommitInfo, RepoInfo, FileChange


class GenericGitProvider(GitProvider):
    """
    通用 Git Provider

    使用浅 clone 方式获取 Git 数据，支持所有标准 Git 仓库。
    适用于：
    - GitHub
    - GitLab（包括自托管）
    - Gitee
    - 云效 Codeup
    - 任何标准 Git 服务器

    特点：
    - 浅 clone 减少下载量
    - 分析完成后自动清理
    - 支持 Token 认证
    """

    def __init__(
        self,
        repositories: List[Dict],
        token: Optional[str] = None,
        temp_dir: Optional[str] = None,
        clone_depth: int = 1000,
        auto_cleanup: bool = True
    ):
        """
        初始化 Generic Git Provider

        Args:
            repositories: 仓库列表，每个仓库需包含:
                - url: Git 仓库 URL
                - name: 仓库名称
                - type: 仓库类型 (java/python/vue/flutter)
                - main_branch: 主分支名称
            token: Git 访问 Token（可选）
            temp_dir: 临时目录路径（默认系统临时目录）
            clone_depth: 克隆深度（默认1000个提交）
            auto_cleanup: 是否自动清理克隆的仓库
        """
        self.repositories = {r['name']: r for r in repositories}
        self.token = token
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), 'code-health-repos')
        self.clone_depth = clone_depth
        self.auto_cleanup = auto_cleanup
        self._cloned_repos: Dict[str, str] = {}  # name -> path

    def _get_auth_url(self, url: str) -> str:
        """
        为 URL 添加认证信息

        Args:
            url: 原始 Git URL

        Returns:
            带认证的 URL
        """
        if not self.token:
            return url

        if url.startswith('https://'):
            parsed = urlparse(url)
            # 格式: https://oauth2:token@host/path
            auth_netloc = f"oauth2:{self.token}@{parsed.netloc}"
            return urlunparse((
                parsed.scheme,
                auth_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        elif url.startswith('git@'):
            # SSH URL 不支持 Token 认证
            return url
        else:
            return url

    def _clone_repo(self, repo_name: str) -> str:
        """
        克隆仓库到临时目录

        Args:
            repo_name: 仓库名称

        Returns:
            克隆后的本地路径
        """
        if repo_name in self._cloned_repos:
            return self._cloned_repos[repo_name]

        repo_info = self.repositories.get(repo_name)
        if not repo_info:
            raise ValueError(f"未知的仓库: {repo_name}")

        repo_url = repo_info.get('url', '')
        if not repo_url:
            raise ValueError(f"仓库 {repo_name} 没有配置 URL")

        repo_path = os.path.join(self.temp_dir, repo_name)

        # 如果已存在，先删除
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)

        # 创建临时目录
        os.makedirs(self.temp_dir, exist_ok=True)

        # 构建带认证的 URL
        auth_url = self._get_auth_url(repo_url)

        # 浅克隆
        try:
            subprocess.run(
                [
                    'git', 'clone',
                    '--depth', str(self.clone_depth),
                    '--no-single-branch',  # 获取所有分支的浅历史
                    auth_url, repo_path
                ],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"克隆仓库 {repo_name} 失败: {e.stderr}")

        # 尝试获取更多历史（可能失败，忽略错误）
        try:
            subprocess.run(
                ['git', '-C', repo_path, 'fetch', '--unshallow'],
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            pass  # 忽略错误（可能已经是完整历史）

        self._cloned_repos[repo_name] = repo_path
        return repo_path

    def _run_git_command(self, repo_path: str, args: List[str]) -> str:
        """
        在仓库中执行 Git 命令

        Args:
            repo_path: 仓库路径
            args: Git 命令参数

        Returns:
            命令输出
        """
        cmd = ['git', '-C', repo_path] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git 命令失败: {' '.join(cmd)}\n{result.stderr}")
        return result.stdout

    def _parse_git_log(self, output: str) -> List[CommitInfo]:
        """
        解析 git log --numstat 输出

        格式:
        hash|author|email|date|message
        added<tab>deleted<tab>filepath
        added<tab>deleted<tab>filepath
        <空行>
        hash|author|email|date|message
        ...
        """
        commits = []
        current_commit = None
        current_files = []

        for line in output.split('\n'):
            line = line.rstrip()

            if not line:
                # 空行表示一个提交结束
                if current_commit:
                    commits.append(CommitInfo(
                        hash=current_commit['hash'],
                        author=current_commit['author'],
                        email=current_commit['email'],
                        date=current_commit['date'],
                        message=current_commit['message'],
                        files=current_files
                    ))
                current_commit = None
                current_files = []
                continue

            if '|' in line and current_commit is None:
                # 提交头信息行
                parts = line.split('|', 4)
                if len(parts) >= 5:
                    current_commit = {
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4],
                    }
                    current_files = []
            elif '\t' in line and current_commit:
                # 文件变更行 (added<tab>deleted<tab>filepath)
                parts = line.split('\t', 2)
                if len(parts) >= 3:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        deleted = int(parts[1]) if parts[1] != '-' else 0
                        filepath = parts[2]
                        current_files.append(FileChange(
                            path=filepath,
                            added=added,
                            deleted=deleted
                        ))
                    except ValueError:
                        pass  # 忽略解析错误

        # 处理最后一个提交
        if current_commit:
            commits.append(CommitInfo(
                hash=current_commit['hash'],
                author=current_commit['author'],
                email=current_commit['email'],
                date=current_commit['date'],
                message=current_commit['message'],
                files=current_files
            ))

        return commits

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
            repo_id: 仓库名称
            since: 开始日期
            until: 结束日期（可选）
            branch: 分支名称，"all" 表示所有分支

        Returns:
            提交信息列表
        """
        repo_path = self._clone_repo(repo_id)

        # 构建 git log 命令
        args = [
            'log',
            f'--since={since}',
            '--pretty=format:%H|%an|%ae|%ad|%s',
            '--date=iso',
            '--numstat',
        ]

        if until:
            args.append(f'--until={until}')

        if branch == 'all':
            args.append('--all')
        else:
            args.append(branch)

        output = self._run_git_command(repo_path, args)
        return self._parse_git_log(output)

    def list_repositories(self) -> List[RepoInfo]:
        """
        返回配置的仓库列表

        Returns:
            仓库信息列表
        """
        return [
            RepoInfo(
                id=name,
                name=name,
                url=info.get('url', ''),
                default_branch=info.get('main_branch', 'main'),
                type=info.get('type', 'unknown'),
            )
            for name, info in self.repositories.items()
        ]

    def get_file_content(
        self,
        repo_id: str,
        filepath: str,
        ref: str = "HEAD"
    ) -> Optional[str]:
        """
        获取文件内容

        Args:
            repo_id: 仓库名称
            filepath: 文件路径
            ref: Git 引用

        Returns:
            文件内容，不存在返回 None
        """
        repo_path = self._clone_repo(repo_id)

        try:
            output = self._run_git_command(repo_path, ['show', f'{ref}:{filepath}'])
            return output
        except RuntimeError:
            return None

    def get_modified_files(
        self,
        repo_id: str,
        since: str,
        until: Optional[str] = None
    ) -> List[str]:
        """
        获取时间范围内修改过的所有文件

        Args:
            repo_id: 仓库名称
            since: 开始日期
            until: 结束日期

        Returns:
            文件路径列表
        """
        repo_path = self._clone_repo(repo_id)

        args = [
            'log',
            f'--since={since}',
            '--name-only',
            '--pretty=format:',
            '--all',
        ]

        if until:
            args.insert(2, f'--until={until}')

        output = self._run_git_command(repo_path, args)

        # 去重并过滤空行
        files = set()
        for line in output.split('\n'):
            line = line.strip()
            if line:
                files.add(line)

        return list(files)

    def cleanup(self) -> None:
        """清理所有克隆的仓库"""
        if self.auto_cleanup and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self._cloned_repos.clear()
