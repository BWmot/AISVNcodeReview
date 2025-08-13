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
        self.logger = logging.getLogger(__name__)
    
    def review_commit(self, commit: SVNCommit) -> Optional[ReviewResult]:
        """对提交进行AI代码审查"""
        try:
            # 构建审查提示
            review_prompt = self._build_review_prompt(commit)
            
            # 调用AI API
            response = self._call_ai_api(review_prompt)
            
            if response:
                # 解析审查结果
                result = self._parse_review_response(commit.revision, response)
                return result
            
        except Exception as e:
            self.logger.error(f"代码审查失败 (提交 {commit.revision}): {e}")
        
        return None
    
    def _build_review_prompt(self, commit: SVNCommit) -> str:
        """构建代码审查提示"""
        prompt_parts = [
            f"## 提交信息",
            f"**版本**: {commit.revision}",
            f"**作者**: {commit.author}",
            f"**时间**: {commit.date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**提交信息**: {commit.message}",
            "",
            f"## 变更文件列表",
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
        
        prompt_parts.extend([
            "",
            f"## 代码变更详情",
            "```diff",
            commit.diff_content[:8000],  # 限制diff长度避免token超限
            "```",
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
    
    def _call_ai_api(self, prompt: str) -> Optional[str]:
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
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return content
            else:
                self.logger.error(f"AI API调用失败: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"AI API请求异常: {e}")
            return None
        except Exception as e:
            self.logger.error(f"AI API调用发生未知错误: {e}")
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
