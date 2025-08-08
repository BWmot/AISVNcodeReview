# 测试文件目录

本目录包含所有测试和验证脚本。

## 📋 测试文件列表

### 🧪 功能测试
- **test_filters.py** - 过滤功能测试
- **test_environment.py** - 环境配置测试
- **test_confirmation.py** - 确认功能测试

### 🔧 修复和验证测试
- **test_fix.py** - 修复功能测试
- **test_fixes.py** - 多个修复测试
- **test_review_result.py** - 审查结果测试

### 📝 消息处理测试
- **test_message_split.py** - 消息分割测试
- **test_revision_filter.py** - 版本号过滤测试

## 🚀 运行测试

### 运行单个测试
```bash
cd tests
python test_environment.py
```

### 运行所有测试
```bash
cd tests
for file in test_*.py; do python "$file"; done
```

## 📝 测试说明

这些测试文件主要用于：
1. **验证功能正确性** - 确保各模块按预期工作
2. **调试和故障排除** - 帮助定位问题
3. **开发验证** - 在开发新功能时验证
4. **回归测试** - 确保更改不破坏现有功能

## 💡 编写新测试

添加新测试时请遵循以下约定：
1. 文件名以 `test_` 开头
2. 包含清晰的测试说明
3. 提供预期的输出示例
4. 更新此 README 文件
