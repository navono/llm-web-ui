# Book Speech API 实现文档

## 概述

本文档描述了 `/v1/book/speech` endpoint 的实现，该端点兼容 Azure TTS 风格的请求，主要用于阅读应用（如 legado）。

## 文件结构

### 核心文件

1. **`book_speech.py`** - 包含所有 book speech 相关的辅助函数
   - `verify_api_key()` - API key 验证
   - `parse_ssml()` - SSML 解析
   - `create_tts_request()` - 创建 TTS 请求对象
   - `check_tts_service()` - TTS 服务健康检查
   - `AudioSpeechRequest` - 请求数据模型

2. **`openai-audio-server.py`** - FastAPI 服务器主文件
   - `/v1/book/speech` endpoint 实现

3. **测试文件**
   - `test_book_speech.py` - 单元测试
   - `test_book_speech_endpoint.py` - 集成测试

## API 端点

### POST /v1/book/speech

#### 请求格式

**Headers:**
```
ocp-apim-subscription-key: <API_KEY>
Content-Type: application/ssml+xml
```

**Body (SSML):**
```xml
<speak>
    <voice name="zh-CN-XiaoxiaoNeural">
        <prosody rate="1.0">
            这是要转换为语音的文本
        </prosody>
    </voice>
</speak>
```

#### 响应格式

**成功响应 (200):**
- Content-Type: `audio/mpeg`
- Body: 音频数据流

**错误响应:**
- `401 Unauthorized` - API key 缺失或无效
- `400 Bad Request` - SSML 格式错误
- `500 Internal Server Error` - 服务器内部错误

## 功能特性

### 1. SSML 解析

支持解析以下 SSML 元素：

- `<speak>` - 根元素
- `<voice name="...">` - 语音选择
- `<prosody rate="...">` - 语速控制

#### 语速格式支持

- 百分比: `"150%"` → 1.5x 速度
- 倍数: `"2"` → 2.0x 速度
- 特殊格式: `"{{speakSpeed*2}}"` → 2.0x 速度

#### 示例

```xml
<!-- 基本格式 -->
<speak>
    <voice name="zh-CN-XiaoxiaoNeural">
        <prosody rate="1.0">
            正常速度的文本
        </prosody>
    </voice>
</speak>

<!-- 快速朗读 -->
<speak>
    <voice name="zh-CN-YunxiNeural">
        <prosody rate="{{speakSpeed*2}}">
            两倍速度的文本
        </prosody>
    </voice>
</speak>

<!-- 带命名空间 -->
<mstts:speak xmlns:mstts="http://www.w3.org/2001/mstts">
    <mstts:voice name="zh-CN-XiaoxiaoNeural">
        <mstts:prosody rate="1.5">
            1.5倍速度的文本
        </mstts:prosody>
    </mstts:voice>
</mstts:speak>
```

### 2. 语音选择

支持多种语音选择方式：

1. **默认语音**: 如果未指定，使用 `江疏影_60.mp3`
2. **自定义语音文件**: 通过 voice name 指定
3. **索引选择**: 使用数字索引选择预设语音

### 3. API Key 验证

- 默认 API key: `pingqixing`
- 通过 header `ocp-apim-subscription-key` 传递
- 验证失败返回 401 错误

### 4. 文本处理

- 自动替换敏感词: `肏` → `操`, `屄` → `逼`
- 支持 UTF-8 编码的中文文本
- 移除 SSML 标签和占位符

## 实现细节

### 与 llm-forwarder 的区别

| 特性 | llm-forwarder | openai-audio-server |
|------|---------------|---------------------|
| TTS 服务 | 转发到外部服务 | 使用本地 IndexTTS2 实例 |
| 服务检查 | 需要健康检查 | 总是可用（同进程） |
| 音频处理 | 通过 HTTP 转发 | 直接调用 TTS 实例 |
| 性能 | 网络延迟 | 本地处理，更快 |

### 工作流程

1. **接收请求** - 获取 SSML 和 headers
2. **验证 API Key** - 检查 `ocp-apim-subscription-key`
3. **解析 SSML** - 提取文本、语速、语音
4. **创建 TTS 请求** - 构建 `AudioSpeechRequest` 对象
5. **处理语音提示** - 选择或加载语音文件
6. **生成语音** - 调用 IndexTTS2.infer()
7. **返回音频流** - StreamingResponse

