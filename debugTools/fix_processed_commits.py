#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复工具 - 重置处理过的提交记录以适应正式环境
"""
import os
import json
from datetime import datetime


def reset_processed_commits():
    """重置处理过的提交记录"""
    
    # 备份当前文件
    processed_file = "../../data/processed_commits.json"
    backup_file = f"../../data/processed_commits_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    if os.path.exists(processed_file):
        # 创建备份
        with open(processed_file, 'r', encoding='utf-8') as f:
            backup_data = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(backup_data)
        
        print(f"✓ 已备份原文件到: {backup_file}")
    
    # 重置为空（或设置最新处理的提交号）
    # 方案1: 完全重置为空，重新开始处理
    reset_data = []
    
    # 方案2: 设置为最新提交前的一个版本，只处理最新的几个提交
    # 根据调试结果，设置为501522，这样会重新处理501523及以后的提交
    # reset_data = [501522]
    
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(reset_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 已重置处理记录文件")
    print(f"  重置后的内容: {reset_data}")
    
    return True


def set_specific_baseline():
    """设置特定的基线版本"""
    processed_file = "../../data/processed_commits.json"
    
    # 设置为最新提交前的版本，这样工具会重新处理最近的提交
    # 根据调试结果，最新提交是501533，设置基线为501520
    baseline_revision = 501520
    
    reset_data = [baseline_revision]
    
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(reset_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 已设置基线版本为: r{baseline_revision}")
    print(f"  工具将处理 r{baseline_revision + 1} 及以后的提交")


if __name__ == "__main__":
    print("选择修复方案:")
    print("1. 完全重置，重新开始处理所有提交")
    print("2. 设置基线版本，只处理最近的提交")
    
    choice = input("请选择 (1/2): ")
    
    if choice == "1":
        reset_processed_commits()
        print("\n建议: 由于正式环境有大量历史提交，建议手动运行一次工具测试")
    elif choice == "2":
        set_specific_baseline()
        print("\n建议: 这样设置后工具会处理最近的提交，比较安全")
    else:
        print("无效选择")
    
    print("\n修复完成！现在可以重新运行主工具进行测试。")
