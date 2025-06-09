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
import platform
import time
import getpass

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
    
    # 记录系统环境信息
    logger.info(f"操作系统: {platform.system()} {platform.release()} ({platform.platform()})")
    logger.info(f"Python版本: {platform.python_version()}")
    logger.info(f"主机名: {platform.node()}")
    logger.info(f"当前用户: {getpass.getuser()}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"进程ID: {os.getpid()}")
    
    # 记录系统资源信息
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    logger.info(f"CPU核心数: {cpu_count} (物理: {psutil.cpu_count(logical=False)})")
    logger.info(f"内存总量: {memory.total / (1024**3):.2f} GB, 可用: {memory.available / (1024**3):.2f} GB")
    
    return logger

# 全局logger
logger = None

def get_process_info(pid):
    """获取进程信息"""
    logger.debug(f"开始获取进程信息，PID: {pid}")
    start_time = time.time()
    
    try:
        process = psutil.Process(pid)
        
        # 获取更多进程信息
        try:
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            num_threads = process.num_threads()
            cmdline = ' '.join(process.cmdline()[:3])  # 只取前3个参数
            if len(process.cmdline()) > 3:
                cmdline += '...'
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            cpu_percent = memory_percent = num_threads = 0
            memory_info = None
            cmdline = "N/A"
            logger.debug(f"无法获取PID {pid} 的详细资源信息")
        
        process_info = {
            'name': process.name(),
            'pid': pid,
            'create_time': datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'status': process.status(),
            'cpu_percent': cpu_percent,
            'memory_mb': memory_info.rss / (1024 * 1024) if memory_info else 0,
            'memory_percent': memory_percent,
            'num_threads': num_threads,
            'cmdline': cmdline
        }
        
        elapsed_time = time.time() - start_time
        logger.debug(f"成功获取进程信息 (耗时: {elapsed_time:.3f}秒): {process_info}")
        return process_info
    except psutil.NoSuchProcess:
        logger.warning(f"进程不存在，PID: {pid}")
        return None
    except psutil.AccessDenied:
        logger.warning(f"无权限访问进程，PID: {pid} (可能需要管理员权限)")
        return None
    except psutil.ZombieProcess:
        logger.warning(f"僵尸进程，PID: {pid}")
        return None
    except Exception as e:
        logger.error(f"获取进程信息时发生未知错误，PID: {pid}, 错误: {str(e)}", exc_info=True)
        return None

def get_local_ip():
    """获取本机IP地址"""
    logger.debug("开始获取本机IP地址")
    start_time = time.time()
    
    try:
        # 获取所有网络接口
        all_interfaces = netifaces.interfaces()
        logger.debug(f"发现 {len(all_interfaces)} 个网络接口: {all_interfaces}")
        
        # 获取默认网关接口
        gateways = netifaces.gateways()
        logger.debug(f"网关信息: {gateways}")
        
        if 'default' not in gateways or netifaces.AF_INET not in gateways['default']:
            logger.warning("未找到默认网关，尝试其他方法获取IP")
            # 尝试通过socket连接获取本地IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_addr = s.getsockname()[0]
                s.close()
                logger.info(f"通过socket方法获取本机IP地址: {ip_addr}")
                return ip_addr
            except:
                logger.error("所有方法都无法获取本机IP地址")
                return "127.0.0.1"
            
        default_interface = gateways['default'][netifaces.AF_INET][1]
        logger.debug(f"默认网络接口: {default_interface}")
        
        # 获取该接口的IP地址
        addresses = netifaces.ifaddresses(default_interface)
        if netifaces.AF_INET in addresses:
            ip_addr = addresses[netifaces.AF_INET][0]['addr']
            elapsed_time = time.time() - start_time
            logger.info(f"成功获取本机IP地址: {ip_addr} (耗时: {elapsed_time:.3f}秒)")
            
            # 记录网络接口的其他信息
            if 'netmask' in addresses[netifaces.AF_INET][0]:
                logger.debug(f"子网掩码: {addresses[netifaces.AF_INET][0]['netmask']}")
            if 'broadcast' in addresses[netifaces.AF_INET][0]:
                logger.debug(f"广播地址: {addresses[netifaces.AF_INET][0]['broadcast']}")
                
            return ip_addr
        else:
            logger.warning(f"接口 {default_interface} 没有IPv4地址")
            return "127.0.0.1"
    except Exception as e:
        logger.error(f"获取本机IP地址时发生错误: {str(e)}", exc_info=True)
        return "127.0.0.1"

def scan_ports(port=None, process_name=None):
    """扫描端口"""
    scan_start_time = time.time()
    logger.info(f"开始扫描端口，过滤条件 - 端口: {port}, 进程名: {process_name}")
    
    # 检查权限
    is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
    logger.info(f"当前用户权限: {'管理员' if is_root else '普通用户'}")
    if not is_root:
        logger.warning("以普通用户权限运行，某些端口信息可能无法获取")
    
    local_ip = get_local_ip()
    print(f"\n本地IP地址: {local_ip}")
    print("\n{:<8} {:<8} {:<20} {:<15} {:<20}".format(
        "端口", "PID", "进程名", "状态", "创建时间"))
    print("-" * 75)

    # 获取所有网络连接
    logger.debug("开始获取网络连接列表")
    conn_start_time = time.time()
    
    try:
        connections = psutil.net_connections(kind='inet')
        conn_elapsed = time.time() - conn_start_time
        logger.info(f"获取到 {len(connections)} 个网络连接 (耗时: {conn_elapsed:.3f}秒)")
    except psutil.AccessDenied as e:
        logger.error(f"获取网络连接时权限不足: {str(e)}")
        print("\n错误: 需要管理员权限才能查看所有网络连接")
        return
    except Exception as e:
        logger.error(f"获取网络连接时发生错误: {str(e)}", exc_info=True)
        return
    
    # 统计信息
    stats = {
        'total_connections': len(connections),
        'listen_connections': 0,
        'established_connections': 0,
        'time_wait_connections': 0,
        'other_connections': 0,
        'matched_ports': 0,
        'no_pid_connections': 0,
        'access_denied_count': 0,
        'ipv4_connections': 0,
        'ipv6_connections': 0
    }
    
    matched_count = 0
    for idx, conn in enumerate(connections):
        # 统计连接类型
        if conn.family == socket.AF_INET:
            stats['ipv4_connections'] += 1
        elif conn.family == socket.AF_INET6:
            stats['ipv6_connections'] += 1
            
        logger.debug(f"[{idx+1}/{len(connections)}] 处理连接: {conn}")
        
        if conn.status == 'LISTEN':
            stats['listen_connections'] += 1
        elif conn.status == 'ESTABLISHED':
            stats['established_connections'] += 1
        elif conn.status == 'TIME_WAIT':
            stats['time_wait_connections'] += 1
        else:
            stats['other_connections'] += 1
            
        if conn.status != 'LISTEN':
            logger.debug(f"跳过非监听状态的连接: {conn.status}")
            continue

        # 获取进程信息
        if conn.pid is None:
            stats['no_pid_connections'] += 1
            logger.debug("连接没有关联的PID，跳过")
            continue
            
        process_info = get_process_info(conn.pid)
        if not process_info:
            stats['access_denied_count'] += 1
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
        stats['matched_ports'] += 1
        logger.info(f"找到匹配的端口: {conn.laddr.port} - {process_info['name']} (PID: {process_info['pid']})")
        logger.debug(f"  详细信息 - CPU: {process_info['cpu_percent']:.1f}%, 内存: {process_info['memory_mb']:.1f}MB ({process_info['memory_percent']:.1f}%), 线程数: {process_info['num_threads']}")
        logger.debug(f"  命令行: {process_info['cmdline']}")
        
        print("{:<8} {:<8} {:<20} {:<15} {:<20}".format(
            conn.laddr.port,
            process_info['pid'],
            process_info['name'][:20],
            process_info['status'],
            process_info['create_time']
        ))
        matched_count += 1
    
    # 扫描完成，输出统计信息
    scan_elapsed = time.time() - scan_start_time
    logger.info(f"扫描完成，总耗时: {scan_elapsed:.3f}秒")
    logger.info(f"扫描统计:")
    logger.info(f"  - 总连接数: {stats['total_connections']}")
    logger.info(f"  - IPv4连接: {stats['ipv4_connections']}, IPv6连接: {stats['ipv6_connections']}")
    logger.info(f"  - 监听状态: {stats['listen_connections']}")
    logger.info(f"  - 已建立连接: {stats['established_connections']}")
    logger.info(f"  - TIME_WAIT: {stats['time_wait_connections']}")
    logger.info(f"  - 其他状态: {stats['other_connections']}")
    logger.info(f"  - 无PID连接: {stats['no_pid_connections']}")
    logger.info(f"  - 权限拒绝: {stats['access_denied_count']}")
    logger.info(f"  - 匹配的端口: {stats['matched_ports']}")
    
    if matched_count == 0:
        logger.warning("没有找到匹配的端口")
        if not is_root:
            logger.info("提示: 尝试使用管理员权限运行可能会显示更多端口")

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
    logger.info("="*60)
    logger.info("端口扫描工具启动")
    logger.info("="*60)
    logger.debug(f"命令行参数: {vars(args)}")
    
    try:
        # 记录开始时的系统资源使用情况
        start_cpu_percent = psutil.cpu_percent(interval=0.1)
        start_memory = psutil.virtual_memory()
        logger.debug(f"开始时CPU使用率: {start_cpu_percent}%")
        logger.debug(f"开始时内存使用: {start_memory.percent}%")
        
        scan_ports(args.port, args.name)
        
        # 记录结束时的系统资源使用情况
        end_cpu_percent = psutil.cpu_percent(interval=0.1)
        end_memory = psutil.virtual_memory()
        logger.debug(f"结束时CPU使用率: {end_cpu_percent}%")
        logger.debug(f"结束时内存使用: {end_memory.percent}%")
        
        logger.info("端口扫描工具正常退出")
        logger.info("="*60)
    except KeyboardInterrupt:
        logger.warning("用户中断程序执行 (Ctrl+C)")
        print("\n程序已终止")
    except PermissionError as e:
        logger.error(f"权限错误: {str(e)}")
        logger.error("需要更高的权限才能执行此操作")
        print(f"\n权限错误: {str(e)}")
        print("提示: 某些端口信息可能需要管理员权限才能访问")
        print("Linux/Mac: 使用 sudo python3 port_scanner.py")
        print("Windows: 以管理员身份运行命令提示符")
    except Exception as e:
        logger.critical(f"发生未预期的错误: {str(e)}", exc_info=True)
        print(f"\n发生错误: {str(e)}")
        print("请查看日志文件获取详细错误信息")

if __name__ == '__main__':
    main() 