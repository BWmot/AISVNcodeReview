"""
AI SVN代码审查工具主程序
监控SVN提交，使用AI进行代码审查，并通过钉钉发送通知
"""

import logging
import schedule
import time
import sys
import threading
import signal
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

from config_manager import config
from svn_monitor import SVNMonitor
from enhanced_monitor import EnhancedSVNMonitor
from ai_reviewer import AIReviewer
from dingtalk_bot import DingTalkBot


def setup_logging():
    """设置日志配置"""
    log_level = getattr(
        logging,
        config.get('logging.level', 'INFO').upper()
    )
    log_file = config.get('logging.file', 'logs/code_review.log')
    
    # 确保日志目录存在
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def process_new_commits():
    """处理新提交的核心逻辑"""
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化各个组件
        svn_monitor = SVNMonitor()
        ai_reviewer = AIReviewer()
        dingtalk_bot = DingTalkBot()
        
        # 检查新提交
        new_commits = svn_monitor.check_new_commits()
        
        if not new_commits:
            logger.debug("没有新的提交需要处理")
            return
        
        # 处理每个新提交
        for commit in new_commits:
            logger.info(f"开始处理提交: {commit.revision} (作者: {commit.author})")
            
            try:
                # 使用AI进行代码审查
                logger.info(f"正在对提交 {commit.revision} 进行AI审查...")
                review_result = ai_reviewer.review_commit(commit)
                
                if review_result:
                    logger.info(
                        f"提交 {commit.revision} 审查完成，"
                        f"评分: {review_result.overall_score}/10"
                    )
                    
                    # 发送钉钉通知
                    logger.info(f"发送钉钉通知...")
                    success = dingtalk_bot.send_review_notification(
                        commit, review_result
                    )
                    
                    if success:
                        logger.info(f"提交 {commit.revision} 处理完成")
                        # 标记为已处理
                        svn_monitor.mark_commit_processed(commit.revision)
                    else:
                        logger.error(f"提交 {commit.revision} 钉钉通知发送失败")
                        
                else:
                    logger.error(f"提交 {commit.revision} AI审查失败")
                    
            except Exception as e:
                logger.error(f"处理提交 {commit.revision} 时发生异常: {e}")
                # 发送错误通知
                dingtalk_bot.send_error_notification(
                    f"处理提交 {commit.revision} 时发生异常: {str(e)}"
                )
                
    except Exception as e:
        logger.error(f"处理新提交时发生异常: {e}")
        try:
            dingtalk_bot = DingTalkBot()
            dingtalk_bot.send_error_notification(
                f"代码审查服务异常: {str(e)}"
            )
        except:
            pass  # 避免在错误处理中再次出错


def main():
    """主函数"""
    # 检查命令行参数，确定运行模式
    enhanced_mode = config.get('monitor.enhanced_mode', False)
    webhook_port = config.get('monitor.webhook_port', 8080)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--enhanced':
            enhanced_mode = True
        elif sys.argv[1] == '--traditional':
            enhanced_mode = False
        elif sys.argv[1] == '--help':
            print_usage()
            return
    
    print("🚀 启动AI SVN代码审查工具...")
    
    try:
        # 设置日志
        logger = setup_logging()
        logger.info("AI SVN代码审查工具启动")
        
        # 确保必要目录存在
        config.ensure_directories()
        
        # 验证配置
        required_configs = [
            'svn.repository_url',
            'ai.api_key',
            'dingtalk.webhook_url'
        ]
        
        missing_configs = []
        for conf in required_configs:
            if not config.get(conf):
                missing_configs.append(conf)
        
        if missing_configs:
            logger.error(f"缺少必要配置: {', '.join(missing_configs)}")
            print(f"❌ 缺少必要配置: {', '.join(missing_configs)}")
            print("请检查 config/config.yaml 文件")
            return
        
        logger.info("配置验证通过")
        print("✅ 配置验证通过")
        
        if enhanced_mode:
            # 增强模式：支持webhook和更好的状态管理
            logger.info(f"使用增强监控模式，Webhook端口: {webhook_port}")
            print(f"🔥 使用增强监控模式，Webhook端口: {webhook_port}")
            
            enhanced_monitor = EnhancedSVNMonitor()
            enhanced_monitor.start(webhook_port=webhook_port)
        else:
            # 传统模式：定时轮询
            logger.info("使用传统轮询模式")
            print("📊 使用传统轮询模式")
            
            # 立即执行一次检查
            logger.info("执行初始检查...")
            print("🔍 执行初始检查...")
            process_new_commits()
            
            # 设置定时任务
            check_interval = config.get('svn.check_interval', 300)  # 默认5分钟
            schedule.every(check_interval).seconds.do(process_new_commits)
            
            logger.info(f"定时任务已设置，检查间隔: {check_interval} 秒")
            print(f"⏰ 定时任务已设置，检查间隔: {check_interval} 秒")
            print("🔄 服务正在运行，按 Ctrl+C 退出...")
            
            # 运行定时任务
            while True:
                schedule.run_pending()
                time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
        print("\n👋 程序已退出")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
        print(f"❌ 程序运行异常: {e}")
        sys.exit(1)


def print_usage():
    """打印使用说明"""
    print("""
AI SVN代码审查工具

用法:
    python main.py [选项]

选项:
    --enhanced      使用增强监控模式（支持webhook）
    --traditional   使用传统轮询模式
    --help          显示此帮助信息

配置:
    可在 config/config.yaml 中设置 monitor.enhanced_mode 来默认选择模式
    """)


if __name__ == "__main__":
    main()
