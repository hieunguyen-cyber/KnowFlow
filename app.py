import streamlit as st
from main import main
import os

# Định nghĩa đường dẫn video đầu ra
OUTPUT_VIDEO_PATH = "./data/output/final_output.mp4"

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
uploaded_file = st.file_uploader("📂 Upload your document (PDF)", type=["pdf"])

# Nếu có file, lưu vào thư mục tạm và lấy đường dẫn
file_path = None
if uploaded_file:
    file_path = f"./data/input/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())  # Lưu file thực tế

# Cấu hình đầu vào
number_of_chunks = st.slider("📜 Number of Chunks", min_value=1, max_value=5, value=3)
gender = st.radio("🗣️ Select Voice Gender", options=["female", "male"])

# Nếu chọn giọng nam, vô hiệu hóa tốc độ (chỉ cho phép "normal")
if gender == "male":
    speed = st.radio("⚡ Speech Speed (Male voice supports only normal)", options=["normal"], disabled=True)
else:
    speed = st.radio("⚡ Speech Speed", options=["fast", "normal", "slow"])

detail_level = st.radio("📖 Detail Level", options=["short", "detailed"])
perspective = st.radio("🔎 Perspective", options=["subjective", "neutral"])
emotion = st.text_input("🎭 Emotion", placeholder="Example: mysterious, romantic,...")
time_setting = st.text_input("⏳ Time Setting", placeholder="Example: modern, medieval,...")
art_style = st.text_input("🎨 Art Style", placeholder="Example: realistic, abstract,...")
style = st.text_input("🖌️ Style", placeholder="Example: realistic, anime,...")
color_palette = st.text_input("🌈 Color Palette", placeholder="Example: vibrant, monochrome,...")

# Nút chạy pipeline
if st.button("🚀 Generate Video"):
    if file_path and os.path.exists(file_path):
        st.success("⏳ Processing started...")
        main(file_path, number_of_chunks, gender, speed, detail_level, perspective, emotion, time_setting, art_style, style, color_palette)

        # Kiểm tra xem video đã được tạo chưa
        if os.path.exists(OUTPUT_VIDEO_PATH):
            st.success("🎉 Video generated successfully!")
            st.video(OUTPUT_VIDEO_PATH)  # Trình chiếu video

            # Tạo link tải về
            with open(OUTPUT_VIDEO_PATH, "rb") as video_file:
                st.download_button(label="📥 Download Video", data=video_file, file_name="final_output.mp4", mime="video/mp4")
        else:
            st.error("⚠️ Video generation failed. Please check the logs.")
    else:
        st.error("⚠️ Please upload a valid PDF file.")