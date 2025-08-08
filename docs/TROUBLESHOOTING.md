# 常见问题快速解决指南

## 🚨 紧急问题处理

### 工具无法启动

**症状**：运行 `python src/main.py` 后立即退出或报错

**快速检查清单**：
1. ✅ Python版本是否 >= 3.7
2. ✅ 依赖包是否安装：`pip install -r requirements.txt`
3. ✅ 配置文件是否存在：`config/config.yaml`
4. ✅ SVN命令是否可用：`svn --version`

**快速修复**：
```bash
# 1. 重新安装依赖
pip install -r requirements.txt

# 2. 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 3. 测试SVN连接
svn info YOUR_SVN_URL --username YOUR_USER --password YOUR_PASS
```

### 检测不到新提交

**症状**：有新提交但工具日志显示"没有发现新提交"

**最可能的原因**：路径匹配问题

**快速修复**：
```bash
# 1. 运行路径检测工具
cd debugTools
python test_changed_files.py

# 2. 检查输出，如果显示路径不匹配，更新config.yaml中的监控路径
# 添加完整路径格式：/仓库名/原路径
```

### AI审查失败

**症状**：检测到提交但AI审查过程失败

**快速检查**：
```bash
# 测试API连接
curl -X POST "YOUR_API_BASE/chat/completions" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"YOUR_MODEL","messages":[{"role":"user","content":"test"}]}'
```

### 钉钉通知失败

**症状**：审查完成但钉钉没有收到消息

**快速检查**：
```bash
# 测试钉钉webhook
curl -X POST "YOUR_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"msgtype":"text","text":{"content":"测试消息"}}'
```

## 🔧 配置问题详解

### SVN路径配置详解

**核心问题**：SVN返回的路径格式包含仓库根目录名称

**示例说明**：
- 仓库URL：`http://server/svn/MyProject`
- 你的监控路径配置：`/src/main`
- SVN实际返回路径：`/MyProject/src/main/file.txt`

**解决方案**：在监控路径前添加仓库名称
```yaml
monitored_paths:
  - "/src/main"              # 原配置
  - "/MyProject/src/main"    # 修正后配置
```

**如何确定仓库名称**：
```bash
# 方法1：查看SVN info输出
svn info YOUR_SVN_URL

# 方法2：使用调试工具
cd debugTools
python test_changed_files.py
```

### 消息分割配置优化

**问题**：钉钉消息被截断，重要信息丢失

**原因**：单条消息超过钉钉长度限制

**解决方案**：
```yaml
dingtalk:
  message_settings:
    max_message_length: 800        # 降低单条消息长度
    enable_message_split: true     # 启用自动分割
    show_all_comments: true        # 确保显示所有内容
```

### 用户映射问题

**问题**：@用户功能不工作

**检查步骤**：
1. 确认手机号格式正确（不含空格、连字符）
2. 确认用户在钉钉群中
3. 确认SVN用户名拼写正确

**配置示例**：
```yaml
users:
  zhangsan: "13812345678"     # 正确：纯数字
  lisi: "138-1234-5678"       # 错误：包含连字符
  wangwu: "138 1234 5678"     # 错误：包含空格
```

## 🐛 运行时错误处理

### 编码错误

**错误信息**：`UnicodeDecodeError: 'utf-8' codec can't decode`

**解决方案**：
1. 工具已内置编码处理，通常无需手动处理
2. 如果仍有问题，检查系统区域设置
3. 确保SVN客户端支持UTF-8编码

### 内存不足

**症状**：工具运行一段时间后崩溃或变慢

**解决方案**：
```yaml
# 1. 调整日志配置
logging:
  max_size_mb: 5              # 减小日志文件大小
  backup_count: 3             # 减少备份文件数量

# 2. 增加检查间隔
svn:
  check_interval: 600         # 增加到10分钟

# 3. 限制AI token数量
ai:
  max_tokens: 1500            # 减少到1500
```

### 网络超时

**错误信息**：`Request timeout` 或 `Connection timeout`

**解决方案**：
1. 检查网络连接稳定性
2. 增加超时时间（在代码中）
3. 使用更快的AI模型
4. 考虑设置网络代理

## 🔄 维护和监控脚本

### 健康检查脚本

