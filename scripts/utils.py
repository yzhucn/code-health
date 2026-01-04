#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码健康监控 - 工具函数库
Author: DevOps Team
Created: 2025-12-30
"""

import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import yaml


def parse_iso_datetime(date_str: str) -> datetime:
    """解析ISO格式日期时间字符串（兼容Python 3.6）"""
    # 移除时区信息
    date_str = date_str.replace(' +0800', '').replace('+0800', '')
    # Python 3.6兼容的解析方式
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        # 尝试其他格式
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')


class GitAnalyzer:
    """Git 仓库分析器"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo_name = os.path.basename(repo_path)

    def run_git_command(self, command: List[str]) -> str:
        """执行 git 命令"""
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path] + command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,  # Python 3.6 兼容
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error in {self.repo_name}: {e}")
            return ""

    def get_commits(self, since: str = "1 day ago", until: str = None, branch: str = "all") -> List[Dict]:
        """获取提交记录"""
        cmd = [
            "log",
            f"--since={since}",
            "--pretty=format:%H|%an|%ae|%ad|%s",
            "--date=iso",
            "--numstat"
        ]

        if until:
            cmd.insert(2, f"--until={until}")

        if branch != "all":
            cmd.append(branch)
        else:
            cmd.append("--all")

        output = self.run_git_command(cmd)
        if not output:
            return []

        commits = []
        lines = output.split('\n')
        i = 0

        while i < len(lines):
            if '|' in lines[i]:
                parts = lines[i].split('|')
                commit = {
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'date': parts[3],
                    'message': parts[4] if len(parts) > 4 else '',
                    'files': [],
                    'lines_added': 0,
                    'lines_deleted': 0
                }

                i += 1
                # 解析文件变更统计
                while i < len(lines) and lines[i] and '|' not in lines[i]:
                    parts = lines[i].split('\t')
                    if len(parts) >= 3:
                        added = parts[0] if parts[0] != '-' else 0
                        deleted = parts[1] if parts[1] != '-' else 0
                        filepath = parts[2]

                        try:
                            added = int(added)
                            deleted = int(deleted)
                        except:
                            added = 0
                            deleted = 0

                        commit['files'].append({
                            'path': filepath,
                            'added': added,
                            'deleted': deleted
                        })
                        commit['lines_added'] += added
                        commit['lines_deleted'] += deleted

                    i += 1

                commits.append(commit)
            else:
                i += 1

        return commits

    def get_file_history(self, filepath: str, since: str = "7 days ago") -> List[Dict]:
        """获取文件修改历史"""
        cmd = [
            "log",
            f"--since={since}",
            "--pretty=format:%H|%an|%ad",
            "--date=iso",
            "--",
            filepath
        ]

        output = self.run_git_command(cmd)
        if not output:
            return []

        history = []
        for line in output.split('\n'):
            if '|' in line:
                parts = line.split('|')
                history.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2]
                })

        return history

    def get_all_modified_files(self, since: str = "1 day ago") -> List[str]:
        """获取所有修改过的文件"""
        cmd = [
            "log",
            f"--since={since}",
            "--name-only",
            "--pretty=format:",
            "--all"
        ]

        output = self.run_git_command(cmd)
        if not output:
            return []

        files = [f for f in output.split('\n') if f.strip()]
        return list(set(files))

    def get_file_size(self, filepath: str) -> int:
        """获取文件行数"""
        full_path = os.path.join(self.repo_path, filepath)
        if not os.path.exists(full_path):
            return 0

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except:
            return 0

    def get_file_authors(self, filepath: str, since: str = "7 days ago") -> set:
        """获取文件的作者列表"""
        history = self.get_file_history(filepath, since)
        return set(h['author'] for h in history)


class ChurnAnalyzer:
    """代码震荡分析器"""

    def __init__(self, git_analyzer: GitAnalyzer, churn_days: int = 3, churn_count: int = 5):
        self.git_analyzer = git_analyzer
        self.churn_days = churn_days
        self.churn_count = churn_count

    def analyze(self) -> Tuple[List[Dict], float]:
        """分析代码震荡"""
        # 获取最近N天修改的所有文件
        files = self.git_analyzer.get_all_modified_files(f"{self.churn_days} days ago")

        churn_files = []
        for filepath in files:
            history = self.git_analyzer.get_file_history(filepath, f"{self.churn_days} days ago")
            modify_count = len(history)

            if modify_count >= self.churn_count:
                authors = self.git_analyzer.get_file_authors(filepath, f"{self.churn_days} days ago")
                churn_files.append({
                    'file': filepath,
                    'count': modify_count,
                    'authors': list(authors),
                    'size': self.git_analyzer.get_file_size(filepath)
                })

        # 计算震荡率
        total_files = len(files) if files else 1
        churn_rate = (len(churn_files) / total_files) * 100

        # 按修改次数排序
        churn_files.sort(key=lambda x: x['count'], reverse=True)

        return churn_files, churn_rate


