# 工具目录

本目录包含各种实用工具、诊断脚本和数据处理工具。

## 📋 工具列表

### 🔍 调试和诊断工具
- **debug_svn.py** - SVN 连接和操作调试工具
- **diagnose.py** - 系统环境诊断工具
- **final_test.py** - 最终测试验证工具
- **status_viewer.py** - 状态查看器
- **verify_fixes.py** - 修复验证工具

### 🛠️ 数据处理工具
- **cleanup.py** - 数据清理工具
- **migrate_data.py** - 数据迁移工具
- **prepare_git.py** - Git 准备工具

### 🚀 服务工具
- **service_wrapper.py** - Windows 服务包装器

## 🚀 使用说明

### 诊断问题
```bash
cd tools
# 检查 SVN 连接
python debug_svn.py

# 系统环境诊断
python diagnose.py

# 查看当前状态
python status_viewer.py
```

### 数据管理
```bash
cd tools
# 清理旧数据
python cleanup.py

# 迁移数据
python migrate_data.py

# 准备 Git 环境
python prepare_git.py
```

### 验证和测试
```bash
cd tools
# 验证修复
python verify_fixes.py

# 最终测试
python final_test.py
```

## ⚙️ 工具说明

### 🔍 诊断工具
| 工具 | 功能 | 使用场景 |
|------|------|----------|
| debug_svn.py | SVN 连接测试 | SVN 连接问题 |
| diagnose.py | 环境诊断 | 系统配置问题 |
| status_viewer.py | 状态监控 | 运行状态检查 |

### 🛠️ 数据工具
| 工具 | 功能 | 使用场景 |
|------|------|----------|
| cleanup.py | 数据清理 | 清理临时文件 |
| migrate_data.py | 数据迁移 | 版本升级 |
| prepare_git.py | Git 配置 | Git 环境准备 |

## 📝 使用建议

1. **诊断问题时**：
   - 首先运行 `diagnose.py` 进行全面检查
   - 如有 SVN 问题，使用 `debug_svn.py`
   - 使用 `status_viewer.py` 监控运行状态

2. **维护数据时**：
   - 定期运行 `cleanup.py` 清理临时文件
   - 升级版本前使用 `migrate_data.py`
   - 需要 Git 支持时运行 `prepare_git.py`

3. **验证修复时**：
   - 修复问题后运行 `verify_fixes.py`
   - 部署前运行 `final_test.py`

## 🔗 相关文档

- [故障排除指南](../docs/TROUBLESHOOTING.md)
- [配置指南](../docs/CONFIGURATION.md)
- [部署指南](../docs/DEPLOYMENT.md)
