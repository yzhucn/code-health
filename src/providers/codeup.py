"""
阿里云 Codeup API Provider
通过云效 Codeup API 获取仓库数据

使用 x-yunxiao-token 认证方式
API 文档: https://help.aliyun.com/document_detail/460465.html
"""

import json
import os
from typing import List, Dict, Optional, Set
from datetime import datetime
import urllib.request
import urllib.error

from .base import GitProvider, CommitInfo, FileChange, RepoInfo


class CodeupProvider(GitProvider):
    """
    阿里云 Codeup API Provider

    使用云效 Codeup API 获取仓库和提交数据
    认证方式: x-yunxiao-token (个人访问令牌)
    """

    API_DOMAIN = "openapi-rdc.aliyuncs.com"

    def __init__(
        self,
        token: str = None,
        organization_id: str = None,
        project: str = None,
        repositories: List[Dict] = None,
        debug: bool = False,
        # 兼容旧参数 (deprecated)
        access_key_id: str = None,
        access_key_secret: str = None,
    ):
        """
        初始化 Codeup Provider

        Args:
            token: 云效个人访问令牌 (优先使用 CODEUP_TOKEN 环境变量)
            organization_id: 云效企业 ID (优先使用 CODEUP_ORG_ID 环境变量)
            project: 项目/命名空间名称，用于自动过滤仓库 (如 "my-project")
            repositories: 指定仓库列表 (可选，如果指定则忽略 project 参数)
            debug: 是否开启调试模式 (显示 API 响应详情)
        """
        # 从环境变量或参数获取认证信息
        self.token = token or os.environ.get('CODEUP_TOKEN', '')
        self.organization_id = organization_id or os.environ.get('CODEUP_ORG_ID', '')
        self.project = project or os.environ.get('CODEUP_PROJECT', '')
        self.repositories_config = repositories or []
        self.debug = debug or os.environ.get('CODEUP_DEBUG', '').lower() in ('1', 'true', 'yes')
        self._debug_shown_commit = False  # 只显示一次提交详情

        if not self.token:
            print("警告: 未配置云效访问令牌 (CODEUP_TOKEN)")
        if not self.organization_id:
            print("警告: 未配置云效企业 ID (CODEUP_ORG_ID)")

    def _api_request(self, path: str, params: Dict = None) -> Optional[Dict]:
        """
        发起 Codeup API 请求

        Args:
            path: API 路径 (不含 /oapi/v1/codeup 前缀)
            params: URL 查询参数

        Returns:
            JSON 响应数据
        """
        # 构建 URL
        base_url = f"https://{self.API_DOMAIN}/oapi/v1/codeup"
        url = f"{base_url}{path}"

        # 添加查询参数
        if params:
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query_string}"

        # 构建请求
        request = urllib.request.Request(url, headers={
            'Content-Type': 'application/json',
            'x-yunxiao-token': self.token,
        })

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            print(f"Codeup API HTTP 错误: {e.code} - {e.reason}")
            if error_body:
                print(f"  响应: {error_body[:200]}")
            return None
        except Exception as e:
            print(f"Codeup API 请求失败: {e}")
            return None

    def list_repositories(self) -> List[RepoInfo]:
        """列出所有仓库"""
        repos = []

        # 获取组织下所有仓库
        all_repos = self._fetch_all_repositories()

        # 优先级: repositories_config > project > 全部
        if self.repositories_config:
            # 按指定仓库列表过滤
            return self._filter_by_config(all_repos)

        if self.project:
            # 按项目/命名空间过滤
            return self._filter_by_project(all_repos, self.project)

        # 没有配置时返回所有非归档仓库
        for repo_data in all_repos:
            if not repo_data.get('archived', False) and not repo_data.get('demoProject', False):
                repos.append(self._parse_repo(repo_data))

        return repos

    def _filter_by_project(self, all_repos: List[Dict], project: str) -> List[RepoInfo]:
        """
        按项目/命名空间过滤仓库

        Args:
            all_repos: 所有仓库数据
            project: 项目名称 (如 "my-project")

        Returns:
            属于该项目的仓库列表
        """
        repos = []
        project_lower = project.lower()

        for repo_data in all_repos:
            # 跳过归档和 demo 仓库
            if repo_data.get('archived', False) or repo_data.get('demoProject', False):
                continue

            # 检查路径是否包含项目名
            path_with_ns = repo_data.get('pathWithNamespace', '').lower()

            # 匹配模式: {org_id}/{project}/ 或 {org_id}/{project}/external/
            if f'/{project_lower}/' in path_with_ns:
                repos.append(self._parse_repo(repo_data))

        return repos

    def _filter_by_config(self, all_repos: List[Dict]) -> List[RepoInfo]:
        """按配置列表过滤仓库"""
        repos = []

        # 构建名称/URL 到配置的映射
        config_by_name = {}
        config_by_url = {}
        config_by_id = {}

        for cfg in self.repositories_config:
            if cfg.get('name'):
                config_by_name[cfg['name']] = cfg
            if cfg.get('url'):
                # 标准化 URL (去掉 .git 后缀)
                url = cfg['url'].rstrip('.git')
                config_by_url[url] = cfg
            if cfg.get('id'):
                config_by_id[str(cfg['id'])] = cfg

        # 过滤并匹配仓库
        for repo_data in all_repos:
            repo_id = str(repo_data.get('id', ''))
            repo_name = repo_data.get('name', '')
            repo_path = repo_data.get('path', '')
            repo_url = (repo_data.get('webUrl', '') or '').rstrip('.git')

            # 按 ID、名称、路径、URL 匹配
            config = None
            if repo_id in config_by_id:
                config = config_by_id[repo_id]
            elif repo_name in config_by_name:
                config = config_by_name[repo_name]
            elif repo_path in config_by_name:
                # 也尝试用 path 匹配 (某些仓库 name 和 path 不同)
                config = config_by_name[repo_path]
            elif repo_url in config_by_url:
                config = config_by_url[repo_url]

            if config:
                repos.append(self._parse_repo(repo_data, config))

        return repos

    def _fetch_all_repositories(self) -> List[Dict]:
        """获取组织下所有仓库的原始数据"""
        all_repos = []
        page = 1

        while True:
            data = self._api_request(
                f"/organizations/{self.organization_id}/repositories",
                params={'page': page, 'perPage': 100}
            )

            if not data or not isinstance(data, list):
                break

            if not data:
                break

            all_repos.extend(data)

            if len(data) < 100:
                break

            page += 1
            if page > 10:
                break

        return all_repos

    def _parse_repo(self, data: Dict, config: Dict = None) -> RepoInfo:
        """解析仓库数据"""
        config = config or {}

        # 获取 Git URL
        web_url = data.get('webUrl', '') or data.get('httpUrlToRepo', '')
        git_url = web_url + '.git' if web_url and not web_url.endswith('.git') else web_url

        # 自动推断仓库类型
        repo_type = config.get('type') or self._infer_repo_type(data)

        return RepoInfo(
            id=str(data.get('id', data.get('projectId', ''))),
            name=config.get('name') or data.get('name', data.get('path', '')),
            url=git_url,
            default_branch=data.get('defaultBranch', 'master'),
            type=repo_type,
            archived=data.get('archived', False),
        )

    def _infer_repo_type(self, data: Dict) -> str:
        """根据仓库名称推断类型"""
        name = (data.get('name', '') or data.get('path', '')).lower()

        # 按名称关键词推断
        if 'android' in name or 'app' in name:
            return 'android'
        if 'web' in name or 'frontend' in name or 'h5' in name:
            return 'vue'
        if 'service' in name or 'backend' in name or 'gateway' in name:
            return 'java'
        if 'agent' in name or 'pipeline' in name or 'etl' in name:
            return 'python'
        if 'infra' in name:
            return 'infra'

        return 'unknown'

    def list_branches(self, repo_id: str) -> List[str]:
        """
        列出仓库的所有分支

        Args:
            repo_id: 仓库 ID

        Returns:
            分支名称列表
        """
        branches = []
        page = 1

        while True:
            data = self._api_request(
                f"/organizations/{self.organization_id}/repositories/{repo_id}/branches",
                params={'page': page, 'perPage': 100}
            )

            if not data or not isinstance(data, list):
                break

            for item in data:
                branch_name = item.get('name', '')
                if branch_name:
                    branches.append(branch_name)

            if len(data) < 100:
                break

            page += 1
            if page > 5:  # 限制最多 500 个分支
                break

        return branches

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
            repo_id: 仓库 ID
            since: 开始日期 (YYYY-MM-DD)
            until: 结束日期 (YYYY-MM-DD)
            branch: 分支名 ("all" 表示所有分支)

        Returns:
            提交列表 (已按 hash 去重)
        """
        if branch == "all":
            # 获取所有分支的提交
            return self._get_commits_all_branches(repo_id, since, until)
        else:
            # 获取指定分支的提交
            return self._get_commits_single_branch(repo_id, since, until, branch)

    def _get_commits_all_branches(
        self,
        repo_id: str,
        since: str,
        until: Optional[str] = None
    ) -> List[CommitInfo]:
        """获取所有分支的提交并去重"""
        branches = self.list_branches(repo_id)

        if not branches:
            # 如果获取分支列表失败，尝试默认分支
            return self._get_commits_single_branch(repo_id, since, until, None)

        all_commits = []
        seen_hashes: Set[str] = set()

        for branch_name in branches:
            commits = self._get_commits_single_branch(repo_id, since, until, branch_name)

            for commit in commits:
                if commit.hash not in seen_hashes:
                    seen_hashes.add(commit.hash)
                    all_commits.append(commit)

        # 按日期降序排序
        all_commits.sort(key=lambda c: c.date, reverse=True)
        return all_commits

    def _get_commits_single_branch(
        self,
        repo_id: str,
        since: str,
        until: Optional[str] = None,
        branch: Optional[str] = None
    ) -> List[CommitInfo]:
        """获取单个分支的提交"""
        all_commits = []
        page = 1

        # Codeup API 必须指定分支，如果没有指定则使用 master
        ref_name = branch or 'master'

        while True:
            params = {
                'page': page,
                'perPage': 100,
                'refName': ref_name,
            }

            data = self._api_request(
                f"/organizations/{self.organization_id}/repositories/{repo_id}/commits",
                params=params
            )

            if not data:
                break

            commits_list = data if isinstance(data, list) else []

            if not commits_list:
                break

            for item in commits_list:
                commit = self._parse_commit(item, repo_id)
                if commit:
                    # 检查时间范围
                    commit_date = commit.date[:10]
                    if since and commit_date < since[:10]:
                        # 已经超出时间范围，停止获取
                        return all_commits
                    if until and commit_date > until[:10]:
                        continue
                    all_commits.append(commit)

            if len(commits_list) < 100:
                break

            page += 1
            if page > 10:
                break

        return all_commits

    def _parse_commit(self, data: Dict, repo_id: str) -> Optional[CommitInfo]:
        """解析提交数据"""
        try:
            commit_id = data.get('id', data.get('sha', ''))

            # 获取提交详情（包含文件变更）
            detail = self._api_request(
                f"/organizations/{self.organization_id}/repositories/{repo_id}/commits/{commit_id}"
            )

            # 调试模式：显示第一个提交的 API 响应结构
            if self.debug and not self._debug_shown_commit and detail:
                self._debug_shown_commit = True
                print(f"\n[DEBUG] 提交详情 API 响应 (commit: {commit_id[:8]}...):")
                print(f"  Keys: {list(detail.keys())}")
                if 'diffs' in detail:
                    print(f"  diffs: {type(detail['diffs'])}, count: {len(detail.get('diffs', []) or [])}")
                    if detail.get('diffs'):
                        print(f"  diffs[0] keys: {list(detail['diffs'][0].keys())}")
                else:
                    print("  diffs: 字段不存在")
                if 'stats' in detail:
                    print(f"  stats: {detail.get('stats')}")
                if 'parentShas' in detail:
                    print(f"  parentShas: {detail.get('parentShas')}")
                print()

            files = []
            if detail:
                # 方法1: 尝试从 diffs 字段获取文件变更
                diffs = detail.get('diffs', []) or []
                for diff in diffs:
                    path = diff.get('newPath', diff.get('oldPath', ''))
                    if path:
                        files.append(FileChange(
                            path=path,
                            added=diff.get('additions', 0),
                            deleted=diff.get('deletions', 0),
                        ))

                # 方法2: 如果 diffs 为空，尝试使用 ListRepositoryCommitDiff API
                if not files:
                    diff_data = self._api_request(
                        f"/organizations/{self.organization_id}/repositories/{repo_id}/commits/{commit_id}/diff"
                    )
                    if diff_data:
                        diff_list = diff_data if isinstance(diff_data, list) else diff_data.get('result', []) or []
                        for diff in diff_list:
                            path = diff.get('newPath', diff.get('oldPath', diff.get('new_path', diff.get('old_path', ''))))
                            if path:
                                files.append(FileChange(
                                    path=path,
                                    added=diff.get('additions', diff.get('addedLines', 0)),
                                    deleted=diff.get('deletions', diff.get('deletedLines', 0)),
                                ))

                # 方法3: 如果还是没有，尝试从 parentIds 获取 compare diff
                if not files and detail.get('parentIds'):
                    parent_sha = detail.get('parentIds', [''])[0] if detail.get('parentIds') else ''
                    if parent_sha:
                        compare_data = self._api_request(
                            f"/organizations/{self.organization_id}/repositories/{repo_id}/compare",
                            params={'from': parent_sha, 'to': commit_id}
                        )
                        if compare_data:
                            diff_list = compare_data.get('diffs', []) or compare_data.get('result', {}).get('diffs', []) or []
                            for diff in diff_list:
                                path = diff.get('newPath', diff.get('oldPath', ''))
                                if path:
                                    files.append(FileChange(
                                        path=path,
                                        added=diff.get('additions', 0),
                                        deleted=diff.get('deletions', 0),
                                    ))

                # 方法4: 如果仍然没有文件信息，使用 stats
                if not files:
                    stats = detail.get('stats', {}) or {}
                    total_added = stats.get('additions', 0)
                    total_deleted = stats.get('deletions', 0)
                    if total_added or total_deleted:
                        files = [FileChange(path='(unknown)', added=total_added, deleted=total_deleted)]

            # 解析作者信息
            author_name = data.get('authorName', '')
            author_email = data.get('authorEmail', '')

            # 解析日期
            date_str = data.get('authoredDate', data.get('committedDate', ''))

            return CommitInfo(
                hash=commit_id,
                author=author_name or 'Unknown',
                email=author_email or '',
                date=self._parse_date(date_str),
                message=(data.get('title', '') or data.get('message', '')).split('\n')[0],
                files=files,
            )
        except Exception as e:
            print(f"解析提交失败: {e}")
            return None

    def _parse_date(self, date_str: str) -> str:
        """将日期字符串转换为标准格式"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            # 尝试解析 ISO 格式
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            # 尝试解析时间戳
            if date_str.isdigit():
                dt = datetime.fromtimestamp(int(date_str) / 1000)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return str(date_str)[:19].replace('T', ' ')
        except (ValueError, TypeError):
            return str(date_str)[:19].replace('T', ' ')

    def get_file_content(
        self,
        repo_id: str,
        filepath: str,
        ref: str = "HEAD"
    ) -> Optional[str]:
        """获取文件内容"""
        import base64

        params = {'filePath': filepath}
        if ref != "HEAD":
            params['ref'] = ref

        data = self._api_request(
            f"/organizations/{self.organization_id}/repositories/{repo_id}/files",
            params=params
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
