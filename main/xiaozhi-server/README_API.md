# 小智 AI FastAPI 服务

基于 FastAPI 重构的独立问答服务，分离 ASR/TTS/LLM 业务逻辑，移除 ESP32 硬件依赖。

## 系统架构

```mermaid
graph TB
    Client["客户端 (Postman / Swagger / 前端)"]
    FastAPI["FastAPI 服务 (端口 8004)"]
    Auth["API Key 认证"]
    ASR["ASR 服务 (语音识别)"]
    LLM["LLM 服务 (大语言模型)"]
    TTS["TTS 服务 (语音合成)"]
    ASR_P["ASR Provider (FunASR / SherpaONNX)"]
    LLM_P["LLM Provider (ChatGLM / DeepSeek)"]
    TTS_P["TTS Provider (EdgeTTS / FishSpeech)"]
    Memory["Memory Provider (记忆系统)"]

    Client -->|HTTP POST| FastAPI
    FastAPI --> Auth
    Auth -->|验证通过| ASR
    Auth -->|验证通过| LLM
    Auth -->|验证通过| TTS
    ASR --> ASR_P
    LLM --> LLM_P
    LLM --> Memory
    TTS --> TTS_P
    
目录结构
xiaozhi-server/
├── api/                    # FastAPI 应用层
│   ├── app.py              # 应用入口、生命周期管理
│   ├── auth.py             # API Key 认证
│   ├── dependencies.py     # 服务容器（依赖注入）
│   ├── routes/
│   │   ├── ask.py          # /ask 问答接口
│   │   └── health.py       # /health 健康检查
│   └── schemas/
│       ├── request.py      # 请求模型
│       └── response.py     # 响应模型
├── services/               # 业务逻辑层
│   ├── asr_service.py      # ASR 语音识别服务
│   ├── llm_service.py      # LLM 对话服务
│   └── tts_service.py      # TTS 语音合成服务
├── core/providers/         # Provider 实现层（复用原有代码）
│   ├── asr/                # ASR 提供者
│   ├── llm/                # LLM 提供者
│   └── tts/                # TTS 提供者
├── app_fastapi.py          # 启动脚本
└── config.yaml             # 配置文件

快速开始

环境要求
Python 3.10+
ffmpeg（conda install -c conda-forge ffmpeg）

安装依赖
conda create -n xiaozhi-server python=3.10
conda activate xiaozhi-server
pip install -r requirements.txt
pip install fastapi uvicorn[standard] python-multipart

启动服务
cd main/xiaozhi-server
python app_fastapi.py

访问文档
Swagger UI: http://localhost:8004/docs
ReDoc: http://localhost:8004/redoc

接口说明
POST /api/v1/ask

| 输入类型 | 输出类型 | 说明 |
|---------|---------|------|
| text | text | 文本问答 |
| audio | text | 语音识别 + 问答 |
| text | audio | 问答 + 语音合成 |
| audio | audio | 语音识别 + 问答 + 语音合成 |

认证方式
在请求头中添加：Authorization: Bearer <api_key> 或在查询参数中传递：?api_key=<api_key>
API Key 在服务启动日志中输出。

