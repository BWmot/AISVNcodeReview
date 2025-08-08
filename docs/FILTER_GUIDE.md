# 批量审查过滤功能使用指南

## 概述

新增了强大的过滤功能，可以通过配置文件和命令行参数精确控制要审查的提交。

## 配置文件过滤

在 `config/config.yaml` 中的 `batch_review.filters` 节配置默认过滤规则：

```yaml
batch_review:
  filters:
    # 版本号过滤
    revision_range:
      min_revision: null    # 最小版本号（包含），null表示不限制
      max_revision: null    # 最大版本号（包含），null表示不限制
    
    # 作者过滤
    include_authors: []     # 只包含指定作者（空=包含所有）
    exclude_authors:        # 排除指定作者
      - "jenkins"
      - "jenkins-ci"
      - "ci"
      - "build"
      - "auto-deploy"
    
    # 提交信息过滤
    include_message_patterns: []  # 只包含匹配模式的提交（空=包含所有）
    exclude_message_patterns:     # 排除匹配模式的提交
      - "auto build"
      - "jenkins"
      - "ci build"
      - "[bot]"
      - "merge branch"
      - "automatic"
    
    # 高级选项
    case_sensitive: false   # 大小写敏感
    use_regex: false       # 正则表达式匹配
```

## 命令行参数过滤

命令行参数会覆盖配置文件设置：

### 基本用法

```bash
# 基本审查（使用配置文件默认过滤）
python simple_batch_review.py 7

# 显示帮助
python simple_batch_review.py --help
```

### 版本号过滤

```bash
# 只审查指定版本号范围的提交
python simple_batch_review.py 7 --min-revision 501000 --max-revision 502000

# 只设置最小版本号
python simple_batch_review.py 7 --min-revision 501500

# 只设置最大版本号
python simple_batch_review.py 7 --max-revision 502000
```

### 作者过滤

```bash
# 只审查指定作者的提交
python simple_batch_review.py 7 --include-authors developer1 team-lead admin

# 排除指定作者
python simple_batch_review.py 7 --exclude-authors jenkins ci build

# 组合使用
python simple_batch_review.py 7 --include-authors dev1 dev2 --exclude-authors jenkins
```

### 消息过滤

```bash
# 只审查包含特定关键词的提交
python simple_batch_review.py 7 --include-messages "bug" "fix" "feature"

# 排除包含特定关键词的提交
python simple_batch_review.py 7 --exclude-messages "auto" "build" "merge"

# 组合使用
python simple_batch_review.py 7 --include-messages "fix" --exclude-messages "auto"
```

### 高级选项

```bash
# 启用大小写敏感匹配
python simple_batch_review.py 7 --case-sensitive --exclude-authors Jenkins

# 使用正则表达式匹配
python simple_batch_review.py 7 --regex --exclude-messages "^auto.*" ".*[Bb]uild.*"

# 自动确认，不询问用户
python simple_batch_review.py 7 --auto-confirm
```

### 完整示例

```bash
# 审查版本500000-502000范围内，排除CI用户，排除自动构建，启用大小写敏感，自动确认
python simple_batch_review.py 7 \
  --min-revision 500000 --max-revision 502000 \
  --exclude-authors jenkins ci build auto-deploy \
  --exclude-messages "auto build" "ci build" "[bot]" \
  --case-sensitive \
  --auto-confirm
```

## 过滤逻辑说明

过滤条件按以下顺序应用：

1. **版本号过滤**: 如果设置了min_revision或max_revision，只包含在此范围内的版本
2. **include_authors**: 如果指定，只包含这些作者的提交
3. **exclude_authors**: 排除这些作者的提交
4. **include_message_patterns**: 如果指定，只包含消息匹配这些模式的提交
5. **exclude_message_patterns**: 排除消息匹配这些模式的提交

注意事项：

- 大小写敏感性和正则表达式设置影响所有文本匹配
- 版本号过滤基于SVN版本号进行数字比较
- 所有过滤条件必须同时满足才会包含该提交

## 实际使用场景

### 场景1：审查特定版本范围

```bash
# 审查上次发布以来的所有提交（假设上次发布是版本501000）
python simple_batch_review.py 7 --min-revision 501000
```

### 场景2：只审查开发者提交

```bash
python simple_batch_review.py 7 --include-authors developer1 developer2 team-lead
```

### 场景3：排除自动化提交

```bash
python simple_batch_review.py 7 --exclude-authors jenkins ci --exclude-messages "auto" "build"
```

### 场景4：只审查Bug修复

```bash
python simple_batch_review.py 7 --include-messages "bug" "fix" "hotfix"
```

### 场景5：排除合并提交

```bash
python simple_batch_review.py 7 --exclude-messages "merge" "Merge branch"
```

### 场景6：使用正则表达式精确匹配

```bash
python simple_batch_review.py 7 --regex --exclude-messages "^Merge.*" ".*\[bot\].*"
```

### 场景7：版本号+作者组合过滤

```bash
# 审查版本501000-502000范围内，特定开发者的提交
python simple_batch_review.py 7 \
  --min-revision 501000 --max-revision 502000 \
  --include-authors developer1 developer2
```

## 配置文件vs命令行

- **配置文件**: 设置默认过滤规则，适合长期使用
- **命令行参数**: 临时覆盖配置，适合特定需求  
- **优先级**: 命令行参数 > 配置文件设置

建议在配置文件中设置常用的过滤规则（如排除CI用户），在命令行中根据具体需求进行调整。

## 版本号过滤说明

版本号过滤是基于SVN版本号的数字比较：

- `min_revision`: 最小版本号（包含此版本）
- `max_revision`: 最大版本号（包含此版本）
- 如果只设置一个，另一个不受限制
- 版本号必须是有效的数字

示例：

- `--min-revision 501000`: 只审查版本号 >= 501000 的提交
- `--max-revision 502000`: 只审查版本号 <= 502000 的提交
- `--min-revision 501000 --max-revision 502000`: 只审查版本号在 501000-502000 范围内的提交
