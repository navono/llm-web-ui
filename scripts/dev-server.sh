#!/bin/bash
# Development server script with proper cleanup

# 从配置文件读取端口
PORT=$(grep -A 2 "http:" config/config.yaml | grep "port:" | awk '{print $2}')
PORT=${PORT:-13001}

# 清理函数
cleanup() {
    echo "Cleaning up..."
    # 查找并终止占用端口的进程
    PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "Killing process $PID on port $PORT"
        kill -9 $PID 2>/dev/null
    fi
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 启动前先清理一次
cleanup

# 启动服务器
uv run -m src.main run
