#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大型提交审查问题诊断工具
用于分析和解决审查结果不完整的问题
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_path = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_path)

from config_manager import ConfigManager


class CommitAnalyzer:
    """提交分析器"""
    
    def __init__(self):
        self.config = ConfigManager()
        
    def analyze_commit_size(self, revision):
        """分析指定提交的大小和复杂度"""
        print(f"\n🔍 分析提交 {revision} 的详细信息...")
        
        # 获取diff内容
        diff_content = self._get_commit_diff(revision)
        
        if not diff_content or diff_content.startswith("获取差异失败"):
            print(f"❌ 无法获取提交 {revision} 的差异内容")
            return None
        
        # 分析diff内容
        analysis = self._analyze_diff_content(diff_content)
        
        # 获取文件列表
        changed_files = self._get_changed_files(revision)
        
        # 输出分析结果
        print(f"\n📊 提交 {revision} 分析结果:")
        print(f"{'='*50}")
        print(f"📝 总字符数: {analysis['total_chars']:,}")
        print(f"📄 总行数: {analysis['total_lines']:,}")
        print(f"➕ 新增行数: {analysis['added_lines']:,}")
        print(f"➖ 删除行数: {analysis['deleted_lines']:,}")
        print(f"📁 修改文件数: {len(changed_files)}")
        print(f"🔢 当前截断长度: 8000 字符")
        print(f"💔 截断丢失率: {((analysis['total_chars'] - 8000) / analysis['total_chars'] * 100):.1f}%" 
              if analysis['total_chars'] > 8000 else "0%")
        
        # 按文件类型分析
        file_types = {}
        for file_info in changed_files:
            path = file_info.get('path', '')
            ext = os.path.splitext(path)[1].lower()
            if not ext:
                ext = '(无扩展名)'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print(f"\n📁 修改文件类型分布:")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ext}: {count} 个文件")
        
        # 建议配置
        print(f"\n💡 建议配置:")
        if analysis['total_chars'] > 8000:
            suggested_limit = min(analysis['total_chars'] + 5000, 50000)
            print(f"  📏 建议diff截断长度: {suggested_limit:,} 字符")
        else:
            print(f"  ✅ 当前截断长度已足够")
        
        # Token估算
        estimated_tokens = analysis['total_chars'] // 3  # 粗略估算
        if estimated_tokens > 2000:
            suggested_max_tokens = min(estimated_tokens + 1000, 8000)
            print(f"  🎯 建议max_tokens: {suggested_max_tokens}")
        else:
            print(f"  ✅ 当前max_tokens已足够")
        
        return analysis
    
    def _get_commit_diff(self, revision):
        """获取提交的完整diff内容"""
        import subprocess
        
        repository_url = self.config.config['svn']['repository_url']
        username = self.config.config['svn']['username'] 
        password = self.config.config['svn']['password']
        
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
                                  encoding='utf-8', timeout=180)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"获取差异失败: {result.stderr}"
                
        except Exception as e:
            return f"获取差异异常: {e}"
    
    def _get_changed_files(self, revision):
        """获取指定版本的变更文件列表"""
        import subprocess
        import xml.etree.ElementTree as ET
        
        repository_url = self.config.config['svn']['repository_url']
        username = self.config.config['svn']['username']
        password = self.config.config['svn']['password']
        
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
                
                return changed_files
            else:
                print(f"获取文件列表失败: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"获取文件列表异常: {e}")
            return []
    
    def _analyze_diff_content(self, diff_content):
        """分析diff内容的统计信息"""
        lines = diff_content.split('\n')
        total_lines = len(lines)
        total_chars = len(diff_content)
        
        added_lines = 0
        deleted_lines = 0
        
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines += 1
            elif line.startswith('-') and not line.startswith('---'):
                deleted_lines += 1
        
        return {
            'total_chars': total_chars,
            'total_lines': total_lines,
            'added_lines': added_lines,
            'deleted_lines': deleted_lines
        }
    
    def suggest_optimizations(self, revision_list):
        """对多个提交分析并提供优化建议"""
        print(f"\n🎯 分析 {len(revision_list)} 个提交，生成优化建议...")
        
        total_analysis = {
            'total_commits': len(revision_list),
            'large_commits': 0,  # 超过8000字符的提交
            'max_chars': 0,
            'avg_chars': 0,
            'max_tokens_needed': 2000,
            'diff_limit_needed': 8000
        }
        
        char_counts = []
        
        for revision in revision_list:
            analysis = self.analyze_commit_size(revision)
            if analysis:
                chars = analysis['total_chars']
                char_counts.append(chars)
                
                if chars > total_analysis['max_chars']:
                    total_analysis['max_chars'] = chars
                
                if chars > 8000:
                    total_analysis['large_commits'] += 1
        
        if char_counts:
            total_analysis['avg_chars'] = sum(char_counts) // len(char_counts)
        
        # 计算建议值
        if total_analysis['max_chars'] > 8000:
            total_analysis['diff_limit_needed'] = min(
                total_analysis['max_chars'] + 10000, 
                100000  # 最大限制
            )
        
        estimated_max_tokens = total_analysis['max_chars'] // 3
        if estimated_max_tokens > 2000:
            total_analysis['max_tokens_needed'] = min(
                estimated_max_tokens + 2000,
                16000  # 最大限制
            )
        
        # 输出总体建议
        print(f"\n🎯 总体优化建议:")
        print(f"{'='*50}")
        print(f"📊 分析了 {total_analysis['total_commits']} 个提交")
        print(f"🔥 大型提交数量: {total_analysis['large_commits']} 个 "
              f"({total_analysis['large_commits']/total_analysis['total_commits']*100:.1f}%)")
        print(f"📏 最大字符数: {total_analysis['max_chars']:,}")
        print(f"📊 平均字符数: {total_analysis['avg_chars']:,}")
        
        print(f"\n⚙️  建议配置更新:")
        print(f"  ai.diff_limit: {total_analysis['diff_limit_needed']:,}  # 当前: 8000")
        print(f"  ai.max_tokens: {total_analysis['max_tokens_needed']}  # 当前: 2000")
        
        if total_analysis['large_commits'] > 0:
            print(f"\n⚠️  警告: 发现 {total_analysis['large_commits']} 个大型提交")
            print(f"   这些提交的内容可能被截断，影响审查质量！")
        
        return total_analysis


def main():
    parser = argparse.ArgumentParser(description='大型提交审查问题诊断工具')
    parser.add_argument('revisions', nargs='+', help='要分析的提交版本号')
    parser.add_argument('--suggest', action='store_true', 
                       help='生成优化建议')
    
    args = parser.parse_args()
    
    analyzer = CommitAnalyzer()
    
    if args.suggest:
        analyzer.suggest_optimizations(args.revisions)
    else:
        for revision in args.revisions:
            analyzer.analyze_commit_size(revision)


if __name__ == '__main__':
    main()
