#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git部署准备脚本
备份敏感配置文件并准备Git仓库
"""

import os
import shutil
import subprocess
from pathlib import Path

def create_backup_files():
    """创建配置文件的本地备份"""
    print("📋 创建配置文件备份...")
    
    backup_tasks = [
        ("config/config.yaml", "config/config.local.yaml"),
        ("config/user_mapping.yaml", "config/user_mapping.local.yaml"),
        ("data/processed_commits.json", "data/processed_commits.local.json"),
        ("data/commit_tracking.json", "data/commit_tracking.local.json")
    ]
    
    for source, backup in backup_tasks:
        if os.path.exists(source):
            try:
                shutil.copy2(source, backup)
                print(f"  ✅ 备份: {source} → {backup}")
            except Exception as e:
                print(f"  ❌ 备份失败: {source} - {e}")
        else:
            print(f"  ℹ️  源文件不存在: {source}")

def clean_sensitive_config():
    """清理配置文件中的敏感信息，准备提交"""
    print("\n🔒 清理敏感配置信息...")
    
    # 重置config.yaml为示例模式
    if os.path.exists("config/config.yaml"):
        if os.path.exists("config/config.example.yaml"):
            try:
                shutil.copy2("config/config.example.yaml", "config/config.yaml")
                print("  ✅ config.yaml 已重置为示例配置")
            except Exception as e:
                print(f"  ❌ 重置失败: {e}")
    
    # 重置user_mapping.yaml为示例模式
    if os.path.exists("config/user_mapping.yaml"):
        if os.path.exists("config/user_mapping.example.yaml"):
            try:
                shutil.copy2("config/user_mapping.example.yaml", "config/user_mapping.yaml")
                print("  ✅ user_mapping.yaml 已重置为示例配置")
            except Exception as e:
                print(f"  ❌ 重置失败: {e}")
    
    # 重置processed_commits.json为空数据
    if os.path.exists("data/processed_commits.json"):
        try:
            with open("data/processed_commits.json", "w", encoding="utf-8") as f:
                f.write("[]")
            print("  ✅ processed_commits.json 已重置为空数据")
        except Exception as e:
            print(f"  ❌ 重置失败: {e}")

def check_git_status():
    """检查Git状态"""
    print("\n📊 检查Git仓库状态...")
    
    if not os.path.exists(".git"):
        print("  ℹ️  Git仓库未初始化")
        response = input("是否初始化Git仓库? (y/N): ").lower()
        if response == 'y':
            try:
                subprocess.run(["git", "init"], check=True)
                print("  ✅ Git仓库已初始化")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Git初始化失败: {e}")
                return False
        else:
            print("  ⏭️  跳过Git初始化")
            return False
    
    # 检查.gitignore
    if not os.path.exists(".gitignore"):
        print("  ⚠️  .gitignore 文件不存在")
        return False
    else:
        print("  ✅ .gitignore 文件存在")
    
    # 显示Git状态
    try:
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"  📝 有未跟踪/修改的文件:")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
        else:
            print("  ✅ 工作目录干净")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 检查Git状态失败: {e}")
    
    return True

def verify_gitignore():
    """验证.gitignore是否正确忽略敏感文件"""
    print("\n🔍 验证.gitignore规则...")
    
    sensitive_files = [
        "config/config.local.yaml",
        "config/user_mapping.local.yaml", 
        "data/processed_commits.local.json",
        "data/commit_tracking.local.json",
        "logs/code_review.log",
        "venv/",
        "src/__pycache__/"
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            try:
                result = subprocess.run(["git", "check-ignore", file_path], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ 已忽略: {file_path}")
                else:
                    print(f"  ⚠️  未忽略: {file_path}")
            except subprocess.CalledProcessError:
                print(f"  ❌ 检查失败: {file_path}")

def show_next_steps():
    """显示下一步操作指南"""
    print("\n🎯 Git部署准备完成！")
    print("\n📋 下一步操作:")
    print("1. 检查配置文件是否已清理:")
    print("   - config/config.yaml (应该是示例配置)")
    print("   - config/user_mapping.yaml (应该是示例配置)")
    print("   - data/processed_commits.json (应该是空数组)")
    print()
    print("2. 添加文件到Git:")
    print("   git add .")
    print()
    print("3. 提交到Git:")
    print('   git commit -m "Initial commit: AI SVN Code Review Tool"')
    print()
    print("4. 添加远程仓库:")
    print("   git remote add origin <your-repository-url>")
    print()
    print("5. 推送到远程:")
    print("   git push -u origin main")
    print()
    print("💡 本地备份文件已保存，不会被提交到Git仓库:")
    print("   - config/config.local.yaml")
    print("   - config/user_mapping.local.yaml")
    print("   - data/processed_commits.local.json")

def main():
    """主函数"""
    print("=" * 60)
    print("   AI SVN代码审查工具 - Git部署准备脚本")
    print("=" * 60)
    
    # 确认当前目录
    if not os.path.exists("src/main.py"):
        print("❌ 错误: 不在正确的项目目录中！")
        return
    
    print(f"📂 当前目录: {os.getcwd()}")
    
    # 询问用户确认
    print("\n⚠️  此脚本将:")
    print("1. 备份当前配置文件到 *.local.* 文件")
    print("2. 将配置文件重置为示例模式（清除敏感信息）")
    print("3. 准备Git仓库用于提交")
    print()
    response = input("是否继续? (y/N): ").lower()
    if response != 'y':
        print("操作已取消")
        return
    
    # 执行准备步骤
    create_backup_files()
    clean_sensitive_config()
    git_ready = check_git_status()
    
    if git_ready:
        verify_gitignore()
    
    show_next_steps()

if __name__ == "__main__":
    main()
