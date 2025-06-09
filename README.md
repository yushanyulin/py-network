# 端口扫描工具 (Port Scanner)

一个功能强大的本地网络端口扫描工具，用于查看本机正在监听的端口及其关联的进程信息。

## 功能特性

- 扫描本机所有监听端口
- 显示端口关联的进程信息（名称、PID、状态、创建时间）
- 支持按端口号或进程名称过滤
- 自动获取本机IP地址
- **完整的日志系统支持**

## 日志功能

### 日志特性
- **双重输出**：同时输出到控制台和文件
- **分级日志**：支持 DEBUG、INFO、WARNING、ERROR、CRITICAL 五个级别
- **自动归档**：日志文件保存在 `logs` 目录，按时间戳命名
- **详细记录**：包含时间戳、日志级别、函数名、行号等信息

### 日志内容

#### 系统环境信息
- 操作系统版本和平台信息
- Python版本
- 主机名和当前用户
- 工作目录和进程ID
- CPU核心数和内存信息

#### 扫描过程记录
- 扫描开始和结束时间
- 权限检查（管理员/普通用户）
- 网络接口和IP地址获取过程
- 每个连接的处理详情（DEBUG级别）
- 进程信息获取（包括CPU、内存、线程数等）

#### 统计信息
- 总连接数、IPv4/IPv6连接分布
- 各种连接状态统计（LISTEN、ESTABLISHED、TIME_WAIT等）
- 匹配的端口数量
- 权限拒绝次数
- 扫描总耗时

#### 性能监控
- 操作耗时记录
- 程序开始和结束时的系统资源使用情况

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
# 扫描所有端口（默认INFO级别日志）
python3 port_scanner.py

# 扫描特定端口
python3 port_scanner.py -p 8080

# 按进程名称过滤
python3 port_scanner.py -n python

# 使用DEBUG级别查看详细信息
python3 port_scanner.py -l DEBUG

# 组合使用
python3 port_scanner.py -p 80 -l DEBUG
```

### 参数说明

- `-p, --port`：指定要查询的端口号
- `-n, --name`：按进程名称过滤（支持部分匹配）
- `-a, --all`：显示所有端口信息（默认）
- `-l, --log-level`：设置日志级别（DEBUG|INFO|WARNING|ERROR|CRITICAL）

### 日志级别说明

- **DEBUG**：最详细的信息，包括每个连接的处理过程
- **INFO**：关键操作信息，适合日常使用
- **WARNING**：警告信息，如权限不足
- **ERROR**：错误信息，但程序可以继续运行
- **CRITICAL**：严重错误，程序无法继续

## 输出示例

```
本地IP地址: 192.168.1.100

端口     PID      进程名                状态            创建时间               
---------------------------------------------------------------------------
80       1234     nginx                running        2024-01-01 10:00:00
3306     5678     mysqld               sleeping       2024-01-01 09:00:00
```

## 日志文件

日志文件保存在 `logs` 目录下，文件名格式：`port_scanner_YYYYMMDD_HHMMSS.log`

查看日志文件：
```bash
# 查看最新的日志文件
ls -lt logs/ | head -5

# 实时查看日志
tail -f logs/port_scanner_*.log
```

## 注意事项

- 某些端口信息可能需要管理员权限才能访问
- Linux/Mac 系统使用 `sudo python3 port_scanner.py` 获取完整信息
- Windows 系统需要以管理员身份运行命令提示符
- 日志文件会持续增长，建议定期清理旧日志

## 依赖

- Python 3.6+
- psutil==5.9.8
- netifaces==0.11.0

## License

MIT License 