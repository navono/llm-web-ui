# Jina Rerank API 使用指南

## 概述

Jina Rerank API 用于对文档进行重新排序，根据查询的相关性对文档列表进行排名。这对于搜索引擎、推荐系统等场景非常有用。

## API 端点

```
POST http://localhost:8080/v1/rerank
```

## 认证

需要提供有效的 API Key：

```bash
X-API-Key: sk-llm-web-ui-2024
```

## 请求格式

### 基本请求

```bash
curl http://localhost:8080/v1/rerank \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -d '{
    "model": "jina-reranker-v2-base-multilingual",
    "query": "Organic skincare products for sensitive skin",
    "documents": [
        "Organic skincare for sensitive skin with aloe vera",
        "New makeup trends focus on bold colors",
        "Bio-Hautpflege für empfindliche Haut"
    ]
  }'
```

### 完整参数

```json
{
  "model": "jina-reranker-v2-base-multilingual",
  "query": "查询文本",
  "documents": [
    "文档1",
    "文档2",
    "文档3"
  ],
  "top_n": 3,
  "return_documents": false
}
```

## 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 模型名称，如 `jina-reranker-v2-base-multilingual` |
| `query` | string | 是 | 查询文本 |
| `documents` | array | 是 | 要排序的文档列表 |
| `top_n` | integer | 否 | 返回前 N 个结果，默认返回所有 |
| `return_documents` | boolean | 否 | 是否返回文档内容，默认 false |

## 支持的模型

- `jina-reranker-v2-base-multilingual` - 多语言基础模型
- `jina-reranker-v1-base-en` - 英文基础模型
- 其他 Jina Rerank 模型

## 响应格式

### 成功响应

```json
{
  "model": "jina-reranker-v2-base-multilingual",
  "usage": {
    "total_tokens": 150,
    "prompt_tokens": 150
  },
  "results": [
    {
      "index": 0,
      "relevance_score": 0.95,
      "document": {
        "text": "Organic skincare for sensitive skin..."
      }
    },
    {
      "index": 2,
      "relevance_score": 0.87,
      "document": {
        "text": "Bio-Hautpflege für empfindliche Haut..."
      }
    },
    {
      "index": 1,
      "relevance_score": 0.23,
      "document": {
        "text": "New makeup trends..."
      }
    }
  ]
}
```

### 错误响应

#### 401 - 无效的 API Key

```json
{
  "error": {
    "message": "Invalid API key. Please provide a valid X-API-Key header.",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

#### 400 - 请求参数错误

```json
{
  "error": {
    "message": "Invalid request parameters",
    "type": "invalid_request_error"
  }
}
```

## 使用示例

### 示例 1: 简单排序

```bash
curl http://localhost:8080/v1/rerank \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -d '{
    "model": "jina-reranker-v2-base-multilingual",
    "query": "Python programming tutorial",
    "documents": [
        "Learn Python basics in 30 days",
        "JavaScript for beginners",
        "Advanced Python programming guide",
        "HTML and CSS fundamentals"
    ]
  }'
```

### 示例 2: 返回前 3 个结果

```bash
curl http://localhost:8080/v1/rerank \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -d '{
    "model": "jina-reranker-v2-base-multilingual",
    "query": "机器学习入门",
    "top_n": 3,
    "documents": [
        "机器学习基础教程",
        "深度学习实战指南",
        "Python 数据分析",
        "神经网络原理",
        "自然语言处理入门"
    ]
  }'
```

### 示例 3: 多语言文档排序

```bash
curl http://localhost:8080/v1/rerank \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -d '{
    "model": "jina-reranker-v2-base-multilingual",
    "query": "Organic skincare products for sensitive skin",
    "top_n": 3,
    "documents": [
        "Organic skincare for sensitive skin with aloe vera and chamomile",
        "New makeup trends focus on bold colors and innovative techniques",
        "Bio-Hautpflege für empfindliche Haut mit Aloe Vera und Kamille",
        "Neue Make-up-Trends setzen auf kräftige Farben",
        "Cuidado de la piel orgánico para piel sensible",
        "针对敏感肌专门设计的天然有机护肤产品",
        "敏感肌のために特別に設計された天然有機スキンケア製品"
    ],
    "return_documents": true
  }'
```

### 示例 4: Python 客户端

```python
import requests

url = "http://localhost:8080/v1/rerank"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "sk-llm-web-ui-2024"
}

data = {
    "model": "jina-reranker-v2-base-multilingual",
    "query": "Best restaurants in New York",
    "top_n": 5,
    "documents": [
        "Italian restaurant in Manhattan with great pasta",
        "Chinese takeout in Brooklyn",
        "French fine dining in Upper East Side",
        "Mexican street food in Queens",
        "Japanese sushi bar in SoHo"
    ],
    "return_documents": True
}

response = requests.post(url, json=data, headers=headers)
results = response.json()

print("Reranked results:")
for result in results["results"]:
    print(f"Score: {result['relevance_score']:.2f} - {result['document']['text']}")
```

### 示例 5: JavaScript 客户端

```javascript
const url = "http://localhost:8080/v1/rerank";
const headers = {
    "Content-Type": "application/json",
    "X-API-Key": "sk-llm-web-ui-2024"
};

const data = {
    model: "jina-reranker-v2-base-multilingual",
    query: "Best programming languages for web development",
    top_n: 3,
    documents: [
        "JavaScript is the most popular language for web development",
        "Python is great for data science and machine learning",
        "TypeScript adds type safety to JavaScript",
        "Java is widely used in enterprise applications",
        "React is a JavaScript library for building user interfaces"
    ]
};