### 参数映射

```python
# SSML → TTS Parameters
{
    "text": parsed_text,           # 从 SSML 提取
    "speed": calculated_speed,     # 从 rate 计算
    "voice": audio_prompt_path,    # 从 voice name 解析
    "output_format": "mp3",        # 固定为 mp3
    
    # IndexTTS2 参数
    "do_sample": True,
    "top_p": 0.8,
    "top_k": 30,
    "temperature": 0.8,
    "num_beams": 3,
    "repetition_penalty": 10.0,
    "max_mel_tokens": 1500,
}
```

## 测试

### 运行单元测试

```bash
cd /home/ping24/sourcecode/llm-web-ui/docker/indextts2
pytest test_book_speech.py -v
```

### 运行集成测试

```bash
pytest test_book_speech_endpoint.py -v
```

### 测试覆盖

#### 单元测试 (`test_book_speech.py`)

- ✅ API key 验证（有效、无效、None）
- ✅ SSML 解析（简单、复杂、无效格式）
- ✅ 语速解析（百分比、倍数、特殊格式）
- ✅ 特殊字符替换
- ✅ TTS 请求创建
- ✅ 默认值处理

#### 集成测试 (`test_book_speech_endpoint.py`)

- ✅ 成功请求流程
- ✅ API key 验证（缺失、无效）
- ✅ SSML 格式验证
- ✅ 自定义语音
- ✅ 语速调整
- ✅ UTF-8 编码
- ✅ 长文本处理
- ✅ 完整工作流程

## 使用示例

### Python 客户端

```python
import requests

url = "http://localhost:12234/v1/book/speech"
headers = {
    "ocp-apim-subscription-key": "pingqixing",
    "Content-Type": "application/ssml+xml"
}

ssml = """<speak>
    <voice name="zh-CN-XiaoxiaoNeural">
        <prosody rate="1.0">
            这是要转换为语音的文本
        </prosody>
    </voice>
</speak>"""

response = requests.post(url, data=ssml.encode('utf-8'), headers=headers)

if response.status_code == 200:
    with open("output.mp3", "wb") as f:
        f.write(response.content)
    print("音频已保存到 output.mp3")
else:
    print(f"错误: {response.status_code} - {response.text}")
```

### cURL 示例

```bash
curl -X POST http://localhost:12234/v1/book/speech \
  -H "ocp-apim-subscription-key: pingqixing" \
  -H "Content-Type: application/ssml+xml" \
  -d '<speak><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="1.0">测试文本</prosody></voice></speak>' \
  --output output.mp3
```

## 故障排除

### 常见问题

1. **401 Unauthorized**
   - 检查 API key 是否正确
   - 确认 header 名称为 `ocp-apim-subscription-key`

2. **400 Bad Request - Invalid SSML**
   - 验证 SSML 格式是否正确
   - 确保包含 `<speak>` 根元素
   - 检查标签是否正确闭合

3. **500 Internal Server Error**
   - 检查服务器日志 `index-tts-server.log`
   - 确认 IndexTTS2 模型已正确加载
   - 验证音频提示文件是否存在

### 日志

服务器日志位置: `index-tts-server.log`

关键日志级别:
- `INFO` - 请求处理信息
- `ERROR` - 错误详情
- `TRACE` - 详细调试信息

## 性能优化

1. **音频文件缓存** - 语音提示文件在内存中缓存
2. **流式响应** - 使用 StreamingResponse 减少内存占用
3. **后台任务** - 自动清理临时文件
4. **本地处理** - 无网络延迟

## 兼容性

- ✅ Legado 阅读应用
- ✅ Azure TTS API 客户端
- ✅ 支持 UTF-8 编码
- ✅ 跨平台（Linux, Windows, macOS）

## 未来改进

- [ ] 支持更多 SSML 标签（volume, pitch 等）
- [ ] 添加语音缓存机制
- [ ] 支持批量请求
- [ ] 添加请求限流
- [ ] 支持更多音频格式（WAV, OGG 等）
