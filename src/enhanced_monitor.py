"""
SVN主动触发监听器
支持SVN post-commit hook和定时检查两种模式
"""

import os
import sys
import threading
import time
from typing import Optional, List
from pathlib import Path
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent))

from config_manager import config
from svn_monitor import SVNMonitor, SVNCommit
from commit_tracker import EnhancedCommitTracker, CommitStatus
from ai_reviewer import AIReviewer
from dingtalk_bot import DingTalkBot


class SVNWebhookHandler(BaseHTTPRequestHandler):
    """SVN Webhook处理器"""
    
    def __init__(self, *args, trigger_callback=None, **kwargs):
        self.trigger_callback = trigger_callback
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """处理POST请求（SVN hook触发）"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # 解析提交信息
            if self.path == '/svn-hook':
                self._handle_svn_hook(post_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            
        except Exception as e:
            logging.error(f"处理SVN webhook失败: {e}")
            self.send_response(500)
            self.end_headers()
    
    def _handle_svn_hook(self, post_data: bytes):
        """处理SVN hook数据"""
        try:
            # 解析hook数据（可能是JSON或表单数据）
            if post_data:
                try:
                    hook_data = json.loads(post_data.decode('utf-8'))
                except json.JSONDecodeError:
                    # 尝试解析为表单数据
                    hook_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                
                # 提取提交信息
                revision = self._extract_revision(hook_data)
                if revision and self.trigger_callback:
                    logging.info(f"SVN hook触发，提交版本: {revision}")
                    self.trigger_callback(revision)
            
        except Exception as e:
            logging.error(f"解析SVN hook数据失败: {e}")
    
    def _extract_revision(self, hook_data) -> Optional[str]:
        """从hook数据中提取版本号"""
        # 支持多种格式的hook数据
        if isinstance(hook_data, dict):
            return (hook_data.get('revision') or 
                   hook_data.get('rev') or 
                   hook_data.get('r'))
        return None
    
    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass


class EnhancedSVNMonitor:
    """增强的SVN监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.commit_tracker = EnhancedCommitTracker()
        self.svn_monitor = SVNMonitor()
        self.ai_reviewer = AIReviewer()
        self.dingtalk_bot = DingTalkBot()
        
        # 配置
        self.webhook_enabled = config.get('svn.webhook.enabled', False)
        self.webhook_port = config.get('svn.webhook.port', 8080)
        self.check_interval = config.get('svn.check_interval', 300)
        self.max_retry_attempts = config.get('svn.max_retry_attempts', 3)
        
        # 运行状态
        self.running = False
        self.webhook_server = None
        self.polling_thread = None
        
    def start(self, webhook_port=None):
        """启动监控
        
        Args:
            webhook_port: 可选的webhook端口，会覆盖配置文件中的设置
        """
        # 如果提供了端口参数，更新配置
        if webhook_port is not None:
            self.webhook_port = webhook_port
            
        self.running = True
        self.logger.info("启动增强SVN监控...")
        
        # 启动webhook服务器（如果启用）
        if self.webhook_enabled:
            self._start_webhook_server()
        
        # 启动定时检查线程
        self._start_polling_thread()
        
        # 处理待处理的提交
        self._process_pending_commits()
        
        # 重试失败的提交
        self._retry_failed_commits()
        
        self.logger.info("增强SVN监控已启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.logger.info("停止增强SVN监控...")
        
        if self.webhook_server:
            self.webhook_server.shutdown()
            self.webhook_server = None
        
        if self.polling_thread:
            self.polling_thread.join(timeout=5)
        
        self.logger.info("增强SVN监控已停止")
    
    def _start_webhook_server(self):
        """启动webhook服务器"""
        try:
            def handler(*args, **kwargs):
                return SVNWebhookHandler(*args, 
                                       trigger_callback=self._handle_webhook_trigger,
                                       **kwargs)
            
            self.webhook_server = HTTPServer(('localhost', self.webhook_port), handler)
            
            # 在单独线程中运行服务器
            webhook_thread = threading.Thread(
                target=self.webhook_server.serve_forever,
                daemon=True
            )
            webhook_thread.start()
            
            self.logger.info(f"SVN Webhook服务器已启动，端口: {self.webhook_port}")
            
        except Exception as e:
            self.logger.error(f"启动webhook服务器失败: {e}")
            self.webhook_enabled = False
    
    def _start_polling_thread(self):
        """启动定时检查线程"""
        self.polling_thread = threading.Thread(
            target=self._polling_loop,
            daemon=True
        )
        self.polling_thread.start()
        self.logger.info(f"定时检查已启动，间隔: {self.check_interval}秒")
    
    def _polling_loop(self):
        """定时检查循环"""
        while self.running:
            try:
                self._check_for_new_commits()
                self._process_pending_commits()
                self._retry_failed_commits()
                
                # 清理旧记录（每天执行一次）
                if int(time.time()) % 86400 == 0:  # 每24小时
                    self.commit_tracker.cleanup_old_records()
                
            except Exception as e:
                self.logger.error(f"定时检查过程中出错: {e}")
            
            # 等待下次检查
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _handle_webhook_trigger(self, revision: str):
        """处理webhook触发"""
        try:
            # 立即检查这个特定的提交
            commit = self._get_commit_info(revision)
            if commit:
                self._process_single_commit(commit)
            else:
                self.logger.warning(f"无法获取提交信息: {revision}")
                
        except Exception as e:
            self.logger.error(f"处理webhook触发失败: {e}")
    
    def _check_for_new_commits(self):
        """检查新提交"""
        try:
            # 获取最新提交
            commits = self.svn_monitor.get_latest_commits()
            
            for commit in commits:
                # 检查是否已存在
                if not self.commit_tracker.is_processed(commit.revision):
                    # 添加到跟踪器
                    if self.commit_tracker.add_detected_commit(
                        commit.revision, commit.author, commit.message
                    ):
                        # 立即处理新提交
                        threading.Thread(
                            target=self._process_single_commit,
                            args=(commit,),
                            daemon=True
                        ).start()
                        
        except Exception as e:
            self.logger.error(f"检查新提交失败: {e}")
    
    def _get_commit_info(self, revision: str) -> Optional[SVNCommit]:
        """获取指定提交的信息"""
        try:
            # 使用SVN monitor获取提交详情
            commits = self.svn_monitor.get_commits_in_range(revision, revision)
            return commits[0] if commits else None
        except Exception as e:
            self.logger.error(f"获取提交 {revision} 信息失败: {e}")
            return None
    
    def _process_pending_commits(self):
        """处理待处理的提交"""
        pending_commits = self.commit_tracker.get_pending_commits()
        
        for record in pending_commits:
            try:
                commit = self._get_commit_info(record.revision)
                if commit:
                    self._process_single_commit(commit)
                else:
                    self.commit_tracker.skip_commit(
                        record.revision, "无法获取提交信息"
                    )
            except Exception as e:
                self.logger.error(f"处理待处理提交 {record.revision} 失败: {e}")
    
    def _retry_failed_commits(self):
        """重试失败的提交"""
        failed_commits = self.commit_tracker.get_failed_commits(self.max_retry_attempts)
        
        for record in failed_commits:
            try:
                commit = self._get_commit_info(record.revision)
                if commit:
                    self.logger.info(f"重试失败提交: {record.revision}")
                    self._process_single_commit(commit)
                    
            except Exception as e:
                self.logger.error(f"重试提交 {record.revision} 失败: {e}")
    
    def _process_single_commit(self, commit: SVNCommit):
        """处理单个提交"""
        start_time = time.time()
        
        try:
            # 开始审查
            if not self.commit_tracker.start_review(commit.revision):
                return
            
            # AI审查
            review_result = self.ai_reviewer.review_commit(commit)
            processing_time = time.time() - start_time
            
            if review_result:
                # 审查成功
                self.commit_tracker.complete_review(
                    commit.revision, 
                    review_result.overall_score,
                    processing_time
                )
                
                # 发送通知
                success = self.dingtalk_bot.send_review_notification(
                    commit, review_result
                )
                
                if success:
                    self.commit_tracker.complete_notification(commit.revision)
                    self.logger.info(f"提交 {commit.revision} 处理完成")
                else:
                    self.commit_tracker.fail_notification(
                        commit.revision, "钉钉通知发送失败"
                    )
            else:
                # 审查失败
                self.commit_tracker.fail_review(
                    commit.revision, "AI审查失败"
                )
                
        except Exception as e:
            error_msg = f"处理提交异常: {str(e)}"
            self.commit_tracker.fail_review(commit.revision, error_msg)
            self.logger.error(f"处理提交 {commit.revision} 异常: {e}")
    
    def get_status_summary(self) -> dict:
        """获取状态摘要"""
        stats = self.commit_tracker.get_statistics()
        
        return {
            'monitoring': {
                'running': self.running,
                'webhook_enabled': self.webhook_enabled,
                'webhook_port': self.webhook_port if self.webhook_enabled else None,
                'check_interval': self.check_interval
            },
            'statistics': stats,
            'pending_count': len(self.commit_tracker.get_pending_commits()),
            'failed_count': len(self.commit_tracker.get_failed_commits())
        }


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/enhanced_monitor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 创建监控器
    monitor = EnhancedSVNMonitor()
    
    try:
        monitor.start()
        
        # 保持运行
        while True:
            time.sleep(60)
            # 每分钟打印一次状态
            status = monitor.get_status_summary()
            logging.info(f"状态摘要: 待处理={status['pending_count']}, "
                        f"失败={status['failed_count']}")
            
    except KeyboardInterrupt:
        logging.info("收到停止信号")
    finally:
        monitor.stop()


if __name__ == "__main__":
    main()
