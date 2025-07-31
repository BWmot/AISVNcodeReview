#!/usr/bin/env python3
"""
系统监控脚本
实时监控AI SVN代码审查工具的运行状态
"""

import os
import sys
import time
import json
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 添加父目录到Python路径，以便导入src模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from config_manager import ConfigManager
except ImportError:
    print("❌ 无法导入配置管理器，请检查路径")
    sys.exit(1)

class SystemMonitor:
    """系统监控类"""
    
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        self.log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'code_review.log')
        self.processed_commits_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_commits.json')
        
        try:
            self.config = ConfigManager(self.config_path)
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            sys.exit(1)
    
    def check_process_running(self):
        """检查主进程是否运行"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'python' in cmdline[0] and 'main.py' in ' '.join(cmdline):
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None
    
    def get_system_stats(self):
        """获取系统资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used // (1024 * 1024),
            'memory_total_mb': memory.total // (1024 * 1024),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free // (1024 * 1024 * 1024)
        }
    
    def analyze_log_file(self):
        """分析日志文件"""
        if not os.path.exists(self.log_path):
            return {
                'exists': False,
                'last_activity': None,
                'recent_errors': [],
                'total_lines': 0
            }
        
        stats = {
            'exists': True,
            'last_activity': None,
            'recent_errors': [],
            'total_lines': 0,
            'last_commit_check': None,
            'last_review': None
        }
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                stats['total_lines'] = len(lines)
                
                # 分析最近的活动
                for line in reversed(lines[-100:]):  # 只检查最后100行
                    if not stats['last_activity'] and any(keyword in line for keyword in ['INFO', 'ERROR', 'DEBUG']):
                        try:
                            # 提取时间戳
                            timestamp_str = line.split(' - ')[0]
                            stats['last_activity'] = timestamp_str
                        except:
                            pass
                    
                    if 'ERROR' in line:
                        stats['recent_errors'].append(line.strip())
                        if len(stats['recent_errors']) >= 5:
                            break
                    
                    if '检查SVN提交' in line and not stats['last_commit_check']:
                        try:
                            timestamp_str = line.split(' - ')[0]
                            stats['last_commit_check'] = timestamp_str
                        except:
                            pass
                    
                    if '审查完成' in line and not stats['last_review']:
                        try:
                            timestamp_str = line.split(' - ')[0]
                            stats['last_review'] = timestamp_str
                        except:
                            pass
                        
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def check_processed_commits(self):
        """检查已处理提交记录"""
        if not os.path.exists(self.processed_commits_path):
            return {
                'exists': False,
                'count': 0,
                'last_commit': None
            }
        
        try:
            with open(self.processed_commits_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, list):
                commits = data
            elif isinstance(data, dict) and 'processed_commits' in data:
                commits = data['processed_commits']
            else:
                commits = []
            
            result = {
                'exists': True,
                'count': len(commits),
                'last_commit': None
            }
            
            if commits:
                # 找到最新的提交
                latest_commit = max(commits, key=lambda x: int(x) if isinstance(x, str) and x.isdigit() else 0)
                result['last_commit'] = latest_commit
            
            return result
            
        except Exception as e:
            return {
                'exists': True,
                'error': str(e),
                'count': 0,
                'last_commit': None
            }
    
    def test_svn_connection(self):
        """测试SVN连接"""
        try:
            repo_url = self.config.get('svn.repository_url')
            username = self.config.get('svn.username')
            password = self.config.get('svn.password')
            
            if not all([repo_url, username, password]):
                return {'success': False, 'error': 'SVN配置不完整'}
            
            cmd = [
                'svn', 'info', repo_url,
                '--username', username,
                '--password', password,
                '--non-interactive', '--trust-server-cert'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'SVN连接超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_latest_svn_revision(self):
        """获取最新的SVN版本号"""
        try:
            cmd = [
                'svn', 'info', self.config.get_svn_config()['repository_url'],
                '--username', self.config.get_svn_config()['username'],
                '--password', self.config.get_svn_config()['password'],
                '--non-interactive', '--trust-server-cert'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Revision:'):
                        return int(line.split(':')[1].strip())
            
            return None
            
        except Exception:
            return None
    
    def generate_report(self):
        """生成完整的监控报告"""
        print("=" * 60)
        print(f"AI SVN代码审查工具监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 检查主进程
        is_running, pid = self.check_process_running()
        if is_running:
            print(f"✅ 主进程运行中 (PID: {pid})")
        else:
            print("❌ 主进程未运行")
        
        # 系统资源
        stats = self.get_system_stats()
        print(f"\n📊 系统资源:")
        print(f"   CPU使用率: {stats['cpu_percent']:.1f}%")
        print(f"   内存使用率: {stats['memory_percent']:.1f}% ({stats['memory_used_mb']}MB/{stats['memory_total_mb']}MB)")
        print(f"   磁盘使用率: {stats['disk_percent']:.1f}% (剩余 {stats['disk_free_gb']}GB)")
        
        # 日志分析
        log_stats = self.analyze_log_file()
        print(f"\n📝 日志状态:")
        if log_stats['exists']:
            print(f"   日志行数: {log_stats['total_lines']}")
            if log_stats['last_activity']:
                print(f"   最后活动: {log_stats['last_activity']}")
            if log_stats['last_commit_check']:
                print(f"   最后检查提交: {log_stats['last_commit_check']}")
            if log_stats['last_review']:
                print(f"   最后审查: {log_stats['last_review']}")
            
            if log_stats['recent_errors']:
                print(f"   ⚠️  最近错误 ({len(log_stats['recent_errors'])}条):")
                for error in log_stats['recent_errors'][-3:]:
                    print(f"     {error[:80]}...")
        else:
            print("   ❌ 日志文件不存在")
        
        # 已处理提交
        commit_stats = self.check_processed_commits()
        print(f"\n🗃️  提交记录:")
        if commit_stats['exists']:
            print(f"   已处理提交数: {commit_stats['count']}")
            if commit_stats['last_commit']:
                print(f"   最后处理版本: {commit_stats['last_commit']}")
            if 'error' in commit_stats:
                print(f"   ⚠️  读取错误: {commit_stats['error']}")
        else:
            print("   ❌ 提交记录文件不存在")
        
        # SVN连接测试
        svn_result = self.test_svn_connection()
        print(f"\n🔗 SVN连接:")
        if svn_result['success']:
            print("   ✅ SVN连接正常")
            latest_rev = self.get_latest_svn_revision()
            if latest_rev:
                print(f"   最新版本号: {latest_rev}")
        else:
            print(f"   ❌ SVN连接失败: {svn_result['error']}")
        
        # 配置检查
        print("\n⚙️  配置检查:")
        try:
            repo_url = self.config.get('svn.repository_url')
            monitored_paths = self.config.get('svn.monitored_paths', [])
            check_interval = self.config.get('svn.check_interval', 300)
            ai_model = self.config.get('ai.model')
            webhook_url = self.config.get('dingtalk.webhook_url')
            
            print(f"   SVN仓库: {repo_url}")
            print(f"   监控路径: {len(monitored_paths)}个")
            print(f"   检查间隔: {check_interval}秒")
            print(f"   AI模型: {ai_model}")
            print(f"   钉钉webhook: {'已配置' if webhook_url else '未配置'}")
            
        except Exception as e:
            print(f"   ❌ 配置读取错误: {e}")
        
        print("=" * 60)
    
    def monitor_continuously(self, interval=60):
        """持续监控模式"""
        print(f"开始持续监控，每{interval}秒更新一次...")
        print("按 Ctrl+C 停止监控")
        
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')  # 清屏
                self.generate_report()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n监控已停止")

def main():
    """主函数"""
    monitor = SystemMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        monitor.monitor_continuously(interval)
    else:
        monitor.generate_report()

if __name__ == "__main__":
    main()
