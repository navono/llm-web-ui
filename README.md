# LLM Web UI

一个基于 Gradio 的多模态大语言模型 Web 界面，支持本地模型和在线服务器连接。

## 主要功能

### 🤖 模型支持

- **本地模型管理**：支持多个本地模型的加载、切换和卸载
- **在线服务器连接**：可连接到远程 LLM 服务器（如 OpenAI 兼容 API）
- **混合使用**：同时支持本地和在线模型的灵活切换
- **智能模型类型检测**：自动识别文本模型和多模态模型

### 📝 多模态生成能力

- **文本生成**：支持流式文本输出，可调节生成参数
- **图像理解**：上传图片进行视觉问答和分析
- **视频分析**：支持视频文件的内容理解和问答
- **PDF 文档处理**：多页面 PDF 的智能解析和摘要
- **GIF 动画理解**：动态图像的内容分析
- **图像描述生成**：自动生成图片的详细描述和属性标签

### 🎛️ 高级配置选项

- **Max New Tokens**：1-4096 token 可调
- **Temperature**：0.1-4.0 温度参数控制创造性
- **Top-p (nucleus sampling)**：0.05-1.0 核采样
- **Top-k**：1-1000 候选词筛选
- **Repetition Penalty**：1.0-2.0 重复惩罚系数

### 🛠️ 技术特性

- **流式输出**：实时显示生成过程
- **双输出格式**：原始文本流 + Markdown 格式化输出
- **GPU 加速**：支持 CUDA 加速推理
- **内存管理**：智能的模型加载和卸载机制
- **PDF 预览**：内置 PDF 页面预览和导航
- **快捷键支持**：Ctrl+Enter 快速提交

## 环境要求

- **Python**: >=3.12
- **CUDA**: 推荐使用 CUDA 12.4 以获得最佳性能
- **GPU Memory**: 建议至少 8GB VRAM（用于 4B 模型）
- **系统**: Linux/macOS/Windows

## 安装步骤

1. **克隆项目:**

   ```bash
   git clone <repository-url>
   cd llm_web_ui
   ```

2. **安装依赖:**

   ```bash
   # 使用 uv (推荐)
   uv sync

   # 或使用 pip
   pip install -e .
   ```

3. **配置模型:**

   编辑 `model_config.json` 文件来配置可用的模型：

   ```json
   {
     "models": {
       "qwen3-4b-fp8": {
         "id": "Qwen/Qwen3-4B-Instruct-2507-FP8",
         "name": "Qwen3 4B FP8 (本地)",
         "type": "text",
         "description": "4B参数的FP8量化版本，适合快速测试"
       },
       "qwen3-vl-30b": {
         "id": "Qwen/Qwen3-VL-30B-A3B-Instruct",
         "name": "Qwen3 VL 30B (多模态)",
         "type": "multimodal",
         "description": "30B参数的多模态视觉语言模型"
       }
     },
     "default_model": "qwen3-4b-fp8"
   }
   ```

## 使用方法

### 启动应用

```bash
# 方法1：使用 Python 模块
python -m llm_web_ui

# 方法2：使用 CLI 命令
llm_web_ui

# 方法3：直接运行主文件
python src/main.py
```

默认服务器地址：`http://localhost:7861`（可在配置文件中修改）

### 本地模型使用

1. **选择模型**：在界面上选择本地模型并点击"切换模型"
2. **文本生成**：在"Text Generation"标签页输入文本并提交
3. **多模态功能**：切换到对应标签页（Image/Video/PDF/GIF）上传文件
4. **调节参数**：展开"Advanced options"调整生成参数

### 在线服务器连接

1. **输入服务器地址**：例如 `http://localhost:8080/v1`
2. **连接服务器**：点击"连接服务器"按钮
3. **选择在线模型**：从下拉列表中选择可用模型
4. **使用在线模型**：点击"使用在线模型"切换到在线模式

## 项目结构

```
llm_web_ui/
├── src/
│   ├── main.py                     # 应用程序入口点
│   ├── app.py                      # 主应用逻辑
│   ├── model_manager.py            # 模型管理器
│   ├── gradio/                     # Gradio 界面模块
│   │   ├── ui_components.py        # UI 组件和布局
│   │   ├── text_generation.py      # 文本生成功能
│   │   ├── multimodal_generation.py # 多模态生成功能
│   │   ├── online_client.py        # 在线模型客户端
│   │   └── theme.py                # 界面主题
│   └── utils/                      # 工具模块
│       ├── config.py               # 配置管理
│       ├── custom_logging.py       # 日志配置
│       └── utils.py                # 通用工具函数
├── tests/                          # 测试文件
├── model_config.json              # 模型配置文件
├── pyproject.toml                 # 项目配置和依赖
└── README.md                       # 项目文档
```

## 配置说明

### 模型配置 (`model_config.json`)

```json
{
  "models": {
    "model_key": {
      "id": "model_identifier",
      "name": "display_name",
      "type": "text|multimodal",
      "description": "model_description",
      "model_class": "AutoModelForCausalLM|Qwen3VLMoeForConditionalGeneration",
      "device_map": "auto|{\"\": 6}",
      "dtype": "float16|bfloat16"
    }
  },
  "default_model": "model_key"
}
```

### 服务器配置

默认配置：

- **HTTP 服务器端口**: 7861
- **监听地址**: 0.0.0.0（所有网络接口）
- **队列大小**: 50
- **日志级别**: INFO

## 开发指南

### 代码质量

```bash
# 代码检查
uv run ruff check .

# 代码格式化
uv run ruff format .
```

### 添加新模型

1. 编辑 `model_config.json` 添加新模型配置
2. 重启应用使配置生效
3. 在界面中选择新添加的模型

### 支持的模型类型

- **文本模型**：仅支持文本输入输出
- **多模态模型**：支持文本、图像、视频、PDF 等多模态输入

### 故障排除

**常见问题：**

1. **模型加载失败**

   - 检查模型 ID 是否正确
   - 确认 GPU 内存是否充足
   - 查看日志文件了解详细错误

2. **多模态功能不可用**

   - 确认当前模型类型为 "multimodal"
   - 检查相关依赖是否安装完整（如 OpenCV、PyMuPDF）

3. **在线服务器连接失败**
   - 检查服务器地址是否正确
   - 确认服务器是否正常运行
   - 验证 API 格式是否兼容

### 性能优化建议

1. **GPU 使用**：确保 CUDA 环境正确配置
2. **内存管理**：及时卸载不需要的模型
3. **模型量化**：使用 FP8 或 INT4 量化版本
4. **批处理**：对于大量请求考虑批处理模式

## 技术栈

- **前端界面**: Gradio 5.49.1+
- **深度学习框架**: PyTorch 2.5.1 (CUDA 12.4)
- **模型库**: Transformers 4.57.0
- **图像处理**: Pillow, OpenCV
- **PDF 处理**: PyMuPDF
- **日志系统**: Loguru
- **代码质量**: Ruff
- **包管理**: UV

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 添加适当的类型注解
- 编写清晰的提交信息
- 更新相关文档

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 致谢

- [Qwen](https://github.com/QwenLM/Qwen) - 优秀的多模态语言模型
- [Gradio](https://gradio.app/) - 快速构建机器学习 Web 界面
- [Transformers](https://huggingface.co/transformers/) - Hugging Face 模型库
- [PyTorch](https://pytorch.org/) - 深度学习框架
