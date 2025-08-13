# AI SVN 代码审查工具

基于Python的智能化SVN代码审查工具，提供实时监控和批量审查功能。

## ✨ 核心功能

- 🔍 **实时监控**: 自动监控S## � 项目结构

```
AISVNcodeReview/
├── src/                    # 核心源代码
│   ├── main.py            # 主程序入口
│   ├── ai_reviewer.py     # AI 代码审查模块
│   ├── svn_monitor.py     # SVN 监控模块
│   └── dingtalk_bot.py    # 钉钉通知模块
├── batch/                  # 批量审查工具
│   ├── simple_batch_review.py  # 简化版批量审查（推荐）
│   ├── batch_review.py    # 完整版批量审查
│   └── batch_review.bat   # Windows 启动脚本
├── tests/                  # 测试文件
│   ├── test_filters.py    # 过滤功能测试
│   └── test_*.py          # 其他测试文件
├── scripts/                # 安装和启动脚本
│   ├── setup_enhanced.bat # 增强安装脚本
│   ├── start.bat          # 启动脚本
│   └── service_manager.bat # 服务管理脚本
├── tools/                  # 实用工具
│   ├── debug_svn.py       # SVN 调试工具
│   ├── diagnose.py        # 系统诊断工具
│   └── cleanup.py         # 数据清理工具
├── config/                 # 配置文件
├── docs/                   # 项目文档
├── data/                   # 数据文件
└── logs/                   # 日志文件
```

- 📖 [文档目录](docs/README.md) - 完整文档列表和阅读指南
- 📖 [用户指南](docs/USER_GUIDE.md) - 详细使用说明
- 📖 [批量审查指南](docs/BATCH_REVIEW_GUIDE.md) - 批量审查功能
- 📖 [过滤功能指南](docs/FILTER_GUIDE.md) - 过滤功能详细说明
- 📖 [配置指南](docs/CONFIGURATION.md) - 详细配置说明
- 🚀 [部署指南](docs/DEPLOYMENT.md) - 生产环境部署
- 🔧 [故障排除](docs/TROUBLESHOOTING.md) - 常见问题解决
- 📋 [项目总结](docs/PROJECT_SUMMARY.md) - 项目概况能代码分析
- 📊 **批量审查**: 批量分析历史提交，生成详细报告
- 🤖 **AI驱动**: 集成OpenAI兼容API，智能发现代码问题
- 📱 **钉钉通知**: 自动@相关人员，发送审查结果
- 🎯 **灵活配置**: 支持多路径监控和用户映射

## 🚀 快速开始

📋 **[完整安装指南](INSTALL_GUIDE.md)** - 详细安装步骤、常见错误解决方案

### 快速安装（Windows）
```cmd
# 1. 运行安装脚本
install.bat

# 2. 编辑配置文件
notepad config\config.yaml
```

### 快速安装（Linux/Mac）
```bash
# 1. 运行安装脚本
chmod +x install.sh && ./install.sh

# 2. 编辑配置文件
nano config/config.yaml
```

### 手动安装
```bash
# 安装依赖
pip install -r requirements.txt

# 复制配置模板
copy config\config.example.yaml config\config.yaml  # Windows
cp config/config.example.yaml config/config.yaml    # Linux/Mac
```

### 3. 运行模式

**实时监控**
```bash
python src/main.py
```

**批量审查**
```bash
batch_review.bat
```

## ⚙️ 核心配置

```yaml
svn:
  repository_url: "http://your-svn-server/svn/repo"
  username: "your_username"
  password: "your_password"

ai:
  api_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-4"

dingtalk:
  webhook_url: "your-webhook-url"
  secret: "your-secret"
```

## 📁 项目结构

```
AISVNcodeReview/
├── src/                    # 核心源代码
│   ├── main.py            # 主程序入口
│   ├── svn_monitor.py     # SVN监控
│   ├── ai_reviewer.py     # AI代码审查
│   └── dingtalk_bot.py    # 钉钉通知
├── config/                # 配置文件
├── reports/               # 批量审查报告
├── batch_review.bat       # 批量审查脚本
└── simple_batch_review.py # 批量审查工具
```

## 🛠️ 高级功能

### 批量审查
- 指定日期范围批量分析SVN提交
- 生成详细HTML/JSON报告
- 静默模式，不发送钉钉通知

### 实时监控
- 支持传统轮询模式
- 支持SVN hook实时触发
- 详细的提交状态跟踪

### 诊断工具
```bash
# 系统诊断
python diagnose.py

# 状态查看
python status_viewer.py
```

## 📚 详细文档

- 📖 [用户指南](USER_GUIDE.md) - 详细使用说明
- 📖 [批量审查指南](BATCH_REVIEW_GUIDE.md) - 批量审查功能
- 📖 [配置指南](CONFIGURATION.md) - 详细配置说明
- 🚀 [部署指南](DEPLOYMENT.md) - 生产环境部署
- 🔧 [故障排除](TROUBLESHOOTING.md) - 常见问题解决
- 📋 [项目总结](PROJECT_SUMMARY.md) - 项目概况

## 🆘 获取帮助

- 🔧 运行 `python diagnose.py` 进行系统诊断
- 📖 查看详细文档了解更多功能
- 🐛 提交Issue报告问题
- 💡 贡献代码改进项目

---

**MIT License** | **享受智能代码审查带来的高效开发体验！** 🚀
