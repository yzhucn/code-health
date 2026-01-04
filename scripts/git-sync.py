#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - Git 同步工具
Author: DevOps Team
Created: 2025-12-30

功能：
1. 自动拉取所有仓库的最新代码
2. 显示拉取状态和冲突
3. 支持多分支拉取
4. 集成到报告生成流程

Usage:
    python git-sync.py [options]

Examples:
    python git-sync.py                    # 拉取所有仓库
    python git-sync.py --branch dev       # 拉取指定分支
    python git-sync.py --dry-run          # 只显示计划
"""

import os
import sys
import subprocess
from datetime import datetime

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils import load_config


class GitSync:
    """Git 同步工具"""

    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.repos = self.config['repositories']

    def run_git_command(self, repo_path: str, command: list) -> tuple:
        """执行 git 命令"""
        try:
            result = subprocess.run(
                ["git", "-C", repo_path] + command,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def get_current_branch(self, repo_path: str) -> str:
        """获取当前分支"""
        success, stdout, _ = self.run_git_command(repo_path, ["branch", "--show-current"])
        return stdout.strip() if success else None

    def get_repo_status(self, repo_path: str) -> dict:
        """获取仓库状态"""
        status = {
            'clean': True,
            'branch': None,
            'uncommitted': 0,
            'untracked': 0
        }

        # 获取当前分支
        status['branch'] = self.get_current_branch(repo_path)

        # 检查未提交的修改
        success, stdout, _ = self.run_git_command(repo_path, ["status", "--porcelain"])
        if success and stdout:
            lines = stdout.strip().split('\n')
            status['clean'] = False
            for line in lines:
                if line.startswith('??'):
                    status['untracked'] += 1
                else:
                    status['uncommitted'] += 1

        return status

    def pull_repo(self, repo: dict, target_branch: str = None, dry_run: bool = False) -> dict:
        """拉取单个仓库"""
        result = {
            'name': repo['name'],
            'path': repo['path'],
            'success': False,
            'message': '',
            'changes': 0
        }

        # 检查仓库是否存在
        if not os.path.exists(repo['path']):
            result['message'] = '路径不存在'
            return result

        # 检查是否是 git 仓库
        if not os.path.exists(os.path.join(repo['path'], '.git')):
            result['message'] = '不是 Git 仓库'
            return result

        # 获取当前状态
        status = self.get_repo_status(repo['path'])

        if not status['clean']:
            result['message'] = f"工作区不干净 (未提交: {status['uncommitted']}, 未跟踪: {status['untracked']})"
            return result

        # 确定要拉取的分支
        branch = target_branch or repo.get('main_branch', status['branch'])

        if dry_run:
            result['message'] = f"将拉取分支: {branch}"
            result['success'] = True
            return result

        # 切换分支（如果需要）
        if status['branch'] != branch:
            print(f"    切换分支: {status['branch']} -> {branch}")
            success, _, stderr = self.run_git_command(repo['path'], ["checkout", branch])
            if not success:
                result['message'] = f"切换分支失败: {stderr}"
                return result

        # 执行 git pull
        success, stdout, stderr = self.run_git_command(repo['path'], ["pull", "--rebase"])

        if success:
            result['success'] = True

            # 检查是否有更新
            if "Already up to date" in stdout or "已经是最新" in stdout:
                result['message'] = "已是最新"
            else:
                # 尝试统计变更文件数
                lines = stdout.split('\n')
                for line in lines:
                    if 'file changed' in line or 'files changed' in line or '个文件被修改' in line:
                        try:
                            result['changes'] = int(line.split()[0])
                        except:
                            pass
                result['message'] = f"拉取成功 ({result['changes']} 文件变更)" if result['changes'] else "拉取成功"
        else:
            result['message'] = f"拉取失败: {stderr}"

        return result

    def sync_all(self, target_branch: str = None, dry_run: bool = False):
        """同步所有仓库"""
        print("=" * 70)
        print("🔄 Git 仓库同步")
        print("=" * 70)

        if dry_run:
            print("\n⚠️  干运行模式：不会实际拉取代码\n")

        results = []
        success_count = 0
        skip_count = 0
        fail_count = 0

        for i, repo in enumerate(self.repos, 1):
            print(f"[{i}/{len(self.repos)}] 📦 {repo['name']}:")

            result = self.pull_repo(repo, target_branch, dry_run)
            results.append(result)

            if result['success']:
                if "已是最新" in result['message'] or "Already" in result['message']:
                    print(f"  ⏭️  {result['message']}")
                    skip_count += 1
                else:
                    print(f"  ✅ {result['message']}")
                    success_count += 1
            else:
                print(f"  ❌ {result['message']}")
                fail_count += 1

        # 总结
        print("\n" + "=" * 70)
        print("📊 同步结果:")
        print(f"  - 成功更新: {success_count}")
        print(f"  - 已是最新: {skip_count}")
        print(f"  - 失败/跳过: {fail_count}")
        print("=" * 70)

        return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='代码健康监控 - Git 同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--branch',
        help='指定要拉取的分支，默认使用配置文件中的 main_branch'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式，只显示计划不实际拉取'
    )

    args = parser.parse_args()

    # 获取配置文件路径
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'config.yaml')

    # 执行同步
    sync = GitSync(config_path)
    sync.sync_all(target_branch=args.branch, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
