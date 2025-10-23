#!/bin/bash
# 测试 Jina Search API

echo "=========================================="
echo "测试 Jina Search API"
echo "=========================================="

# 配置
API_URL="http://localhost:8080/v1/search"
API_KEY="sk-llm-web-ui-2024"

echo ""
echo "1. 测试无 API Key（应该返回 401）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  "$API_URL?q=Jina+AI"

echo ""
echo ""
echo "2. 测试基本搜索"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "X-API-Key: $API_KEY" \
  "$API_URL?q=Jina+AI"

echo ""
echo ""
echo "3. 测试搜索（不返回内容）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "X-API-Key: $API_KEY" \
  -H "X-Respond-With: no-content" \
  "$API_URL?q=OpenAI+GPT-4"

echo ""
echo ""
echo "4. 测试搜索特定 URL"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "X-API-Key: $API_KEY" \
  "$API_URL?url=https://example.com"

echo ""
echo ""
echo "5. 测试搜索（带图片摘要）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "X-API-Key: $API_KEY" \
  -H "X-With-Images-Summary: true" \
  "$API_URL?q=Python+programming"

echo ""
echo ""
echo "6. 测试搜索（带链接摘要）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "X-API-Key: $API_KEY" \
  -H "X-With-Links-Summary: true" \
  "$API_URL?q=Machine+Learning"

echo ""
echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
