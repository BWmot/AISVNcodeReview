# 脚本目录

本目录包含各种安装、启动和管理脚本。

## 📋 脚本列表

### 🚀 启动脚本
- **start.bat** - 基本启动脚本
- **start_complete.bat** - 完整启动脚本（包含环境检查）

### ⚙️ 安装设置脚本
- **setup_simple.bat** - 简单安装脚本
- **setup_enhanced.bat** - 增强安装脚本（包含更多功能）

### 🔧 服务管理脚本
- **service_manager.bat** - Windows 服务管理脚本

## 🚀 使用说明

### 首次安装
```cmd
# 运行增强安装脚本（推荐）
setup_enhanced.bat

# 或运行简单安装脚本
setup_simple.bat
```

### 启动应用
```cmd
# 基本启动
start.bat

# 完整启动（包含环境检查）
start_complete.bat
```

### 服务管理
```cmd
# 管理 Windows 服务
service_manager.bat
```

## ⚙️ 脚本功能对比

| 脚本 | 功能 | 适用场景 |
|------|------|----------|
| setup_simple.bat | 基本依赖安装 | 快速安装 |
| setup_enhanced.bat | 完整环境配置 | 生产环境 |
| start.bat | 直接启动应用 | 开发测试 |
| start_complete.bat | 环境检查+启动 | 生产环境 |
| service_manager.bat | 服务管理 | 服务器部署 |

## 📝 注意事项

1. **管理员权限**：某些脚本可能需要管理员权限运行
2. **路径依赖**：请在项目根目录下运行这些脚本
3. **环境要求**：确保已安装 Python 3.7+ 和必要的依赖

## 🔗 相关文档

- [部署指南](../docs/DEPLOYMENT.md)
- [配置指南](../docs/CONFIGURATION.md)
- [故障排除](../docs/TROUBLESHOOTING.md)
