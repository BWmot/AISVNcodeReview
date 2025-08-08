"""
提交状态查看工具
显示当前提交的处理状态和统计信息
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from commit_tracker import CommitTracker
    ENHANCED_MODE_AVAILABLE = True
except ImportError:
    ENHANCED_MODE_AVAILABLE = False


def show_traditional_status():
    """显示传统模式的状态"""
    print("📊 传统模式状态")
    print("=" * 50)
    
    processed_file = Path('data/processed_commits.json')
    if not processed_file.exists():
        print("ℹ️  未找到已处理提交记录文件")
        return
    
    try:
        with open(processed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            count = len(data)
            print(f"✅ 已处理提交数量: {count}")
            if count > 0:
                recent = data[-5:] if count > 5 else data
                print(f"📝 最近处理的提交: {', '.join(map(str, recent))}")
        elif isinstance(data, dict):
            count = len(data)
            print(f"✅ 已处理提交数量: {count}")
            if count > 0:
                recent = list(data.keys())[-5:] if count > 5 else list(data.keys())
                print(f"📝 最近处理的提交: {', '.join(recent)}")
        else:
            print("⚠️  提交记录格式不识别")
            
    except Exception as e:
        print(f"❌ 读取提交记录失败: {e}")


def show_enhanced_status():
    """显示增强模式的状态"""
    print("🔥 增强模式状态")
    print("=" * 50)
    
    if not ENHANCED_MODE_AVAILABLE:
        print("❌ 增强模式不可用（缺少commit_tracker模块）")
        return
    
    try:
        tracker = CommitTracker()
        
        # 获取各状态统计
        statuses = ['detected', 'reviewing', 'reviewed', 'notified', 'failed']
        status_counts = {}
        total_count = 0
        
        print("📈 提交状态统计:")
        for status in statuses:
            commits = tracker.get_commits_by_status(status)
            count = len(commits)
            status_counts[status] = count
            total_count += count
            
            status_display = {
                'detected': '🔍 已检测',
                'reviewing': '⏳ 审查中',
                'reviewed': '✅ 已审查',
                'notified': '📤 已通知',
                'failed': '❌ 失败'
            }
            
            print(f"  {status_display.get(status, status)}: {count}")
        
        print(f"\n📊 总计: {total_count} 条记录")
        
        # 显示最近的记录
        recent_commits = tracker.get_recent_commits(limit=10)
        if recent_commits:
            print(f"\n📝 最近的 {len(recent_commits)} 条记录:")
            for commit in recent_commits:
                time_str = commit.timestamp.strftime('%m-%d %H:%M')
                status_emoji = {
                    'detected': '🔍',
                    'reviewing': '⏳',
                    'reviewed': '✅',
                    'notified': '📤',
                    'failed': '❌'
                }.get(commit.status, '❓')
                
                print(f"  {status_emoji} 版本 {commit.revision} ({time_str}) - {commit.status}")
        
        # 显示今日统计
        today = datetime.now().date()
        today_commits = []
        for commit in tracker.get_recent_commits(limit=100):
            if commit.timestamp.date() == today:
                today_commits.append(commit)
        
        if today_commits:
            print(f"\n📅 今日处理: {len(today_commits)} 条提交")
            
            # 今日状态分布
            today_status = {}
            for commit in today_commits:
                today_status[commit.status] = today_status.get(commit.status, 0) + 1
            
            for status, count in today_status.items():
                if count > 0:
                    print(f"  {status}: {count}")
        
    except Exception as e:
        print(f"❌ 获取增强模式状态失败: {e}")


def show_recent_activity(hours=24):
    """显示最近活动"""
    print(f"\n⏰ 最近 {hours} 小时活动")
    print("=" * 50)
    
    if not ENHANCED_MODE_AVAILABLE:
        print("ℹ️  增强模式不可用，无法显示详细活动")
        return
    
    try:
        tracker = CommitTracker()
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_commits = tracker.get_recent_commits(limit=100)
        activity_commits = [
            c for c in recent_commits 
            if c.timestamp >= cutoff_time
        ]
        
        if not activity_commits:
            print(f"ℹ️  最近 {hours} 小时内没有活动")
            return
        
        print(f"📊 找到 {len(activity_commits)} 条活动记录")
        
        # 按时间倒序显示
        for commit in sorted(activity_commits, key=lambda x: x.timestamp, reverse=True):
            time_str = commit.timestamp.strftime('%m-%d %H:%M:%S')
            status_emoji = {
                'detected': '🔍',
                'reviewing': '⏳',
                'reviewed': '✅',
                'notified': '📤',
                'failed': '❌'
            }.get(commit.status, '❓')
            
            print(f"  {time_str} - {status_emoji} 版本 {commit.revision} ({commit.status})")
            
            # 显示详情（如果有）
            if commit.details:
                if commit.status == 'failed' and 'error' in commit.details:
                    print(f"    💥 错误: {commit.details['error']}")
                elif commit.status == 'reviewed' and 'score' in commit.details:
                    print(f"    📝 评分: {commit.details['score']}")
        
    except Exception as e:
        print(f"❌ 获取活动记录失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI SVN代码审查工具 - 状态查看器')
    parser.add_argument('--mode', choices=['traditional', 'enhanced', 'both'], 
                       default='both', help='显示模式')
    parser.add_argument('--activity-hours', type=int, default=24,
                       help='显示最近N小时的活动（默认24小时）')
    parser.add_argument('--no-activity', action='store_true',
                       help='不显示活动记录')
    
    args = parser.parse_args()
    
    print("AI SVN代码审查工具 - 状态查看器")
    print("=" * 60)
    print(f"⏰ 查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 显示传统模式状态
    if args.mode in ['traditional', 'both']:
        show_traditional_status()
        print()
    
    # 显示增强模式状态
    if args.mode in ['enhanced', 'both']:
        show_enhanced_status()
        print()
    
    # 显示最近活动
    if not args.no_activity and ENHANCED_MODE_AVAILABLE:
        show_recent_activity(args.activity_hours)
    
    print("\n💡 提示:")
    print("  - 使用 --mode enhanced 仅查看增强模式状态")
    print("  - 使用 --activity-hours 12 查看最近12小时活动")
    print("  - 使用 --no-activity 跳过活动记录显示")


if __name__ == "__main__":
    main()
