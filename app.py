import streamlit as st
import os
import main  # Import file main.py
import google.generativeai as genai
from huggingface_hub import InferenceClient

# Write your own secrets.toml and run this in terminal: mv secrets.toml .streamlit/secrets.toml

HF_API_KEY = st.secrets["secrets"]["HUGGINGFACE_API_KEY"]
GOOGLE_API_KEY = st.secrets["secrets"]["GOOGLE_API_KEY"] 

# Sử dụng API key mà không hardcode
genai.configure(api_key=GOOGLE_API_KEY)
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)

def process_file(uploaded_file):
    if uploaded_file is not None:
        # Hiển thị thanh progress
        progress_bar = st.progress(0)
        
        # Lưu file vào thư mục tạm
        input_path = os.path.join("./data/input", uploaded_file.name)
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        progress_bar.progress(30)
        
        # Gọi hàm main() để xử lý
        main.main(input_path)
        
        progress_bar.progress(70)
        
        output_path = "./data/output/final_output.mp4"
        if os.path.exists(output_path):
            progress_bar.progress(100)
            return output_path
        else:
            st.error("Lỗi: Không tìm thấy video đầu ra!")
    return None

# UI chính
st.title("KnowFlow - Tạo bài giảng từ tài liệu")
uploaded_file = st.file_uploader("Tải lên file của bạn:", type=["pdf", "docx"])

if uploaded_file is not None:
    st.write("### File đã tải lên:", uploaded_file.name)
    output_path = process_file(uploaded_file)
    
    if output_path:
        st.video(output_path)
        with open(output_path, "rb") as file:
            st.download_button(label="Tải video xuống", data=file, file_name="./data/output/final_output.mp4", mime="video/mp4")
