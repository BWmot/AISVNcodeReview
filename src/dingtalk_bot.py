"""
钉钉机器人模块
负责发送代码审查结果到钉钉群
"""

import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
from typing import List, Optional

from config_manager import config
from ai_reviewer import ReviewResult
from svn_monitor import SVNCommit


class DingTalkBot:
    def __init__(self):
        self.webhook_url = config.get('dingtalk.webhook_url')
        self.secret = config.get('dingtalk.secret')
        self.at_all = config.get('dingtalk.at_all', False)
        self.logger = logging.getLogger(__name__)
    
    def send_review_notification(
        self, 
        commit: SVNCommit, 
        review_result: ReviewResult
    ) -> bool:
        """发送代码审查通知"""
        try:
            # 构建消息内容
            message = self._build_review_message(commit, review_result)
            
            # 检查消息长度并分割
            max_length = config.get('dingtalk.message_settings.max_message_length', 3000)
            enable_split = config.get('dingtalk.message_settings.enable_message_split', True)
            
            if enable_split and len(message) > max_length:
                return self._send_split_messages(commit, review_result, message)
            else:
                # 构建@用户列表
                at_users = self._get_at_users(commit)
                return self._send_message(message, at_users)
            
        except Exception as e:
            self.logger.error(f"发送钉钉通知失败: {e}")
            return False
    
    def _build_review_message(
        self, 
        commit: SVNCommit, 
        review_result: ReviewResult
    ) -> str:
        """构建审查消息内容"""
        # 评分对应的emoji
        score_emoji = {
            range(1, 4): "🔴",  # 差
            range(4, 7): "🟡",  # 一般
            range(7, 9): "🟢",  # 好
            range(9, 11): "✅"  # 优秀
        }
        
        emoji = "❓"
        for score_range, em in score_emoji.items():
            if review_result.overall_score in score_range:
                emoji = em
                break
        
        # 构建基础信息
        message_parts = [
            f"## {emoji} 代码审查报告",
            "",
            f"**📝 提交信息**",
            f"- 版本: `{commit.revision}`",
            f"- 作者: {commit.author}",
            f"- 时间: {commit.date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 描述: {commit.message}",
            "",
            f"**📊 审查评分: {review_result.overall_score}/10**",
            "",
        ]
        
        # 添加总结
        if review_result.summary:
            message_parts.extend([
                f"**📋 审查总结**",
                review_result.summary,
                ""
            ])
        
        # 添加详细评论
        if review_result.detailed_comments:
            message_parts.append("**💬 详细评论**")
            # 显示所有评论，不再截断
            for i, comment in enumerate(review_result.detailed_comments):
                comment_type = comment.get('type', '建议')
                file_path = comment.get('file', '')
                comment_text = comment.get('comment', '')
                
                type_emoji = {
                    '错误': '❌',
                    '警告': '⚠️', 
                    '建议': '💡'
                }.get(comment_type, '💬')
                
                # 如果评论太长，进行截断并添加省略号
                if len(comment_text) > 100:
                    comment_text = comment_text[:100] + "..."
                
                message_parts.append(
                    f"{i+1}. {type_emoji} **{comment_type}** "
                    f"({file_path}): {comment_text}"
                )
            message_parts.append("")
        
        # 添加改进建议
        if review_result.suggestions:
            message_parts.append("**✨ 改进建议**")
            # 显示所有建议，不再截断
            for i, suggestion in enumerate(review_result.suggestions):
                # 如果建议太长，进行截断
                if len(suggestion) > 150:
                    suggestion = suggestion[:150] + "..."
                message_parts.append(f"{i+1}. {suggestion}")
            message_parts.append("")
        
        # 添加风险提示
        if review_result.risks:
            message_parts.append("**⚠️ 潜在风险**")
            # 显示所有风险，不再截断
            for i, risk in enumerate(review_result.risks):
                # 如果风险描述太长，进行截断
                if len(risk) > 150:
                    risk = risk[:150] + "..."
                message_parts.append(f"{i+1}. {risk}")
            message_parts.append("")
        
        # 添加变更文件列表
        if commit.changed_files:
            message_parts.append("**📁 变更文件**")
            for file_info in commit.changed_files[:5]:
                action_emoji = {
                    'A': '➕',
                    'M': '✏️',
                    'D': '➖',
                    'R': '🔄'
                }.get(file_info['action'], '📄')
                
                message_parts.append(
                    f"- {action_emoji} {file_info['path']}"
                )
            
            if len(commit.changed_files) > 5:
                message_parts.append(
                    f"... 还有 {len(commit.changed_files) - 5} 个文件"
                )
        
        return "\n".join(message_parts)
    
    def _send_split_messages(
        self, 
        commit: SVNCommit, 
        review_result: ReviewResult,
        full_message: str
    ) -> bool:
        """分割长消息并分批发送"""
        try:
            at_users = self._get_at_users(commit)
            
            # 第一条消息：基本信息和总结
            basic_info = self._build_basic_info_message(commit, review_result)
            success1 = self._send_message(basic_info, at_users)
            
            # 第二条消息：详细评论
            if review_result.detailed_comments:
                comments_msg = self._build_comments_message(review_result)
                success2 = self._send_message(comments_msg)
            else:
                success2 = True
            
            # 第三条消息：建议和风险
            suggestions_risks_msg = self._build_suggestions_risks_message(review_result)
            if suggestions_risks_msg.strip():
                success3 = self._send_message(suggestions_risks_msg)
            else:
                success3 = True
            
            return success1 and success2 and success3
            
        except Exception as e:
            self.logger.error(f"分割消息发送失败: {e}")
            return False
    
    def _build_basic_info_message(
        self, 
        commit: SVNCommit, 
        review_result: ReviewResult
    ) -> str:
        """构建基本信息消息"""
        # 评分对应的emoji
        score_emoji = {
            range(1, 4): "🔴",
            range(4, 7): "🟡",
            range(7, 9): "🟢",
            range(9, 11): "✅"
        }
        
        emoji = "❓"
        for score_range, em in score_emoji.items():
            if review_result.overall_score in score_range:
                emoji = em
                break
        
        message_parts = [
            f"## {emoji} 代码审查报告 (1/3)",
            "",
            "**📝 提交信息**",
            f"- 版本: `{commit.revision}`",
            f"- 作者: {commit.author}",
            f"- 时间: {commit.date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 描述: {commit.message}",
            "",
            f"**📊 审查评分: {review_result.overall_score}/10**",
            "",
        ]
        
        # 添加总结
        if review_result.summary:
            message_parts.extend([
                "**📋 审查总结**",
                review_result.summary,
                ""
            ])
        
        # 添加变更文件列表（简化版）
        if commit.changed_files:
            message_parts.append("**📁 变更文件**")
            for file_info in commit.changed_files[:5]:
                action_emoji = {
                    'A': '➕',
                    'M': '✏️',
                    'D': '➖',
                    'R': '🔄'
                }.get(file_info['action'], '📄')
                
                message_parts.append(f"- {action_emoji} {file_info['path']}")
            
            if len(commit.changed_files) > 5:
                message_parts.append(f"... 还有 {len(commit.changed_files) - 5} 个文件")
        
        return "\n".join(message_parts)
    
    def _build_comments_message(self, review_result: ReviewResult) -> str:
        """构建详细评论消息"""
        message_parts = [
            "## 💬 详细评论 (2/3)",
            ""
        ]
        
        # 添加详细评论（显示全部）
        for i, comment in enumerate(review_result.detailed_comments):
            comment_type = comment.get('type', '建议')
            file_path = comment.get('file', '')
            comment_text = comment.get('comment', '')
            
            type_emoji = {
                '错误': '❌',
                '警告': '⚠️',
                '建议': '💡'
            }.get(comment_type, '💬')
            
            # 动态截断长度配置
            max_length = config.get('dingtalk.message_settings.comment_max_length', 200)
            if len(comment_text) > max_length:
                comment_text = comment_text[:max_length] + "..."
            
            message_parts.append(
                f"{i+1}. {type_emoji} **{comment_type}** ({file_path}): {comment_text}"
            )
        
        return "\n".join(message_parts)
    
    def _build_suggestions_risks_message(self, review_result: ReviewResult) -> str:
        """构建建议和风险消息"""
        message_parts = [
            "## ✨ 建议与风险 (3/3)",
            ""
        ]
        
        # 添加改进建议（显示全部）
        if review_result.suggestions:
            message_parts.append("**💡 改进建议**")
            max_length = config.get('dingtalk.message_settings.suggestion_max_length', 200)
            
            for i, suggestion in enumerate(review_result.suggestions):
                if len(suggestion) > max_length:
                    suggestion = suggestion[:max_length] + "..."
                message_parts.append(f"{i+1}. {suggestion}")
            message_parts.append("")
        
        # 添加风险提示（显示全部）
        if review_result.risks:
            message_parts.append("**⚠️ 潜在风险**")
            max_length = config.get('dingtalk.message_settings.suggestion_max_length', 200)
            
            for i, risk in enumerate(review_result.risks):
                if len(risk) > max_length:
                    risk = risk[:max_length] + "..."
                message_parts.append(f"{i+1}. {risk}")
        
        return "\n".join(message_parts)
    
    def _get_at_users(self, commit: SVNCommit) -> List[str]:
        """获取需要@的用户列表"""
        at_users = []
        
        # 获取提交作者对应的钉钉用户
        author_dingtalk = config.get_user_dingtalk_id(commit.author)
        if author_dingtalk:
            at_users.append(author_dingtalk)
        
        # 获取路径相关的审查者
        for file_info in commit.changed_files:
            path_reviewers = config.get_path_reviewers(file_info['path'])
            for reviewer in path_reviewers:
                reviewer_dingtalk = config.get_user_dingtalk_id(reviewer)
                if reviewer_dingtalk and reviewer_dingtalk not in at_users:
                    at_users.append(reviewer_dingtalk)
        
        # 如果没有找到相关用户，使用默认审查者
        if not at_users:
            default_reviewers = config.get_default_reviewers()
            for reviewer in default_reviewers:
                if reviewer not in at_users:
                    at_users.append(reviewer)
        
        return at_users
    
    def _send_message(self, message: str, at_users: List[str] = None) -> bool:
        """发送钉钉消息"""
        if not self.webhook_url:
            self.logger.error("钉钉Webhook URL未配置")
            return False
        
        # 生成签名
        url = self.webhook_url
        if self.secret:
            url = self._generate_signed_url()
        
        # 处理@用户列表
        at_mobiles = []
        at_user_ids = []
        
        if at_users:
            for user in at_users:
                if user.startswith('@'):
                    at_mobiles.append(user[1:])
                elif user.isdigit() or (len(user) == 11 and user.startswith('1')):
                    at_mobiles.append(user)
                else:
                    at_user_ids.append(user)
        
        # 构建消息体
        data = {
            'msgtype': 'markdown',
            'markdown': {
                'title': '代码审查报告',
                'text': message
            },
            'at': {
                'atMobiles': at_mobiles,
                'atUserIds': at_user_ids,
                'isAtAll': self.at_all
            }
        }
        
        try:
            response = requests.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    self.logger.info("钉钉消息发送成功")
                    return True
                else:
                    self.logger.error(f"钉钉消息发送失败: {result}")
                    return False
            else:
                self.logger.error(
                    f"钉钉API调用失败: {response.status_code} - {response.text}"
                )
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"钉钉消息发送异常: {e}")
            return False
    
    def _generate_signed_url(self) -> str:
        """生成带签名的钉钉Webhook URL"""
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        
        hmac_code = hmac.new(
            secret_enc, 
            string_to_sign_enc, 
            digestmod=hashlib.sha256
        ).digest()
        
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
    
    def send_error_notification(self, error_message: str) -> bool:
        """发送错误通知"""
        message = f"## ❌ 代码审查服务异常\n\n{error_message}"
        return self._send_message(message)
