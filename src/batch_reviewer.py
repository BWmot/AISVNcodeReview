#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量代码审查模块
支持指定日期范围和路径的批量SVN提交审查，生成详细报告
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import subprocess
import xml.etree.ElementTree as ET
import time

from config_manager import ConfigManager
from ai_reviewer import AIReviewer


class BatchReviewer:
    """批量代码审查器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化批量审查器"""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.ai_reviewer = AIReviewer(config_path)
        
        # 批量审查配置
        self.batch_config = self.config.get('batch_review', {})
        self.reports_dir = self.batch_config.get('reports_dir', 'reports')
        self.report_format = self.batch_config.get('report_format', 'html')
        
        # 确保报告目录存在
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
    def get_commits_by_date_range(self, start_date: datetime,
                                  end_date: datetime,
                                  paths: Optional[List[str]] = None
                                  ) -> List[Dict[str, Any]]:
        """获取指定日期范围内的提交记录

        Args:
            start_date: 开始日期
            end_date: 结束日期
            paths: 监控路径列表，如果为None则使用配置中的路径

        Returns:
            提交记录列表
        """
        if paths is None:
            paths = self.batch_config.get(
                'default_paths',
                self.config['svn']['monitored_paths']
            )
        
        repository_url = self.config['svn']['repository_url']
        username = self.config['svn']['username']
        password = self.config['svn']['password']
        
        commits = []
        
        # 格式化日期为SVN可识别的格式
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        self.logger.info(f"获取日期范围 {start_str} 到 {end_str} 的提交记录")
        
        for path in paths:
            try:
                # 构建SVN log命令
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
                
                self.logger.debug(f"执行SVN命令: {' '.join(cmd[:6])}...")  # 隐藏密码
                
                # 执行SVN命令
                result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    encoding='utf-8', timeout=300
                )

                if result.returncode != 0:
                    self.logger.warning(
                        f"SVN log失败 (路径: {path}): {result.stderr}"
                    )
                    continue
                
                # 解析XML结果
                path_commits = self._parse_svn_log_xml(result.stdout, path)
                commits.extend(path_commits)
                
            except subprocess.TimeoutExpired:
                self.logger.error(f"SVN log超时 (路径: {path})")
            except Exception as e:
                self.logger.error(f"获取提交记录失败 (路径: {path}): {e}")
        
        # 按版本号排序并去重
        unique_commits = {}
        for commit in commits:
            revision = commit['revision']
            if revision not in unique_commits:
                unique_commits[revision] = commit

        sorted_commits = sorted(
            unique_commits.values(),
            key=lambda x: int(x['revision'])
        )

        self.logger.info(f"总共找到 {len(sorted_commits)} 个唯一提交")
        return sorted_commits

    def _parse_svn_log_xml(self, xml_content: str,
                           path: str) -> List[Dict[str, Any]]:
        """解析SVN log的XML输出"""
        commits = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for logentry in root.findall('logentry'):
                revision = logentry.get('revision')
                
                # 获取作者
                author_elem = logentry.find('author')
                author = (author_elem.text if author_elem is not None
                          else 'unknown')
                
                # 获取日期
                date_elem = logentry.find('date')
                date_str = date_elem.text if date_elem is not None else ''
                
                # 获取提交消息
                msg_elem = logentry.find('msg')
                message = msg_elem.text if msg_elem is not None else ''
                
                # 获取修改的路径
                paths_elem = logentry.find('paths')
                changed_paths = []
                if paths_elem is not None:
                    for path_elem in paths_elem.findall('path'):
                        changed_paths.append({
                            'action': path_elem.get('action', ''),
                            'path': path_elem.text or ''
                        })
                
                commit_info = {
                    'revision': revision,
                    'author': author,
                    'date': date_str,
                    'message': message,
                    'changed_paths': changed_paths,
                    'monitored_path': path
                }
                
                commits.append(commit_info)
                
        except ET.ParseError as e:
            self.logger.error(f"解析SVN XML失败: {e}")
        
        return commits
    
    def get_commit_diff(self, revision: str) -> str:
        """获取指定版本的代码差异"""
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
            
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding='utf-8', timeout=120
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.warning(f"获取版本 {revision} 差异失败: {result.stderr}")
                return f"获取差异失败: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"获取版本 {revision} 差异超时")
            return "获取差异超时"
        except Exception as e:
            self.logger.error(f"获取版本 {revision} 差异异常: {e}")
            return f"获取差异异常: {e}"
    
    def batch_review_commits(self, commits: List[Dict[str, Any]],
                             progress_callback: Optional[callable] = None
                             ) -> List[Dict[str, Any]]:
        """批量审查提交记录

        Args:
            commits: 提交记录列表
            progress_callback: 进度回调函数

        Returns:
            审查结果列表
        """
        results = []
        ai_settings = self.batch_config.get('ai_settings', {})
        batch_size = ai_settings.get('batch_size', 5)
        delay = ai_settings.get('delay_between_batches', 2)
        
        self.logger.info(f"开始批量审查 {len(commits)} 个提交")
        
        for i, commit in enumerate(commits):
            try:
                revision = commit['revision']
                
                # 更新进度
                if progress_callback:
                    progress_callback(i + 1, len(commits), revision)
                
                self.logger.info(f"审查版本 {revision} ({i+1}/{len(commits)})")
                
                # 获取代码差异
                diff_content = self.get_commit_diff(revision)
                
                # 进行AI审查
                review_result = self.ai_reviewer.review_code(
                    commit['author'],
                    commit['message'],
                    diff_content,
                    revision
                )
                
                # 组装结果
                result = {
                    'commit': commit,
                    'diff': diff_content,
                    'review': review_result,
                    'reviewed_at': datetime.now().isoformat(),
                    'review_success': review_result is not None
                }
                
                results.append(result)
                
                # 批次延迟
                if (i + 1) % batch_size == 0 and i < len(commits) - 1:
                    self.logger.info(f"批次完成，等待 {delay} 秒...")
                    time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"审查版本 {commit['revision']} 失败: {e}")
                
                # 添加失败记录
                result = {
                    'commit': commit,
                    'diff': '',
                    'review': None,
                    'reviewed_at': datetime.now().isoformat(),
                    'review_success': False,
                    'error': str(e)
                }
                results.append(result)
        
        success_count = sum(1 for r in results if r['review_success'])
        failed_count = sum(1 for r in results if not r['review_success'])
        self.logger.info(f"批量审查完成，成功: {success_count}, 失败: {failed_count}")

        return results

    def generate_report(self, review_results: List[Dict[str, Any]],
                        start_date: datetime, end_date: datetime,
                        paths: List[str]) -> str:
        """生成审查报告

        Args:
            review_results: 审查结果列表
            start_date: 开始日期
            end_date: 结束日期
            paths: 审查路径列表

        Returns:
            报告文件路径
        """
        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        date_range = f"{start_str}-{end_str}"
        
        if self.report_format == 'html':
            filename = f"code_review_report_{date_range}_{timestamp}.html"
            report_path = os.path.join(self.reports_dir, filename)
            self._generate_html_report(review_results, start_date, end_date, paths, report_path)
        elif self.report_format == 'markdown':
            filename = f"code_review_report_{date_range}_{timestamp}.md"
            report_path = os.path.join(self.reports_dir, filename)
            self._generate_markdown_report(review_results, start_date, end_date, paths, report_path)
        else:  # json
            filename = f"code_review_report_{date_range}_{timestamp}.json"
            report_path = os.path.join(self.reports_dir, filename)
            self._generate_json_report(review_results, start_date, end_date, paths, report_path)
        
        self.logger.info(f"报告已生成: {report_path}")
        return report_path
    
    def _generate_html_report(self, results: List[Dict[str, Any]], 
                             start_date: datetime, end_date: datetime,
                             paths: List[str], output_path: str):
        """生成HTML格式报告"""
        # 计算统计数据
        stats = self._calculate_statistics(results)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVN代码审查报告 - {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #333; }}
        .header {{ text-align: center; border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #007acc; }}
        .commit {{ border: 1px solid #ddd; margin: 20px 0; border-radius: 6px; }}
        .commit-header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
        .commit-content {{ padding: 15px; }}
        .diff {{ background: #f8f8f8; padding: 10px; border-radius: 4px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 12px; max-height: 300px; }}
        .review {{ background: #e8f4f8; padding: 15px; border-radius: 4px; margin-top: 10px; }}
        .success {{ border-left: 4px solid #28a745; }}
        .error {{ border-left: 4px solid #dc3545; }}
        .meta {{ color: #666; font-size: 0.9em; }}
        .path-list {{ background: #f8f9fa; padding: 10px; border-radius: 4px; }}
        .toc {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .toc ul {{ margin: 0; padding-left: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 SVN代码审查报告</h1>
            <p><strong>审查期间:</strong> {start_date.strftime('%Y年%m月%d日')} 至 {end_date.strftime('%Y年%m月%d日')}</p>
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
        
        <div class="path-list">
            <h3>📁 审查路径</h3>
            <ul>
                {''.join(f'<li>{path}</li>' for path in paths)}
            </ul>
        </div>
        
        <h2>📊 审查统计</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{stats['total_commits']}</div>
                <div>总提交数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['successful_reviews']}</div>
                <div>成功审查</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['failed_reviews']}</div>
                <div>审查失败</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['unique_authors']}</div>
                <div>参与开发者</div>
            </div>
        </div>
        
        <div class="toc">
            <h3>📋 目录</h3>
            <ul>
                <li><a href="#summary">审查总结</a></li>
                <li><a href="#details">详细审查内容</a></li>
            </ul>
        </div>
        
        <h2 id="summary">📝 审查总结</h2>
        {self._generate_summary_html(results)}
        
        <h2 id="details">📋 详细审查内容</h2>
        {self._generate_details_html(results)}
        
        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 0.9em;">
            <p>由 AI SVN代码审查工具 自动生成</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_summary_html(self, results: List[Dict[str, Any]]) -> str:
        """生成HTML总结部分"""
        successful_results = [r for r in results if r['review_success'] and r['review']]
        
        if not successful_results:
            return "<p>没有成功的审查结果可供总结。</p>"
        
        # 分析常见问题和建议
        all_issues = []
        all_suggestions = []
        
        for result in successful_results:
            review = result['review']
            if 'issues' in review:
                all_issues.extend(review['issues'])
            if 'suggestions' in review:
                all_suggestions.extend(review['suggestions'])
        
        summary_html = f"""
        <div class="review">
            <h3>🎯 主要发现</h3>
            <p><strong>代码质量概览:</strong></p>
            <ul>
                <li>共审查了 {len(results)} 个提交</li>
                <li>发现了 {len(all_issues)} 个潜在问题</li>
                <li>提供了 {len(all_suggestions)} 条改进建议</li>
            </ul>
            
            <h4>🔍 常见问题类型</h4>
            <ul>
                {self._get_common_issues_html(all_issues)}
            </ul>
            
            <h4>💡 主要建议</h4>
            <ul>
                {self._get_main_suggestions_html(all_suggestions)}
            </ul>
        </div>
        """
        
        return summary_html
    
    def _get_common_issues_html(self, issues: List[str]) -> str:
        """获取常见问题的HTML"""
        if not issues:
            return "<li>未发现明显问题</li>"
        
        # 简单的问题分类（可以根据需要扩展）
        issue_keywords = {
            "安全": ["密码", "token", "key", "secret", "安全"],
            "性能": ["性能", "效率", "优化", "缓存"],
            "代码规范": ["命名", "格式", "规范", "风格"],
            "逻辑": ["逻辑", "条件", "循环", "判断"]
        }
        
        categorized = {category: 0 for category in issue_keywords}
        
        for issue in issues:
            for category, keywords in issue_keywords.items():
                if any(keyword in issue for keyword in keywords):
                    categorized[category] += 1
                    break
        
        html_items = []
        for category, count in categorized.items():
            if count > 0:
                html_items.append(f"<li>{category}相关问题: {count} 个</li>")
        
        return "".join(html_items) if html_items else "<li>问题类型分析中...</li>"
    
    def _get_main_suggestions_html(self, suggestions: List[str]) -> str:
        """获取主要建议的HTML"""
        if not suggestions:
            return "<li>暂无具体建议</li>"
        
        # 取前5个建议作为主要建议
        main_suggestions = suggestions[:5]
        return "".join(f"<li>{suggestion}</li>" for suggestion in main_suggestions)
    
    def _generate_details_html(self, results: List[Dict[str, Any]]) -> str:
        """生成HTML详细内容部分"""
        details_html = ""
        
        for i, result in enumerate(results, 1):
            commit = result['commit']
            review = result['review']
            success = result['review_success']
            
            status_class = "success" if success else "error"
            status_icon = "✅" if success else "❌"
            
            # 处理差异内容
            diff_content = result.get('diff', '').strip()
            if len(diff_content) > 2000:  # 限制显示长度
                diff_content = diff_content[:2000] + "\n... (内容过长，已截断)"
            
            details_html += f"""
            <div class="commit {status_class}">
                <div class="commit-header">
                    <h3>{status_icon} 版本 {commit['revision']} - {commit['author']}</h3>
                    <div class="meta">
                        <strong>时间:</strong> {commit['date']}<br>
                        <strong>消息:</strong> {commit['message']}<br>
                        <strong>路径:</strong> {commit.get('monitored_path', 'N/A')}
                    </div>
                </div>
                <div class="commit-content">
            """
            
            if success and review:
                details_html += f"""
                    <div class="review">
                        <h4>🤖 AI审查结果</h4>
                        <p><strong>总体评价:</strong> {review.get('summary', '无总结')}</p>
                        
                        <h5>🔍 发现的问题:</h5>
                        <ul>
                            {self._format_list_items(review.get('issues', []))}
                        </ul>
                        
                        <h5>💡 改进建议:</h5>
                        <ul>
                            {self._format_list_items(review.get('suggestions', []))}
                        </ul>
                    </div>
                """
            else:
                error_msg = result.get('error', '审查失败')
                details_html += f"""
                    <div class="review error">
                        <h4>❌ 审查失败</h4>
                        <p>错误信息: {error_msg}</p>
                    </div>
                """
            
            # 添加代码差异（如果配置允许）
            if (self.batch_config.get('include_code_diff', True) and 
                diff_content and diff_content != '获取差异失败'):
                details_html += f"""
                    <h4>📝 代码变更</h4>
                    <div class="diff">{self._escape_html(diff_content)}</div>
                """
            
            details_html += """
                </div>
            </div>
            """
        
        return details_html
    
    def _format_list_items(self, items: List[str]) -> str:
        """格式化列表项为HTML"""
        if not items:
            return "<li>无</li>"
        return "".join(f"<li>{self._escape_html(item)}</li>" for item in items)
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _generate_markdown_report(self, results: List[Dict[str, Any]], 
                                 start_date: datetime, end_date: datetime,
                                 paths: List[str], output_path: str):
        """生成Markdown格式报告"""
        # 计算统计数据
        stats = self._calculate_statistics(results)
        
        md_content = f"""# 🔍 SVN代码审查报告

**审查期间:** {start_date.strftime('%Y年%m月%d日')} 至 {end_date.strftime('%Y年%m月%d日')}
**生成时间:** {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

## 📁 审查路径

{chr(10).join(f'- {path}' for path in paths)}

## 📊 审查统计

| 指标 | 数量 |
|------|------|
| 总提交数 | {stats['total_commits']} |
| 成功审查 | {stats['successful_reviews']} |
| 审查失败 | {stats['failed_reviews']} |
| 参与开发者 | {stats['unique_authors']} |

## 📝 审查总结

{self._generate_summary_markdown(results)}

## 📋 详细审查内容

{self._generate_details_markdown(results)}

---
*由 AI SVN代码审查工具 自动生成*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _generate_summary_markdown(self, results: List[Dict[str, Any]]) -> str:
        """生成Markdown总结部分"""
        successful_results = [r for r in results if r['review_success'] and r['review']]
        
        if not successful_results:
            return "没有成功的审查结果可供总结。"
        
        return f"""
### 🎯 主要发现

- 共审查了 {len(results)} 个提交
- 审查成功率: {len(successful_results)/len(results)*100:.1f}%

### 💡 总体建议

基于本次审查结果，建议团队关注代码质量和最佳实践的遵循。
"""
    
    def _generate_details_markdown(self, results: List[Dict[str, Any]]) -> str:
        """生成Markdown详细内容部分"""
        details_md = ""
        
        for result in results:
            commit = result['commit']
            review = result['review']
            success = result['review_success']
            
            status_icon = "✅" if success else "❌"
            
            details_md += f"""
### {status_icon} 版本 {commit['revision']} - {commit['author']}

**时间:** {commit['date']}
**消息:** {commit['message']}
**路径:** {commit.get('monitored_path', 'N/A')}

"""
            
            if success and review:
                details_md += f"""
**🤖 AI审查结果:**

**总体评价:** {review.get('summary', '无总结')}

**🔍 发现的问题:**
{self._format_markdown_list(review.get('issues', []))}

**💡 改进建议:**
{self._format_markdown_list(review.get('suggestions', []))}

"""
            else:
                error_msg = result.get('error', '审查失败')
                details_md += f"**❌ 审查失败:** {error_msg}\n\n"
        
        return details_md
    
    def _format_markdown_list(self, items: List[str]) -> str:
        """格式化列表项为Markdown"""
        if not items:
            return "- 无\n"
        return "\n".join(f"- {item}" for item in items) + "\n"
    
    def _generate_json_report(self, results: List[Dict[str, Any]], 
                             start_date: datetime, end_date: datetime,
                             paths: List[str], output_path: str):
        """生成JSON格式报告"""
        stats = self._calculate_statistics(results)
        
        report_data = {
            'metadata': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'paths': paths,
                'report_format': 'json'
            },
            'statistics': stats,
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计数据"""
        total = len(results)
        successful = sum(1 for r in results if r['review_success'])
        failed = total - successful
        
        authors = set()
        for result in results:
            authors.add(result['commit']['author'])
        
        return {
            'total_commits': total,
            'successful_reviews': successful,
            'failed_reviews': failed,
            'success_rate': round(successful / total * 100, 1) if total > 0 else 0,
            'unique_authors': len(authors),
            'authors_list': list(authors)
        }


def print_progress(current: int, total: int, revision: str):
    """打印进度信息"""
    percentage = (current / total) * 100
    print(f"进度: {current}/{total} ({percentage:.1f}%) - 正在审查版本 {revision}")


if __name__ == "__main__":
    # 示例用法
    reviewer = BatchReviewer()
    
    # 设置日期范围（最近7天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"开始批量代码审查: {start_date.date()} 至 {end_date.date()}")
    
    # 获取提交记录
    commits = reviewer.get_commits_by_date_range(start_date, end_date)
    print(f"找到 {len(commits)} 个提交")
    
    if commits:
        # 批量审查
        results = reviewer.batch_review_commits(commits, print_progress)
        
        # 生成报告
        report_path = reviewer.generate_report(results, start_date, end_date, 
                                             reviewer.batch_config.get('default_paths', []))
        print(f"报告已生成: {report_path}")
    else:
        print("没有找到提交记录")
