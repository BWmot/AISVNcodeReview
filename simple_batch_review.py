#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版批量代码审查脚本
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timedelta

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

try:
    from config_manager import ConfigManager
    from ai_reviewer import AIReviewer
    from svn_monitor import SVNCommit
    import xml.etree.ElementTree as ET
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"请确保src目录存在并包含必要的模块")
    sys.exit(1)


class SimpleBatchReviewer:
    """简化版批量审查器"""
    
    def __init__(self, config_path="config/config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.ai_reviewer = AIReviewer()
        
        # 创建报告目录
        self.reports_dir = "reports"
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
                
                # 过滤Jenkins提交
                if author.lower() in ['jenkins', 'jenkins-ci', 'ci', 'build']:
                    continue
                
                date_elem = logentry.find('date')
                date_str = date_elem.text if date_elem is not None else ''
                
                msg_elem = logentry.find('msg')
                message = msg_elem.text if msg_elem is not None else ''
                
                # 过滤自动构建相关的提交信息
                if any(keyword in message.lower() for keyword in ['auto build', 'jenkins', 'ci build', '[bot]']):
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
    
    def get_commit_diff(self, revision):
        """获取提交的代码差异"""
        repository_url = self.config['svn']['repository_url']
        username = self.config['svn']['username']
        password = self.config['svn']['password']
        
        try:
            cmd = [
                'svn', 'diff',
                f'{repository_url}',
                f'-c{revision}',
                '--username', username,
                '--password', password,
                '--non-interactive',
                '--trust-server-cert'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding='utf-8', timeout=120)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"获取差异失败: {result.stderr}"
                
        except Exception as e:
            return f"获取差异异常: {e}"
    
    def batch_review(self, commits):
        """批量审查提交"""
        results = []
        total = len(commits)
        
        print(f"开始审查 {total} 个提交...")
        
        for i, commit in enumerate(commits, 1):
            revision = commit['revision']
            print(f"[{i}/{total}] 审查版本 {revision}")
            
            try:
                # 获取代码差异
                diff_content = self.get_commit_diff(revision)
                
                # 创建SVNCommit对象
                commit_date = datetime.fromisoformat(commit['date'].replace('Z', '+00:00')) if commit['date'] else datetime.now()
                svn_commit = SVNCommit(
                    revision=commit['revision'],
                    author=commit['author'],
                    date=commit_date,
                    message=commit['message'],
                    changed_files=[],  # 简化版暂时不获取详细文件信息
                    diff_content=diff_content
                )
                
                # AI审查
                review_result = self.ai_reviewer.review_commit(svn_commit)
                
                result = {
                    'commit': commit,
                    'diff': diff_content,
                    'review': review_result,
                    'reviewed_at': datetime.now().isoformat(),
                    'success': review_result is not None
                }
                
                if review_result:
                    print(f"  ✓ 审查成功")
                else:
                    print(f"  ✗ 审查失败")
                
            except Exception as e:
                print(f"  ✗ 错误: {e}")
                result = {
                    'commit': commit,
                    'diff': '',
                    'review': None,
                    'reviewed_at': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                }
            
            results.append(result)
        
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


def main():
    """主函数"""
    print("=== SVN批量代码审查工具 ===")
    
    # 获取参数
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            days = 7
    else:
        days = 7
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"审查最近 {days} 天的提交")
    print(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    try:
        reviewer = SimpleBatchReviewer()
        
        # 获取提交
        commits = reviewer.get_svn_commits(start_date, end_date)
        
        if not commits:
            print("没有找到提交记录")
            return
        
        # 确认继续
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
