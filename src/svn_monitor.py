"""
SVN监控模块
负责监控SVN提交记录，获取代码变更信息
"""

import subprocess
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from pathlib import Path

from config_manager import config


@dataclass
class SVNCommit:
    """SVN提交信息数据类"""
    revision: str
    author: str
    date: datetime
    message: str
    changed_files: List[Dict[str, str]]
    diff_content: str = ""


class SVNMonitor:
    def __init__(self):
        self.repo_url = config.get('svn.repository_url')
        self.username = config.get('svn.username')
        self.password = config.get('svn.password')
        self.monitored_paths = config.get('svn.monitored_paths', [])
        self.processed_commits_file = config.get('data.processed_commits_file')
        self.logger = logging.getLogger(__name__)
        
        # 加载已处理的提交记录
        self.processed_commits = self._load_processed_commits()
    
    def _load_processed_commits(self) -> set:
        """加载已处理的提交记录"""
        try:
            if Path(self.processed_commits_file).exists():
                with open(self.processed_commits_file, 'r') as f:
                    data = json.load(f)
                    
                    # 兼容多种格式
                    if isinstance(data, dict):
                        # 新格式 {"processed_commits": [...]}
                        if 'processed_commits' in data:
                            return set(str(item) for item in data['processed_commits'])
                        # 旧格式 {"123": {...}, "124": {...}}
                        else:
                            return set(data.keys())
                    elif isinstance(data, list):
                        # 数组格式 [123, 124, ...]
                        return set(str(item) for item in data)
                    else:
                        self.logger.warning(f"未知的提交记录格式: {type(data)}")
                        return set()
        except Exception as e:
            self.logger.warning(f"加载已处理提交记录失败: {e}")
        return set()
    
    def _save_processed_commits(self):
        """保存已处理的提交记录"""
        try:
            Path(self.processed_commits_file).parent.mkdir(parents=True, 
                                                           exist_ok=True)
            with open(self.processed_commits_file, 'w') as f:
                # 统一使用数组格式，便于维护
                commit_list = [int(rev) if rev.isdigit() else rev 
                              for rev in self.processed_commits]
                json.dump(sorted(commit_list), f, indent=2)
        except Exception as e:
            self.logger.error(f"保存已处理提交记录失败: {e}")
    
    def _run_svn_command(self, command: List[str]) -> str:
        """执行SVN命令"""
        try:
            # 添加认证参数
            full_command = ['svn'] + command
            if self.username:
                full_command.extend(['--username', self.username])
            if self.password:
                full_command.extend(['--password', self.password])
            full_command.append('--non-interactive')
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.error(f"SVN命令执行失败: {result.stderr}")
                return ""
            
            return result.stdout
        except subprocess.TimeoutExpired:
            self.logger.error("SVN命令执行超时")
            return ""
        except Exception as e:
            self.logger.error(f"执行SVN命令时发生异常: {e}")
            return ""
    
    def get_latest_commits(self, limit: int = 10) -> List[SVNCommit]:
        """获取最新的SVN提交记录"""
        commits = []
        
        # 获取最新的提交日志
        command = ['log', self.repo_url, '--xml', f'--limit={limit}']
        output = self._run_svn_command(command)
        
        if not output:
            return commits
        
        try:
            root = ET.fromstring(output)
            for logentry in root.findall('logentry'):
                revision = logentry.get('revision')
                
                # 跳过已处理的提交（支持字符串和数字比较）
                if (revision in self.processed_commits or 
                    int(revision) in self.processed_commits):
                    continue
                
                author = logentry.find('author').text if logentry.find('author') is not None else "unknown"
                date_str = logentry.find('date').text if logentry.find('date') is not None else ""
                message = logentry.find('msg').text if logentry.find('msg') is not None else ""
                
                # 解析日期
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    date = datetime.now()
                
                # 获取变更的文件列表
                changed_files = self._get_changed_files(revision)
                
                # 过滤监控路径
                if self.monitored_paths:
                    filtered_files = []
                    for file_info in changed_files:
                        file_path = file_info['path']
                        if any(file_path.startswith(path) for path in self.monitored_paths):
                            filtered_files.append(file_info)
                    changed_files = filtered_files
                
                # 如果没有相关文件变更，跳过
                if not changed_files:
                    continue
                
                # 获取diff内容
                diff_content = self._get_commit_diff(revision)
                
                commit = SVNCommit(
                    revision=revision,
                    author=author,
                    date=date,
                    message=message,
                    changed_files=changed_files,
                    diff_content=diff_content
                )
                
                commits.append(commit)
                
        except ET.ParseError as e:
            self.logger.error(f"解析SVN日志XML失败: {e}")
        
        return commits
    
    def _get_changed_files(self, revision: str) -> List[Dict[str, str]]:
        """获取指定版本的变更文件列表"""
        command = ['log', self.repo_url, f'-r{revision}', '--xml', '--verbose']
        output = self._run_svn_command(command)
        
        changed_files = []
        if not output:
            return changed_files
        
        try:
            root = ET.fromstring(output)
            logentry = root.find('logentry')
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
        except ET.ParseError as e:
            self.logger.error(f"解析变更文件列表失败: {e}")
        
        return changed_files
    
    def _get_commit_diff(self, revision: str) -> str:
        """获取指定版本的diff内容"""
        prev_revision = str(int(revision) - 1)
        command = ['diff', self.repo_url, f'-r{prev_revision}:{revision}']
        
        diff_output = self._run_svn_command(command)
        return diff_output
    
    def mark_commit_processed(self, revision: str):
        """标记提交为已处理"""
        self.processed_commits.add(revision)
        self._save_processed_commits()
    
    def check_new_commits(self) -> List[SVNCommit]:
        """检查是否有新的提交"""
        self.logger.info("检查新的SVN提交...")
        commits = self.get_latest_commits()
        
        if commits:
            self.logger.info(f"发现 {len(commits)} 个新提交")
        else:
            self.logger.debug("没有发现新提交")
        
        return commits
