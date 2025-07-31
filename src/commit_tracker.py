"""
增强的提交状态管理模块
支持详细的提交状态追踪和主动触发机制
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import logging


class CommitStatus(Enum):
    """提交处理状态枚举"""
    DETECTED = "detected"           # 已检测到
    REVIEWING = "reviewing"         # 正在审查中
    REVIEWED = "reviewed"           # 审查完成
    NOTIFIED = "notified"          # 已通知
    FAILED_REVIEW = "failed_review" # 审查失败
    FAILED_NOTIFY = "failed_notify" # 通知失败
    SKIPPED = "skipped"            # 跳过（不在监控路径）


@dataclass
class CommitRecord:
    """提交记录数据类"""
    revision: str
    author: str
    message: str
    timestamp: str
    status: CommitStatus
    review_attempts: int = 0
    last_attempt: Optional[str] = None
    error_message: Optional[str] = None
    review_score: Optional[float] = None
    notification_sent: bool = False
    processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommitRecord':
        """从字典创建实例"""
        data['status'] = CommitStatus(data['status'])
        return cls(**data)


class EnhancedCommitTracker:
    """增强的提交状态跟踪器"""
    
    def __init__(self, data_file: str = "data/commit_tracking.json"):
        self.data_file = Path(data_file)
        self.logger = logging.getLogger(__name__)
        self.commits: Dict[str, CommitRecord] = {}
        self._load_data()
    
    def _load_data(self):
        """加载提交跟踪数据"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.commits = {}
                for revision, commit_data in data.get('commits', {}).items():
                    try:
                        self.commits[revision] = CommitRecord.from_dict(commit_data)
                    except Exception as e:
                        self.logger.warning(f"跳过无效的提交记录 {revision}: {e}")
                
                self.logger.info(f"加载了 {len(self.commits)} 条提交记录")
            else:
                self.logger.info("创建新的提交跟踪文件")
                self._migrate_old_data()
        except Exception as e:
            self.logger.error(f"加载提交跟踪数据失败: {e}")
            self.commits = {}
    
    def _migrate_old_data(self):
        """迁移旧的processed_commits.json数据"""
        old_file = Path("data/processed_commits.json")
        if old_file.exists():
            try:
                with open(old_file, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                
                # 处理旧格式数据
                if isinstance(old_data, dict) and 'processed_commits' in old_data:
                    old_commits = old_data['processed_commits']
                elif isinstance(old_data, list):
                    old_commits = old_data
                else:
                    old_commits = []
                
                # 创建基础记录
                for revision in old_commits:
                    revision_str = str(revision)
                    self.commits[revision_str] = CommitRecord(
                        revision=revision_str,
                        author="unknown",
                        message="migrated from old data",
                        timestamp=datetime.now().isoformat(),
                        status=CommitStatus.NOTIFIED  # 假设旧数据都已完成
                    )
                
                self.logger.info(f"迁移了 {len(old_commits)} 条旧记录")
                self._save_data()
                
                # 备份旧文件
                backup_file = old_file.with_suffix('.json.backup')
                old_file.rename(backup_file)
                self.logger.info(f"旧文件已备份为: {backup_file}")
                
            except Exception as e:
                self.logger.error(f"迁移旧数据失败: {e}")
    
    def _save_data(self):
        """保存提交跟踪数据"""
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_commits': len(self.commits),
                'commits': {rev: record.to_dict() for rev, record in self.commits.items()}
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存提交跟踪数据失败: {e}")
    
    def add_detected_commit(self, revision: str, author: str, message: str) -> bool:
        """添加新检测到的提交"""
        if revision in self.commits:
            return False  # 已存在
        
        self.commits[revision] = CommitRecord(
            revision=revision,
            author=author,
            message=message,
            timestamp=datetime.now().isoformat(),
            status=CommitStatus.DETECTED
        )
        
        self._save_data()
        self.logger.info(f"检测到新提交: {revision} (作者: {author})")
        return True
    
    def start_review(self, revision: str) -> bool:
        """开始审查提交"""
        if revision not in self.commits:
            return False
        
        record = self.commits[revision]
        record.status = CommitStatus.REVIEWING
        record.review_attempts += 1
        record.last_attempt = datetime.now().isoformat()
        
        self._save_data()
        self.logger.info(f"开始审查提交: {revision} (第{record.review_attempts}次尝试)")
        return True
    
    def complete_review(self, revision: str, score: float, processing_time: float = None) -> bool:
        """完成审查"""
        if revision not in self.commits:
            return False
        
        record = self.commits[revision]
        record.status = CommitStatus.REVIEWED
        record.review_score = score
        record.processing_time = processing_time
        record.error_message = None
        
        self._save_data()
        self.logger.info(f"完成审查: {revision} (评分: {score})")
        return True
    
    def fail_review(self, revision: str, error_message: str) -> bool:
        """标记审查失败"""
        if revision not in self.commits:
            return False
        
        record = self.commits[revision]
        record.status = CommitStatus.FAILED_REVIEW
        record.error_message = error_message
        
        self._save_data()
        self.logger.warning(f"审查失败: {revision} - {error_message}")
        return True
    
    def complete_notification(self, revision: str) -> bool:
        """完成通知"""
        if revision not in self.commits:
            return False
        
        record = self.commits[revision]
        record.status = CommitStatus.NOTIFIED
        record.notification_sent = True
        
        self._save_data()
        self.logger.info(f"通知完成: {revision}")
        return True
    
    def fail_notification(self, revision: str, error_message: str) -> bool:
        """标记通知失败"""
        if revision not in self.commits:
            return False
        
        record = self.commits[revision]
        record.status = CommitStatus.FAILED_NOTIFY
        record.error_message = error_message
        
        self._save_data()
        self.logger.warning(f"通知失败: {revision} - {error_message}")
        return True
    
    def skip_commit(self, revision: str, reason: str) -> bool:
        """跳过提交"""
        if revision not in self.commits:
            return False
        
        record = self.commits[revision]
        record.status = CommitStatus.SKIPPED
        record.error_message = reason
        
        self._save_data()
        self.logger.info(f"跳过提交: {revision} - {reason}")
        return True
    
    def get_commits_by_status(self, status: CommitStatus) -> List[CommitRecord]:
        """根据状态获取提交列表"""
        return [record for record in self.commits.values() if record.status == status]
    
    def get_failed_commits(self, max_attempts: int = 3) -> List[CommitRecord]:
        """获取需要重试的失败提交"""
        failed_commits = []
        for record in self.commits.values():
            if (record.status in [CommitStatus.FAILED_REVIEW, CommitStatus.FAILED_NOTIFY] 
                and record.review_attempts < max_attempts):
                failed_commits.append(record)
        return failed_commits
    
    def get_pending_commits(self) -> List[CommitRecord]:
        """获取待处理的提交"""
        return self.get_commits_by_status(CommitStatus.DETECTED)
    
    def get_commit_status(self, revision: str) -> Optional[CommitStatus]:
        """获取提交状态"""
        record = self.commits.get(revision)
        return record.status if record else None
    
    def is_processed(self, revision: str) -> bool:
        """检查提交是否已完全处理"""
        status = self.get_commit_status(revision)
        return status in [CommitStatus.NOTIFIED, CommitStatus.SKIPPED]
    
    def cleanup_old_records(self, days: int = 30):
        """清理旧记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for revision, record in self.commits.items():
            try:
                record_date = datetime.fromisoformat(record.timestamp)
                if record_date < cutoff_date and record.status == CommitStatus.NOTIFIED:
                    to_remove.append(revision)
            except Exception:
                continue
        
        for revision in to_remove:
            del self.commits[revision]
        
        if to_remove:
            self._save_data()
            self.logger.info(f"清理了 {len(to_remove)} 条旧记录")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total': len(self.commits),
            'by_status': {},
            'by_author': {},
            'recent_24h': 0,
            'avg_processing_time': 0,
            'failed_attempts': 0
        }
        
        # 按状态统计
        for status in CommitStatus:
            stats['by_status'][status.value] = len(self.get_commits_by_status(status))
        
        # 按作者统计
        for record in self.commits.values():
            author = record.author
            if author not in stats['by_author']:
                stats['by_author'][author] = 0
            stats['by_author'][author] += 1
        
        # 最近24小时统计
        recent_time = datetime.now() - timedelta(hours=24)
        processing_times = []
        
        for record in self.commits.values():
            try:
                record_time = datetime.fromisoformat(record.timestamp)
                if record_time > recent_time:
                    stats['recent_24h'] += 1
                
                if record.processing_time:
                    processing_times.append(record.processing_time)
                
                if record.review_attempts > 1:
                    stats['failed_attempts'] += record.review_attempts - 1
                    
            except Exception:
                continue
        
        # 平均处理时间
        if processing_times:
            stats['avg_processing_time'] = sum(processing_times) / len(processing_times)
        
        return stats

    # 为了向后兼容的方法别名
    def update_commit_status(self, revision: str, status: str, details: dict = None) -> bool:
        """向后兼容的方法别名"""
        try:
            if status == 'reviewed':
                return self.mark_reviewed(revision, 'migration', details or {})
            elif status == 'notified':
                return self.mark_notified(revision)
            elif status == 'failed':
                return self.mark_failed_review(revision, 'migration error')
            else:
                return self.add_detected_commit(revision, 'unknown', 'migrated')
        except Exception:
            return False
    
    def get_recent_commits(self, limit: int = 10) -> List[CommitRecord]:
        """获取最近的提交记录"""
        return sorted(self.commits.values(), 
                     key=lambda x: x.timestamp, 
                     reverse=True)[:limit]


# 为了向后兼容，提供别名
CommitTracker = EnhancedCommitTracker