class ReworkAnalyzer:
    """返工率分析器"""

    def __init__(self, git_analyzer: GitAnalyzer, add_days: int = 7, delete_days: int = 3):
        self.git_analyzer = git_analyzer
        self.add_days = add_days
        self.delete_days = delete_days

    def analyze(self) -> Tuple[int, int, float]:
        """分析返工率
        Returns: (返工行数, 总新增行数, 返工率)
        """
        # 获取最近N天的提交
        commits = self.git_analyzer.get_commits(f"{self.add_days} days ago")

        # 统计每个文件的新增和删除
        file_changes = {}
        for commit in commits:
            commit_date = parse_iso_datetime(commit['date'])

            for file_info in commit['files']:
                filepath = file_info['path']
                if filepath not in file_changes:
                    file_changes[filepath] = []

                file_changes[filepath].append({
                    'date': commit_date,
                    'added': file_info['added'],
                    'deleted': file_info['deleted']
                })

        # 检测返工：N天内新增，M天内被删除
        rework_lines = 0
        total_added = 0

        for filepath, changes in file_changes.items():
            changes.sort(key=lambda x: x['date'])

            for i, change in enumerate(changes):
                total_added += change['added']

                # 检查这次新增是否在后续几天内被删除
                for j in range(i + 1, len(changes)):
                    days_diff = (changes[j]['date'] - change['date']).days
                    if days_diff <= self.delete_days:
                        # 简化计算：如果后续有删除，认为是部分返工
                        estimated_rework = min(change['added'], changes[j]['deleted'])
                        rework_lines += estimated_rework

        # 计算返工率
        rework_rate = (rework_lines / total_added * 100) if total_added > 0 else 0

        return rework_lines, total_added, rework_rate


class HotspotAnalyzer:
    """高危文件分析器"""

    def __init__(self, git_analyzer: GitAnalyzer, config: Dict):
        self.git_analyzer = git_analyzer
        self.config = config

    def analyze(self) -> List[Dict]:
        """分析高危文件"""
        days = self.config.get('hotspot_days', 7)
        files = self.git_analyzer.get_all_modified_files(f"{days} days ago")

        hotspots = []
        for filepath in files:
            # 跳过排除的文件
            if self._should_exclude(filepath):
                continue

            history = self.git_analyzer.get_file_history(filepath, f"{days} days ago")
            modify_count = len(history)
            file_size = self.git_analyzer.get_file_size(filepath)
            authors = self.git_analyzer.get_file_authors(filepath, f"{days} days ago")

            # 计算风险分数
            risk_score = self._calculate_risk_score(modify_count, file_size, len(authors))

            # 识别风险标签
            tags = self._get_risk_tags(modify_count, file_size, len(authors), filepath)

            if risk_score > 40:  # 只记录中等以上风险
                hotspots.append({
                    'file': filepath,
                    'risk_score': risk_score,
                    'modify_count': modify_count,
                    'file_size': file_size,
                    'author_count': len(authors),
                    'authors': list(authors),
                    'tags': tags,
                    'suggestion': self._get_suggestion(tags, file_size)
                })

        # 按风险分数排序
        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)

        return hotspots

    def _calculate_risk_score(self, modify_count: int, file_size: int, author_count: int) -> float:
        """计算风险分数"""
        freq_score = min(modify_count / 10 * 100, 100)
        size_score = min(file_size / 1000 * 100, 100)
        author_score = min(author_count / 5 * 100, 100)

        risk = (freq_score * 0.3 + size_score * 0.25 + author_score * 0.2)
        return round(risk, 2)

    def _get_risk_tags(self, modify_count: int, file_size: int, author_count: int, filepath: str) -> List[str]:
        """获取风险标签"""
        tags = []

        if modify_count >= self.config.get('hotspot_count', 10):
            tags.append("高频修改")

        if file_size >= self.config.get('large_file', 1000):
            tags.append("大型文件")

        if author_count >= self.config.get('multi_author_count', 3):
            tags.append("多人协作")

        # 基于文件类型判断复杂度
        if filepath.endswith('.java'):
            # 简化：假设大文件 = 复杂文件
            if file_size > 800:
                tags.append("复杂文件")
        elif filepath.endswith('.py'):
            if file_size > 500:
                tags.append("复杂文件")

        return tags

    def _get_suggestion(self, tags: List[str], file_size: int) -> str:
        """获取改进建议"""
        if "大型文件" in tags and "复杂文件" in tags:
            return "🔴 建议拆分文件，提取公共逻辑"
        elif "高频修改" in tags:
            return "🟠 建议稳定接口，减少频繁修改"
        elif "多人协作" in tags:
            return "🟡 建议明确模块职责，减少协作冲突"
        else:
            return "🟢 保持关注"

    def _should_exclude(self, filepath: str) -> bool:
        """判断是否应该排除此文件"""
        exclude_patterns = self.config.get('exclude_patterns', [])
        exclude_dirs = self.config.get('exclude_dirs', [])

        # 检查目录
        for dir_pattern in exclude_dirs:
            if dir_pattern in filepath:
                return True

        # 检查文件模式
        for pattern in exclude_patterns:
            if pattern.startswith('*.'):
                ext = pattern[1:]
                if filepath.endswith(ext):
                    return True
            elif pattern in filepath:
                return True

        return False


