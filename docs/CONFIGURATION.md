# AI SVN 代码审查工具 - 详细配置文档

## 📋 目录

1. [概述](#概述)
2. [配置文件详解](#配置文件详解)
3. [用户映射配置](#用户映射配置)
4. [环境要求](#环境要求)
5. [部署指南](#部署指南)
6. [常见问题与解决方案](#常见问题与解决方案)
7. [维护与监控](#维护与监控)
8. [最佳实践](#最佳实践)

## 概述

AI SVN 代码审查工具是一个自动化代码审查系统，能够：

- 🔍 监控 SVN 仓库的提交记录
- 🤖 使用 AI 对代码变更进行智能分析
- 📱 通过钉钉机器人发送审查结果通知
- 👥 支持用户映射，自动 @ 相关开发人员
- 🔄 支持定时监控和实时处理

## 配置文件详解

### 主配置文件：`config/config.yaml`

```yaml
# SVN配置
svn:
  repository_url: "http://172.16.0.198/res_svn7/MGame/cHero250108"  # SVN仓库URL
  username: "your_username"                                         # SVN用户名
  password: "your_password"                                         # SVN密码
  check_interval: 300                                               # 检查间隔（秒），建议300-600
  monitored_paths:                                                  # 监控路径列表
    - "/Bin/Client/Assets/Lua"                                      # 相对路径格式
    - "/Tools/AISVNreviewTool"                                      
    - "/cHero250108/Bin/Client/Assets/Lua"                        # 完整路径格式（推荐）
    - "/cHero250108/Tools/AISVNreviewTool"

# AI API配置
ai:
  api_base: "https://chat-test.q1.com/v1"                          # OpenAI兼容API基础URL
  api_key: "sk-test"                                                # API密钥
  model: "claude-sonnet-4"                                          # 模型名称
  max_tokens: 2000                                                  # 最大生成token数
  temperature: 0.3                                                  # 生成温度（0-1）
  system_prompt: |                                                  # 系统提示词
    你是一个专业的代码审查助手。请分析以下代码变更，并提供建设性的审查意见。
    重点关注：
    1. 代码质量和最佳实践
    2. 潜在的bug和安全问题
    3. 性能优化建议
    4. 代码可读性和维护性
    请提供简洁明了的中文反馈。

# 钉钉机器人配置
dingtalk:
  webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"  # 钉钉机器人webhook
  secret: "YOUR_SECRET"                                             # 机器人密钥（可选）
  at_all: false                                                     # 是否@所有人
  message_settings:                                                 # 消息设置
    max_message_length: 800                                         # 单条消息最大长度
    enable_message_split: true                                      # 是否启用消息分割
    show_all_comments: true                                         # 是否显示所有评论
    comment_max_length: 100                                         # 单条评论最大长度
    suggestion_max_length: 150                                     # 单条建议最大长度

# 用户映射配置文件路径
user_mapping_file: "config/user_mapping.yaml"

# 日志配置
logging:
  level: "INFO"                                                     # 日志级别：DEBUG, INFO, WARNING, ERROR
  file: "logs/code_review.log"                                     # 日志文件路径
  max_size_mb: 10                                                   # 日志文件最大大小（MB）
  backup_count: 5                                                   # 保留的备份文件数量

# 数据存储
data:
  processed_commits_file: "data/processed_commits.json"            # 已处理提交记录文件
  cache_dir: "data/cache"                                          # 缓存目录
```

### 配置项详细说明

#### SVN 配置 (`svn`)

| 配置项 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `repository_url` | string | ✅ | SVN仓库根URL | `http://svn.example.com/repo` |
| `username` | string | ✅ | SVN认证用户名 | `developer` |
| `password` | string | ✅ | SVN认证密码 | `password123` |
| `check_interval` | integer | ✅ | 检查间隔（秒） | `300` (5分钟) |
| `monitored_paths` | array | ✅ | 监控路径列表 | 见下方说明 |

**监控路径配置注意事项：**

- **格式1（相对路径）**：`/Bin/Client/Assets/Lua`
- **格式2（完整路径）**：`/仓库名/Bin/Client/Assets/Lua`
- **推荐使用完整路径格式**，因为SVN返回的路径包含仓库根目录名称
- 支持多路径监控，可以配置多个不同的代码目录

#### AI API 配置 (`ai`)

| 配置项 | 类型 | 必填 | 说明 | 推荐值 |
|--------|------|------|------|--------|
| `api_base` | string | ✅ | API基础URL | OpenAI兼容端点 |
| `api_key` | string | ✅ | API密钥 | 从服务提供商获取 |
| `model` | string | ✅ | 模型名称 | `claude-sonnet-4`, `gpt-4` |
| `max_tokens` | integer | ✅ | 最大token数 | `2000-4000` |
| `temperature` | float | ✅ | 生成温度 | `0.1-0.3` (更稳定) |
| `system_prompt` | string | ✅ | 系统提示词 | 自定义审查标准 |

#### 钉钉配置 (`dingtalk`)

| 配置项 | 类型 | 必填 | 说明 | 推荐值 |
|--------|------|------|------|--------|
| `webhook_url` | string | ✅ | 钉钉机器人webhook地址 | 从钉钉群获取 |
| `secret` | string | ❌ | 机器人安全密钥 | 启用签名验证时必填 |
| `at_all` | boolean | ✅ | 是否@所有人 | `false` |
| `message_settings.max_message_length` | integer | ✅ | 单条消息最大长度 | `800-2000` |
| `message_settings.enable_message_split` | boolean | ✅ | 启用消息分割 | `true` |

## 用户映射配置

### 配置文件：`config/user_mapping.yaml`

```yaml
# SVN用户名到钉钉用户的映射
# 格式：svn_username: dingtalk_mobile
users:
  huangziquan: "138****8888"      # SVN用户名: 钉钉手机号
  zhangsan: "139****9999"
  lisi: "135****5555"

# 默认通知设置
default:
  notify_all: false               # 找不到映射时是否通知所有人
  fallback_message: "相关开发人员请关注"  # 找不到映射时的替代消息
```

### 获取钉钉手机号的方法

1. 打开钉钉群聊
2. 点击群成员头像
3. 查看个人信息中的手机号
4. 将手机号添加到映射配置中

## 环境要求

### 系统要求

- **操作系统**：Windows 10/11, Windows Server 2016+
- **Python版本**：3.7+
- **内存**：最少 512MB，推荐 1GB+
- **存储空间**：最少 100MB，推荐 500MB+

### 必需软件

1. **SVN客户端**
   ```bash
   # 安装TortoiseSVN或命令行SVN
   # 确保svn命令在PATH中可用
   svn --version
   ```

2. **Python依赖包**
   ```bash
   pip install -r requirements.txt
   ```

### 网络要求

- SVN服务器访问权限
- AI API服务访问权限（可能需要代理）
- 钉钉机器人webhook访问权限

## 部署指南

### 1. 标准部署

```bash
# 1. 克隆或下载项目
git clone <repository-url>
cd AISVNcodeReview

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置文件
cp config/config.example.yaml config/config.yaml
# 编辑 config/config.yaml 配置文件

# 4. 测试运行
python src/main.py

# 5. 后台运行
nohup python src/main.py > logs/app.log 2>&1 &
```

### 2. Windows服务部署

```bash
# 1. 安装服务
python service_wrapper.py install

# 2. 启动服务
python service_wrapper.py start

# 3. 停止服务
python service_wrapper.py stop

# 4. 卸载服务
python service_wrapper.py remove
```

### 3. 批处理文件部署

```bash
# 直接运行
./start.bat

# 或使用服务管理器
./service_manager.bat
```

## 常见问题与解决方案

### 🔧 SVN相关问题

#### 问题1：SVN连接失败
```
错误：svn: E170013: Unable to connect to a repository
```

**解决方案：**
1. 检查网络连接和SVN服务器状态
2. 验证用户名密码是否正确
3. 检查SVN服务器是否需要证书验证
4. 尝试手动执行SVN命令测试

#### 问题2：路径匹配问题
```
错误：提交未被检测到，但确实在监控路径下
```

**解决方案：**
1. 检查监控路径配置是否包含仓库根目录名称
2. 使用debug工具检查实际SVN返回的路径格式：
   ```bash
   cd debugTools
   python test_changed_files.py
   ```
3. 更新监控路径配置，添加完整路径格式

#### 问题3：编码问题
```
错误：UnicodeDecodeError: 'utf-8' codec can't decode
```

**解决方案：**
1. 工具已内置编码处理逻辑
2. 如仍有问题，检查系统区域设置
3. 确保SVN客户端版本支持UTF-8

### 🤖 AI API相关问题

#### 问题1：API调用失败
```
错误：HTTP 401 Unauthorized
```

**解决方案：**
1. 检查API密钥是否正确
2. 验证API基础URL是否正确
3. 检查网络是否能访问AI服务
4. 确认账户是否有足够的API额度

#### 问题2：响应超时
```
错误：Request timeout
```

**解决方案：**
1. 增加请求超时时间
2. 减少max_tokens参数
3. 检查网络连接稳定性
4. 考虑使用更快的模型

#### 问题3：生成内容质量差
**解决方案：**
1. 优化system_prompt提示词
2. 调整temperature参数（0.1-0.3）
3. 增加max_tokens限制
4. 尝试不同的模型

### 📱 钉钉机器人问题

#### 问题1：消息发送失败
```
错误：钉钉API返回错误
```

**解决方案：**
1. 检查webhook URL是否正确
2. 验证机器人是否在群聊中
3. 检查安全设置（IP白名单、关键词、签名）
4. 确认消息格式是否符合钉钉要求

#### 问题2：@用户失败
**解决方案：**
1. 检查用户映射配置是否正确
2. 确认手机号格式是否正确
3. 验证用户是否在群聊中
4. 检查机器人是否有@权限

#### 问题3：消息被截断
**解决方案：**
1. 启用消息分割功能
2. 调整max_message_length参数
3. 优化消息格式，减少冗余信息

### 💾 数据与存储问题

#### 问题1：处理记录格式错误
```
错误：'list' object has no attribute 'get'
```

**解决方案：**
1. 删除`data/processed_commits.json`重新开始
2. 或使用修复工具：
   ```bash
   cd Tools/AISVNreviewTool
   python fix_processed_commits.py
   ```

#### 问题2：日志文件过大
**解决方案：**
1. 调整logging配置中的max_size_mb参数
2. 增加backup_count数量
3. 定期清理旧日志文件

#### 问题3：权限问题
**解决方案：**
1. 确保工具有读写data目录的权限
2. 检查logs目录的写入权限
3. 在Windows上可能需要管理员权限

## 维护与监控

### 🔍 日志监控

#### 查看实时日志
```bash
# Windows
Get-Content logs/code_review.log -Tail 50 -Wait

# Linux/Mac
tail -f logs/code_review.log
```

#### 关键日志信息
- `INFO - 发现 X 个新提交` - 检测到新提交
- `INFO - 提交 X 审查完成，评分: Y/10` - AI审查完成
- `INFO - 钉钉消息发送成功` - 通知发送成功
- `ERROR` - 各种错误信息

### 📊 性能监控

#### 监控指标
- 提交检测延迟
- AI API响应时间
- 钉钉消息发送成功率
- 内存和CPU使用情况

#### 性能优化建议
1. 适当调整check_interval（不要太频繁）
2. 限制并发处理的提交数量
3. 定期清理缓存和日志文件
4. 监控网络连接质量

### 🔄 维护任务

#### 定期维护（每周）
1. 检查日志文件大小
2. 验证SVN连接状态
3. 测试AI API可用性
4. 确认钉钉机器人状态

#### 定期维护（每月）
1. 更新依赖包版本
2. 备份配置文件
3. 清理旧的缓存数据
4. 检查存储空间使用情况

## 最佳实践

### 🎯 配置最佳实践

1. **监控路径设置**
   - 使用完整路径格式：`/仓库名/路径`
   - 避免监控过于宽泛的路径
   - 根据团队结构设置合理的监控范围

2. **AI提示词优化**
   - 根据项目特点自定义system_prompt
   - 明确指定关注重点（安全、性能、规范等）
   - 要求AI提供具体、可操作的建议

3. **钉钉通知设置**
   - 启用消息分割避免信息丢失
   - 合理设置消息长度限制
   - 配置准确的用户映射

### ⚡ 性能最佳实践

1. **检查间隔设置**
   - 生产环境建议300-600秒
   - 开发环境可以更频繁（60-180秒）
   - 避免过于频繁的检查

2. **资源使用优化**
   - 定期清理日志和缓存
   - 监控内存使用情况
   - 合理设置日志级别

3. **网络优化**
   - 使用稳定的网络连接
   - 考虑设置代理（如需要）
   - 监控API调用频率和成功率

### 🔒 安全最佳实践

1. **凭据管理**
   - 定期更换SVN密码
   - 保护API密钥安全
   - 使用环境变量存储敏感信息

2. **访问控制**
   - 限制工具运行权限
   - 定期检查SVN用户权限
   - 监控异常访问行为

3. **数据保护**
   - 备份重要配置文件
   - 保护处理记录数据
   - 定期检查文件权限

### 📈 监控和告警

1. **设置告警机制**
   - 监控工具运行状态
   - API调用失败告警
   - 长时间无新提交告警

2. **性能基线**
   - 记录正常运行时的性能指标
   - 设置合理的性能阈值
   - 定期review性能数据

## 📞 技术支持

### 常用调试工具

项目提供了以下调试工具（位于debugTools目录）：

1. **test_environment.py** - 环境检测工具
2. **test_latest_commits.py** - 提交检测测试
3. **test_changed_files.py** - 文件变更测试
4. **fix_processed_commits.py** - 处理记录修复工具

### 获取帮助

如遇到问题，请提供以下信息：
1. 详细的错误日志
2. 配置文件内容（隐去敏感信息）
3. 操作系统和Python版本
4. 复现步骤

---

**版本信息**
- 文档版本：v1.0
- 更新日期：2025-07-31
- 适用工具版本：v1.0+
