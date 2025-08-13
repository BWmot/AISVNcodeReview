"""
AI代码审查模块
使用OpenAI兼容的API对代码变更进行智能分析
"""

import requests
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from config_manager import get_config
from svn_monitor import SVNCommit


@dataclass
class ReviewResult:
    """代码审查结果数据类"""
    commit_revision: str
    overall_score: int  # 1-10分
    summary: str
    detailed_comments: List[Dict[str, str]]
    suggestions: List[str]
    risks: List[str]


class AIReviewer:
    def __init__(self):
        config = get_config()
        self.api_base = config.get('ai.api_base')
        self.api_key = config.get('ai.api_key')
        self.model = config.get('ai.model', 'gpt-3.5-turbo')
        self.max_tokens = config.get('ai.max_tokens', 2000)
        self.temperature = config.get('ai.temperature', 0.3)
        self.system_prompt = config.get('ai.system_prompt', '')
        # 新增配置项
        self.diff_limit = config.get('ai.diff_limit', 8000)  # diff内容截断长度
        self.enable_chunked_review = config.get('ai.enable_chunked_review', True)  # 启用分块审查
        self.chunk_size = config.get('ai.chunk_size', 15000)  # 分块大小
        self.logger = logging.getLogger(__name__)
    
    def review_commit(self, commit: SVNCommit, monitor=None) -> Optional[ReviewResult]:
        """对提交进行AI代码审查"""
        try:
            if monitor:
                monitor.log_details("构建审查提示...", 2)
            
            # 检查diff内容大小
            diff_size = len(commit.diff_content)
            if monitor:
                monitor.log_details(f"原始diff大小: {diff_size:,} 字符", 2)
            
            # 根据大小决定审查策略
            if self.enable_chunked_review and diff_size > self.chunk_size:
                if monitor:
                    monitor.log_details("启用分块审查模式", 2)
                return self._review_commit_chunked(commit, monitor)
            else:
                if monitor:
                    monitor.log_details("使用标准审查模式", 2)
                return self._review_commit_standard(commit, monitor)
                
        except Exception as e:
            self.logger.error(f"代码审查失败 (提交 {commit.revision}): {e}")
            if monitor:
                monitor.log_details(f"审查异常: {str(e)}", 2)
        
        return None
    
    def _review_commit_standard(self, commit: SVNCommit, monitor=None) -> Optional[ReviewResult]:
        """标准审查模式（单次处理）"""
        # 构建审查提示
        review_prompt = self._build_review_prompt(commit, self.diff_limit)
        
        if monitor:
            prompt_length = len(review_prompt)
            monitor.log_details(f"提示长度: {prompt_length:,} 字符", 2)
            monitor.log_details("调用AI API...", 2)
        
        # 调用AI API
        response = self._call_ai_api(review_prompt, monitor)
        
        if response:
            if monitor:
                monitor.log_details("解析AI响应...", 2)
            # 解析审查结果
            result = self._parse_review_response(commit.revision, response)
            
            if monitor:
                monitor.log_details("AI审查响应解析完成", 2)
            return result
        else:
            if monitor:
                monitor.log_details("AI API未返回有效响应", 2)
        
        return None
    
    def _review_commit_chunked(self, commit: SVNCommit, monitor=None) -> Optional[ReviewResult]:
        """分块审查模式（适用于大型提交）"""
        if monitor:
            monitor.log_details("开始分块审查...", 2)
        
        # 分析文件变更，按文件分块
        chunks = self._split_diff_by_files(commit.diff_content, commit.changed_files)
        
        if monitor:
            monitor.log_details(f"分为 {len(chunks)} 个块进行审查", 2)
        
        chunk_results = []
        for i, chunk in enumerate(chunks, 1):
            if monitor:
                monitor.log_details(f"审查第 {i}/{len(chunks)} 块...", 3)
            
            # 创建临时commit对象用于审查
            temp_commit = SVNCommit(
                revision=commit.revision,
                author=commit.author,
                date=commit.date,
                message=commit.message,
                changed_files=chunk['files'],
                diff_content=chunk['diff']
            )
            
            # 审查当前块
            chunk_result = self._review_commit_standard(temp_commit, monitor)
            if chunk_result:
                chunk_results.append(chunk_result)
        
        # 合并分块结果
        if chunk_results:
            return self._merge_chunk_results(commit.revision, chunk_results, monitor)
        
        return None
    
    def _build_review_prompt(self, commit: SVNCommit, diff_limit: int = None) -> str:
        """构建代码审查提示"""
        if diff_limit is None:
            diff_limit = self.diff_limit
            
        prompt_parts = [
            "## 提交信息",
            f"**版本**: {commit.revision}",
            f"**作者**: {commit.author}",
            f"**时间**: {commit.date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**提交信息**: {commit.message}",
            "",
            "## 变更文件列表",
        ]
        
        for file_info in commit.changed_files:
            action_desc = {
                'A': '新增',
                'M': '修改',
                'D': '删除',
                'R': '重命名'
            }.get(file_info['action'], file_info['action'])
            
            prompt_parts.append(
                f"- {action_desc}: {file_info['path']}"
            )
        
        # 检查diff内容大小并适当截断
        diff_content = commit.diff_content
        original_size = len(diff_content)
        
        if original_size > diff_limit:
            # 智能截断：保留文件头信息，截断中间内容
            diff_content = self._smart_truncate_diff(diff_content, diff_limit)
            truncated_note = (f"\n\n⚠️ 注意：原始diff内容 {original_size:,} 字符，"
                            f"已截断至 {len(diff_content):,} 字符以控制token数量。\n"
                            f"请重点关注关键变更和潜在风险。")
        else:
            truncated_note = ""
        
        prompt_parts.extend([
            "",
            "## 代码变更详情",
            "```diff",
            diff_content,
            "```",
            truncated_note,
            "",
            "请对以上代码变更进行详细审查，并按以下JSON格式返回结果：",
            "```json",
            "{",
            '  "overall_score": 8,',
            '  "summary": "整体评估摘要",',
            '  "detailed_comments": [',
            '    {',
            '      "file": "文件路径",',
            '      "line": "行号（如适用）",',
            '      "type": "建议|警告|错误",',
            '      "comment": "具体评论"',
            '    }',
            '  ],',
            '  "suggestions": [',
            '    "改进建议1",',
            '    "改进建议2"',
            '  ],',
            '  "risks": [',
            '    "潜在风险1",',
            '    "潜在风险2"',
            '  ]',
            "}",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    def _smart_truncate_diff(self, diff_content: str, limit: int) -> str:
        """智能截断diff内容，保留关键信息"""
        if len(diff_content) <= limit:
            return diff_content
        
        lines = diff_content.split('\n')
        important_lines = []
        current_size = 0
        
        # 优先保留文件头和重要变更
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            # 保留文件头信息（以---、+++、@@开头的行）
            if (line.startswith('---') or line.startswith('+++') or 
                line.startswith('@@') or line.startswith('Index:')):
                important_lines.append(line)
                current_size += line_size
                continue
            
            # 检查是否还有空间
            if current_size + line_size > limit:
                # 添加截断提示
                important_lines.append("... (内容已截断) ...")
                break
            
            important_lines.append(line)
            current_size += line_size
        
        return '\n'.join(important_lines)
    
    def _split_diff_by_files(self, diff_content: str, changed_files: List) -> List[Dict]:
        """按文件分割diff内容"""
        chunks = []
        lines = diff_content.split('\n')
        current_chunk = []
        current_files = []
        current_size = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_size = len(line) + 1
            
            # 检测文件分界线
            if line.startswith('Index:') or line.startswith('==='):
                # 如果当前块已有内容且达到大小限制，保存当前块
                if current_chunk and current_size > self.chunk_size:
                    chunks.append({
                        'diff': '\n'.join(current_chunk),
                        'files': current_files.copy()
                    })
                    current_chunk = []
                    current_files = []
                    current_size = 0
                
                # 开始新文件
                if line.startswith('Index:'):
                    file_path = line.replace('Index: ', '').strip()
                    # 在changed_files中查找对应文件信息
                    file_info = next((f for f in changed_files 
                                    if f.get('path', '').endswith(file_path)), 
                                   {'path': file_path, 'action': 'M'})
                    current_files.append(file_info)
            
            current_chunk.append(line)
            current_size += line_size
            i += 1
        
        # 添加最后一块
        if current_chunk:
            chunks.append({
                'diff': '\n'.join(current_chunk),
                'files': current_files
            })
        
        return chunks if chunks else [{'diff': diff_content, 'files': changed_files}]
    
    def _merge_chunk_results(self, revision: str, chunk_results: List[ReviewResult], 
                           monitor=None) -> ReviewResult:
        """合并分块审查结果"""
        if monitor:
            monitor.log_details(f"合并 {len(chunk_results)} 个分块结果", 2)
        
        # 计算整体评分（加权平均）
        total_score = sum(result.overall_score for result in chunk_results)
        overall_score = total_score // len(chunk_results)
        
        # 合并摘要
        summaries = [result.summary for result in chunk_results if result.summary]
        combined_summary = "分块审查结果汇总：\n" + "\n".join(f"• {s}" for s in summaries)
        
        # 合并详细评论
        detailed_comments = []
        for result in chunk_results:
            detailed_comments.extend(result.detailed_comments)
        
        # 合并建议
        suggestions = []
        for result in chunk_results:
            suggestions.extend(result.suggestions)
        
        # 合并风险
        risks = []
        for result in chunk_results:
            risks.extend(result.risks)
        
        return ReviewResult(
            commit_revision=revision,
            overall_score=overall_score,
            summary=combined_summary,
            detailed_comments=detailed_comments,
            suggestions=list(set(suggestions)),  # 去重
            risks=list(set(risks))  # 去重
        )
    
    def _call_ai_api(self, prompt: str, monitor=None) -> Optional[str]:
        """调用AI API"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': self.system_prompt
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
        
        try:
            if monitor:
                monitor.log_details(f"发送请求到: {self.api_base}", 3)
                monitor.log_details(f"使用模型: {self.model}", 3)
                
            import time
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            api_time = time.time() - start_time
            
            if monitor:
                monitor.log_details(f"API响应时间: {api_time:.2f}秒", 3)
                monitor.log_details(f"HTTP状态码: {response.status_code}", 3)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                if monitor:
                    content_length = len(content)
                    monitor.log_details(f"响应内容长度: {content_length} 字符", 3)
                    
                    # 检查token使用情况
                    usage = result.get('usage', {})
                    if usage:
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        total_tokens = usage.get('total_tokens', 0)
                        monitor.log_details(f"Token使用: {prompt_tokens}+{completion_tokens}={total_tokens}", 3)
                
                return content
            else:
                error_msg = f"AI API调用失败: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                if monitor:
                    monitor.log_details(f"API错误: {response.status_code}", 3)
                    monitor.log_details(f"错误信息: {response.text[:200]}", 3)
                return None
                
        except requests.Timeout:
            error_msg = "AI API请求超时 (60秒)"
            self.logger.error(error_msg)
            if monitor:
                monitor.log_details("API请求超时", 3)
            return None
        except requests.RequestException as e:
            error_msg = f"AI API请求异常: {e}"
            self.logger.error(error_msg)
            if monitor:
                monitor.log_details(f"网络请求异常: {str(e)}", 3)
            return None
        except Exception as e:
            error_msg = f"AI API调用发生未知错误: {e}"
            self.logger.error(error_msg)
            if monitor:
                monitor.log_details(f"未知错误: {str(e)}", 3)
            return None
    
    def _parse_review_response(self, revision: str, response: str) -> ReviewResult:
        """解析AI审查响应"""
        try:
            # 尝试从响应中提取JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                review_data = json.loads(json_str)
                
                return ReviewResult(
                    commit_revision=revision,
                    overall_score=review_data.get('overall_score', 5),
                    summary=review_data.get('summary', ''),
                    detailed_comments=review_data.get('detailed_comments', []),
                    suggestions=review_data.get('suggestions', []),
                    risks=review_data.get('risks', [])
                )
            else:
                # 如果无法解析JSON，创建简单的结果
                return ReviewResult(
                    commit_revision=revision,
                    overall_score=5,
                    summary=response[:500],
                    detailed_comments=[],
                    suggestions=[],
                    risks=[]
                )
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"解析AI响应JSON失败: {e}")
            # 返回包含原始响应的简化结果
            return ReviewResult(
                commit_revision=revision,
                overall_score=5,
                summary=response[:500],
                detailed_comments=[],
                suggestions=[],
                risks=[]
            )
        except Exception as e:
            self.logger.error(f"解析AI响应时发生错误: {e}")
            return ReviewResult(
                commit_revision=revision,
                overall_score=1,
                summary="审查结果解析失败",
                detailed_comments=[],
                suggestions=[],
                risks=["审查结果解析异常"]
            )
