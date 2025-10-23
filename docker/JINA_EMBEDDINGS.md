# Jina Embeddings API 集成

## 概述

通过 nginx 代理，可以将 Jina AI 的 Embeddings API 集成到本地服务中，统一通过 `http://localhost:8080/v1/embeddings` 访问。

## 配置说明

### Nginx 配置

已在 `nginx.conf` 中添加 `/v1/embeddings` 端点，代理到 Jina AI API：

```nginx
location /v1/embeddings {
    proxy_pass https://api.jina.ai/v1/embeddings;
    proxy_ssl_server_name on;
    proxy_set_header Host api.jina.ai;
    proxy_set_header Authorization $http_authorization;
    # ... 其他配置
}
```

### 关键特性

- ✅ **HTTPS 代理**：安全地转发到 Jina AI
- ✅ **Authorization 转发**：自动转发 Bearer token
- ✅ **超时优化**：60秒超时，适合大批量文本
- ✅ **无缓冲**：支持流式响应
- ✅ **SSL 验证**：TLS 1.2/1.3 支持

## 使用方法

### 1. 获取 Jina API Key

访问 [Jina AI](https://jina.ai/) 获取 API Key（格式：`jina_xxx`）

### 2. 重启 Nginx

```bash
cd docker
docker compose restart nginx

# 或者重新加载配置
docker exec llm-web-ui-gateway nginx -s reload
```

### 3. 测试 Embeddings API

#### 基础示例

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer jina_xxx" \
  -d '{
    "model": "jina-embeddings-v3",
    "input": ["Hello, world!"]
  }'
```

#### 多语言文本匹配示例

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer jina_xxx" \
  -d @- <<'EOF'
{
  "model": "jina-embeddings-v3",
  "task": "text-matching",
  "input": [
    "Organic skincare for sensitive skin with aloe vera and chamomile",
    "Bio-Hautpflege für empfindliche Haut mit Aloe Vera und Kamille",
    "Cuidado de la piel orgánico para piel sensible con aloe vera y manzanilla",
    "针对敏感肌专门设计的天然有机护肤产品",
    "新しいメイクのトレンドは鮮やかな色と革新的な技術に焦点を当てています"
  ]
}
EOF
```

#### 文本分类示例

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer jina_xxx" \
  -d '{
    "model": "jina-embeddings-v3",
    "task": "classification",
    "input": [
      "The new movie is absolutely fantastic!",
      "I really disliked the service at that restaurant.",
      "The weather today is quite pleasant."
    ]
  }'
```

## 支持的模型

### Jina Embeddings V3

- **模型 ID**: `jina-embeddings-v3`
- **维度**: 1024
- **最大 tokens**: 8192
- **支持任务**:
  - `retrieval.query` - 检索查询
  - `retrieval.passage` - 检索文档
  - `text-matching` - 文本匹配
  - `classification` - 文本分类
  - `separation` - 文本分离

### Jina Embeddings V2

- **模型 ID**: `jina-embeddings-v2-base-en`
- **维度**: 768
- **最大 tokens**: 8192

## API 参数

### 请求参数

```json
{
  "model": "jina-embeddings-v3",      // 必需: 模型 ID
  "input": ["text1", "text2"],        // 必需: 文本数组
  "task": "text-matching",            // 可选: 任务类型
  "dimensions": 1024,                 // 可选: 输出维度
  "normalized": true,                 // 可选: 是否归一化
  "embedding_type": "float"           // 可选: 嵌入类型
}
```

### 响应格式

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.123, -0.456, ...]
    }
  ],
  "model": "jina-embeddings-v3",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

## Python 示例

### 使用 OpenAI SDK

```python
from openai import OpenAI

# 配置客户端使用本地代理
client = OpenAI(
    api_key="jina_xxx",
    base_url="http://localhost:8080/v1"
)

# 获取 embeddings
response = client.embeddings.create(
    model="jina-embeddings-v3",
    input=[
        "Organic skincare for sensitive skin",
        "Bio-Hautpflege für empfindliche Haut"
    ]
)

# 提取向量
embeddings = [item.embedding for item in response.data]
print(f"Got {len(embeddings)} embeddings")
print(f"Dimension: {len(embeddings[0])}")
```

### 使用 Requests

```python
import requests

