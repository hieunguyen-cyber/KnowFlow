import streamlit as st
from main import main
import os
import subprocess

# Định nghĩa đường dẫn video đầu ra
OUTPUT_VIDEO_PATH = "./data/output/final_output.mp4"
OUTPUT_VIDEO_FIXED_PATH = "./data/output/final_output_fixed.mp4"

# Tiêu đề ứng dụng
st.set_page_config(page_title="KnowFlow", page_icon="📖")
st.markdown("<h1 style='text-align: center;'>📖 KnowFlow 🌊</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Convert documents into videos with AI-powered storytelling</h4>", unsafe_allow_html=True)

# Thông tin tác giả
st.markdown("---")
st.markdown("👨‍💻 **Author:** Nguyễn Trung Hiếu")
st.markdown("🔗 [GitHub Repository](https://github.com/hieunguyen-cyber/KnowFlow.git)")
st.markdown("---")

# Upload file PDF
uploaded_file = st.file_uploader("📂 Upload your document (PDF)", type=["pdf","docx"])

# Nếu có file, lưu vào thư mục tạm và lấy đường dẫn
file_path = None
if uploaded_file:
    file_path = f"./data/input/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())  # Lưu file thực tế
number_of_images = st.slider("🖼️ Nhập số ảnh",1,10,3)
# Cấu hình đầu vào
gender = st.radio("🗣️ Select Voice Gender", options=["female", "male"])

# Nếu chọn giọng nam, vô hiệu hóa tốc độ (chỉ cho phép "normal")
if gender == "male":
    speed = st.radio("⚡ Speech Speed (Male voice supports only normal)", options=["normal"], disabled=True)
else:
    speed = st.radio("⚡ Speech Speed", options=["fast", "normal", "slow"])
analysis_level = st.radio("Analysis Level", options=["basic", "detailed"])
writting_style = st.radio("Writting Style", options  = ["academic","popular","creative","humorous"])

# Tạo thanh trượt với giá trị từ 50 đến 250, bước nhảy 50
word_lower_limit, word_upper_limit = st.slider(
    "Chọn khoảng độ dài văn bản:",
    min_value=50,
    max_value=250,
    value=(50, 250),  # Giá trị mặc định
    step=50
)

st.write(f"Giới hạn độ dài văn bản từ **{word_lower_limit}** đến **{word_upper_limit}** ký tự.")
detail_level = st.radio("📖 Detail Level of Image Description", options=["short", "detailed"])
perspective = st.radio("🔎 Perspective", options=["subjective", "neutral"])
emotion = st.text_input("🎭 Emotion", placeholder="Example: mysterious, romantic,...")
time_setting = st.text_input("⏳ Time Setting", placeholder="Example: modern, medieval,...")
art_style = st.text_input("🖌️ Image Description Style", placeholder="Example: realistic, abstract,...")
style = st.text_input("🎨 Image Style", placeholder="Example: realistic, anime,...")
color_palette = st.text_input("🌈 Color Palette", placeholder="Example: vibrant, monochrome,...")

def convert_audio_format(video_input, video_output):
    """ Chuyển đổi định dạng âm thanh của video sang AAC """
    command = [
        "ffmpeg", "-i", video_input,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        video_output
    ]
    subprocess.run(command, check=True)

# Nút chạy pipeline
if st.button("🚀 Generate Video"):
    if file_path and os.path.exists(file_path):
        st.success("⏳ Processing started...")
        main(file_path, analysis_level, writting_style, word_lower_limit, word_upper_limit, gender, speed, number_of_images, detail_level, perspective, emotion, time_setting, art_style, style, color_palette)

        # Kiểm tra xem video đã được tạo chưa
        if os.path.exists(OUTPUT_VIDEO_PATH):
            st.success("🎉 Video generated successfully!")
            
            # Chuyển đổi định dạng âm thanh
            convert_audio_format(OUTPUT_VIDEO_PATH, OUTPUT_VIDEO_FIXED_PATH)

            st.video(OUTPUT_VIDEO_FIXED_PATH)  # Trình chiếu video

            # Tạo link tải về
            with open(OUTPUT_VIDEO_FIXED_PATH, "rb") as video_file:
                st.download_button(label="📥 Download Video", data=video_file, file_name="final_output_fixed.mp4", mime="video/mp4")
        else:
            st.error("⚠️ Video generation failed. Please check the logs.")
    else:
        st.error("⚠️ Please upload a valid PDF file.")
