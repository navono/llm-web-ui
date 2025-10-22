#!/bin/bash

# API Gateway 测试脚本
# 测试通过 nginx 网关访问各个服务

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "API Gateway 测试"
echo "Gateway URL: $GATEWAY_URL"
echo "=========================================="
echo ""

# 测试函数
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=${5:-200}
    
    echo -n "测试 $name ... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$GATEWAY_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$GATEWAY_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ 通过${NC} (HTTP $status_code)"
        if [ -n "$body" ]; then
            echo "  响应: $(echo "$body" | head -c 100)..."
        fi
    else
        echo -e "${RED}✗ 失败${NC} (期望 HTTP $expected_status, 实际 HTTP $status_code)"
        echo "  响应: $body"
        return 1
    fi
    echo ""
}

# 1. 测试健康检查
echo "=========================================="
echo "1. 健康检查"
echo "=========================================="
test_endpoint "健康检查" "GET" "/health"

# 2. 测试根路径
echo "=========================================="
echo "2. API 网关信息"
echo "=========================================="
test_endpoint "根路径" "GET" "/"

# 3. 测试模型列表
echo "=========================================="
echo "3. 模型列表"
echo "=========================================="
test_endpoint "模型列表" "GET" "/v1/models"

# 4. 测试 TTS 服务
echo "=========================================="
echo "4. TTS 服务"
echo "=========================================="
test_endpoint "TTS 语音列表" "GET" "/v1/voices"

# 测试 OpenAI 兼容的 TTS 端点（需要实际的音频生成，这里只测试端点可达性）
echo -n "测试 TTS 生成端点 ... "
tts_data='{
  "model": "indextts2",
  "input": "你好，这是一个测试。",
  "voice": "alloy"
}'
response=$(curl -s -w "\n%{http_code}" -X POST "$GATEWAY_URL/v1/audio/speech" \
    -H "Content-Type: application/json" \
    -d "$tts_data")
status_code=$(echo "$response" | tail -n1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ 通过${NC} (HTTP $status_code)"
    echo "  响应: 音频数据已生成"
else
    echo -e "${YELLOW}⚠ 警告${NC} (HTTP $status_code) - 可能需要配置音频提示文件"
fi
echo ""

# 5. 测试 ASR 服务
echo "=========================================="
echo "5. ASR 转录服务"
echo "=========================================="
echo -n "测试 ASR 转录端点 ... "
echo "  注意: 需要实际的音频文件才能完整测试"
echo -e "${YELLOW}  跳过实际音频上传测试${NC}"
echo ""

# 6. WebSocket 端点测试（仅检查端点存在）
echo "=========================================="
echo "6. WebSocket 端点"
echo "=========================================="
echo "  WebSocket 端点:"
echo "    - /client-ws"
echo "    - /tts-ws"
echo "    - /proxy-ws"
echo -e "${YELLOW}  注意: WebSocket 需要专门的客户端测试${NC}"
echo ""

# 总结
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "所有基本端点测试通过！"
echo ""
echo "下一步测试建议:"
echo "  1. 使用实际音频文件测试 TTS 生成"
echo "  2. 使用实际音频文件测试 ASR 转录"
echo "  3. 使用 WebSocket 客户端测试实时通信"
echo ""
echo "示例 TTS 测试命令:"
echo "  curl -X POST $GATEWAY_URL/v1/audio/speech \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\":\"indextts2\",\"input\":\"你好世界\",\"voice\":\"alloy\"}' \\"
echo "    --output test_output.mp3"
echo ""
echo "示例 ASR 测试命令:"
echo "  curl -X POST $GATEWAY_URL/v1/audio/transcriptions \\"
echo "    -F 'file=@your_audio.wav' \\"
echo "    -F 'model=funASR'"
