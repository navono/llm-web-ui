# Jina Reader API 使用指南

## 概述

Jina Reader API 将任何 URL 转换为 LLM 友好的干净文本，提取网页的主要内容。

## API 端点

```
GET http://localhost:8080/v1/reader/{url}
```

## 认证

```bash
X-API-Key: sk-llm-web-ui-2024
```

## 基本用法

```bash
curl "http://localhost:8080/v1/reader/https://example.com" \
  -H "Accept: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024"
```

## 请求头

| 头部 | 说明 |
|------|------|
| `X-Engine` | 引擎类型：`direct`, `browser` |
| `X-With-Generated-Alt` | 生成图片 alt 文本 |
| `X-With-Links-Summary` | 包含链接摘要 |
| `X-With-Images-Summary` | 包含图片摘要 |
| `X-Target-Selector` | CSS 选择器 |
| `X-Wait-For-Selector` | 等待的选择器 |
| `X-Remove-Selector` | 移除的选择器 |
| `X-Timeout` | 超时时间（秒） |
| `X-No-Cache` | 禁用缓存 |

## 使用示例

### 示例 1: 基本读取

```bash
curl "http://localhost:8080/v1/reader/https://news.ycombinator.com" \
  -H "Accept: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024"
```

### 示例 2: 使用 direct 引擎

```bash
curl "http://localhost:8080/v1/reader/https://www.example.com" \
  -H "Accept: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -H "X-Engine: direct"
```

### 示例 3: 带图片和链接摘要

```bash
curl "http://localhost:8080/v1/reader/https://github.com" \
  -H "Accept: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -H "X-With-Images-Summary: true" \
  -H "X-With-Links-Summary: true"
```

### 示例 4: 使用 CSS 选择器

```bash
curl "http://localhost:8080/v1/reader/https://example.com" \
  -H "Accept: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -H "X-Target-Selector: .main-content"
```

## Python 示例

```python
import requests

url = "http://localhost:8080/v1/reader/https://example.com"
headers = {
    "Accept": "application/json",
    "X-API-Key": "sk-llm-web-ui-2024",
    "X-Engine": "direct"
}

response = requests.get(url, headers=headers)
data = response.json()

print(f"Title: {data['data']['title']}")
print(f"Content: {data['data']['content'][:200]}...")
```

## JavaScript 示例

```javascript
const url = "http://localhost:8080/v1/reader/https://news.ycombinator.com";
const headers = {
    "Accept": "application/json",
    "X-API-Key": "sk-llm-web-ui-2024",
    "X-With-Links-Summary": "true"
};

fetch(url, { headers })
    .then(response => response.json())
    .then(data => {
        console.log("Title:", data.data.title);
        console.log("Content:", data.data.content);
    });
```

## 响应格式

```json
{
  "code": 200,
  "status": "success",
  "data": {
    "title": "Example Domain",
    "description": "Example description",
    "url": "https://example.com",
    "content": "Clean text content...",
    "images": [...],
    "links": [...]
  }
}
```

## 应用场景

1. **RAG 应用**: 为 AI 提供干净的网页内容
2. **内容提取**: 提取文章主要内容
3. **数据收集**: 批量抓取网页文本
4. **知识库构建**: 从网页构建知识库

## 测试

```bash
chmod +x docker/test_jina_reader.sh
cd docker
./test_jina_reader.sh
```

## 重启服务

```bash
cd docker
docker compose restart nginx
```

## 总结

✅ **已配置**: Nginx 代理到 r.jina.ai  
🔒 **安全**: API Key 验证  
🚀 **功能**: 网页内容提取、LLM 友好格式
