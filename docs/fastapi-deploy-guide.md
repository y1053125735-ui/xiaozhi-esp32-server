# 小智 AI FastAPI 部署指南

## 1. 系统架构

### 1.1 整体架构图

```mermaid
graph TB
    subgraph 客户端
        A["Web 前端 / Postman / curl"]
    end

    subgraph FastAPI服务["FastAPI 服务 (:8004)"]
        B["API 路由层 (routes/)"]
        C["认证中间件 (auth.py)"]
        D["服务容器 (dependencies.py)"]
    end

    subgraph 业务逻辑层["业务逻辑层 (services/)"]
        E["ASR Service"]
        F["LLM Service"]
        G["TTS Service"]
    end

    subgraph Provider层["Provider 层 (core/providers/)"]
        H["FunASR / SherpaONNX"]
        I["ChatGLM / DeepSeek"]
        J["EdgeTTS / FishSpeech"]
        K["Memory Provider"]
    end

    A -->|HTTP POST| B
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    E --> H
    F --> I
    F --> K
    G --> J

1.2 请求处理流程
graph LR
    A["用户输入"] --> B{"input_type?"}
    B -->|text| C["直接使用文本"]
    B -->|audio| D["ASR 语音识别"]
    D --> C
    C --> E["LLM 对话"]
    E --> F{"output_type?"}
    F -->|text| G["返回 JSON"]
    F -->|audio| H["TTS 语音合成"]
    H --> I["返回音频文件"]

2. 环境部署

2.1 系统要求
项目       要求
Python    3.10+
操作系统    Linux / Windows / macOS
内存       4GB 以上（ASR 模型需要）
磁盘       2GB 以上（模型文件）
系统依赖    ffmpeg

2.2 安装步骤
# 1. 创建 conda 环境
conda create -n xiaozhi-server python=3.10 -y
conda activate xiaozhi-server

# 2. 克隆项目
git clone https://github.com/xinnan-tech/xiaozhi-esp32-server.git
cd xiaozhi-esp32-server/main/xiaozhi-server

# 3. 安装 Python 依赖
pip install -r requirements.txt
pip install fastapi uvicorn[standard] python-multipart

# 4. 安装 ffmpeg
conda install -c conda-forge ffmpeg -y

2.3 配置文件
编辑 data/.config.yaml，设置 LLM 的 API Key：
LLM:
  ChatGLMLLM:
    api_key: "你的真实API Key"

selected_module:
  ASR: FunASR
  LLM: ChatGLMLLM
  TTS: EdgeTTS

3. 启动服务

3.1 开发模式（带热重载）
python app_fastapi.py

3.2 生产模式
python app_fastapi.py --no-reload --workers 4

3.3 启动成功标志
╔═══════════════════════════════════════════════╗
║          小智 AI FastAPI 服务                  ║
║  地址: http://0.0.0.0:8004                    ║
║  文档: http://localhost:8004/docs              ║
╚═══════════════════════════════════════════════╝

INFO: Application startup complete.
INFO: API Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

4. 接口测试

4.1 Swagger UI（推荐）
浏览器打开 http://localhost:8004/docs，点击 "Try it out" 直接测试。

4.2 curl 命令
# 文本问答
curl -X POST http://localhost:8004/api/v1/ask \
  -H "Authorization: Bearer <api_key>" \
  -F "input_type=text" \
  -F "output_type=text" \
  -F "text=你好，小智"

# 语音输入
curl -X POST http://localhost:8004/api/v1/ask \
  -H "Authorization: Bearer <api_key>" \
  -F "input_type=audio" \
  -F "output_type=text" \
  -F "audio=@test.wav"

4.3 Postman
导入 main/xiaozhi-server/docs/postman_collection.json，设置 api_key 变量后即可使用。

5. 常见问题
问题               解决方案
ffmpeg 找不到      conda install -c conda-forge ffmpeg
API Key 认证失败    查看启动日志获取自动生成的 Key
ASR 识别乱码        检查 SenseVoice 模型权重文件位置
LLM 报错           确认 API Key 是真实密钥，非中文占位符