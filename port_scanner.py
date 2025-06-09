#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psutil
import argparse
from datetime import datetime
import socket
import netifaces
import logging
import sys
import os

# 创建日志目录
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 配置日志
def setup_logging(log_level='INFO'):
    """设置日志配置"""
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # 设置日志级别
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'无效的日志级别: {log_level}')
    
    # 配置根日志记录器
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            # 控制台输出
            logging.StreamHandler(sys.stdout),
            # 文件输出
            logging.FileHandler(
                os.path.join(LOG_DIR, f'port_scanner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                encoding='utf-8'
            )
        ]
    )
    
    # 创建专用的logger
    logger = logging.getLogger('PortScanner')
    logger.info(f"日志系统初始化完成，日志级别: {log_level}")
    return logger

# 全局logger
logger = None

def get_process_info(pid):
    """获取进程信息"""
    logger.debug(f"开始获取进程信息，PID: {pid}")
    try:
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
        logger.warning(f"进程不存在，PID: {pid}")
        return None
    except psutil.AccessDenied:
        logger.warning(f"无权限访问进程，PID: {pid}")
        return None
    except psutil.ZombieProcess:
        logger.warning(f"僵尸进程，PID: {pid}")
        return None
    except Exception as e:
        logger.error(f"获取进程信息时发生未知错误，PID: {pid}, 错误: {str(e)}")
        return None

def get_local_ip():
    """获取本机IP地址"""
    logger.debug("开始获取本机IP地址")
    try:
        # 获取默认网关接口
        gateways = netifaces.gateways()
        logger.debug(f"网关信息: {gateways}")
        
        if 'default' not in gateways or netifaces.AF_INET not in gateways['default']:
            logger.warning("未找到默认网关")
            return "127.0.0.1"
            
        default_interface = gateways['default'][netifaces.AF_INET][1]
        logger.debug(f"默认网络接口: {default_interface}")
        
        # 获取该接口的IP地址
        addresses = netifaces.ifaddresses(default_interface)
        if netifaces.AF_INET in addresses:
            ip_addr = addresses[netifaces.AF_INET][0]['addr']
            logger.info(f"成功获取本机IP地址: {ip_addr}")
            return ip_addr
        else:
            logger.warning(f"接口 {default_interface} 没有IPv4地址")
            return "127.0.0.1"
    except Exception as e:
        logger.error(f"获取本机IP地址时发生错误: {str(e)}")
        return "127.0.0.1"

def scan_ports(port=None, process_name=None):
    """扫描端口"""
    logger.info(f"开始扫描端口，过滤条件 - 端口: {port}, 进程名: {process_name}")
    
    local_ip = get_local_ip()
    print(f"\n本地IP地址: {local_ip}")
    print("\n{:<8} {:<8} {:<20} {:<15} {:<20}".format(
        "端口", "PID", "进程名", "状态", "创建时间"))
    print("-" * 75)

    # 获取所有网络连接
    logger.debug("开始获取网络连接列表")
    connections = psutil.net_connections(kind='inet')
    logger.info(f"获取到 {len(connections)} 个网络连接")
    
    matched_count = 0
    for conn in connections:
        logger.debug(f"处理连接: {conn}")
        
        if conn.status != 'LISTEN':
            logger.debug(f"跳过非监听状态的连接: {conn.status}")
            continue

        # 获取进程信息
        if conn.pid is None:
            logger.debug("连接没有关联的PID，跳过")
            continue
            
        process_info = get_process_info(conn.pid)
        if not process_info:
            logger.debug(f"无法获取PID {conn.pid} 的进程信息，跳过")
            continue

        # 过滤条件
        if port and conn.laddr.port != port:
            logger.debug(f"端口 {conn.laddr.port} 不匹配指定端口 {port}，跳过")
            continue
        if process_name and process_name.lower() not in process_info['name'].lower():
            logger.debug(f"进程名 {process_info['name']} 不匹配指定名称 {process_name}，跳过")
            continue

        # 打印信息
        logger.info(f"找到匹配的端口: {conn.laddr.port} - {process_info['name']} (PID: {process_info['pid']})")
        print("{:<8} {:<8} {:<20} {:<15} {:<20}".format(
            conn.laddr.port,
            process_info['pid'],
            process_info['name'][:20],
            process_info['status'],
            process_info['create_time']
        ))
        matched_count += 1
    
    logger.info(f"扫描完成，共找到 {matched_count} 个匹配的端口")

def main():
    global logger
    
    parser = argparse.ArgumentParser(description='本地网络端口扫描工具')
    parser.add_argument('-p', '--port', type=int, help='指定要查询的端口号')
    parser.add_argument('-n', '--name', type=str, help='按进程名称过滤')
    parser.add_argument('-a', '--all', action='store_true', help='显示所有端口信息（默认）')
    parser.add_argument('-l', '--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='设置日志级别 (默认: INFO)')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging(args.log_level)
    logger.info("端口扫描工具启动")
    logger.debug(f"命令行参数: {vars(args)}")
    
    try:
        scan_ports(args.port, args.name)
        logger.info("端口扫描工具正常退出")
    except KeyboardInterrupt:
        logger.warning("用户中断程序执行")
        print("\n程序已终止")
    except PermissionError as e:
        logger.error(f"权限错误: {str(e)}")
        print(f"\n权限错误: {str(e)}")
        print("提示: 某些端口信息可能需要管理员权限才能访问")
    except Exception as e:
        logger.critical(f"发生未预期的错误: {str(e)}", exc_info=True)
        print(f"\n发生错误: {str(e)}")

if __name__ == '__main__':
    main() 