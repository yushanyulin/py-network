#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psutil
import argparse
from datetime import datetime
import socket
import netifaces
import logging
import os
import sys

# 配置日志
def setup_logging(log_level='INFO', log_file=None):
    """配置日志系统"""
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 基础配置
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[]
    )
    
    # 获取logger
    logger = logging.getLogger('PortScanner')
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file is None:
        log_file = f"logs/port_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"日志系统初始化完成，日志级别: {log_level}, 日志文件: {log_file}")
    return logger

# 创建全局logger
logger = None

def get_process_info(pid):
    """获取进程信息"""
    global logger
    try:
        logger.debug(f"正在获取PID {pid} 的进程信息")
        process = psutil.Process(pid)
        process_info = {
            'name': process.name(),
            'pid': pid,
            'create_time': datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'status': process.status()
        }
        logger.debug(f"成功获取进程信息: {process_info}")
        return process_info
    except psutil.NoSuchProcess:
        logger.warning(f"进程不存在: PID {pid}")
        return None
    except psutil.AccessDenied:
        logger.warning(f"访问被拒绝: PID {pid}")
        return None
    except psutil.ZombieProcess:
        logger.warning(f"僵尸进程: PID {pid}")
        return None
    except Exception as e:
        logger.error(f"获取进程信息时发生未知错误: {str(e)}", exc_info=True)
        return None

def get_local_ip():
    """获取本机IP地址"""
    global logger
    try:
        logger.debug("开始获取本地IP地址")
        # 获取默认网关接口
        gateways = netifaces.gateways()
        logger.debug(f"网关信息: {gateways}")
        
        default_interface = gateways['default'][netifaces.AF_INET][1]
        logger.debug(f"默认网络接口: {default_interface}")
        
        # 获取该接口的IP地址
        addresses = netifaces.ifaddresses(default_interface)
        local_ip = addresses[netifaces.AF_INET][0]['addr']
        logger.info(f"成功获取本地IP地址: {local_ip}")
        return local_ip
    except KeyError as e:
        logger.warning(f"无法获取默认网关信息: {str(e)}")
        return "127.0.0.1"
    except Exception as e:
        logger.error(f"获取本地IP地址时发生错误: {str(e)}", exc_info=True)
        return "127.0.0.1"

def scan_ports(port=None, process_name=None):
    """扫描端口"""
    global logger
    logger.info("开始端口扫描")
    logger.info(f"扫描参数 - 指定端口: {port}, 进程名称过滤: {process_name}")
    
    local_ip = get_local_ip()
    print(f"\n本地IP地址: {local_ip}")
    print("\n{:<8} {:<8} {:<20} {:<15} {:<20}".format(
        "端口", "PID", "进程名", "状态", "创建时间"))
    print("-" * 75)
    
    try:
        # 获取所有网络连接
        connections = psutil.net_connections(kind='inet')
        logger.info(f"获取到 {len(connections)} 个网络连接")
        
        scanned_count = 0
        listening_count = 0
        matched_count = 0
        
        for conn in connections:
            scanned_count += 1
            
            if conn.status != 'LISTEN':
                logger.debug(f"跳过非监听状态的连接: {conn.laddr.port} (状态: {conn.status})")
                continue
            
            listening_count += 1
            logger.debug(f"发现监听端口: {conn.laddr.port} (PID: {conn.pid})")
            
            # 获取进程信息
            process_info = get_process_info(conn.pid)
            if not process_info:
                logger.debug(f"无法获取端口 {conn.laddr.port} 的进程信息")
                continue
            
            # 过滤条件
            if port and conn.laddr.port != port:
                logger.debug(f"端口 {conn.laddr.port} 不匹配指定端口 {port}")
                continue
            if process_name and process_name.lower() not in process_info['name'].lower():
                logger.debug(f"进程名 {process_info['name']} 不匹配过滤条件 {process_name}")
                continue
            
            matched_count += 1
            # 打印信息
            print("{:<8} {:<8} {:<20} {:<15} {:<20}".format(
                conn.laddr.port,
                process_info['pid'],
                process_info['name'][:20],
                process_info['status'],
                process_info['create_time']
            ))
            
            logger.info(f"找到匹配端口: {conn.laddr.port} - 进程: {process_info['name']} (PID: {process_info['pid']})")
        
        logger.info(f"扫描完成 - 总连接数: {scanned_count}, 监听端口数: {listening_count}, 匹配结果数: {matched_count}")
        
    except Exception as e:
        logger.error(f"扫描端口时发生错误: {str(e)}", exc_info=True)
        raise

def main():
    parser = argparse.ArgumentParser(description='本地网络端口扫描工具')
    parser.add_argument('-p', '--port', type=int, help='指定要查询的端口号')
    parser.add_argument('-n', '--name', type=str, help='按进程名称过滤')
    parser.add_argument('-a', '--all', action='store_true', help='显示所有端口信息（默认）')
    parser.add_argument('-l', '--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='设置日志级别 (默认: INFO)')
    parser.add_argument('--log-file', type=str, help='指定日志文件路径')
    
    args = parser.parse_args()
    
    # 设置日志
    global logger
    logger = setup_logging(args.log_level, args.log_file)
    
    logger.info("="*60)
    logger.info("端口扫描工具启动")
    logger.info(f"命令行参数: {vars(args)}")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"操作系统: {os.name}")
    logger.info("="*60)
    
    try:
        scan_ports(args.port, args.name)
        logger.info("端口扫描正常结束")
    except KeyboardInterrupt:
        logger.warning("程序被用户中断 (Ctrl+C)")
        print("\n程序已终止")
    except Exception as e:
        logger.critical(f"发生严重错误: {str(e)}", exc_info=True)
        print(f"\n发生错误: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("程序退出")

if __name__ == '__main__':
    main() 