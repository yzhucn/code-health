"""
GitHub API Provider
通过 GitHub REST API 获取仓库数据
"""

import json
from typing import List, Dict, Optional
from datetime import datetime
import urllib.request
import urllib.error
import base64

from .base import GitProvider, CommitInfo, FileChange, RepoInfo


class GitHubProvider(GitProvider):
    """
    GitHub API Provider

    使用 GitHub REST API v3 获取仓库和提交数据
    优点：无需克隆仓库，速度快
    缺点：有 API 速率限制
    """

    API_BASE = "https://api.github.com"

    def __init__(
        self,
        token: str,
        org: str = None,
        user: str = None,
        repos: List[str] = None,
    ):
        """
        初始化 GitHub Provider

        Args:
            token: GitHub Personal Access Token
            org: 组织名称 (用于列出组织仓库)
            user: 用户名 (用于列出用户仓库)
            repos: 指定仓库列表 (格式: owner/repo)
        """
        self.token = token
        self.org = org
        self.user = user
        self.repos = repos or []
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Code-Health-Monitor",
        }

    def _api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        发起 GitHub API 请求

        Args:
            endpoint: API 端点 (如 /repos/owner/repo/commits)
            params: 查询参数

        Returns:
            JSON 响应数据
        """
        url = f"{self.API_BASE}{endpoint}"
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items() if v)
            url = f"{url}?{query_string}"

        request = urllib.request.Request(url, headers=self._headers)

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"GitHub API 错误: {e.code} - {e.reason}")
            return None
        except Exception as e:
            print(f"GitHub API 请求失败: {e}")
            return None

    def _api_request_list(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        发起 GitHub API 请求，处理分页

        Args:
            endpoint: API 端点
            params: 查询参数

        Returns:
            所有分页数据的合并列表
        """
        results = []
        params = params or {}
        params['per_page'] = 100
        page = 1

        while True:
            params['page'] = page
            data = self._api_request(endpoint, params)

            if not data or not isinstance(data, list):
                break

            results.extend(data)

            if len(data) < 100:
                break

            page += 1
            if page > 10:  # 最多获取1000条记录
                break

        return results

    def list_repositories(self) -> List[RepoInfo]:
        """列出所有仓库"""
        repos = []

        # 如果指定了仓库列表，直接获取这些仓库的信息
        if self.repos:
            for repo_name in self.repos:
                data = self._api_request(f"/repos/{repo_name}")
                if data:
                    repos.append(self._parse_repo(data))
            return repos

        # 获取组织仓库
        if self.org:
            data = self._api_request_list(f"/orgs/{self.org}/repos")
            for item in data:
                repos.append(self._parse_repo(item))

        # 获取用户仓库
        if self.user:
            data = self._api_request_list(f"/users/{self.user}/repos")
            for item in data:
                repos.append(self._parse_repo(item))

        return repos

    def _parse_repo(self, data: Dict) -> RepoInfo:
        """解析仓库数据"""
        return RepoInfo(
            id=data.get('full_name', ''),
            name=data.get('name', ''),
            url=data.get('clone_url', ''),
            default_branch=data.get('default_branch', 'main'),
            type=self._detect_repo_type(data),
            archived=data.get('archived', False),
        )

    def _detect_repo_type(self, data: Dict) -> str:
        """根据仓库语言检测类型"""
        language = data.get('language', '').lower()
        type_map = {
            'java': 'java',
            'python': 'python',
            'javascript': 'vue',
            'typescript': 'vue',
            'vue': 'vue',
            'dart': 'flutter',
            'go': 'go',
            'rust': 'rust',
        }
        return type_map.get(language, 'unknown')

    def get_commits(
        self,
        repo_id: str,
        since: str,
        until: Optional[str] = None,
        branch: str = "all"
    ) -> List[CommitInfo]:
        """获取提交记录"""
        params = {
            'since': self._format_datetime(since),
        }
        if until:
            params['until'] = self._format_datetime(until)
        if branch != "all":
            params['sha'] = branch

        commits_data = self._api_request_list(f"/repos/{repo_id}/commits", params)
        commits = []

        for item in commits_data:
            # 获取详细的提交信息（包含文件变更）
            detail = self._api_request(f"/repos/{repo_id}/commits/{item['sha']}")
            if detail:
                commits.append(self._parse_commit(detail))

        return commits

    def _format_datetime(self, date_str: str) -> str:
        """将日期字符串转换为 ISO 8601 格式"""
        if 'T' in date_str:
            return date_str
        return f"{date_str}T00:00:00Z"

    def _parse_commit(self, data: Dict) -> CommitInfo:
        """解析提交数据"""
        commit_info = data.get('commit', {})
        author_info = commit_info.get('author', {})
        files = data.get('files', [])

        return CommitInfo(
            hash=data.get('sha', ''),
            author=author_info.get('name', 'Unknown'),
            email=author_info.get('email', ''),
            date=self._parse_github_date(author_info.get('date', '')),
            message=commit_info.get('message', '').split('\n')[0],
            files=[
                FileChange(
                    path=f.get('filename', ''),
                    added=f.get('additions', 0),
                    deleted=f.get('deletions', 0),
                )
                for f in files
            ]
        )

    def _parse_github_date(self, date_str: str) -> str:
        """将 GitHub 日期格式转换为标准格式"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return date_str

    def get_file_content(
        self,
        repo_id: str,
        filepath: str,
        ref: str = "HEAD"
    ) -> Optional[str]:
        """获取文件内容"""
        params = {'ref': ref} if ref != "HEAD" else {}
        data = self._api_request(f"/repos/{repo_id}/contents/{filepath}", params)

        if not data:
            return None

        if data.get('type') != 'file':
            return None

        content = data.get('content', '')
        encoding = data.get('encoding', 'base64')

        if encoding == 'base64':
            try:
                return base64.b64decode(content).decode('utf-8')
            except Exception:
                return None

        return content
