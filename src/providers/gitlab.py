"""
GitLab API Provider
通过 GitLab REST API 获取仓库数据
"""

import json
from typing import List, Dict, Optional
from datetime import datetime
import urllib.request
import urllib.error
import urllib.parse
import base64

from .base import GitProvider, CommitInfo, FileChange, RepoInfo


class GitLabProvider(GitProvider):
    """
    GitLab API Provider

    使用 GitLab REST API v4 获取仓库和提交数据
    支持自托管 GitLab 和 GitLab.com
    """

    def __init__(
        self,
        token: str,
        base_url: str = "https://gitlab.com",
        group: str = None,
        user: str = None,
        projects: List[str] = None,
    ):
        """
        初始化 GitLab Provider

        Args:
            token: GitLab Personal Access Token
            base_url: GitLab 实例 URL
            group: 群组名称/ID
            user: 用户名
            projects: 指定项目列表 (格式: group/project 或 project ID)
        """
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v4"
        self.group = group
        self.user = user
        self.projects = projects or []
        self._headers = {
            "PRIVATE-TOKEN": token,
            "Content-Type": "application/json",
        }

    def _api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        发起 GitLab API 请求

        Args:
            endpoint: API 端点
            params: 查询参数

        Returns:
            JSON 响应数据
        """
        url = f"{self.api_base}{endpoint}"
        if params:
            query_string = "&".join(
                f"{k}={urllib.parse.quote(str(v))}"
                for k, v in params.items() if v is not None
            )
            url = f"{url}?{query_string}"

        request = urllib.request.Request(url, headers=self._headers)

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"GitLab API 错误: {e.code} - {e.reason}")
            return None
        except Exception as e:
            print(f"GitLab API 请求失败: {e}")
            return None

    def _api_request_list(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        发起 GitLab API 请求，处理分页

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
            if page > 10:
                break

        return results

    def list_repositories(self) -> List[RepoInfo]:
        """列出所有仓库"""
        repos = []

        # 如果指定了项目列表
        if self.projects:
            for project in self.projects:
                encoded = urllib.parse.quote(project, safe='')
                data = self._api_request(f"/projects/{encoded}")
                if data:
                    repos.append(self._parse_repo(data))
            return repos

        # 获取群组项目
        if self.group:
            encoded_group = urllib.parse.quote(self.group, safe='')
            data = self._api_request_list(
                f"/groups/{encoded_group}/projects",
                {'include_subgroups': 'true'}
            )
            for item in data:
                repos.append(self._parse_repo(item))

        # 获取用户项目
        if self.user:
            data = self._api_request_list(f"/users/{self.user}/projects")
            for item in data:
                repos.append(self._parse_repo(item))

        # 如果没有指定，获取当前用户可访问的所有项目
        if not self.group and not self.user and not self.projects:
            data = self._api_request_list("/projects", {'membership': 'true'})
            for item in data:
                repos.append(self._parse_repo(item))

        return repos

    def _parse_repo(self, data: Dict) -> RepoInfo:
        """解析仓库数据"""
        return RepoInfo(
            id=str(data.get('id', '')),
            name=data.get('name', ''),
            url=data.get('http_url_to_repo', '') or data.get('ssh_url_to_repo', ''),
            default_branch=data.get('default_branch', 'main'),
            type=self._detect_repo_type(data),
            archived=data.get('archived', False),
        )

    def _detect_repo_type(self, data: Dict) -> str:
        """根据仓库信息检测类型"""
        # GitLab 没有单一的 language 字段，尝试从 name 推断
        name = data.get('name', '').lower()
        path = data.get('path', '').lower()

        if any(x in name or x in path for x in ['java', 'spring', 'backend']):
            return 'java'
        if any(x in name or x in path for x in ['python', 'django', 'flask']):
            return 'python'
        if any(x in name or x in path for x in ['vue', 'react', 'frontend', 'web']):
            return 'vue'
        if any(x in name or x in path for x in ['flutter', 'mobile', 'app']):
            return 'flutter'

        return 'unknown'

    def get_commits(
        self,
        repo_id: str,
        since: str,
        until: Optional[str] = None,
        branch: str = "all"
    ) -> List[CommitInfo]:
        """获取提交记录"""
        encoded_id = urllib.parse.quote(repo_id, safe='')

        params = {
            'since': self._format_datetime(since),
            'with_stats': 'true',
        }
        if until:
            params['until'] = self._format_datetime(until)
        if branch != "all":
            params['ref_name'] = branch
        else:
            params['all'] = 'true'

        commits_data = self._api_request_list(f"/projects/{encoded_id}/repository/commits", params)
        commits = []

        for item in commits_data:
            # 获取详细的提交信息（包含文件变更）
            detail = self._api_request(
                f"/projects/{encoded_id}/repository/commits/{item['id']}/diff"
            )

            files = []
            if detail and isinstance(detail, list):
                for diff in detail:
                    # GitLab diff 不直接提供行数，需要从 stats 获取
                    files.append(FileChange(
                        path=diff.get('new_path', diff.get('old_path', '')),
                        added=0,  # 需要另外获取
                        deleted=0,
                    ))

            # 获取 stats
            stats = item.get('stats', {})
            total_added = stats.get('additions', 0)
            total_deleted = stats.get('deletions', 0)

            # 均分到文件
            if files:
                per_file_added = total_added // len(files)
                per_file_deleted = total_deleted // len(files)
                for f in files:
                    f.added = per_file_added
                    f.deleted = per_file_deleted
            else:
                # 如果没有文件信息，创建一个虚拟文件
                files = [FileChange(path='(unknown)', added=total_added, deleted=total_deleted)]

            commits.append(CommitInfo(
                hash=item.get('id', ''),
                author=item.get('author_name', 'Unknown'),
                email=item.get('author_email', ''),
                date=self._parse_gitlab_date(item.get('authored_date', '')),
                message=item.get('title', ''),
                files=files,
            ))

        return commits

    def _format_datetime(self, date_str: str) -> str:
        """将日期字符串转换为 ISO 8601 格式"""
        if 'T' in date_str:
            return date_str
        return f"{date_str}T00:00:00Z"

    def _parse_gitlab_date(self, date_str: str) -> str:
        """将 GitLab 日期格式转换为标准格式"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            # GitLab 日期格式: 2025-01-10T08:30:00.000+08:00
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return date_str[:19].replace('T', ' ')

    def get_file_content(
        self,
        repo_id: str,
        filepath: str,
        ref: str = "HEAD"
    ) -> Optional[str]:
        """获取文件内容"""
        encoded_id = urllib.parse.quote(repo_id, safe='')
        encoded_path = urllib.parse.quote(filepath, safe='')

        params = {'ref': ref} if ref != "HEAD" else {}
        data = self._api_request(
            f"/projects/{encoded_id}/repository/files/{encoded_path}",
            params
        )

        if not data:
            return None

        content = data.get('content', '')
        encoding = data.get('encoding', 'base64')

        if encoding == 'base64':
            try:
                return base64.b64decode(content).decode('utf-8')
            except Exception:
                return None

        return content
