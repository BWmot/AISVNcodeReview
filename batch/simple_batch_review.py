#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版批量代码审查脚本
"""

import os
import sys
import subprocess
import json
import argparse
import time
from datetime import datetime, timedelta

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # 获取项目根目录
src_path = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_path)

try:
    from config_manager import ConfigManager
    from ai_reviewer import AIReviewer
    from svn_monitor import SVNCommit
    import xml.etree.ElementTree as ET
except ImportError as e:
    print("=" * 60)
    print("❌ 导入错误:", str(e))
    print("=" * 60)
    print("🔧 解决方案:")
    print("1. 安装依赖包:")
    print("   pip install -r requirements.txt")
    print("   或者:")
    print("   pip install pyyaml requests schedule")
    print()
    print("2. 确保在项目根目录或正确设置Python路径")
    print("3. 如果使用虚拟环境，请先激活虚拟环境")
    print()
    print("📋 完整安装步骤:")
    print("   cd /path/to/project")
    print("   pip install -r requirements.txt")
    print("   python batch/simple_batch_review.py 7")
    print("=" * 60)
    sys.exit(1)


class ProgressMonitor:
    """进度监控器"""
    
    def __init__(self, total_commits):
        self.total_commits = total_commits
        self.current_commit = 0
        self.start_time = time.time()
        self.stage_start_time = time.time()
        self.stages = {}
        
    def start_commit(self, commit_index, revision):
        """开始处理提交"""
        self.current_commit = commit_index
        self.stage_start_time = time.time()
        elapsed = time.time() - self.start_time
        
        if commit_index > 1:
            avg_time = elapsed / (commit_index - 1)
            remaining_commits = self.total_commits - commit_index + 1
            eta = remaining_commits * avg_time
            eta_str = self._format_time(eta)
        else:
            eta_str = "计算中..."
        
        print(f"\n{'='*60}")
        print(f"📋 处理进度: [{commit_index}/{self.total_commits}] ({(commit_index/self.total_commits*100):.1f}%)")
        print(f"🔄 当前版本: {revision}")
        print(f"⏱️  已用时间: {self._format_time(elapsed)}")
        print(f"⏰ 预计剩余: {eta_str}")
        print(f"{'='*60}")
    
    def start_stage(self, stage_name):
        """开始处理阶段"""
        self.stage_start_time = time.time()
        print(f"🔸 {stage_name}...")
        
    def end_stage(self, stage_name, success=True):
        """结束处理阶段"""
        elapsed = time.time() - self.stage_start_time
        status = "✅" if success else "❌"
        print(f"  {status} {stage_name} - 耗时: {self._format_time(elapsed)}")
        
        if stage_name not in self.stages:
            self.stages[stage_name] = []
        self.stages[stage_name].append(elapsed)
    
    def log_details(self, message, indent=1):
        """记录详细信息"""
        prefix = "  " * indent + "🔹 "
        print(f"{prefix}{message}")
    
    def show_final_stats(self):
        """显示最终统计"""
        total_time = time.time() - self.start_time
        print(f"\n{'='*60}")
        print(f"📊 批量审查完成统计")
        print(f"{'='*60}")
        print(f"⏱️  总用时: {self._format_time(total_time)}")
        print(f"📝 总提交数: {self.total_commits}")
        print(f"⚡ 平均每提交: {self._format_time(total_time / max(1, self.total_commits))}")
        
        print(f"\n📋 各阶段耗时统计:")
        for stage, times in self.stages.items():
            avg_time = sum(times) / len(times)
            total_stage_time = sum(times)
            print(f"  🔸 {stage}:")
            print(f"     总计: {self._format_time(total_stage_time)} | 平均: {self._format_time(avg_time)} | 次数: {len(times)}")
    
    def _format_time(self, seconds):
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}分{secs:.1f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}时{minutes}分{secs:.1f}秒"


class SimpleBatchReviewer:
    """简化版批量审查器"""
    
    def __init__(self, config_path=None):
        if config_path is None:
            # 自动检测配置文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            config_path = os.path.join(parent_dir, "config", "config.yaml")
        
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.ai_reviewer = AIReviewer()
        
        # 创建报告目录 - 也需要相对于项目根目录
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.reports_dir = os.path.join(parent_dir, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def get_svn_commits(self, start_date, end_date, paths=None):
        """获取SVN提交记录"""
        if paths is None:
            paths = self.config['svn'].get('monitored_paths', [])
        
        repository_url = self.config['svn']['repository_url']
        username = self.config['svn']['username']
        password = self.config['svn']['password']
        
        commits = []
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        print(f"获取 {start_str} 到 {end_str} 的提交记录...")
        
        for path in paths:
            try:
                cmd = [
                    'svn', 'log',
                    f'{repository_url}{path}',
                    f'-r{{{start_str}}}:{{{end_str}}}',
                    '--xml',
                    '--username', username,
                    '--password', password,
                    '--non-interactive',
                    '--trust-server-cert'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True,
                                      encoding='utf-8', timeout=300)
                
                if result.returncode == 0:
                    path_commits = self.parse_svn_xml(result.stdout, path)
                    commits.extend(path_commits)
                else:
                    print(f"获取路径 {path} 失败: {result.stderr}")
                    
            except Exception as e:
                print(f"路径 {path} 错误: {e}")
        
        # 去重并排序
        unique_commits = {}
        for commit in commits:
            revision = commit['revision']
            if revision not in unique_commits:
                unique_commits[revision] = commit
        
        sorted_commits = sorted(unique_commits.values(),
                              key=lambda x: int(x['revision']))
        
        print(f"找到 {len(sorted_commits)} 个唯一提交")
        return sorted_commits
    
    def parse_svn_xml(self, xml_content, path):
        """解析SVN XML输出"""
        commits = []
        try:
            root = ET.fromstring(xml_content)
            for logentry in root.findall('logentry'):
                revision = logentry.get('revision')
                
                author_elem = logentry.find('author')
                author = author_elem.text if author_elem is not None else 'unknown'
                
                date_elem = logentry.find('date')
                date_str = date_elem.text if date_elem is not None else ''
                
                msg_elem = logentry.find('msg')
                message = msg_elem.text if msg_elem is not None else ''
                
                # 使用配置化的过滤逻辑
                if not self.should_include_commit(author, message, revision):
                    continue
                
                commit_info = {
                    'revision': revision,
                    'author': author,
                    'date': date_str,
                    'message': message,
                    'path': path
                }
                commits.append(commit_info)
        except ET.ParseError as e:
            print(f"解析XML失败: {e}")
        
        return commits
    
    def should_include_commit(self, author, message, revision=None):
        """判断是否应该包含此提交"""
        filters = self.config.get('batch_review', {}).get('filters', {})
        
        # 获取过滤配置
        revision_range = filters.get('revision_range', {})
        min_revision = revision_range.get('min_revision')
        max_revision = revision_range.get('max_revision')
        include_authors = filters.get('include_authors', [])
        exclude_authors = filters.get('exclude_authors', [])
        include_message_patterns = filters.get('include_message_patterns', [])
        exclude_message_patterns = filters.get('exclude_message_patterns', [])
        case_sensitive = filters.get('case_sensitive', False)
        use_regex = filters.get('use_regex', False)
        
        # 版本号过滤
        if revision is not None:
            try:
                rev_num = int(revision)
                if min_revision is not None and rev_num < min_revision:
                    return False
                if max_revision is not None and rev_num > max_revision:
                    return False
            except (ValueError, TypeError):
                # 如果版本号不是数字，跳过版本号过滤
                pass
        
        # 处理大小写
        if not case_sensitive:
            author_check = author.lower()
            message_check = message.lower()
            include_authors = [a.lower() for a in include_authors]
            exclude_authors = [a.lower() for a in exclude_authors]
            include_message_patterns = [p.lower() for p in include_message_patterns]
            exclude_message_patterns = [p.lower() for p in exclude_message_patterns]
        else:
            author_check = author
            message_check = message
        
        # 作者过滤
        if include_authors and author_check not in include_authors:
            return False
        
        if exclude_authors and author_check in exclude_authors:
            return False
        
        # 消息过滤
        if include_message_patterns:
            if use_regex:
                import re
                if not any(re.search(pattern, message_check) for pattern in include_message_patterns):
                    return False
            else:
                if not any(pattern in message_check for pattern in include_message_patterns):
                    return False
        
        if exclude_message_patterns:
            if use_regex:
                import re
                if any(re.search(pattern, message_check) for pattern in exclude_message_patterns):
                    return False
            else:
                if any(pattern in message_check for pattern in exclude_message_patterns):
                    return False
        
        return True
    
    def apply_cli_filters(self, args):
        """应用命令行过滤参数"""
        filters = self.config.setdefault('batch_review', {}).setdefault('filters', {})
        
        # 应用版本号范围过滤
        if hasattr(args, 'min_revision') or hasattr(args, 'max_revision'):
            revision_range = filters.setdefault('revision_range', {})
            if args.min_revision is not None:
                revision_range['min_revision'] = args.min_revision
            if args.max_revision is not None:
                revision_range['max_revision'] = args.max_revision
        
        # 应用命令行参数
        if args.include_authors:
            filters['include_authors'] = args.include_authors
        if args.exclude_authors:
            filters['exclude_authors'] = args.exclude_authors
        if args.include_messages:
            filters['include_message_patterns'] = args.include_messages
        if args.exclude_messages:
            filters['exclude_message_patterns'] = args.exclude_messages
        
        # 设置匹配选项
        filters['case_sensitive'] = args.case_sensitive
        filters['use_regex'] = args.regex
        
        print(f"已应用过滤条件:")
        revision_range = filters.get('revision_range', {})
        if revision_range.get('min_revision') is not None:
            print(f"  最小版本号: {revision_range['min_revision']}")
        if revision_range.get('max_revision') is not None:
            print(f"  最大版本号: {revision_range['max_revision']}")
        if filters.get('include_authors'):
            print(f"  包含作者: {filters['include_authors']}")
        if filters.get('exclude_authors'):
            print(f"  排除作者: {filters['exclude_authors']}")
        if filters.get('include_message_patterns'):
            print(f"  包含消息: {filters['include_message_patterns']}")
        if filters.get('exclude_message_patterns'):
            print(f"  排除消息: {filters['exclude_message_patterns']}")
    
    def get_commit_diff(self, revision, monitor=None):
        """获取提交的代码差异"""
        if monitor:
            monitor.start_stage("获取代码差异")
        
        repository_url = self.config['svn']['repository_url']
        username = self.config['svn']['username']
        password = self.config['svn']['password']
        
        try:
            if monitor:
                monitor.log_details(f"执行SVN diff命令 (版本: {revision})")
                
            cmd = [
                'svn', 'diff',
                f'{repository_url}',
                f'-c{revision}',
                '--username', username,
                '--password', password,
                '--non-interactive',
                '--trust-server-cert'
            ]
            
            if monitor:
                monitor.log_details("等待SVN服务器响应...")
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding='utf-8', timeout=120)
            
            if result.returncode == 0:
                diff_size = len(result.stdout)
                if monitor:
                    monitor.log_details(f"获取到 {diff_size} 字符的差异内容")
                    monitor.end_stage("获取代码差异", True)
                return result.stdout
            else:
                error_msg = f"获取差异失败: {result.stderr}"
                if monitor:
                    monitor.log_details(f"SVN命令失败: {result.stderr}", 2)
                    monitor.end_stage("获取代码差异", False)
                return error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "获取差异超时 (120秒)"
            if monitor:
                monitor.log_details("SVN命令执行超时", 2)
                monitor.end_stage("获取代码差异", False)
            return error_msg
        except Exception as e:
            error_msg = f"获取差异异常: {e}"
            if monitor:
                monitor.log_details(f"发生异常: {str(e)}", 2)
                monitor.end_stage("获取代码差异", False)
            return error_msg
    
    def get_changed_files(self, revision, monitor=None):
        """获取提交的变更文件列表"""
        if monitor:
            monitor.log_details(f"获取版本 {revision} 的文件变更列表", 2)
        
        repository_url = self.config['svn']['repository_url']
        username = self.config['svn']['username']
        password = self.config['svn']['password']
        
        try:
            cmd = [
                'svn', 'log',
                repository_url,
                f'-r{revision}',
                '--xml',
                '--verbose',
                '--username', username,
                '--password', password,
                '--non-interactive',
                '--trust-server-cert'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding='utf-8', timeout=60)
            
            if result.returncode == 0:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(result.stdout)
                logentry = root.find('logentry')
                changed_files = []
                
                if logentry is not None:
                    paths = logentry.find('paths')
                    if paths is not None:
                        for path in paths.findall('path'):
                            file_info = {
                                'path': path.text,
                                'action': path.get('action', ''),
                                'kind': path.get('kind', 'file')
                            }
                            changed_files.append(file_info)
                
                if monitor:
                    monitor.log_details(f"找到 {len(changed_files)} 个变更文件", 2)
                
                return changed_files
            else:
                if monitor:
                    monitor.log_details(f"获取文件列表失败: {result.stderr}", 2)
                return []
                
        except Exception as e:
            if monitor:
                monitor.log_details(f"获取文件列表异常: {str(e)}", 2)
            return []
    
    def batch_review(self, commits):
        """批量审查提交"""
        results = []
        total = len(commits)
        
        # 创建进度监控器
        monitor = ProgressMonitor(total)
        
        print(f"🚀 开始批量审查 {total} 个提交...")
        
        for i, commit in enumerate(commits, 1):
            revision = commit['revision']
            
            # 开始处理当前提交
            monitor.start_commit(i, revision)
            
            try:
                # 阶段1: 获取代码差异
                diff_content = self.get_commit_diff(revision, monitor)
                
                # 阶段2: 准备审查数据
                monitor.start_stage("准备审查数据")
                monitor.log_details(f"作者: {commit['author']}")
                monitor.log_details(f"提交信息: {commit['message'][:100]}{'...' if len(commit['message']) > 100 else ''}")
                
                # 获取详细的文件变更信息
                changed_files = self.get_changed_files(revision, monitor)
                
                # 创建SVNCommit对象
                commit_date = (datetime.fromisoformat(commit['date'].replace('Z', '+00:00')) 
                             if commit['date'] else datetime.now())
                svn_commit = SVNCommit(
                    revision=commit['revision'],
                    author=commit['author'],
                    date=commit_date,
                    message=commit['message'],
                    changed_files=changed_files,  # 使用实际的文件变更信息
                    diff_content=diff_content
                )
                
                # 统计差异信息
                diff_lines = len(diff_content.split('\n')) if diff_content else 0
                monitor.log_details(f"差异行数: {diff_lines}")
                monitor.log_details(f"变更文件: {len(changed_files)} 个")
                monitor.end_stage("准备审查数据", True)
                
                # 阶段3: AI审查
                monitor.start_stage("AI智能审查")
                monitor.log_details("发送请求到AI服务...")
                
                review_result = self.ai_reviewer.review_commit(svn_commit, monitor)
                
                if review_result:
                    monitor.log_details(f"AI评分: {review_result.overall_score}/10")
                    monitor.log_details(f"发现风险: {len(review_result.risks)} 个")
                    monitor.log_details(f"改进建议: {len(review_result.suggestions)} 个")
                    monitor.end_stage("AI智能审查", True)
                else:
                    monitor.log_details("AI审查返回空结果", 2)
                    monitor.end_stage("AI智能审查", False)
                
                # 构建结果
                result = {
                    'commit': commit,
                    'diff': diff_content,
                    'review': review_result,
                    'reviewed_at': datetime.now().isoformat(),
                    'success': review_result is not None
                }
                
                print(f"✅ 版本 {revision} 审查完成")
                
            except Exception as e:
                monitor.log_details(f"处理异常: {str(e)}", 2)
                monitor.end_stage("异常处理", False)
                
                result = {
                    'commit': commit,
                    'diff': '',
                    'review': None,
                    'reviewed_at': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                }
                
                print(f"❌ 版本 {revision} 审查失败: {e}")
            
            results.append(result)
            
            # 在提交之间添加短暂延迟，避免过于频繁的API调用
            if i < total:
                time.sleep(1)
        
        # 显示最终统计
        monitor.show_final_stats()
        
        return results
    
    def generate_html_report(self, results, start_date, end_date):
        """生成HTML报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
        filename = f"batch_review_{date_range}_{timestamp}.html"
        report_path = os.path.join(self.reports_dir, filename)
        
        # 统计数据
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>批量代码审查报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; padding: 20px; background: #f5f5f5; }}
        .stats {{ display: flex; justify-content: center; gap: 20px; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 10px; background: #e8f4f8; border-radius: 5px; }}
        .commit {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
        .success {{ border-left: 4px solid #28a745; }}
        .failed {{ border-left: 4px solid #dc3545; }}
        .diff {{ background: #f8f8f8; padding: 10px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .review {{ background: #e8f4f8; padding: 10px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 SVN批量代码审查报告</h1>
        <p>审查期间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat">
            <h3>{total}</h3>
            <p>总提交数</p>
        </div>
        <div class="stat">
            <h3>{success}</h3>
            <p>成功审查</p>
        </div>
        <div class="stat">
            <h3>{failed}</h3>
            <p>审查失败</p>
        </div>
    </div>
    
    <h2>详细结果</h2>
"""
        
        for result in results:
            commit = result['commit']
            review = result['review']
            success_class = 'success' if result['success'] else 'failed'
            status_icon = '✅' if result['success'] else '❌'
            
            html_content += f"""
    <div class="commit {success_class}">
        <h3>{status_icon} 版本 {commit['revision']} - {commit['author']}</h3>
        <p><strong>时间:</strong> {commit['date']}</p>
        <p><strong>消息:</strong> {commit['message']}</p>
        <p><strong>路径:</strong> {commit['path']}</p>
"""
            
            if result['success'] and review:
                html_content += f"""
        <div class="review">
            <h4>🤖 AI审查结果</h4>
            <p><strong>总结:</strong> {review.summary if review.summary else '无'}</p>
            <p><strong>评分:</strong> {review.overall_score}/10</p>
            <p><strong>风险问题:</strong></p>
            <ul>
"""
                for risk in review.risks:
                    html_content += f"<li>{risk}</li>"
                    
                html_content += """
            </ul>
            <p><strong>建议:</strong></p>
            <ul>
"""
                for suggestion in review.suggestions:
                    html_content += f"<li>{suggestion}</li>"
                    
                html_content += """
            </ul>
            <p><strong>详细评论:</strong></p>
            <ul>
"""
                for comment in review.detailed_comments:
                    file_name = comment.get('file', '未知文件')
                    comment_text = comment.get('comment', '')
                    html_content += f"<li><strong>{file_name}:</strong> {comment_text}</li>"
                
                html_content += """
            </ul>
        </div>
"""
            else:
                error_msg = result.get('error', '审查失败')
                html_content += f"""
        <div class="review">
            <h4>❌ 审查失败</h4>
            <p>{error_msg}</p>
        </div>
"""
            
            # 添加代码差异（限制长度）
            diff = result.get('diff', '')
            if diff and len(diff) > 100:
                if len(diff) > 2000:
                    diff = diff[:2000] + "\\n... (内容过长，已截断)"
                html_content += f"""
        <h4>代码变更</h4>
        <div class="diff">{diff.replace('<', '&lt;').replace('>', '&gt;')}</div>
"""
            
            html_content += "</div>"
        
        html_content += """
</body>
</html>
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='SVN批量代码审查工具')
    parser.add_argument('days', type=int, nargs='?', default=7,
                        help='审查最近几天的提交 (默认: 7)')
    parser.add_argument('--min-revision', type=int,
                        help='最小版本号（包含）')
    parser.add_argument('--max-revision', type=int,
                        help='最大版本号（包含）')
    parser.add_argument('--include-authors', nargs='*',
                        help='只包含指定作者的提交')
    parser.add_argument('--exclude-authors', nargs='*',
                        help='排除指定作者的提交')
    parser.add_argument('--include-messages', nargs='*',
                        help='只包含匹配关键词的提交信息')
    parser.add_argument('--exclude-messages', nargs='*',
                        help='排除匹配关键词的提交信息')
    parser.add_argument('--case-sensitive', action='store_true',
                        help='启用大小写敏感匹配')
    parser.add_argument('--regex', action='store_true',
                        help='使用正则表达式匹配')
    parser.add_argument('--auto-confirm', action='store_true',
                        help='自动确认审查，不询问用户')
    
    return parser.parse_args()


def main():
    """主函数"""
    print("=== SVN批量代码审查工具 ===")
    
    # 解析命令行参数
    args = parse_arguments()
    days = args.days
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"审查最近 {days} 天的提交")
    print(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    # 显示过滤条件
    if args.min_revision is not None:
        print(f"最小版本号: {args.min_revision}")
    if args.max_revision is not None:
        print(f"最大版本号: {args.max_revision}")
    if args.include_authors:
        print(f"包含作者: {', '.join(args.include_authors)}")
    if args.exclude_authors:
        print(f"排除作者: {', '.join(args.exclude_authors)}")
    if args.include_messages:
        print(f"包含消息关键词: {', '.join(args.include_messages)}")
    if args.exclude_messages:
        print(f"排除消息关键词: {', '.join(args.exclude_messages)}")
    if args.case_sensitive:
        print("启用大小写敏感匹配")
    if args.regex:
        print("启用正则表达式匹配")
    
    try:
        reviewer = SimpleBatchReviewer()
        
        # 应用命令行过滤参数
        if any([args.min_revision is not None, args.max_revision is not None,
                args.include_authors, args.exclude_authors, 
                args.include_messages, args.exclude_messages]):
            print("\\n应用命令行过滤参数...")
            reviewer.apply_cli_filters(args)
        
        # 获取提交
        commits = reviewer.get_svn_commits(start_date, end_date)
        
        if not commits:
            print("没有找到提交记录")
            return
        
        # 确认继续
        if args.auto_confirm:
            print(f"\\n找到 {len(commits)} 个提交，自动开始审查...")
        else:
            response = input(f"\\n找到 {len(commits)} 个提交，是否继续审查？(y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("已取消")
                return
        
        # 批量审查
        results = reviewer.batch_review(commits)
        
        # 生成报告
        report_path = reviewer.generate_html_report(results, start_date, end_date)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        print(f"\\n=== 完成 ===")
        print(f"总计: {len(results)}")
        print(f"成功: {success_count}")
        print(f"失败: {len(results) - success_count}")
        print(f"报告: {report_path}")
        
        # 尝试打开报告
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
            print("已在浏览器中打开报告")
        except Exception:
            pass
            
    except KeyboardInterrupt:
        print("\\n已中断")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
