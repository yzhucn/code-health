#!/usr/bin/env python3
"""
调试 Codeup API 脚本

用法:
    # 设置环境变量
    export CODEUP_TOKEN="your_token"
    export CODEUP_ORG_ID="your_org_id"

    # 运行调试
    python3 scripts/debug_codeup_api.py
"""

import os
import sys
import json
import urllib.request
import urllib.error

# 配置
TOKEN = os.environ.get('CODEUP_TOKEN', '')
ORG_ID = os.environ.get('CODEUP_ORG_ID', '')
API_DOMAIN = "openapi-rdc.aliyuncs.com"


def api_request(path: str, params: dict = None) -> dict:
    """发起 API 请求"""
    base_url = f"https://{API_DOMAIN}/oapi/v1/codeup"
    url = f"{base_url}{path}"

    if params:
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query_string}"

    request = urllib.request.Request(url, headers={
        'Content-Type': 'application/json',
        'x-yunxiao-token': TOKEN,
    })

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP 错误: {e.code} - {e.reason}")
        if e.fp:
            print(f"响应: {e.read().decode('utf-8')[:500]}")
        return {}
    except Exception as e:
        print(f"请求失败: {e}")
        return {}


def main():
    print("=" * 60)
    print("Codeup API 调试脚本")
    print("=" * 60)
    print()

    # 检查配置
    print("1. 检查配置")
    print("-" * 40)
    print(f"Token: {TOKEN[:10]}..." if TOKEN else "Token: 未配置")
    print(f"Org ID: {ORG_ID}")
    print()

    if not TOKEN or not ORG_ID:
        print("错误: 请先设置 CODEUP_TOKEN 和 CODEUP_ORG_ID 环境变量")
        sys.exit(1)

    # 获取仓库列表
    print("2. 获取仓库列表")
    print("-" * 40)
    repos_data = api_request(
        f"/organizations/{ORG_ID}/repositories",
        params={'pageSize': 5}
    )

    if not repos_data:
        print("错误: 无法获取仓库列表")
        sys.exit(1)

    repos = repos_data if isinstance(repos_data, list) else repos_data.get('result', [])
    print(f"仓库数量: {len(repos)}")

    if not repos:
        print("错误: 仓库列表为空")
        sys.exit(1)

    for i, repo in enumerate(repos[:5]):
        print(f"  [{i+1}] {repo.get('name', 'N/A')} (ID: {repo.get('id', 'N/A')})")
    print()

    # 获取第一个仓库的提交
    repo = repos[0]
    repo_id = repo.get('id')
    repo_name = repo.get('name')

    print(f"3. 获取仓库 '{repo_name}' 的提交列表")
    print("-" * 40)
    commits_data = api_request(
        f"/organizations/{ORG_ID}/repositories/{repo_id}/commits",
        params={'pageSize': 5}
    )

    if not commits_data:
        print("错误: 无法获取提交列表")
        sys.exit(1)

    commits = commits_data if isinstance(commits_data, list) else commits_data.get('result', [])
    print(f"提交数量: {len(commits)}")

    if not commits:
        print("错误: 提交列表为空")
        sys.exit(1)

    for i, commit in enumerate(commits[:5]):
        print(f"  [{i+1}] {commit.get('id', 'N/A')[:12]}... - {commit.get('title', 'N/A')[:40]}")
    print()

    # 获取提交详情
    commit = commits[0]
    commit_id = commit.get('id', commit.get('sha', ''))

    print(f"4. 获取提交详情 (commit: {commit_id[:12]}...)")
    print("-" * 40)
    detail = api_request(
        f"/organizations/{ORG_ID}/repositories/{repo_id}/commits/{commit_id}"
    )

    if not detail:
        print("错误: 无法获取提交详情")
    else:
        print(f"API 响应 Keys: {list(detail.keys())}")
        print()

        # 检查 diffs 字段
        print("  diffs 字段:")
        if 'diffs' in detail:
            diffs = detail.get('diffs', []) or []
            print(f"    类型: {type(diffs)}")
            print(f"    数量: {len(diffs)}")
            if diffs:
                print(f"    第一个 diff 的 keys: {list(diffs[0].keys())}")
                print(f"    示例 diff: {json.dumps(diffs[0], indent=6, ensure_ascii=False)[:500]}")
        else:
            print("    字段不存在!")
        print()

        # 检查 stats 字段
        print("  stats 字段:")
        if 'stats' in detail:
            print(f"    {detail.get('stats')}")
        else:
            print("    字段不存在!")
        print()

        # 检查 parentShas 字段
        print("  parentShas 字段:")
        if 'parentShas' in detail:
            print(f"    {detail.get('parentShas')}")
        else:
            print("    字段不存在!")
        print()

    # 尝试获取提交 diff (备用方法)
    print(f"5. 尝试获取提交 diff (备用方法)")
    print("-" * 40)
    diff_data = api_request(
        f"/organizations/{ORG_ID}/repositories/{repo_id}/commits/{commit_id}/diff"
    )

    if not diff_data:
        print("  备用方法失败或不可用")
    else:
        print(f"  API 响应类型: {type(diff_data)}")
        if isinstance(diff_data, list):
            print(f"  diff 数量: {len(diff_data)}")
            if diff_data:
                print(f"  第一个 diff keys: {list(diff_data[0].keys())}")
        elif isinstance(diff_data, dict):
            print(f"  Keys: {list(diff_data.keys())}")
    print()

    # 尝试 compare API
    if detail and detail.get('parentShas'):
        parent_sha = detail.get('parentShas', [''])[0]
        if parent_sha:
            print(f"6. 尝试 compare API")
            print("-" * 40)
            compare_data = api_request(
                f"/organizations/{ORG_ID}/repositories/{repo_id}/compare",
                params={'from': parent_sha, 'to': commit_id}
            )

            if not compare_data:
                print("  compare API 失败或不可用")
            else:
                print(f"  API 响应类型: {type(compare_data)}")
                print(f"  Keys: {list(compare_data.keys())}")
                if 'diffs' in compare_data:
                    diffs = compare_data.get('diffs', [])
                    print(f"  diffs 数量: {len(diffs)}")

    print()
    print("=" * 60)
    print("调试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
