#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量代码审查脚本
使用现有模块实现批量SVN代码审查功能
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加src目录到路径
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

from config_manager import ConfigManager
from batch_reviewer import BatchReviewer


def parse_date(date_str):
    """解析日期字符串"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的日期格式: {date_str}，请使用 YYYY-MM-DD 格式")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SVN批量代码审查工具')
    
    parser.add_argument('--start-date', type=parse_date, 
                       help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=parse_date, 
                       help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=7,
                       help='审查最近N天的提交 (默认: 7)')
    parser.add_argument('--paths', nargs='*',
                       help='指定要审查的SVN路径')
    parser.add_argument('--output-format', choices=['html', 'markdown', 'json'],
                       default='html', help='报告输出格式')
    parser.add_argument('--config', default='config/config.yaml',
                       help='配置文件路径')
    parser.add_argument('--output-dir', default='reports',
                       help='报告输出目录')
    
    args = parser.parse_args()
    
    # 确定日期范围
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    
    print(f"=== SVN批量代码审查工具 ===")
    print(f"审查期间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"配置文件: {args.config}")
    print(f"输出格式: {args.output_format}")
    print()
    
    try:
        # 初始化批量审查器
        reviewer = BatchReviewer(args.config)
        
        # 临时设置输出格式和目录
        reviewer.report_format = args.output_format
        reviewer.reports_dir = args.output_dir
        os.makedirs(reviewer.reports_dir, exist_ok=True)
        
        # 获取提交记录
        print("正在获取SVN提交记录...")
        commits = reviewer.get_commits_by_date_range(start_date, end_date, args.paths)
        
        if not commits:
            print("没有找到符合条件的提交记录")
            return
        
        print(f"找到 {len(commits)} 个提交记录")
        print()
        
        # 确认是否继续
        response = input("是否继续进行批量审查？(y/N): ").lower()
        if response not in ['y', 'yes']:
            print("已取消操作")
            return
        
        # 批量审查
        print("开始批量代码审查...")
        results = reviewer.batch_review_commits(commits, print_progress)
        
        # 生成报告
        print("\n正在生成报告...")
        paths = args.paths or reviewer.batch_config.get('default_paths', [])
        report_path = reviewer.generate_report(results, start_date, end_date, paths)
        
        # 输出结果统计
        success_count = sum(1 for r in results if r['review_success'])
        failed_count = len(results) - success_count
        
        print(f"\n=== 审查完成 ===")
        print(f"总提交数: {len(results)}")
        print(f"成功审查: {success_count}")
        print(f"审查失败: {failed_count}")
        print(f"成功率: {success_count/len(results)*100:.1f}%")
        print(f"报告文件: {report_path}")
        
        # 自动打开报告（如果是HTML格式）
        if args.output_format == 'html':
            try:
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(report_path)}")
                print("已在浏览器中打开报告")
            except Exception:
                pass
        
    except KeyboardInterrupt:
        print("\n\n操作已被用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        return 1
    
    return 0


def print_progress(current, total, revision):
    """打印进度"""
    percentage = (current / total) * 100
    print(f"进度: {current:3d}/{total} ({percentage:5.1f}%) - 版本 {revision}")


if __name__ == "__main__":
    sys.exit(main())
