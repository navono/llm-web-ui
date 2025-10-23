#!/bin/bash
# 测试 Jina Reader API

echo "=========================================="
echo "测试 Jina Reader API"
echo "=========================================="

# 配置
API_URL="http://localhost:8080/v1/reader"
API_KEY="sk-llm-web-ui-2024"

echo ""
echo "1. 测试无 API Key（应该返回 401）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Accept: application/json" \
  "$API_URL/https://example.com"

echo ""
echo ""
echo "2. 测试读取网页（基本）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Accept: application/json" \
  -H "X-API-Key: $API_KEY" \
  "$API_URL/https://example.com"

echo ""
echo ""
echo "3. 测试读取网页（使用 direct 引擎）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Accept: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-Engine: direct" \
  "$API_URL/https://www.example.com"

echo ""
echo ""
echo "4. 测试读取网页（带图片摘要）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Accept: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-With-Images-Summary: true" \
  "$API_URL/https://news.ycombinator.com"

echo ""
echo ""
echo "5. 测试读取网页（带链接摘要）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Accept: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-With-Links-Summary: true" \
  "$API_URL/https://github.com"

echo ""
echo ""
echo "6. 测试读取网页（使用 CSS 选择器）"
echo "=========================================="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Accept: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-Target-Selector: .main-content" \
  "$API_URL/https://example.com"

echo ""
echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
