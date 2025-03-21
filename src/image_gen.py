from PIL import Image
import os
import glob
from collections import defaultdict
from google import genai
from tqdm import tqdm
import random
import time
from dotenv import load_dotenv
import base64
from google.genai import types
def set_up_api():
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    client_gemini = genai.Client(api_key = GOOGLE_API_KEY)
    return client_gemini
def split_text_for_images(number_of_images):
    with open("text.txt", "r", encoding="utf-8") as file:
        text = file.read().strip()

    total_length = len(text)
    chunk_size = total_length // number_of_images  # Độ dài trung bình của mỗi đoạn

    chunks = []
    start = 0

    for i in range(number_of_images):
        # Xác định điểm kết thúc gần nhất tại dấu câu (nếu có)
        end = start + chunk_size
        if i < number_of_images - 1:
            while end < total_length and text[end] not in ".!?":  
                end += 1  # Mở rộng đến dấu câu gần nhất để tránh cắt ngang câu
            if end < total_length - 1:
                end += 1  # Bao gồm cả dấu câu vào đoạn

        chunk = text[start:end].strip()
        chunks.append(chunk)
        start = end  # Bắt đầu đoạn tiếp theo từ đây

    return chunks
def describe_image(description, client_gemini, detail_level="short", perspective="neutral", emotion=None, time_setting=None, art_style=None):
    """
    Nhận một đoạn văn mô tả chi tiết và trả về một câu mô tả hình ảnh theo các tùy chỉnh.

    Args:
        description (str): Đoạn văn mô tả chi tiết.
        detail_level (str): Mức độ chi tiết ("short" hoặc "detailed").
        perspective (str): Góc nhìn ("subjective" hoặc "neutral").
        emotion (str, optional): Cảm xúc chủ đạo (nếu có, ví dụ: "mysterious", "romantic").
        time_setting (str, optional): Bối cảnh thời gian (ví dụ: "modern", "medieval", "futuristic").
        art_style (str, optional): Phong cách nghệ thuật (ví dụ: "realistic", "abstract", "sketch").

    Returns:
        str: Một câu mô tả hình ảnh theo yêu cầu.
    """
    
    prompt = f"""
    Bạn là chuyên gia mô tả hình ảnh. Hãy đọc đoạn mô tả dưới đây và tạo một mô tả hình ảnh theo các tiêu chí sau:
    - Mức độ chi tiết: {"Ngắn gọn" if detail_level == "short" else "Chi tiết"}.
    - Góc nhìn: {"Chủ quan" if perspective == "subjective" else "Trung lập"}.
    {f"- Cảm xúc chủ đạo: {emotion}." if emotion else ""}
    {f"- Bối cảnh thời gian: {time_setting}." if time_setting else ""}
    {f"- Phong cách nghệ thuật: {art_style}." if art_style else ""}

    Đoạn mô tả:
    {description}

    Hãy tạo một mô tả hình ảnh phù hợp với yêu cầu trên bằng Tiếng Anh.
    """

    try:
        response = client_gemini.models.generate_content(
            model = "gemini-2.0-flash", contents = [prompt]
        )
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return ""
def generate_image(prompt, client, output_path, style=None, color_palette=None):
    """
    Tạo hình ảnh từ mô tả văn bản với các tùy chỉnh linh hoạt.
    
    :param prompt: Mô tả hình ảnh đầu vào.
    :param output_path: Đường dẫn lưu ảnh đầu ra.
    :param style: Phong cách hình ảnh (nếu có, ví dụ: 'realistic', 'anime', 'cyberpunk').
    :param color_palette: Bảng màu ưu tiên (nếu có, ví dụ: 'vibrant', 'monochrome').
    """
    custom_prompt = f"Create an image based on the following description: {prompt}"
    
    if style:
        custom_prompt += f" in {style} style"
    if color_palette:
        custom_prompt += f" with {color_palette} color scheme"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=custom_prompt,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print("🔹 API returned text:", part.text)
            elif part.inline_data is not None:
                print("🔹 API returned an image (base64 detected)")
                print(f"🔍 Base64 data length: {len(part.inline_data.data)} bytes")

                try:
                    # Giải mã base64
                    image_data = base64.b64decode(part.inline_data.data)
                    with open(output_path, "wb") as f:
                        f.write(image_data)

                    print(f"✅ Successfully saved image as {output_path}")
                except Exception as e:
                    print(f"❌ Error decoding and saving image: {e}")
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")

def image_gen(number_of_images = 3,detail_level = "short", perspective="neutral", emotion=None, time_setting=None, art_style=None, style=None, color_palette=None):
    client_gemini = set_up_api()
    texts = split_text_for_images(number_of_images)
    index = 0
    for text in tqdm(texts, desc="Processing", unit="image"):
        output_path = f"{index}.png"
        prompt = describe_image(text, client_gemini, detail_level, perspective, emotion, time_setting, art_style)
        print(prompt)
        generate_image(prompt, client_gemini, output_path, style, color_palette)
        index += 1
if __name__ == "__main__":
    image_gen(number_of_images = 1,detail_level = "short", perspective="neutral", emotion=None, time_setting=None, art_style=None, style=None, color_palette=None)