创建 `debugTools/health_check.py`：
```python
#!/usr/bin/env python3
"""健康检查脚本"""
import os
import sys
import subprocess
import requests
import yaml

def check_health():
    print("=== AI SVN代码审查工具健康检查 ===")
    
    # 检查配置文件
    try:
        with open('../config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ 配置文件正常")
    except Exception as e:
        print(f"❌ 配置文件错误: {e}")
        return False
    
    # 检查SVN连接
    try:
        cmd = ['svn', 'info', config['svn']['repository_url'],
               '--username', config['svn']['username'],
               '--password', config['svn']['password'],
               '--non-interactive', '--trust-server-cert']
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0:
            print("✅ SVN连接正常")
        else:
            print(f"❌ SVN连接失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ SVN测试异常: {e}")
        return False
    
    # 检查AI API连接
    try:
        response = requests.get(config['ai']['api_base'], timeout=10)
        print("✅ AI API连接正常")
    except Exception as e:
        print(f"❌ AI API连接失败: {e}")
    
    # 检查钉钉webhook
    try:
        test_data = {
            "msgtype": "text",
            "text": {"content": "健康检查测试消息"}
        }
        response = requests.post(config['dingtalk']['webhook_url'], 
                               json=test_data, timeout=10)
        if response.status_code == 200:
            print("✅ 钉钉webhook正常")
        else:
            print(f"❌ 钉钉webhook异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 钉钉测试失败: {e}")
    
    print("\n健康检查完成！")
    return True

if __name__ == "__main__":
    check_health()
```

### 日志分析脚本

创建 `debugTools/log_analyzer.py`：
```python
#!/usr/bin/env python3
"""日志分析脚本"""
import re
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_logs():
    log_file = "../logs/code_review.log"
    
    stats = {
        'total_commits': 0,
        'successful_reviews': 0,
        'failed_reviews': 0,
        'dingtalk_success': 0,
        'dingtalk_failed': 0,
        'errors': [],
        'performance': []
    }
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 统计提交处理
                if '发现' in line and '个新提交' in line:
                    match = re.search(r'发现 (\d+) 个新提交', line)
                    if match:
                        stats['total_commits'] += int(match.group(1))
                
                # 统计审查结果
                if '审查完成，评分:' in line:
                    stats['successful_reviews'] += 1
                
                # 统计钉钉通知
                if '钉钉消息发送成功' in line:
                    stats['dingtalk_success'] += 1
                
                # 收集错误
                if 'ERROR' in line:
                    stats['errors'].append(line.strip())
    
    except FileNotFoundError:
        print("❌ 日志文件不存在")
        return
    
    print("=== 日志分析报告 ===")
    print(f"总提交数: {stats['total_commits']}")
    print(f"成功审查: {stats['successful_reviews']}")
    print(f"钉钉通知成功: {stats['dingtalk_success']}")
    print(f"错误数量: {len(stats['errors'])}")
    
    if stats['errors']:
        print("\n最近的错误:")
        for error in stats['errors'][-5:]:
            print(f"  {error}")

if __name__ == "__main__":
    analyze_logs()
```

## 📝 性能优化建议

### 针对不同环境的配置建议

#### 开发环境
```yaml
svn:
  check_interval: 120         # 2分钟检查一次
ai:
  max_tokens: 1500           # 较少的token
  temperature: 0.2           # 更稳定的输出
logging:
  level: "DEBUG"             # 详细日志
```

#### 生产环境
```yaml
svn:
  check_interval: 300         # 5分钟检查一次
ai:
  max_tokens: 2000           # 更详细的审查
  temperature: 0.3           # 平衡稳定性和创造性
logging:
  level: "INFO"              # 正常日志级别
  max_size_mb: 20            # 更大的日志文件
```

#### 高频环境
```yaml
svn:
  check_interval: 600         # 10分钟检查一次
dingtalk:
  message_settings:
    max_message_length: 1200  # 更长的消息
    enable_message_split: true
```

### 资源使用优化

#### 内存优化
1. 定期重启服务（每24小时）
2. 限制并发处理数量
3. 及时清理临时文件

#### 网络优化
1. 使用本地网络环境部署
2. 配置合适的超时时间
3. 考虑API缓存机制

#### 存储优化
1. 定期清理旧日志
2. 压缩历史数据
3. 监控磁盘使用情况

---

这个补充文档涵盖了实际运行中可能遇到的各种问题和解决方案，帮助用户快速定位和解决问题。