url = "http://localhost:8080/v1/embeddings"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer jina_xxx"
}
data = {
    "model": "jina-embeddings-v3",
    "task": "text-matching",
    "input": [
        "Hello, world!",
        "Bonjour le monde!",
        "你好，世界！"
    ]
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

for item in result["data"]:
    print(f"Index {item['index']}: {len(item['embedding'])} dimensions")
```

## 应用场景

### 1. 语义搜索

```python
# 1. 为文档库生成 embeddings
documents = [
    "Python is a programming language",
    "JavaScript is used for web development",
    "Machine learning is a subset of AI"
]

doc_embeddings = client.embeddings.create(
    model="jina-embeddings-v3",
    task="retrieval.passage",
    input=documents
).data

# 2. 为查询生成 embedding
query = "What is Python?"
query_embedding = client.embeddings.create(
    model="jina-embeddings-v3",
    task="retrieval.query",
    input=[query]
).data[0].embedding

# 3. 计算相似度并排序
import numpy as np

similarities = []
for doc_emb in doc_embeddings:
    similarity = np.dot(query_embedding, doc_emb.embedding)
    similarities.append(similarity)

# 找到最相关的文档
best_match_idx = np.argmax(similarities)
print(f"Best match: {documents[best_match_idx]}")
```

### 2. 文本聚类

```python
from sklearn.cluster import KMeans
import numpy as np

texts = [
    "I love programming in Python",
    "Python is great for data science",
    "JavaScript is used for web apps",
    "React is a JavaScript framework",
    "Machine learning with TensorFlow",
    "Deep learning using PyTorch"
]

# 获取 embeddings
response = client.embeddings.create(
    model="jina-embeddings-v3",
    task="classification",
    input=texts
)

embeddings = np.array([item.embedding for item in response.data])

# K-means 聚类
kmeans = KMeans(n_clusters=3, random_state=42)
clusters = kmeans.fit_predict(embeddings)

# 显示结果
for i, text in enumerate(texts):
    print(f"Cluster {clusters[i]}: {text}")
```

### 3. 多语言文本匹配

```python
# 不同语言的相似文本
texts = {
    "en": "Organic skincare for sensitive skin",
    "de": "Bio-Hautpflege für empfindliche Haut",
    "es": "Cuidado de la piel orgánico para piel sensible",
    "zh": "针对敏感肌专门设计的天然有机护肤产品"
}

response = client.embeddings.create(
    model="jina-embeddings-v3",
    task="text-matching",
    input=list(texts.values())
)

# 计算相似度矩阵
embeddings = np.array([item.embedding for item in response.data])
similarity_matrix = np.dot(embeddings, embeddings.T)

print("Similarity Matrix:")
print(similarity_matrix)
```

## 性能优化

### 批量处理

```python
# 一次处理多个文本（最多 8192 tokens）
large_batch = ["text" + str(i) for i in range(100)]

response = client.embeddings.create(
    model="jina-embeddings-v3",
    input=large_batch
)

print(f"Processed {len(response.data)} texts")
print(f"Total tokens: {response.usage.total_tokens}")
```

### 维度缩减

```python
# 使用较小的维度以节省存储和计算
response = client.embeddings.create(
    model="jina-embeddings-v3",
    input=["sample text"],
    dimensions=512  # 默认 1024，可以设置为 256, 512, 768
)
```

## 故障排查

### 1. 测试 nginx 配置

```bash
# 检查配置语法
docker exec llm-web-ui-gateway nginx -t

# 查看 nginx 日志
docker logs llm-web-ui-gateway
```

### 2. 测试连接

```bash
# 测试到 Jina API 的连接
docker exec llm-web-ui-gateway wget -O- https://api.jina.ai/v1/embeddings

# 测试本地端点
curl -I http://localhost:8080/v1/embeddings
```

### 3. 常见错误

#### 401 Unauthorized

```json
{"error": "Invalid API key"}
```

**解决**：检查 Authorization 头是否正确：
```bash
-H "Authorization: Bearer jina_xxx"  # ✅ 正确
-H "Authorization: jina_xxx"         # ❌ 错误（缺少 Bearer）
```

#### 504 Gateway Timeout

**原因**：文本太多或网络慢

**解决**：
1. 减少批量大小
2. 增加 nginx 超时设置
3. 检查网络连接

#### SSL 错误

**解决**：确保 nginx 配置中有：
```nginx
proxy_ssl_server_name on;
proxy_ssl_protocols TLSv1.2 TLSv1.3;
```

## 成本估算

Jina AI 定价（参考官网最新价格）：

- **免费额度**：每月 1M tokens
- **付费计划**：按 token 计费

**示例计算**：
- 100 个单词 ≈ 133 tokens
- 1000 个文档（每个 100 词）≈ 133K tokens
- 成本：根据当前定价计算

## 安全建议

1. **不要硬编码 API Key**
   ```bash
   # 使用环境变量
   export JINA_API_KEY="jina_xxx"
   curl -H "Authorization: Bearer $JINA_API_KEY" ...
   ```

2. **限制访问**
   ```nginx
   # 在 nginx 中添加 IP 白名单
   location /v1/embeddings {
       allow 192.168.1.0/24;
       deny all;
       # ... 其他配置
   }
   ```

3. **监控使用量**
   - 定期检查 Jina AI 控制台
   - 设置使用量警报

## 相关资源

- [Jina AI 官方文档](https://jina.ai/embeddings/)
- [Jina Embeddings V3 介绍](https://jina.ai/news/jina-embeddings-v3/)
- [OpenAI Embeddings API 规范](https://platform.openai.com/docs/api-reference/embeddings)

## 总结

通过 nginx 代理集成 Jina Embeddings API：

- ✅ 统一的 API 端点（`/v1/embeddings`）
- ✅ 与 OpenAI SDK 兼容
- ✅ 支持多语言和多任务
- ✅ 高性能向量化
- ✅ 简单的配置和使用

现在可以通过 `http://localhost:8080/v1/embeddings` 使用 Jina AI 的强大 embeddings 功能！
