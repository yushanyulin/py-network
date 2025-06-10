# 本地网络端口扫描工具

这是一个简单的Python脚本工具，用于查询本地网络端口的使用情况。

## 功能特点

- 显示所有正在使用的网络端口
- 显示每个端口对应的进程信息
- 支持按端口号或进程名进行过滤
- 详细的日志记录功能，支持不同日志级别
- 自动保存日志到文件，便于问题排查

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
- `-l, --log-level`: 设置日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL（默认：INFO）
- `--log-file`: 指定日志文件路径（默认：logs/port_scanner_时间戳.log）

## 示例

```bash
# 查看所有端口
python port_scanner.py

# 查看特定端口
python port_scanner.py -p 8080

# 按进程名过滤
python port_scanner.py -n python

# 使用DEBUG级别查看详细日志
python port_scanner.py -l DEBUG

# 指定日志文件
python port_scanner.py --log-file my_scan.log

# 组合使用：查看8080端口并开启DEBUG日志
python port_scanner.py -p 8080 -l DEBUG
```

## 日志功能说明

程序会自动创建`logs`目录并保存日志文件。日志包含以下信息：

- **INFO级别**：基本操作信息，如启动、扫描结果统计等
- **DEBUG级别**：详细的调试信息，包括每个端口的扫描过程、进程信息获取等
- **WARNING级别**：警告信息，如无法访问某些进程等
- **ERROR级别**：错误信息和异常堆栈
- **CRITICAL级别**：严重错误信息

日志同时输出到控制台和文件，方便实时查看和后续分析。 