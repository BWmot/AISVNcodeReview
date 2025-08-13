# 🚀 AI SVN代码审查工具 - 安装部署指南

## ❌ 常见错误及解决方案

### 错误1: No module named 'yaml'

```txt
ImportError: No module named 'yaml'
```

**原因**: 缺少 PyYAML 依赖包

**解决方案**:

```bash
# 方案1: 使用安装脚本（推荐）
# Windows:
install.bat

# Linux/Mac:
chmod +x install.sh
./install.sh

# 方案2: 手动安装
pip install pyyaml requests schedule

# 方案3: 使用requirements.txt
pip install -r requirements.txt
```

### 错误2: No module named 'requests'

```txt
ImportError: No module named 'requests'
```

**解决方案**: 同上，安装所有依赖包

### 错误3: 配置文件不存在

```txt
FileNotFoundError: 配置文件不存在: config/config.yaml
```

**解决方案**:

```bash
# 复制示例配置文件
copy config\config.example.yaml config\config.yaml  # Windows
cp config/config.example.yaml config/config.yaml    # Linux/Mac
```

## 📦 快速安装

### Windows 环境

```cmd
# 1. 运行安装脚本
install.bat

# 2. 编辑配置文件
notepad config\config.yaml

# 3. 测试运行
cd batch
python simple_batch_review.py 1
```

### Linux/Mac 环境

```bash
# 1. 运行安装脚本
chmod +x install.sh
./install.sh

# 2. 编辑配置文件
nano config/config.yaml

# 3. 测试运行
cd batch
python3 simple_batch_review.py 1
```

## 🔧 手动安装步骤

### 1. 检查Python环境

```bash
python --version  # 需要 Python 3.7+
pip --version      # 确保pip可用
```

### 2. 安装依赖包

```bash
# 基本依赖
pip install pyyaml requests schedule

# 或使用requirements.txt
pip install -r requirements.txt

# 如果网络慢，使用国内镜像
pip install pyyaml requests schedule -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 3. 配置文件设置

```bash
# 复制配置模板
cp config/config.example.yaml config/config.yaml

# 编辑配置文件，设置:
# - SVN仓库地址、用户名、密码
# - AI API配置
# - 钉钉机器人配置
```

### 4. 验证安装

```bash
# 运行验证脚本
python verify_setup.py

# 或直接测试
python batch/simple_batch_review.py --help
```

## 🐳 Docker 部署（可选）

### 创建 Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

COPY . .
CMD ["python", "src/main.py"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t ai-svn-review .

# 运行容器
docker run -v $(pwd)/config:/app/config -v $(pwd)/data:/app/data ai-svn-review
```

## 🌐 网络环境配置

### 代理设置

```bash
# 如果需要代理
pip install --proxy http://proxy.company.com:8080 pyyaml requests schedule

# 或设置环境变量
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

### 镜像源配置

```bash
# 临时使用镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ pyyaml requests schedule

# 永久配置（创建 ~/.pip/pip.conf）
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
trusted-host = pypi.tuna.tsinghua.edu.cn
```

## 📋 环境检查清单

### Python 环境

- [ ] Python 3.7+ 已安装
- [ ] pip 包管理器可用
- [ ] 网络连接正常

### 项目文件

- [ ] 所有源码文件完整
- [ ] config/config.example.yaml 存在
- [ ] requirements.txt 存在

### 依赖包

- [ ] pyyaml 已安装
- [ ] requests 已安装  
- [ ] schedule 已安装

### 配置文件

- [ ] config/config.yaml 已创建
- [ ] SVN 配置正确
- [ ] AI API 配置正确
- [ ] 钉钉配置正确（可选）

## 🚨 故障排除

### 问题1: pip 安装失败

```bash
# 升级pip
python -m pip install --upgrade pip

# 清除缓存
pip cache purge

# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ pyyaml
```

### 问题2: 权限问题

```bash
# Linux/Mac 使用用户安装
pip install --user pyyaml requests schedule

# Windows 以管理员身份运行
# 右键点击 cmd -> "以管理员身份运行"
```

### 问题3: 虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 在虚拟环境中安装
pip install -r requirements.txt
```

## 📞 技术支持

如果遇到其他问题，请提供以下信息：

1. 操作系统版本
2. Python 版本 (`python --version`)
3. 完整的错误信息
4. 安装步骤和环境信息

## 🎯 快速测试

安装完成后，运行以下命令测试：

```bash
# 1. 验证安装
python verify_setup.py

# 2. 测试配置
python batch/simple_batch_review.py --help

# 3. 快速审查
python batch/simple_batch_review.py 1
```

如果以上命令都能正常运行，说明安装成功！