fetch(url, {
    method: "POST",
    headers: headers,
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(results => {
    console.log("Reranked results:");
    results.results.forEach(result => {
        console.log(`Score: ${result.relevance_score.toFixed(2)} - Index: ${result.index}`);
    });
})
.catch(error => console.error("Error:", error));
```

## 应用场景

### 1. 搜索引擎优化

```python
# 对搜索结果进行重新排序
search_results = ["doc1", "doc2", "doc3", ...]
query = "user search query"

reranked = rerank_api.rerank(
    query=query,
    documents=search_results,
    top_n=10
)
```

### 2. 推荐系统

```python
# 根据用户偏好对推荐内容排序
user_preference = "likes organic skincare"
candidates = ["product1", "product2", "product3", ...]

ranked_recommendations = rerank_api.rerank(
    query=user_preference,
    documents=candidates,
    top_n=5
)
```

### 3. 问答系统

```python
# 找到最相关的答案
question = "How to install Python?"
candidate_answers = ["answer1", "answer2", "answer3", ...]

best_answers = rerank_api.rerank(
    query=question,
    documents=candidate_answers,
    top_n=3
)
```

### 4. 文档检索

```python
# RAG (Retrieval-Augmented Generation) 应用
user_query = "What is machine learning?"
retrieved_chunks = ["chunk1", "chunk2", "chunk3", ...]

relevant_chunks = rerank_api.rerank(
    query=user_query,
    documents=retrieved_chunks,
    top_n=5
)
```

## 性能优化

### 1. 批量处理

```python
# 一次处理多个文档
documents = ["doc1", "doc2", ..., "doc100"]  # 最多 100 个文档
results = rerank_api.rerank(query=query, documents=documents)
```

### 2. 限制返回数量

```python
# 只返回最相关的结果
results = rerank_api.rerank(
    query=query,
    documents=documents,
    top_n=5  # 只返回前 5 个
)
```

### 3. 不返回文档内容

```python
# 节省带宽
results = rerank_api.rerank(
    query=query,
    documents=documents,
    return_documents=False  # 只返回索引和分数
)
```

## 测试

### 运行测试脚本

```bash
# 给脚本添加执行权限
chmod +x docker/test_jina_rerank.sh

# 运行测试
cd docker
./test_jina_rerank.sh
```

### 手动测试

```bash
# 测试无 API Key（应返回 401）
curl http://localhost:8080/v1/rerank \
  -H "Content-Type: application/json" \
  -d '{"model": "jina-reranker-v2-base-multilingual", "query": "test", "documents": ["doc1"]}'

# 测试有效 API Key（应返回结果）
curl http://localhost:8080/v1/rerank \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-llm-web-ui-2024" \
  -d '{"model": "jina-reranker-v2-base-multilingual", "query": "test", "documents": ["doc1", "doc2"]}'
```

## 配置

### Nginx 配置

Rerank API 的配置位于 `docker/nginx/nginx.conf`：

```nginx
location /v1/rerank {
    # API Key 验证
    if ($api_key_valid = 0) {
        return 401 '{"error": {"message": "Invalid API key..."}}';
    }
    
    # 代理到 Jina AI Rerank API
    proxy_pass https://api.jina.ai/v1/rerank;
    proxy_set_header Authorization "Bearer ${JINA_API_KEY}";
    # ... 其他配置
}
```

### 环境变量

在 `docker/.env` 中配置：

```bash
# Jina API Key
JINA_API_KEY=jina_2c7b15da5fc047b2bcd991ae4fa38406qLzVfcj6sMrSzdwlVjCMuFuNJSga

# 自定义 API Keys
API_KEY_1=sk-llm-web-ui-2024
API_KEY_2=sk-local-dev-key
```

## 重启服务

修改配置后需要重启 nginx：

```bash
cd docker
docker compose restart nginx

# 或使用 Makefile
make docker-restart
```

## 故障排查

### 问题 1: 401 错误

**原因**: 未提供或提供了无效的 API Key

**解决**:
```bash
# 确保请求包含正确的 API Key
curl -H "X-API-Key: sk-llm-web-ui-2024" ...
```

### 问题 2: 502 错误

**原因**: 无法连接到 Jina API

**解决**:
```bash
# 检查 JINA_API_KEY 是否正确设置
docker exec llm-web-ui-gateway env | grep JINA_API_KEY

# 测试 Jina API 连接
curl https://api.jina.ai/v1/rerank \
  -H "Authorization: Bearer $JINA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "jina-reranker-v2-base-multilingual", "query": "test", "documents": ["doc1"]}'
```

### 问题 3: 超时错误

**原因**: 文档太多或太长

**解决**:
- 减少文档数量（建议 < 100）
- 缩短文档长度
- 增加超时时间（在 nginx.conf 中）

## 最佳实践

1. **限制文档数量**: 每次请求不超过 100 个文档
2. **控制文档长度**: 每个文档不超过 512 tokens
3. **使用 top_n**: 只返回需要的结果数量
4. **缓存结果**: 对相同查询缓存排序结果
5. **异步处理**: 对大量文档使用异步处理
6. **监控使用**: 跟踪 API 调用次数和成本

## 相关链接

- [Jina AI 官方文档](https://jina.ai/reranker/)
- [API 参考](https://api.jina.ai/redoc#tag/rerank)
- [定价信息](https://jina.ai/pricing/)

## 总结

✅ **已配置**:
- Nginx 代理到 Jina Rerank API
- API Key 验证
- 环境变量管理

🔒 **安全特性**:
- 自定义 API Key 验证
- Jina API Key 通过环境变量管理
- HTTPS 连接到 Jina API

🚀 **易用性**:
- OpenAI 兼容的接口
- 多语言支持
- 简单的 REST API

现在你可以通过本地网关安全地使用 Jina Rerank API 了！