class HealthScoreCalculator:
    """健康评分计算器"""

    def __init__(self, config: Dict):
        self.config = config

    def calculate(self, metrics: Dict) -> Tuple[float, List[str]]:
        """计算健康评分
        Returns: (分数, 扣分原因列表)
        """
        score = 100.0
        deductions = []

        # 大提交扣分
        large_commits = metrics.get('large_commits', 0)
        if large_commits > 0:
            deduction = large_commits * 5
            score -= deduction
            deductions.append(f"大提交 ({large_commits}次): -{deduction}分")

        # 震荡率扣分
        churn_rate = metrics.get('churn_rate', 0)
        if churn_rate > 30:
            deduction = 20
            score -= deduction
            deductions.append(f"高震荡率 ({churn_rate:.1f}%): -{deduction}分")
        elif churn_rate > 10:
            deduction = 10
            score -= deduction
            deductions.append(f"中等震荡率 ({churn_rate:.1f}%): -{deduction}分")

        # 返工率扣分
        rework_rate = metrics.get('rework_rate', 0)
        if rework_rate > 30:
            deduction = 15
            score -= deduction
            deductions.append(f"高返工率 ({rework_rate:.1f}%): -{deduction}分")
        elif rework_rate > 15:
            deduction = 8
            score -= deduction
            deductions.append(f"中等返工率 ({rework_rate:.1f}%): -{deduction}分")

        # 提交信息质量扣分
        message_quality = metrics.get('message_quality', 100)
        if message_quality < 60:
            deduction = 10
            score -= deduction
            deductions.append(f"提交信息质量差 ({message_quality:.0f}%): -{deduction}分")

        # 深夜/周末工作扣分
        late_commits = metrics.get('late_night_commits', 0)
        weekend_commits = metrics.get('weekend_commits', 0)
        abnormal_commits = late_commits + weekend_commits
        if abnormal_commits > 0:
            deduction = abnormal_commits * 2
            score -= deduction
            deductions.append(f"异常工作时间 ({abnormal_commits}次): -{deduction}分")

        # 未处理高危文件扣分
        high_risk_files = metrics.get('high_risk_files', 0)
        if high_risk_files > 0:
            deduction = min(high_risk_files * 3, 15)
            score -= deduction
            deductions.append(f"高危文件 ({high_risk_files}个): -{deduction}分")

        score = max(0, score)
        return round(score, 1), deductions

    def get_level(self, score: float) -> Tuple[str, str]:
        """获取评分等级
        Returns: (等级emoji, 等级描述)
        """
        if score >= self.config.get('health_score_excellent', 80):
            return "🟢", "优秀"
        elif score >= self.config.get('health_score_good', 60):
            return "🟡", "良好"
        elif score >= self.config.get('health_score_warning', 40):
            return "🟠", "警告"
        else:
            return "🔴", "危险"


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def format_number(num: int) -> str:
    """格式化数字，添加千分位"""
    return f"{num:,}"


def get_time_range(hours: int = 24) -> str:
    """获取时间范围字符串"""
    if hours == 24:
        return "1 day ago"
    elif hours == 168:  # 7 days
        return "7 days ago"
    else:
        return f"{hours} hours ago"


def is_late_night(time_str: str, config: Dict) -> bool:
    """判断是否深夜提交"""
    try:
        time = parse_iso_datetime(time_str)
        hour = time.hour

        late_start = int(config['working_hours']['late_night_start'].split(':')[0])
        late_end = int(config['working_hours']['late_night_end'].split(':')[0])

        if late_start > late_end:  # 跨天
            return hour >= late_start or hour < late_end
        else:
            return late_start <= hour < late_end
    except:
        return False


def is_weekend(time_str: str) -> bool:
    """判断是否周末提交"""
    try:
        time = parse_iso_datetime(time_str)
        return time.weekday() >= 5  # 5=Saturday, 6=Sunday
    except:
        return False


def is_overtime(time_str: str, config: Dict) -> bool:
    """判断是否加班时间提交
    加班时间定义为: 18:00-21:00
    """
    try:
        time = parse_iso_datetime(time_str)
        hour = time.hour
        minute = time.minute

        # 从配置读取加班时间段
        overtime_start = config.get('working_hours', {}).get('overtime_start', '18:00')
        overtime_end = config.get('working_hours', {}).get('overtime_end', '21:00')

        start_hour, start_minute = map(int, overtime_start.split(':'))
        end_hour, end_minute = map(int, overtime_end.split(':'))

        # 转换为分钟进行比较
        current_minutes = hour * 60 + minute
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        return start_minutes <= current_minutes < end_minutes
    except:
        return False


def calculate_message_quality(commits: List[Dict]) -> float:
    """计算提交信息质量"""
    if not commits:
        return 100.0

    good_patterns = [
        r'^(feat|fix|refactor|docs|test|chore|style|perf)(\(.+\))?:',
        r'.{10,}',  # 至少10个字符
    ]

    good_count = 0
    for commit in commits:
        message = commit.get('message', '')
        is_good = any(re.match(pattern, message) for pattern in good_patterns)
        if is_good:
            good_count += 1

    return (good_count / len(commits)) * 100
