#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径修复验证脚本
验证目录重组后所有模块能否正常导入和运行
"""

import os
import sys
from pathlib import Path

def test_imports():
    """测试所有主要模块的导入"""
    print("🧪 测试模块导入...")
    
    # 添加src目录到路径
    current_dir = Path(__file__).parent
    src_path = current_dir / 'src'
    sys.path.insert(0, str(src_path))
    
    test_results = {}
    
    # 测试核心模块
    modules_to_test = [
        'config_manager',
        'ai_reviewer', 
        'svn_monitor',
        'dingtalk_bot',
        'enhanced_monitor',
        'batch_reviewer',
        'commit_tracker'
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            test_results[module_name] = "✅ 成功"
            print(f"  {module_name}: ✅ 导入成功")
        except Exception as e:
            test_results[module_name] = f"❌ 失败: {str(e)}"
            print(f"  {module_name}: ❌ 导入失败 - {str(e)}")
    
    return test_results

def test_config_manager():
    """测试配置管理器"""
    print("\n🔧 测试配置管理器...")
    
    try:
        from config_manager import ConfigManager
        
        # 检查配置文件是否存在
        config_path = Path('config/config.yaml')
        if not config_path.exists():
            print("  ⚠️  配置文件不存在，使用示例配置")
            config_path = Path('config/config.example.yaml')
        
        if config_path.exists():
            config_manager = ConfigManager(str(config_path))
            print(f"  ✅ 配置文件加载成功: {config_path}")
            print(f"  📊 配置项数量: {len(config_manager.config)}")
        else:
            print("  ❌ 找不到配置文件")
            return False
            
    except Exception as e:
        print(f"  ❌ 配置管理器测试失败: {str(e)}")
        return False
    
    return True

def test_batch_review():
    """测试批量审查脚本"""
    print("\n📊 测试批量审查脚本...")
    
    batch_dir = Path('batch')
    scripts_to_test = [
        'simple_batch_review.py',
        'batch_review.py', 
        'demo_batch_review.py'
    ]
    
    for script in scripts_to_test:
        script_path = batch_dir / script
        if script_path.exists():
            print(f"  ✅ 找到脚本: {script}")
        else:
            print(f"  ❌ 缺失脚本: {script}")

def test_directory_structure():
    """测试目录结构"""
    print("\n📁 检查目录结构...")
    
    expected_dirs = [
        'src',
        'config', 
        'docs',
        'batch',
        'tests',
        'scripts',
        'tools',
        'data',
        'logs'
    ]
    
    for dir_name in expected_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            file_count = len(list(dir_path.glob('*')))
            print(f"  ✅ {dir_name}/ ({file_count} 个文件)")
        else:
            print(f"  ❌ 缺失目录: {dir_name}/")

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 AI SVN代码审查工具 - 路径修复验证")
    print("=" * 60)
    
    # 切换到项目根目录
    os.chdir(Path(__file__).parent)
    
    # 运行测试
    test_directory_structure()
    test_results = test_imports()
    config_ok = test_config_manager()
    test_batch_review()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 测试汇总")
    print("=" * 60)
    
    # 模块导入结果
    success_count = sum(1 for result in test_results.values() if "✅" in result)
    total_count = len(test_results)
    print(f"模块导入: {success_count}/{total_count} 成功")
    
    for module, result in test_results.items():
        print(f"  {module}: {result}")
    
    print(f"\n配置管理器: {'✅ 正常' if config_ok else '❌ 异常'}")
    
    # 建议
    print(f"\n💡 建议:")
    if success_count == total_count and config_ok:
        print("  🎉 所有测试通过！系统已准备就绪。")
        print("  🚀 可以运行以下命令开始使用：")
        print("     python src/main.py                    # 启动监控")
        print("     python batch/simple_batch_review.py 7 # 批量审查")
    else:
        print("  🔧 发现问题，请检查以下项目：")
        if success_count < total_count:
            print("     - 检查Python环境和依赖包安装")
            print("     - 确保所有必要文件都在正确位置")
        if not config_ok:
            print("     - 检查配置文件是否存在和格式正确")
            print("     - 复制 config.example.yaml 为 config.yaml")

if __name__ == "__main__":
    main()
