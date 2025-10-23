# Jina Search API 使用指南

## 概述

Jina Search API 提供网页搜索和内容抓取功能，可以搜索网页内容并返回结构化的数据。

## API 端点

```
GET http://localhost:8080/v1/search
```

## 认证

需要提供有效的 API Key：

```bash
X-API-Key: sk-llm-web-ui-2024
```

## 基本用法

### 搜索查询

```bash
curl "http://localhost:8080/v1/search?q=Jina+AI" \
  -H "X-API-Key: sk-llm-web-ui-2024"
```

### 搜索特定 URL

```bash
curl "http://localhost:8080/v1/search?url=https://example.com" \
  -H "X-API-Key: sk-llm-web-ui-2024"
```

## 请求参数

### 查询参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `q` | string | 否 | 搜索查询文本 |
| `url` | string | 否 | 要抓取的 URL |

**注意**: `q` 和 `url` 至少需要提供一个。

### 请求头

| 头部 | 类型 | 说明 |
|------|------|------|
| `X-Respond-With` | string | 响应格式，如 `no-content` |
| `X-With-Generated-Alt` | boolean | 生成图片 alt 文本 |
| `X-With-Links-Summary` | boolean | 包含链接摘要 |
| `X-With-Images-Summary` | boolean | 包含图片摘要 |
| `X-Proxy-Url` | string | 使用代理 URL |
| `X-Target-Selector` | string | CSS 选择器 |
| `X-Wait-For-Selector` | string | 等待的 CSS 选择器 |
| `X-Remove-Selector` | string | 移除的 CSS 选择器 |

## 使用示例

### 示例 1: 基本搜索

```bash
curl "http://localhost:8080/v1/search?q=Python+programming" \
  -H "X-API-Key: sk-llm-web-ui-2024"
```

### 示例 2: 不返回内容

```bash
curl "http://localhost:8080/v1/search?q=OpenAI" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -H "X-Respond-With: no-content"
```

### 示例 3: 抓取特定网页

```bash
curl "http://localhost:8080/v1/search?url=https://news.ycombinator.com" \
  -H "X-API-Key: sk-llm-web-ui-2024"
```

### 示例 4: 带图片摘要

```bash
curl "http://localhost:8080/v1/search?q=Machine+Learning" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -H "X-With-Images-Summary: true"
```

### 示例 5: 带链接摘要

```bash
curl "http://localhost:8080/v1/search?q=AI+news" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -H "X-With-Links-Summary: true"
```

### 示例 6: 使用 CSS 选择器

```bash
curl "http://localhost:8080/v1/search?url=https://example.com" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -H "X-Target-Selector: .main-content"
```

## Python 示例

```python
import requests

url = "http://localhost:8080/v1/search"
headers = {
    "X-API-Key": "sk-llm-web-ui-2024"
}

# 搜索查询
params = {"q": "Jina AI"}
response = requests.get(url, params=params, headers=headers)
print(response.json())

# 抓取网页
params = {"url": "https://example.com"}
headers["X-With-Links-Summary"] = "true"
response = requests.get(url, params=params, headers=headers)
print(response.json())
```

## JavaScript 示例

```javascript
const url = "http://localhost:8080/v1/search?q=Python+programming";
const headers = {
    "X-API-Key": "sk-llm-web-ui-2024",
    "X-With-Images-Summary": "true"
};

fetch(url, { headers })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error("Error:", error));
```

## 响应格式

### 成功响应

```json
{
  "code": 200,
  "status": "success",
  "data": {
    "title": "Page Title",
    "description": "Page description",
    "url": "https://example.com",
    "content": "Page content...",
    "images": [...],
    "links": [...]
  }
}
```

### 错误响应

```json
{
  "error": {
    "message": "Invalid API key...",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

## 应用场景

1. **网页搜索**: 搜索互联网内容
2. **内容抓取**: 提取网页结构化数据
3. **RAG 应用**: 为 AI 提供实时网页数据
4. **数据收集**: 批量抓取网页信息

## 测试

```bash
# 给脚本添加执行权限
chmod +x docker/test_jina_search.sh

# 运行测试
cd docker
./test_jina_search.sh
```

## 配置

### Nginx 配置

```nginx
location /v1/search {
    # API Key 验证
    if ($api_key_valid = 0) {
        return 401 '{"error": {...}}';
    }
    
    # 重写 URL
    rewrite ^/v1/search(.*)$ /$1 break;
    
    # 代理到 s.jina.ai
    proxy_pass https://s.jina.ai;
    proxy_set_header Authorization "Bearer ${JINA_API_KEY}";
    # ...
}
```

## 重启服务

```bash
cd docker
docker compose restart nginx
```

## 总结

✅ **已配置**:
- Nginx 代理到 s.jina.ai
- API Key 验证
- 自定义头转发

🔒 **安全特性**:
- 自定义 API Key 验证
- Jina API Key 环境变量管理

🚀 **功能**:
- 网页搜索
- 内容抓取
- 结构化数据提取
