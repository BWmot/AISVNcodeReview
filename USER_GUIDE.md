# AI SVN代码审查工具 - 使用手册

## 📚 目录

1. [快速入门](#快速入门)
2. [基本使用](#基本使用)
3. [配置详解](#配置详解)
4. [常用命令](#常用命令)
5. [问题解决](#问题解决)
6. [最佳实践](#最佳实践)

---

## 🚀 快速入门

### 第一步：环境检查

运行快速诊断工具检查你的环境：

```bash
python debugTools/quick_diagnostic.py
```

如果发现问题，工具会自动尝试修复。

### 第二步：配置设置

1. **复制配置模板**：
   ```bash
   copy config\config.example.yaml config\config.yaml
   ```

2. **编辑主配置文件**（`config/config.yaml`）：
   ```yaml
   svn:
     repository_url: "http://your-svn-server/svn/project"
     username: "your_username"
     password: "your_password"
     monitored_paths:
       - "/src/main"
       - "/ProjectName/src/main"  # 包含仓库名的完整路径
   
   ai:
     api_base: "https://api.openai.com/v1"
     api_key: "sk-your-api-key"
     model: "gpt-4"
   
   dingtalk:
     webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
   ```

3. **配置用户映射**（`config/user_mapping.yaml`）：
   ```yaml
   users:
     zhangsan: "13812345678"    # SVN用户名: 钉钉手机号
     lisi: "13987654321"
   ```

### 第三步：启动工具

最简单的方式：
```bash
start_complete.bat
```

选择"1"前台运行模式，查看实时日志。

---

## 🎯 基本使用

### 启动模式选择

1. **开发测试模式**（前台运行）：
   ```bash
   python src/main.py
   ```
   - 实时查看日志
   - 按 Ctrl+C 停止
   - 适合调试和测试

2. **生产环境模式**（后台运行）：
   ```bash
   start /min python src/main.py
   ```
   - 后台静默运行
   - 使用任务管理器管理
   - 适合服务器部署

3. **Windows服务模式**：
   ```bash
   python service_wrapper.py install
   python service_wrapper.py start
   ```
   - 开机自启
   - 系统级管理
   - 最稳定的部署方式

### 监控工具状态

实时监控工具运行状态：
```bash
python debugTools/system_monitor.py
```

持续监控模式（每60秒刷新）：
```bash
python debugTools/system_monitor.py --continuous 60
```

---

## ⚙️ 配置详解

### SVN配置要点

#### 1. 路径配置
**关键技巧**：同时配置相对路径和完整路径

```yaml
svn:
  monitored_paths:
    - "/src/main"              # 相对路径
    - "/MyProject/src/main"    # 完整路径（含仓库名）
```

**为什么要这样配置？**
- SVN返回的路径格式可能包含仓库根目录名
- 双重配置确保路径匹配的准确性

#### 2. 检查间隔设置
```yaml
svn:
  check_interval: 300  # 5分钟检查一次
```

推荐设置：
- 开发环境：120-300秒
- 生产环境：300-600秒
- 高频环境：600-900秒

### AI配置优化

#### 1. 模型选择
```yaml
ai:
  model: "gpt-4"           # 推荐：质量最高
  # model: "gpt-3.5-turbo" # 备选：速度更快，成本更低
```

#### 2. 参数调优
```yaml
ai:
  max_tokens: 2000      # 推荐：1500-2500
  temperature: 0.3      # 推荐：0.2-0.4（更稳定）
```

### 钉钉配置技巧

#### 1. 消息分割设置
```yaml
dingtalk:
  message_settings:
    max_message_length: 1000     # 单条消息最大长度
    enable_message_split: true   # 启用自动分割
    show_all_comments: true      # 显示完整审查内容
```

#### 2. 获取Webhook URL
1. 钉钉群 → 群设置 → 智能群助手
2. 添加机器人 → 自定义
3. 安全设置选择"加签"
4. 复制Webhook URL和密钥

---

## 🛠️ 常用命令

### 诊断命令

```bash
# 快速健康检查
python debugTools/quick_diagnostic.py

# 系统状态监控
python debugTools/system_monitor.py

# 测试SVN路径匹配
python debugTools/test_changed_files.py

# 检查最新提交
python debugTools/test_latest_commits.py
```

### 维护命令

```bash
# 重置已处理提交记录
python Tools/AISVNreviewTool/fix_processed_commits.py

# 查看日志分析
python debugTools/log_analyzer.py

# 健康检查报告
python debugTools/health_check.py
```

### 服务管理命令

```bash
# 安装Windows服务
python service_wrapper.py install

# 启动服务
python service_wrapper.py start

# 停止服务
python service_wrapper.py stop

# 卸载服务
python service_wrapper.py remove
```

---

## 🔧 问题解决

### 问题1：检测不到新提交

**症状**：有新提交但工具显示"没有发现新提交"

**解决步骤**：
1. 运行路径测试：
   ```bash
   python debugTools/test_changed_files.py
   ```

2. 如果显示路径不匹配，更新配置：
   ```yaml
   monitored_paths:
     - "/src/main"                    # 原配置
     - "/YourRepositoryName/src/main" # 添加完整路径
   ```

3. 重启工具验证

### 问题2：AI审查失败

**症状**：SVN检测正常但AI审查失败

**解决步骤**：
1. 测试API连接：
   ```bash
   curl -X POST "YOUR_API_BASE/chat/completions" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"model":"gpt-4","messages":[{"role":"user","content":"test"}]}'
   ```

2. 检查配置格式：
   - API密钥是否正确
   - API地址是否可访问
   - 模型名称是否正确

### 问题3：钉钉通知失败

**症状**：审查完成但钉钉没收到消息

**解决步骤**：
1. 测试Webhook：
   ```bash
   curl -X POST "YOUR_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d '{"msgtype":"text","text":{"content":"测试消息"}}'
   ```

2. 检查常见问题：
   - Webhook URL是否正确
   - 密钥是否配置
   - 机器人是否被移出群聊

### 问题4：工具无法启动

**解决方案**：
```bash
# 一键诊断修复
python debugTools/quick_diagnostic.py
```

工具会自动检查并修复：
- Python版本问题
- 依赖包缺失
- 配置文件错误
- 目录结构问题

---

## 💡 最佳实践

### 1. 部署建议

#### 开发环境
```yaml
svn:
  check_interval: 120        # 2分钟检查
logging:
  level: "DEBUG"             # 详细日志
ai:
  max_tokens: 1500          # 节省成本
```

#### 生产环境
```yaml
svn:
  check_interval: 300        # 5分钟检查
logging:
  level: "INFO"              # 标准日志
  max_size_mb: 20           # 更大日志文件
ai:
  max_tokens: 2000          # 更详细审查
```

### 2. 监控策略

#### 定期检查（推荐每天）
```bash
# 创建监控脚本 daily_check.bat
@echo off
echo === 每日健康检查 ===
python debugTools/system_monitor.py
python debugTools/log_analyzer.py
pause
```

#### 自动化监控
1. 设置Windows任务计划程序
2. 每小时运行健康检查
3. 异常时发送邮件通知

### 3. 性能优化

#### 内存优化
- 定期重启服务（每24小时）
- 清理旧日志文件
- 监控内存使用

#### 网络优化
- 使用本地网络部署
- 配置合适的超时时间
- 考虑API缓存

### 4. 安全建议

#### 配置文件安全
- 不要将配置文件提交到版本控制
- 使用环境变量存储敏感信息
- 定期轮换API密钥

#### 权限控制
- 使用专用的SVN账户
- 限制钉钉机器人权限
- 定期审核访问日志

---

## 📞 获取帮助

### 文档资源
- [详细配置指南](CONFIGURATION.md)
- [故障排除手册](TROUBLESHOOTING.md)
- [项目README](README.md)

### 快速支持
1. 运行诊断工具：`python debugTools/quick_diagnostic.py`
2. 查看日志文件：`logs/code_review.log`
3. 使用监控工具：`python debugTools/system_monitor.py`

### 社区支持
- 提交Issue报告问题
- 查看现有Issue寻找解决方案
- 贡献代码改进工具

---

**祝您使用愉快！** 🎉
