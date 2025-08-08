#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量审查功能演示脚本
用于测试和演示批量审查功能
"""

import os
import sys
from datetime import datetime, timedelta

def main():
    """演示批量审查功能"""
    print("=" * 60)
    print("🚀 AI SVN代码审查工具 - 批量审查功能演示")
    print("=" * 60)
    print()
    
    # 检查文件存在性
    parent_dir = os.path.dirname(os.path.dirname(__file__))  # 获取项目根目录
    required_files = [
        "simple_batch_review.py",
        "batch_review.bat",
        os.path.join(parent_dir, "src/config_manager.py"),
        os.path.join(parent_dir, "src/ai_reviewer.py"),
        os.path.join(parent_dir, "config/config.example.yaml")
    ]
    
    print("📋 检查必要文件...")
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - 缺失")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  警告: 发现 {len(missing_files)} 个缺失文件")
        print("请确保项目文件完整后再运行批量审查")
        return
    
    print("\n✅ 所有必要文件检查通过")
    
    # 配置检查
    print("\n📋 检查配置文件...")
    config_files = [
        ("config/config.yaml", "主配置文件"),
        ("config/user_mapping.yaml", "用户映射文件")
    ]
    
    for config_file, description in config_files:
        if os.path.exists(config_file):
            print(f"  ✅ {config_file} - {description}")
        else:
            print(f"  ⚠️  {config_file} - {description} 不存在")
            example_file = config_file.replace('.yaml', '.example.yaml')
            if os.path.exists(example_file):
                print(f"      建议复制 {example_file} 为 {config_file}")
    
    # 显示使用方法
    print("\n" + "=" * 60)
    print("📖 批量审查功能使用方法")
    print("=" * 60)
    
    print("\n1. 使用批处理脚本（推荐新手）:")
    print("   batch_review.bat")
    print("   - 图形化界面，输入天数即可")
    print("   - 自动生成HTML报告")
    print("   - 自动在浏览器中打开")
    
    print("\n2. 使用Python脚本（推荐高级用户）:")
    print("   python simple_batch_review.py [天数]")
    print("   例如:")
    print("   - python simple_batch_review.py 7    # 审查最近7天")
    print("   - python simple_batch_review.py 30   # 审查最近30天")
    
    print("\n3. 功能特点:")
    print("   ✅ 指定日期范围批量审查")
    print("   ✅ AI智能代码分析")
    print("   ✅ 生成详细HTML报告")
    print("   ✅ 不发送钉钉通知（静默模式）")
    print("   ✅ 自动打开浏览器查看报告")
    
    # 报告示例路径
    print("\n📊 报告输出:")
    print("   报告保存位置: reports/ 目录")
    print("   文件名格式: batch_review_YYYYMMDD-YYYYMMDD_HHMMSS.html")
    print("   例如: batch_review_20241201-20241208_143022.html")
    
    # 配置提示
    print("\n⚙️  配置要求:")
    print("   ✅ SVN服务器连接配置")
    print("   ✅ AI API密钥配置")
    print("   ⚠️  注意: 批量审查不需要钉钉配置")
    
    # 演示命令
    print("\n" + "=" * 60)
    print("🎯 快速开始演示")
    print("=" * 60)
    
    # 获取用户输入
    print("\n是否要启动批量审查演示？")
    print("1. 启动批处理脚本")
    print("2. 启动Python脚本（审查最近3天）")
    print("3. 仅查看配置文档")
    print("0. 退出")
    
    try:
        choice = input("\n请选择 (0-3): ").strip()
        
        if choice == "1":
            print("\n🚀 启动批处理脚本...")
            if os.path.exists("batch_review.bat"):
                os.system("batch_review.bat")
            else:
                print("❌ batch_review.bat 文件不存在")
        
        elif choice == "2":
            print("\n🚀 启动Python脚本（审查最近3天）...")
            if os.path.exists("simple_batch_review.py"):
                os.system("python simple_batch_review.py 3")
            else:
                print("❌ simple_batch_review.py 文件不存在")
        
        elif choice == "3":
            print("\n📖 配置文档说明:")
            print("详细配置说明请参考: BATCH_REVIEW_GUIDE.md")
            if os.path.exists("BATCH_REVIEW_GUIDE.md"):
                print("✅ 批量审查指南文档已就绪")
            else:
                print("⚠️  批量审查指南文档不存在")
        
        elif choice == "0":
            print("\n👋 谢谢使用，再见！")
        
        else:
            print("\n❌ 无效选择")
    
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，再见！")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    
    print("\n" + "=" * 60)
    print("💡 提示: 如需帮助，请查看 BATCH_REVIEW_GUIDE.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
