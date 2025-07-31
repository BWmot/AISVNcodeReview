"""
Windows服务包装器
将AI代码审查工具作为Windows服务运行
"""

import sys
import os
import servicemanager
import win32serviceutil
import win32service
import win32event
import time
from pathlib import Path

# 添加源代码路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / 'src'))

from main import process_new_commits, setup_logging
from config_manager import config


class CodeReviewService(win32serviceutil.ServiceFramework):
    """AI代码审查服务类"""
    
    _svc_name_ = "AICodeReviewService"
    _svc_display_name_ = "AI SVN Code Review Service"
    _svc_description_ = "监控SVN提交并进行AI代码审查的Windows服务"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
        
        # 设置工作目录
        os.chdir(current_dir)
        
        # 初始化日志
        self.logger = setup_logging()
        
    def SvcStop(self):
        """服务停止"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        self.logger.info("AI代码审查服务正在停止...")
        
    def SvcDoRun(self):
        """服务运行主循环"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.logger.info("AI代码审查服务已启动")
        
        try:
            # 获取检查间隔
            check_interval = config.get('svn.check_interval', 300)  # 默认5分钟
            
            while self.is_alive:
                try:
                    # 执行代码审查检查
                    process_new_commits()
                    
                    # 等待指定间隔或停止信号
                    if win32event.WaitForSingleObject(
                        self.hWaitStop, 
                        check_interval * 1000
                    ) == win32event.WAIT_OBJECT_0:
                        break
                        
                except Exception as e:
                    self.logger.error(f"服务执行异常: {e}")
                    time.sleep(60)  # 出错后等待1分钟再重试
                    
        except Exception as e:
            self.logger.error(f"服务运行异常: {e}")
            servicemanager.LogErrorMsg(f"服务运行异常: {e}")
        
        self.logger.info("AI代码审查服务已停止")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CodeReviewService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(CodeReviewService)
