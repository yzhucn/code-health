"""
工具函数库
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple


def parse_iso_datetime(date_str: str) -> datetime:
    """解析ISO格式日期时间字符串"""
    # 移除时区信息
    date_str = date_str.replace(' +0800', '').replace('+0800', '')
    date_str = date_str.replace(' +0000', '').replace('+0000', '')

    # 尝试多种格式
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S %z',
        '%Y-%m-%dT%H:%M:%SZ',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str[:19], fmt[:19].replace(' %z', ''))
        except ValueError:
            continue

    # 回退：解析前19个字符
    return datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')


def is_late_night(time_str: str, config: Dict) -> bool:
    """判断是否深夜提交"""
    try:
        time = parse_iso_datetime(time_str)
        hour = time.hour

        working_hours = config.get('working_hours', {})
        late_start = int(working_hours.get('late_night_start', '22:00').split(':')[0])
        late_end = int(working_hours.get('late_night_end', '06:00').split(':')[0])

        if late_start > late_end:  # 跨天 (22:00 - 06:00)
            return hour >= late_start or hour < late_end
        else:
            return late_start <= hour < late_end
    except Exception:
        return False


def is_weekend(time_str: str) -> bool:
    """判断是否周末提交"""
    try:
        time = parse_iso_datetime(time_str)
        return time.weekday() >= 5  # 5=Saturday, 6=Sunday
    except Exception:
        return False


def is_overtime(time_str: str, config: Dict) -> bool:
    """判断是否加班时间提交 (18:00-21:00)"""
    try:
        time = parse_iso_datetime(time_str)
        hour = time.hour
        minute = time.minute

        working_hours = config.get('working_hours', {})
        overtime_start = working_hours.get('overtime_start', '18:00')
        overtime_end = working_hours.get('overtime_end', '21:00')

        start_hour, start_minute = map(int, overtime_start.split(':'))
        end_hour, end_minute = map(int, overtime_end.split(':'))

        current_minutes = hour * 60 + minute
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        return start_minutes <= current_minutes < end_minutes
    except Exception:
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
        # 支持 CommitInfo 对象和 dict
        if hasattr(commit, 'message'):
            message = commit.message
        else:
            message = commit.get('message', '')

        is_good = any(re.match(pattern, message) for pattern in good_patterns)
        if is_good:
            good_count += 1

    return (good_count / len(commits)) * 100


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


def get_level_emoji(score: float, thresholds: Dict) -> Tuple[str, str]:
    """获取评分等级
    Returns: (等级emoji, 等级描述)
    """
    excellent = thresholds.get('health_score_excellent', 80)
    good = thresholds.get('health_score_good', 60)
    warning = thresholds.get('health_score_warning', 40)

    if score >= excellent:
        return "🟢", "优秀"
    elif score >= good:
        return "🟡", "良好"
    elif score >= warning:
        return "🟠", "警告"
    else:
        return "🔴", "危险"
