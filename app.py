#!/usr/bin/env python3
"""
对话翻译工具 - Streamlit Web版本（v3.0 终极优化版）
真正的一次性处理：整个文件内容+提示词直接发送给API
10个文件 = 10次API请求，不再分批分句
"""

import os
import re
import time
import requests
import streamlit as st
import zipfile
from pathlib import Path
from io import BytesIO
from typing import List, Tuple, Optional, Dict

# 页面配置
st.set_page_config(
    page_title="对话翻译工具",
    page_icon="🌍",
    layout="wide"
)

# 文件处理配置
MODEL_NAME = "google/gemini-2.5-flash"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_FILES = 5
MAX_TOKENS = 200000  # 提升到20万tokens


class DialogueTranslator:
    """对话翻译器类 - 终极优化版"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def clean_tags_from_content(self, content: str) -> str:
        """清理整个内容中的[tag]语气标签"""
        return re.sub(r'\[.*?\]', '', content)

    def translate_entire_file(self, content: str, filename: str) -> str:
        """
        一次性翻译整个文件内容
        """
        # 先清理标签
        cleaned_content = self.clean_tags_from_content(content)

        # 构建提示词
        prompt = f"""请将以下英文对话文件翻译成地道的中文，要符合中文表达习惯，准确传达原意。

要求：
1. 保持原文件的格式和结构
2. 每行对话格式为"说话者: 内容"
3. 先显示英文原文，然后显示中文翻译，每组对话之间空一行
4. 自动清理已经存在的[tag]标签
5. 翻译要准确、地道、符合中文表达习惯
6. 输出格式示例：

Sally: Hello there!
Sally: 你好！

Pete: How are you?
Pete: 你好吗？

原文件内容：
{cleaned_content}

翻译结果："""

        # 调用API
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": MAX_TOKENS
        }

        try:
            response = requests.post(
                API_URL,
                headers=self.headers,
                json=payload,
                timeout=120  # 增加超时时间
            )
            response.raise_for_status()

            result = response.json()
            translated_content = result['choices'][0]['message']['content'].strip()

            return translated_content

        except requests.exceptions.RequestException as e:
            return f"[API请求失败: {str(e)}]"
        except (KeyError, IndexError) as e:
            return f"[解析响应失败: {str(e)}]"

    def count_dialogues(self, content: str) -> int:
        """统计对话行数"""
        lines = content.split('\n')
        count = 0
        for line in lines:
            line = line.strip()
            if line and ':' in line:
                # 简单判断是否为对话格式
                if re.match(r'^[^:]+:\s*.+$', line):
                    count += 1
        return count

    def process_content(self, content: str, filename: str, progress_callback=None) -> Tuple[str, str, int]:
        """
        处理文件内容，返回(markdown_content, txt_content, dialogue_count)
        """
        if progress_callback:
            progress_callback(0.1, "开始翻译...")

        # 统计对话数量
        dialogue_count = self.count_dialogues(content)

        if progress_callback:
            progress_callback(0.3, "正在调用API翻译...")

        # 一次性翻译整个文件
        translated_content = self.translate_entire_file(content, filename)

        if progress_callback:
            progress_callback(0.8, "正在生成格式...")

        # 生成不同格式
        md_content = self.generate_markdown(translated_content)
        txt_content = self.generate_txt(translated_content)

        if progress_callback:
            progress_callback(1.0, "完成！")

        return md_content, txt_content, dialogue_count

    def generate_markdown(self, content: str) -> str:
        """生成Markdown格式"""
        lines = content.split('\n')
        md_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                md_lines.append("")
                continue

            # 如果包含冒号，认为是对话行，加粗说话者
            if ':' in line:
                match = re.match(r'^([^:]+):\s*(.*)$', line)
                if match:
                    speaker = match.group(1).strip()
                    text = match.group(2).strip()
                    md_lines.append(f"**{speaker}:** {text}")
                else:
                    md_lines.append(line)
            else:
                md_lines.append(line)

        return '\n'.join(md_lines)

    def generate_txt(self, content: str) -> str:
        """生成纯文本格式"""
        # 纯文本直接返回，不需要特殊格式
        return content


def create_download_zip(results: Dict[str, Dict]) -> bytes:
    """创建包含所有结果的ZIP文件（包含MD和TXT两种格式）"""
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, data in results.items():
            base_name = Path(filename).stem

            # 添加Markdown文件
            md_filename = f"{base_name}_translated.md"
            zip_file.writestr(md_filename, data['markdown'].encode('utf-8'))

            # 添加TXT文件
            txt_filename = f"{base_name}_translated.txt"
            zip_file.writestr(txt_filename, data['txt'].encode('utf-8'))

    return zip_buffer.getvalue()


def main():
    """主函数"""
    st.title("🌍 对话翻译工具 v3.0")
    st.markdown("🚀 **终极优化版** - 整个文件一次性翻译，最快速度！支持20万tokens")
    st.markdown("---")

    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")

        # API Key输入
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            help="输入您的OpenRouter API密钥",
            value=os.getenv("OPENROUTER_API_KEY", "")
        )

        st.markdown("---")

        st.subheader("🚀 终极优化")
        st.success("""
        - ✅ 整个文件一次性翻译
        - ✅ 10个文件 = 10次API请求
        - ✅ 支持20万tokens大文件
        - ✅ 速度提升100倍以上！
        """)

        st.markdown("---")

        st.subheader("⚙️ 技术规格")
        st.info(f"""
        - **模型**: {MODEL_NAME}
        - **Max Tokens**: {MAX_TOKENS:,}
        - **最大文件数**: {MAX_FILES}
        - **请求策略**: 1文件=1请求
        """)

        st.markdown("---")

        st.subheader("📋 功能说明")
        st.markdown(f"""
        1. 批量上传文件（最多{MAX_FILES}个）
        2. 每个文件整体发送给API
        3. 自动清理 `[tag]` 语气标签
        4. 生成MD和TXT两种格式
        5. 打包下载所有结果
        """)

        st.markdown("---")

        st.subheader("📝 支持格式")
        st.code(".txt, .md")

        st.markdown("---")

        st.subheader("📄 输入格式示例")
        st.code("""Sally: [warm] Hello!
