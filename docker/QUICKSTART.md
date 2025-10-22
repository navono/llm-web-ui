# 快速开始指南

## 前置要求

- Docker 和 Docker Compose
- NVIDIA Docker (如果使用 GPU)
- 已构建的镜像：
  - `open-llm-vtuber:latest`
  - `indextts2:latest`

## 5 分钟快速部署

### 1. 启动所有服务

```bash
# 在项目根目录
make docker-up

# 或者在 docker 目录
cd docker
docker compose up -d
```

### 2. 检查服务状态

```bash
make docker-ps

# 或者
cd docker
docker compose ps
```

期望输出：
```
NAME                IMAGE                  STATUS
llm-api-gateway     nginx:alpine           Up (healthy)
open-llm-vtuber     open-llm-vtuber:latest Up (healthy)
indextts2           indextts2:latest       Up
```

### 3. 测试 API

```bash
# 测试健康检查
curl http://localhost:8080/health

# 查看 API 信息
curl http://localhost:8080/

# 运行完整测试
make docker-test
```

### 4. 使用 API

#### TTS 生成音频

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "indextts2",
    "input": "你好，这是一个测试。",
    "voice": "alloy"
  }' \
  --output output.mp3
```

#### ASR 转录音频

```bash
curl -X POST http://localhost:8080/v1/audio/transcriptions \
  -F 'file=@your_audio.wav' \
  -F 'model=funASR'
```

### 5. 查看日志

```bash
# 所有服务日志
make docker-logs

# 只看 nginx 日志
make docker-logs-nginx

# 只看 vtuber 日志
make docker-logs-vtuber
```

### 6. 停止服务

```bash
make docker-down

# 或者
cd docker
docker compose down
```

## 常用命令

```bash
# 启动服务
make docker-up

# 停止服务
make docker-down

# 重启服务
make docker-restart

# 查看状态
make docker-ps

# 查看日志
make docker-logs

# 测试 API
make docker-test

# 构建镜像
make docker-build-all
```

## 访问端点

- **API Gateway**: http://localhost:8080
- **健康检查**: http://localhost:8080/health
- **API 文档**: http://localhost:8080/

## 故障排查

### 服务启动失败

```bash
# 查看详细日志
docker compose logs

# 检查特定服务
docker compose logs nginx
docker compose logs open-llm-vtuber
docker compose logs indextts2
```

### 端口被占用

修改 `docker-compose.yml` 中的端口：

```yaml
nginx:
  ports:
    - "8081:8080"  # 改为其他端口
```

### GPU 不可用

检查 NVIDIA Docker：

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## 下一步

- 阅读完整文档: [README.md](README.md)
- 配置环境变量: 复制 `.env.example` 为 `.env`
- 自定义 nginx 配置: 编辑 `nginx/nginx.conf`
- 添加新服务: 参考 README.md 中的扩展说明
