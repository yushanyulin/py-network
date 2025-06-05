#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psutil
import argparse
from datetime import datetime
import socket
import netifaces

def get_process_info(pid):
    """获取进程信息"""
    try:
        process = psutil.Process(pid)
        return {
            'name': process.name(),
            'pid': pid,
            'create_time': datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'status': process.status()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 获取默认网关接口
        gateways = netifaces.gateways()
        default_interface = gateways['default'][netifaces.AF_INET][1]
        # 获取该接口的IP地址
        addresses = netifaces.ifaddresses(default_interface)
        return addresses[netifaces.AF_INET][0]['addr']
    except:
        return "127.0.0.1"

def scan_ports(port=None, process_name=None):
    """扫描端口"""
    local_ip = get_local_ip()
    print(f"\n本地IP地址: {local_ip}")
    print("\n{:<8} {:<8} {:<20} {:<15} {:<20}".format(
        "端口", "PID", "进程名", "状态", "创建时间"))
    print("-" * 75)

    for conn in psutil.net_connections(kind='inet'):
        if conn.status != 'LISTEN':
            continue

        # 获取进程信息
        process_info = get_process_info(conn.pid)
        if not process_info:
            continue

        # 过滤条件
        if port and conn.laddr.port != port:
            continue
        if process_name and process_name.lower() not in process_info['name'].lower():
            continue

        # 打印信息
        print("{:<8} {:<8} {:<20} {:<15} {:<20}".format(
            conn.laddr.port,
            process_info['pid'],
            process_info['name'][:20],
            process_info['status'],
            process_info['create_time']
        ))

def main():
    parser = argparse.ArgumentParser(description='本地网络端口扫描工具')
    parser.add_argument('-p', '--port', type=int, help='指定要查询的端口号')
    parser.add_argument('-n', '--name', type=str, help='按进程名称过滤')
    parser.add_argument('-a', '--all', action='store_true', help='显示所有端口信息（默认）')
    
    args = parser.parse_args()
    
    try:
        scan_ports(args.port, args.name)
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")

if __name__ == '__main__':
    main() 