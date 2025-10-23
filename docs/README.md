# LLM Web UI Docker 部署

使用 Docker Compose 部署 LLM Web UI 服务，包含 nginx API 网关统一路由。

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx API Gateway                     │
│                   (localhost:8080)                       │
└───────────────┬─────────────────────┬───────────────────┘
                │                     │
    ┌───────────▼──────────┐  ┌──────▼──────────────┐
    │  open-llm-vtuber     │  │    indextts2        │
    │  (ASR + WebSocket)   │  │    (TTS 服务)       │
    │  Port: 12393         │  │    Port: 12234      │
    └──────────────────────┘  └─────────────────────┘
```

## 服务说明

### 1. Nginx API Gateway (端口 8080)
统一的 API 入口，负责路由请求到不同的后端服务。

### 2. open-llm-vtuber (内部端口 12393)
提供以下功能：
- ASR 语音转录
- WebSocket 实时通信
- Live2D 模型管理
- Web 工具界面

### 3. indextts2 (内部端口 12234)
提供 TTS (文本转语音) 服务。

## API 端点

### TTS (文本转语音)

#### OpenAI 兼容端点
```bash
POST /v1/audio/speech
Content-Type: application/json

{
  "model": "indextts2",
  "input": "你好，这是一个测试。",
  "voice": "alloy",
  "response_format": "mp3"
}
```

#### 自定义 TTS 端点
```bash
POST /v1/tts
Content-Type: application/json

{
  "text": "你好世界",
  "audio_prompt": "Female-成熟_01.wav",
  "output_format": "mp3"
}
```

#### 获取可用语音列表
```bash
GET /v1/voices
```

### ASR (语音转录)

#### OpenAI 兼容端点
```bash
POST /v1/audio/transcriptions
Content-Type: multipart/form-data

file: <audio_file>
model: funASR
```

#### 自定义 ASR 端点
```bash
POST /asr
Content-Type: multipart/form-data

file: <audio_file>
```

### 模型列表

```bash
GET /v1/models
```

返回所有可用模型的列表。

### WebSocket 端点

- `/client-ws` - 客户端 WebSocket 连接
- `/tts-ws` - TTS WebSocket 流式传输
- `/proxy-ws` - 代理 WebSocket 连接

### 健康检查

```bash
GET /health
```

## 快速开始

### 1. 启动服务

```bash
cd docker
docker-compose up -d
```

### 2. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f nginx
docker-compose logs -f open-llm-vtuber
docker-compose logs -f indextts2
```

### 3. 测试 API

运行测试脚本：

```bash
chmod +x test_api_gateway.sh
./test_api_gateway.sh
```

或手动测试：

```bash
# 测试健康检查
curl http://localhost:8080/health

# 测试 API 网关信息
curl http://localhost:8080/

# 测试模型列表
curl http://localhost:8080/v1/models

# 测试 TTS
curl -X POST http://localhost:8080/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"indextts2","input":"你好世界","voice":"alloy"}' \
  --output test_output.mp3

# 测试 ASR
curl -X POST http://localhost:8080/v1/audio/transcriptions \
  -F 'file=@your_audio.wav' \
  -F 'model=funASR'
```

### 4. 停止服务

```bash
docker-compose down
```

## 配置说明

### 环境变量

在 `docker-compose.yml` 同级目录创建 `.env` 文件：

```env
# 代理设置（可选）
PROXY_SERVER=http://your-proxy:port
NO_PROXY=localhost,127.0.0.1

# GPU 设置
CUDA_VISIBLE_DEVICES=0
```

### Nginx 配置

nginx 配置文件位于 `nginx/nginx.conf`。

#### 添加新的 OpenAI 兼容服务

如果需要添加其他服务（如 LLM、Embedding 等），可以在 nginx 配置中添加：

```nginx
# 在 http 块中添加 upstream
upstream llm-service {
    server llm-service:8000;
}

# 在 server 块中添加 location
location /v1/chat/completions {
    proxy_pass http://llm-service;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    
    proxy_buffering off;
}
```

然后在 `docker-compose.yml` 中添加服务：

```yaml
services:
  llm-service:
    image: your-llm-image:latest
    container_name: llm-service
    networks:
      - llm-network
    expose:
      - "8000"
    # ... 其他配置
```

### 网络配置

所有服务都在 `llm-network` 桥接网络中运行，只有 nginx 网关暴露到主机的 8080 端口。

如果需要直接访问某个服务（调试用），可以临时添加端口映射：

```yaml
services:
  indextts2:
    ports:
      - "12234:12234"  # 临时暴露端口
```

## 故障排查

### 1. 服务无法启动

检查日志：
```bash
docker-compose logs
```

### 2. 端口冲突

如果 8080 端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
nginx:
  ports:
    - "8081:8080"  # 改为其他端口
```

### 3. GPU 不可用

确保已安装 nvidia-docker 并配置正确：

```bash
# 测试 GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 4. 网络连接问题

检查容器网络：

```bash
# 查看网络
docker network ls

# 检查容器网络连接
docker network inspect llm-network
```

### 5. Nginx 配置错误

测试 nginx 配置：

```bash
docker-compose exec nginx nginx -t
```

重新加载配置：

```bash
docker-compose exec nginx nginx -s reload
```

## 性能优化

### 1. 调整 Nginx Worker 进程

在 `nginx/nginx.conf` 中：

```nginx
worker_processes auto;  # 自动根据 CPU 核心数
worker_connections 1024;  # 每个 worker 的连接数
```

### 2. 启用缓存

对于静态资源，可以添加缓存配置：

```nginx
location /static {
    proxy_pass http://open-llm-vtuber;
    proxy_cache_valid 200 1h;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
}
```

### 3. 调整超时时间

根据实际需求调整超时时间：

```nginx
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
```

## 安全建议

1. **生产环境**：不要使用 `network_mode: host`
2. **访问控制**：配置防火墙规则限制访问
3. **HTTPS**：在生产环境中使用 HTTPS
4. **认证**：添加 API 认证机制
5. **日志**：定期检查和轮转日志文件

## 扩展阅读

- [Nginx 官方文档](https://nginx.org/en/docs/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [OpenAI API 参考](https://platform.openai.com/docs/api-reference)
