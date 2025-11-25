#!/bin/sh
# 自定义 entrypoint 脚本，用于处理 nginx.conf 中的环境变量

set -e

# 定义需要替换的环境变量
VARS='$API_KEY_1:$API_KEY_2:$JINA_API_KEY'

# 使用 envsubst 替换环境变量
envsubst "$VARS" < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "Environment variables substituted in nginx.conf"

# 测试 nginx 配置
nginx -t

echo "Nginx configuration is valid"
