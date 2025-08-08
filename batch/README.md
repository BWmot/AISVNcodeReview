# 批量审查工具目录

本目录包含所有批量代码审查相关的脚本和工具。

## 📋 文件列表

### 🎯 主要批量审查工具
- **simple_batch_review.py** - 简化版批量审查工具（推荐使用）
- **batch_review.py** - 完整版批量审查工具
- **demo_batch_review.py** - 演示版批量审查工具

### 🚀 启动脚本
- **batch_review.bat** - Windows 批处理启动脚本

## 🚀 使用方法

### 快速开始（推荐）
```bash
cd batch
python simple_batch_review.py 7
```

### 高级用法
```bash
# 指定版本范围
python simple_batch_review.py 7 --min-revision 501000 --max-revision 502000

# 过滤特定作者
python simple_batch_review.py 7 --exclude-authors jenkins ci

# 组合过滤条件
python simple_batch_review.py 7 \
  --min-revision 501000 \
  --exclude-authors jenkins ci \
  --exclude-messages "auto build" "merge"
```

### 使用批处理脚本
```cmd
batch_review.bat
```

## ⚙️ 工具对比

| 工具 | 特点 | 适用场景 |
|------|------|----------|
| simple_batch_review.py | 简化界面，强大过滤功能 | 日常使用，推荐 |
| batch_review.py | 完整功能，复杂配置 | 高级用户 |
| demo_batch_review.py | 演示功能，学习参考 | 新用户学习 |

## 📖 详细文档

更多使用说明请参考：
- [批量审查指南](../docs/BATCH_REVIEW_GUIDE.md)
- [过滤功能指南](../docs/FILTER_GUIDE.md)
- [配置指南](../docs/CONFIGURATION.md)

## 🔧 配置要求

使用前请确保：
1. 已安装所有依赖：`pip install -r ../requirements.txt`
2. 已配置 `../config/config.yaml`
3. 已配置 `../config/user_mapping.yaml`