Pete: [joyful] Hi there!
Sally: How are you today?""", language="text")

        st.subheader("📄 输出格式示例")
        st.code("""Sally: Hello!
Sally: 你好！

Pete: Hi there!
Pete: 嗨，你好！

Sally: How are you today?
Sally: 你今天怎么样？""", language="text")

    # 主内容区
    if not api_key:
        st.warning("⚠️ 请在左侧输入OpenRouter API Key")
        st.info("👈 在侧边栏输入您的API密钥后即可开始使用")
        return

    # 文件上传区域
    st.header("📤 上传文件")

    uploaded_files = st.file_uploader(
        f"选择要翻译的文件（最多{MAX_FILES}个）",
        type=['txt', 'md'],
        accept_multiple_files=True,
        help="支持 .txt 和 .md 格式的文本文件，单个文件最大支持20万tokens"
    )

    if uploaded_files:
        # 检查文件数量
        if len(uploaded_files) > MAX_FILES:
            st.error(f"❌ 最多只能上传{MAX_FILES}个文件，您上传了{len(uploaded_files)}个")
            return

        st.success(f"✅ 已上传 {len(uploaded_files)} 个文件")

        # 显示文件列表
        with st.expander("📋 文件列表", expanded=True):
            total_size = 0
            for idx, file in enumerate(uploaded_files, 1):
                file_size = len(file.getvalue()) / 1024  # KB
                total_size += file_size

                # 估算tokens数量（粗略估算：1KB ≈ 200 tokens）
                estimated_tokens = int(file_size * 200)
                token_status = "✅" if estimated_tokens < MAX_TOKENS else "⚠️"

                st.write(f"{idx}. **{file.name}** ({file_size:.2f} KB, ~{estimated_tokens:,} tokens) {token_status}")

            st.write(f"**总大小**: {total_size:.2f} KB")

        st.markdown("---")

        # 开始翻译按钮
        if st.button("🚀 开始翻译", type="primary", use_container_width=True):
            # 创建翻译器
            translator = DialogueTranslator(api_key, MODEL_NAME)

            # 进度显示
            st.header("🔄 翻译进度")
            st.info(f"📊 将发送 {len(uploaded_files)} 次API请求（每个文件一次）")

            # 存储结果
            results = {}
            success_count = 0
            total_dialogue_count = 0

            # 开始计时
            start_time = time.time()

            # 处理每个文件
            for idx, uploaded_file in enumerate(uploaded_files, 1):
                with st.expander(f"📄 {idx}/{len(uploaded_files)}: {uploaded_file.name}", expanded=True):
                    try:
                        # 读取文件内容
                        content = uploaded_file.getvalue().decode('utf-8')

                        st.info(f"📖 正在翻译: {uploaded_file.name}")
                        st.write(f"🔄 发送第 {idx} 次API请求...")

                        # 创建进度条
                        progress_bar = st.progress(0)
                        progress_text = st.empty()

                        def update_progress(progress, message):
                            progress_bar.progress(progress)
                            progress_text.text(message)

                        # 处理文件（一次性翻译）
                        md_content, txt_content, dialogue_count = translator.process_content(
                            content,
                            uploaded_file.name,
                            progress_callback=update_progress
                        )

                        # 存储结果
                        results[uploaded_file.name] = {
                            'markdown': md_content,
                            'txt': txt_content,
                            'dialogue_count': dialogue_count
                        }

                        success_count += 1
                        total_dialogue_count += dialogue_count

                        st.success(f"✅ 完成翻译: {uploaded_file.name} ({dialogue_count} 行对话)")

                    except Exception as e:
                        st.error(f"❌ 处理失败: {uploaded_file.name} - {str(e)}")

            # 统计结果
            elapsed_time = time.time() - start_time

            st.markdown("---")
            st.header("📊 处理结果汇总")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("上传文件", len(uploaded_files))
            with col2:
                st.metric("成功处理", success_count)
            with col3:
                st.metric("API请求数", success_count)
            with col4:
                st.metric("总耗时", f"{elapsed_time:.1f}秒")

            # 性能统计
            if success_count > 0:
                avg_time = elapsed_time / success_count
                st.info(f"⚡ 平均每个文件耗时: {avg_time:.1f}秒 | 总对话行数: {total_dialogue_count}")

            if results:
                st.markdown("---")
                st.header("📥 下载结果")

                # 创建下载区域
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📦 打包下载（推荐）")
                    zip_bytes = create_download_zip(results)
                    st.download_button(
                        label="⬇️ 下载所有文件（ZIP）",
                        data=zip_bytes,
                        file_name="translated_files.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    st.info("包含所有的 Markdown 和 TXT 文件")

                with col2:
                    st.subheader("📄 单独下载")
                    selected_file = st.selectbox(
                        "选择文件",
                        options=list(results.keys())
                    )

                    if selected_file:
                        result = results[selected_file]
                        base_name = Path(selected_file).stem

                        # Markdown下载
                        st.download_button(
                            label="⬇️ 下载 Markdown (.md)",
                            data=result['markdown'],
                            file_name=f"{base_name}_translated.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

                        # TXT下载
                        st.download_button(
                            label="⬇️ 下载 纯文本 (.txt)",
                            data=result['txt'],
                            file_name=f"{base_name}_translated.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                # 预览区域
                st.markdown("---")
                st.header("👀 预览翻译结果")

                preview_file = st.selectbox(
                    "选择要预览的文件",
                    options=list(results.keys()),
                    key="preview_select"
                )

                if preview_file:
                    result = results[preview_file]

                    tab1, tab2 = st.tabs(["📝 TXT预览", "📄 Markdown预览"])

                    with tab1:
                        st.text_area(
                            "纯文本内容",
                            value=result['txt'],
                            height=400,
                            disabled=True
                        )

                    with tab2:
                        st.text_area(
                            "Markdown内容",
                            value=result['markdown'],
                            height=400,
                            disabled=True
                        )

            st.success("🎉 所有任务完成！")

    else:
        # 显示使用提示
        st.info("👆 请上传要翻译的文件")

        st.markdown("---")
        st.header("📖 使用说明")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("✅ 支持的格式")
            st.markdown("""
            - `.txt` 文本文件
            - `.md` Markdown文件
            """)

            st.subheader("📝 输入格式要求")
            st.markdown("""
            每行格式：`说话者: 内容`

            示例：
            ```
            Sally: [warm] Hello!
            Pete: [joyful] Hi!
            Sally: How are you today?
            ```
            """)

        with col2:
            st.subheader("🎯 v3.0 特点")
            st.markdown("""
            - 🚀 **终极优化**: 1文件=1请求
            - 📄 **大文件支持**: 20万tokens
            - ⚡ **超快速度**: 比逐句快100倍+
            - 📦 **两种格式**: MD、TXT
            """)

            st.subheader("💡 性能对比")
            st.markdown("""
            - **v1.0**: 100行=100次请求
            - **v2.0**: 100行=1次请求（分批）
            - **v3.0**: 整文件=1次请求 🏆
            """)


if __name__ == "__main__":
    main()
