import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, time as dtime
from typing import Literal

# 确保日志目录存在
log_dir = os.path.join(os.getcwd(), 'log')
os.makedirs(log_dir, exist_ok=True)

class DailyRotatingFileHandler(TimedRotatingFileHandler):
    """自定义日志处理器，每天凌晨0点切分日志"""
    def __init__(self, filename):
        at_time = dtime(0, 0, 0)  # 凌晨4点
        super().__init__(
            filename=filename,
            when='midnight',
            interval=1,
            encoding='utf-8',
            atTime=at_time 
        )

def setup_logger(filename:str,cmd_level:Literal["INFO","DEBUG"]="INFO") -> logging.Logger:
    """配置日志系统"""
    # 设置日志文件名格式
    date_str = datetime.now().strftime('%Y_%m_%d')
    log_file = os.path.join(log_dir, f'{filename}_{date_str}.log')
    
    file_handler = DailyRotatingFileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # 文件记录DEBUG及以上级别日志
    
    console_handler = logging.StreamHandler(sys.stdout)
    if cmd_level == "DEBUG":
        console_handler.setLevel(logging.DEBUG)  # 控制台输出DEBUG及以上级别日志
    else:
        console_handler.setLevel(logging.INFO)  # 控制台输出INFO及以上级别日志
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    return logger
