"""
配置管理模块
负责加载和管理应用程序配置
"""

import yaml
import os
from typing import Dict, Any, List
from pathlib import Path


class ConfigManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # 自动检测配置文件位置
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = str(config_path)
        self.config = {}
        self.user_mapping = {}
        self.load_config()
        self.load_user_mapping()
    
    def load_config(self) -> Dict[str, Any]:
        """加载主配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            return self.config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def load_user_mapping(self) -> Dict[str, str]:
        """加载用户映射配置"""
        default_mapping_file = str(Path(self.config_path).parent / 'user_mapping.yaml')
        mapping_file = self.get('user_mapping_file', default_mapping_file)
        try:
            with open(mapping_file, 'r', encoding='utf-8') as file:
                mapping_data = yaml.safe_load(file)
                self.user_mapping = mapping_data.get('user_mapping', {})
            return self.user_mapping
        except FileNotFoundError:
            print(f"警告: 用户映射文件不存在: {mapping_file}")
            return {}
        except yaml.YAMLError as e:
            print(f"警告: 用户映射文件格式错误: {e}")
            return {}
    
    def get(self, key_path: str, default=None):
        """
        获取配置值，支持嵌套键路径
        例: get('ai.api_key') 或 get('svn.repository_url')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_user_dingtalk_id(self, svn_username: str) -> str:
        """获取SVN用户对应的钉钉ID"""
        return self.user_mapping.get(svn_username)
    
    def get_path_reviewers(self, file_path: str) -> List[str]:
        """根据文件路径获取特定的审查者"""
        path_reviewers = self.get('path_reviewers', {})
        
        for path_pattern, reviewers in path_reviewers.items():
            if file_path.startswith(path_pattern):
                return reviewers
        
        return []
    
    def get_default_reviewers(self) -> List[str]:
        """获取默认审查者列表"""
        return self.get('default_reviewer', [])
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        dirs_to_create = [
            'logs',
            'data',
            'data/cache',
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


# 全局配置实例（延迟初始化）
config = None

def get_config():
    """获取全局配置实例，延迟初始化"""
    global config
    if config is None:
        config = ConfigManager()
    return config
