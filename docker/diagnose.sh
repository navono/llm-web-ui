#!/bin/bash
# 诊断 Docker 服务状态

echo "=========================================="
echo "Docker 容器状态"
echo "=========================================="
docker compose ps

echo ""
echo "=========================================="
echo "检查后端服务连接"
echo "=========================================="

# 检查 indextts2
echo "检查 indextts2 (端口 12234)..."
if docker compose exec nginx wget -q -O- http://indextts2:12234/v1/voices 2>/dev/null; then
    echo "✅ indextts2 可访问"
else
    echo "❌ indextts2 不可访问"
    echo "indextts2 日志："
    docker compose logs --tail 20 indextts2
fi

echo ""

# 检查 open-llm-vtuber
echo "检查 open-llm-vtuber (端口 12393)..."
if docker compose exec nginx wget -q -O- http://open-llm-vtuber:12393/ 2>/dev/null; then
    echo "✅ open-llm-vtuber 可访问"
else
    echo "❌ open-llm-vtuber 不可访问"
    echo "open-llm-vtuber 日志："
    docker compose logs --tail 20 open-llm-vtuber
fi

echo ""
echo "=========================================="
echo "Nginx 错误日志"
echo "=========================================="
docker compose logs --tail 20 nginx | grep -i error || echo "无错误"

echo ""
echo "=========================================="
echo "网络连接测试"
echo "=========================================="
docker compose exec nginx ping -c 2 indextts2 2>/dev/null || echo "❌ 无法 ping indextts2"
docker compose exec nginx ping -c 2 open-llm-vtuber 2>/dev/null || echo "❌ 无法 ping open-llm-vtuber"
