# 部署指南

本文档介绍如何在Windows环境下部署AI SVN代码审查工具。

## 系统要求

- Windows 10/11 或 Windows Server 2016+
- Python 3.7 或更高版本
- SVN客户端工具
- 网络访问权限（用于访问SVN服务器、AI API和钉钉API）

## 快速部署

### 1. 下载项目

将项目文件放置到目标服务器上，例如：`C:\AICodeReview\`

### 2. 运行安装脚本

以管理员身份运行命令提示符，执行：

```bash
cd C:\AICodeReview
start.bat
```

首次运行会自动：
- 创建Python虚拟环境
- 安装依赖包
- 复制配置文件模板

### 3. 配置参数

编辑 `config\config.yaml` 文件，设置以下参数：

#### SVN配置
```yaml
svn:
  repository_url: "https://your-svn-server/svn/project"
  username: "svn_username"
  password: "svn_password"
  check_interval: 300  # 检查间隔（秒）
  monitored_paths:
    - "/trunk/src"
    - "/branches/dev"
```

#### AI API配置
```yaml
ai:
  api_base: "https://api.openai.com/v1"
  api_key: "your_openai_api_key"
  model: "gpt-3.5-turbo"
  max_tokens: 2000
  temperature: 0.3
```

#### 钉钉配置
```yaml
dingtalk:
  webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=your_token"
  secret: "your_dingtalk_secret"  # 可选
```

### 4. 配置用户映射

编辑 `config\user_mapping.yaml`，设置SVN用户到钉钉用户的映射：

```yaml
user_mapping:
  "john.doe": "13800138000"
  "jane.smith": "userid_123"
```

### 5. 测试运行

配置完成后，再次运行 `start.bat` 测试程序是否正常工作。

## 部署为Windows服务

### 1. 安装服务

以管理员身份运行：

```bash
service_manager.bat install
```

### 2. 启动服务

```bash
service_manager.bat start
```

### 3. 服务管理

使用Windows服务管理器或命令行管理服务：

```bash
# 查看服务状态
sc query AICodeReviewService

# 启动服务
sc start AICodeReviewService

# 停止服务
sc stop AICodeReviewService
```

## 定时任务部署

如果不想使用Windows服务，可以使用Windows任务计划程序：

### 1. 创建基本任务

1. 打开"任务计划程序"
2. 选择"创建基本任务"
3. 名称：`AI代码审查工具`

### 2. 设置触发器

- 触发器：每天
- 重复间隔：5分钟
- 持续时间：无限期

### 3. 设置操作

- 程序/脚本：`C:\AICodeReview\start.bat`
- 起始位置：`C:\AICodeReview\`

## 监控和维护

### 日志查看

日志文件位置：`logs\code_review.log`

### 数据备份

重要文件备份：
- `config\config.yaml` - 主配置文件
- `config\user_mapping.yaml` - 用户映射
- `data\processed_commits.json` - 已处理的提交记录

### 性能调优

1. **检查间隔调整**：根据提交频率调整 `check_interval`
2. **AI模型选择**：根据成本和质量需求选择合适的模型
3. **日志级别**：生产环境建议使用 `INFO` 级别

## 故障排除

### 常见问题

1. **SVN连接失败**
   - 检查网络连接
   - 验证SVN用户名密码
   - 确认SVN客户端已安装

2. **AI API调用失败**
   - 检查API密钥是否正确
   - 验证网络是否能访问API地址
   - 检查API配额是否充足

3. **钉钉消息发送失败**
   - 检查Webhook URL是否正确
   - 验证机器人权限设置
   - 检查消息格式是否符合要求

### 调试模式

临时启用调试日志：

```yaml
logging:
  level: "DEBUG"
```

## 安全建议

1. **敏感信息保护**
   - 使用环境变量存储密钥
   - 设置合适的文件权限
   - 定期更换API密钥

2. **网络安全**
   - 使用HTTPS连接
   - 配置防火墙规则
   - 启用钉钉机器人签名验证

3. **访问控制**
   - 限制服务器访问权限
   - 使用专用服务账号运行
   - 定期审查用户映射配置
