# 本地网络端口扫描工具

这是一个简单的Python脚本工具，用于查询本地网络端口的使用情况。

## 功能特点

- 显示所有正在使用的网络端口
- 显示每个端口对应的进程信息
- 支持按端口号或进程名进行过滤

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python port_scanner.py
```

## 参数说明

- `-p, --port`: 指定要查询的端口号
- `-n, --name`: 按进程名称过滤
- `-a, --all`: 显示所有端口信息（默认）

## 示例

```bash
# 查看所有端口
python port_scanner.py

# 查看特定端口
python port_scanner.py -p 8080

# 按进程名过滤
python port_scanner.py -n python
``` 