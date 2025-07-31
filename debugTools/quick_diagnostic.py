#!/usr/bin/env python3
"""
快速诊断工具
一键检测和修复AI SVN代码审查工具的常见问题
"""

import os
import sys
import json
import subprocess
import yaml
import shutil
from datetime import datetime

class QuickDiagnostic:
    """快速诊断类"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.config_path = os.path.join(self.base_dir, 'config', 'config.yaml')
        self.requirements_path = os.path.join(self.base_dir, 'requirements.txt')
        self.processed_commits_path = os.path.join(self.base_dir, 'data', 'processed_commits.json')
        
        self.issues = []
        self.fixes_applied = []
    
    def log_issue(self, issue, severity="WARNING"):
        """记录发现的问题"""
        self.issues.append({
            'severity': severity,
            'issue': issue,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{'❌' if severity == 'ERROR' else '⚠️'} {issue}")
    
    def log_fix(self, fix):
        """记录应用的修复"""
        self.fixes_applied.append({
            'fix': fix,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✅ {fix}")
    
    def check_python_version(self):
        """检查Python版本"""
        print("\n🐍 检查Python版本...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.log_issue(f"Python版本过低: {version.major}.{version.minor}, 需要 >= 3.7", "ERROR")
            return False
        else:
            print(f"✅ Python版本正常: {version.major}.{version.minor}.{version.micro}")
            return True
    
    def check_dependencies(self):
        """检查依赖包"""
        print("\n📦 检查依赖包...")
        
        if not os.path.exists(self.requirements_path):
            self.log_issue("requirements.txt 文件不存在", "ERROR")
            return False
        
        # 检查必需的包
        required_packages = ['requests', 'pyyaml', 'schedule']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"✅ {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                self.log_issue(f"缺少依赖包: {package}")
        
        if missing_packages:
            print(f"\n🔧 尝试安装缺少的包...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, 
                             check=True, capture_output=True)
                self.log_fix(f"已安装依赖包: {', '.join(missing_packages)}")
                return True
            except subprocess.CalledProcessError as e:
                self.log_issue(f"依赖包安装失败: {e}", "ERROR")
                return False
        
        return True
    
    def check_config_file(self):
        """检查配置文件"""
        print("\n⚙️ 检查配置文件...")
        
        if not os.path.exists(self.config_path):
            self.log_issue("config.yaml 文件不存在", "ERROR")
            
            # 尝试从示例配置复制
            example_config = os.path.join(self.base_dir, 'config', 'config.example.yaml')
            if os.path.exists(example_config):
                try:
                    shutil.copy2(example_config, self.config_path)
                    self.log_fix("已从示例配置创建 config.yaml，请手动配置")
                except Exception as e:
                    self.log_issue(f"无法复制示例配置: {e}", "ERROR")
            return False
        
        # 检查配置文件格式
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查必需的配置项
            required_sections = ['svn', 'ai', 'dingtalk']
            for section in required_sections:
                if section not in config:
                    self.log_issue(f"配置缺少 {section} 部分")
                else:
                    print(f"✅ {section} 配置存在")
            
            # 检查SVN配置
            if 'svn' in config:
                svn_config = config['svn']
                required_svn_keys = ['repository_url', 'username', 'password', 'monitored_paths']
                for key in required_svn_keys:
                    if key not in svn_config:
                        self.log_issue(f"SVN配置缺少 {key}")
                    elif not svn_config[key]:
                        self.log_issue(f"SVN配置 {key} 为空")
            
            return True
            
        except yaml.YAMLError as e:
            self.log_issue(f"配置文件格式错误: {e}", "ERROR")
            return False
        except Exception as e:
            self.log_issue(f"读取配置文件失败: {e}", "ERROR")
            return False
    
    def check_svn_command(self):
        """检查SVN命令"""
        print("\n🔗 检查SVN命令...")
        
        try:
            result = subprocess.run(['svn', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✅ SVN可用: {version_line}")
                return True
            else:
                self.log_issue("SVN命令执行失败", "ERROR")
                return False
        except FileNotFoundError:
            self.log_issue("SVN命令不存在，请安装SVN客户端", "ERROR")
            return False
        except Exception as e:
            self.log_issue(f"SVN命令检查失败: {e}", "ERROR")
            return False
    
    def check_directories(self):
        """检查必需的目录结构"""
        print("\n📁 检查目录结构...")
        
        required_dirs = ['config', 'src', 'logs', 'data', 'data/cache']
        
        for dir_name in required_dirs:
            dir_path = os.path.join(self.base_dir, dir_name)
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    self.log_fix(f"已创建目录: {dir_name}")
                except Exception as e:
                    self.log_issue(f"无法创建目录 {dir_name}: {e}", "ERROR")
            else:
                print(f"✅ 目录存在: {dir_name}")
        
        return True
    
    def fix_processed_commits(self):
        """修复processed_commits.json文件"""
        print("\n🗃️ 检查提交记录文件...")
        
        if not os.path.exists(self.processed_commits_path):
            # 创建空的processed_commits.json
            try:
                initial_data = {"processed_commits": []}
                with open(self.processed_commits_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=2)
                self.log_fix("已创建空的 processed_commits.json")
                return True
            except Exception as e:
                self.log_issue(f"无法创建 processed_commits.json: {e}", "ERROR")
                return False
        
        # 检查文件格式
        try:
            with open(self.processed_commits_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 统一格式为字典形式
            if isinstance(data, list):
                # 如果是列表，转换为字典格式
                new_data = {"processed_commits": data}
                with open(self.processed_commits_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2)
                self.log_fix("已修复 processed_commits.json 格式")
            elif isinstance(data, dict) and 'processed_commits' in data:
                print("✅ processed_commits.json 格式正确")
            else:
                # 格式不正确，重置
                new_data = {"processed_commits": []}
                with open(self.processed_commits_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2)
                self.log_fix("已重置 processed_commits.json")
            
            return True
            
        except json.JSONDecodeError:
            # JSON格式错误，重新创建
            try:
                new_data = {"processed_commits": []}
                with open(self.processed_commits_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2)
                self.log_fix("已修复损坏的 processed_commits.json")
                return True
            except Exception as e:
                self.log_issue(f"无法修复 processed_commits.json: {e}", "ERROR")
                return False
    
    def test_basic_functionality(self):
        """测试基本功能"""
        print("\n🧪 测试基本功能...")
        
        # 测试配置加载
        try:
            sys.path.insert(0, os.path.join(self.base_dir, 'src'))
            from config_manager import ConfigManager
            config_manager = ConfigManager(self.config_path)
            print("✅ 配置管理器加载成功")
        except Exception as e:
            self.log_issue(f"配置管理器加载失败: {e}", "ERROR")
            return False
        
        # 测试SVN连接（如果配置正确）
        try:
            repo_url = config_manager.get('svn.repository_url')
            username = config_manager.get('svn.username')
            password = config_manager.get('svn.password')
            
            if all([repo_url, username, password]):
                cmd = [
                    'svn', 'info', repo_url,
                    '--username', username,
                    '--password', password,
                    '--non-interactive', '--trust-server-cert'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("✅ SVN连接测试成功")
                else:
                    self.log_issue("SVN连接测试失败，请检查配置")
            else:
                print("⚠️ SVN配置不完整，跳过连接测试")
        except Exception as e:
            self.log_issue(f"SVN连接测试异常: {e}")
        
        return True
    
    def generate_diagnostic_report(self):
        """生成诊断报告"""
        print("\n" + "="*60)
        print("诊断报告")
        print("="*60)
        
        if not self.issues:
            print("🎉 未发现任何问题，系统状态良好！")
        else:
            print(f"📋 发现 {len(self.issues)} 个问题:")
            for issue in self.issues:
                severity_icon = "🔴" if issue['severity'] == 'ERROR' else "🟡"
                print(f"  {severity_icon} {issue['issue']}")
        
        if self.fixes_applied:
            print(f"\n🔧 应用了 {len(self.fixes_applied)} 个修复:")
            for fix in self.fixes_applied:
                print(f"  ✅ {fix['fix']}")
        
        # 统计问题严重程度
        errors = [i for i in self.issues if i['severity'] == 'ERROR']
        warnings = [i for i in self.issues if i['severity'] == 'WARNING']
        
        print(f"\n📊 问题统计:")
        print(f"  错误: {len(errors)}个")
        print(f"  警告: {len(warnings)}个")
        print(f"  修复: {len(self.fixes_applied)}个")
        
        print("="*60)
        
        return len(errors) == 0
    
    def run_full_diagnostic(self):
        """运行完整诊断"""
        print("🔍 开始系统诊断...")
        print("="*60)
        
        # 按顺序执行检查
        checks = [
            self.check_python_version,
            self.check_directories,
            self.check_dependencies,
            self.check_config_file,
            self.check_svn_command,
            self.fix_processed_commits,
            self.test_basic_functionality
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.log_issue(f"检查过程异常: {e}", "ERROR")
        
        return self.generate_diagnostic_report()

def main():
    """主函数"""
    diagnostic = QuickDiagnostic()
    
    try:
        success = diagnostic.run_full_diagnostic()
        
        if success:
            print("\n🚀 系统诊断完成，可以启动工具了！")
            print("   运行命令: python src/main.py")
        else:
            print("\n⚠️ 发现关键问题，请解决后重试")
            
    except KeyboardInterrupt:
        print("\n诊断被中断")
    except Exception as e:
        print(f"\n诊断过程发生异常: {e}")

if __name__ == "__main__":
    main()
