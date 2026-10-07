import gradio as gr
import time

custom_css = """
.header-title { font-size: 28px; font-weight: bold; display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
.sub-header { color: #666; font-size: 14px; margin-bottom: 20px; }
.section-title { background-color: #EEF2FF; color: #4F46E5; padding: 6px 12px; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 14px; margin-bottom: 10px; }
.record-btn { background-color: #F8FAFC !important; border: 1px solid #E2E8F0 !important; color: #333 !important; font-weight: bold !important; border-radius: 6px !important; display: flex; align-items: center; justify-content: center; }
.record-btn:hover { background-color: #F1F5F9 !important; }
.red-dot { display: inline-block; width: 14px; height: 14px; background-color: #4F46E5; border-radius: 50%; margin-right: 10px; }
.record-indicator { height: 12px; background-color: #E2E8F0; border-radius: 6px; margin-top: 15px; width: 100%; }
.audio-placeholder { height: 100px; display: flex; align-items: center; justify-content: center; background-color: #F8FAFC; border-radius: 8px; color: #CBD5E1; font-size: 30px; }
"""


# --- 交互逻辑模拟 ---
def process_recording():
    """模拟录音与处理过程"""
    yield "正在录音...", "⏹️ 停止"
    time.sleep(2)  # 模拟录音耗时
    yield "系统处理中...", "⏳ 处理中"
    time.sleep(2)  # 模拟处理耗时
    yield "准备就绪", "● 录制"


# --- 界面构建 ---
with gr.Blocks(css=custom_css, title="智能语音聊天助手") as demo:
    # 1. 顶部标题区
    gr.HTML('<div class="header-title">🎙️ 智能语音聊天助手</div>')
    gr.HTML('<div class="sub-header">点击下方按钮开始录音，松开按钮后系统会自动处理</div>')

    # 2. 主体内容区
    with gr.Row():
        # 左侧：对话历史
        with gr.Column(scale=6):
            gr.HTML('<div class="section-title">💬 对话历史</div>')
            chatbot = gr.Chatbot(label="对话历史", height=450, show_label=False)

        # 右侧：录音与回复控制区
        with gr.Column(scale=4):
            # 录音区
            gr.HTML('<div class="section-title">🎵 点击录音</div>')
            with gr.Row():
                record_btn = gr.Button("● 录制", elem_classes="record-btn")
                mic_select = gr.Dropdown(
                    choices=["默认值 - 麦克风阵列 (Realtek)", "其他麦克风设备"],
                    value="默认值 - 麦克风阵列 (Realtek)",
                    show_label=False
                )
            # 模拟的灰色进度条/状态条
            gr.HTML('<div class="record-indicator"></div>')

            # 语音回复区
            gr.HTML('<div class="section-title" style="margin-top: 20px;">🎵 语音回复</div>')
            # 使用 HTML 完美还原示例图中的音符占位符
            audio_placeholder = gr.HTML('<div class="audio-placeholder">♪</div>')

    # 3. 底部状态区
    gr.HTML('<div class="section-title" style="margin-top: 20px;">系统状态</div>')
    status_text = gr.Textbox(value="准备就绪", show_label=False, interactive=False)

    # --- 绑定交互事件 ---
    # 这里演示了点击按钮后的交互效果：改变按钮文字和底部状态
    record_btn.click(
        fn=process_recording,
        inputs=[],
        outputs=[status_text, record_btn]
    )

# 启动应用
if __name__ == "__main__":
    demo.launch()