from huggingface_hub import InferenceClient
import os
import glob
from collections import defaultdict
import google.generativeai as genai
from tqdm import tqdm
from huggingface_hub.utils import HfHubHTTPError
import random
import time
from dotenv import load_dotenv

load_dotenv()
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)

def merge_grouped_texts(folder_path):
    """
    Nhóm các file theo {group}_{number}.txt, sau đó tổng hợp nội dung từng nhóm.
    
    Args:
        folder_path (str): Đường dẫn tới thư mục chứa các file .txt
    
    Returns:
        list: Danh sách các văn bản tổng hợp của từng nhóm
    """
    files = glob.glob(os.path.join(folder_path, "*.txt"))
    grouped_files = defaultdict(list)
    
    # Nhóm file theo group và sắp xếp theo số thứ tự
    for file in files:
        filename = os.path.basename(file)
        parts = filename.rsplit("_", 1)
        if len(parts) == 2 and parts[1].endswith(".txt"):
            group, number = parts[0], parts[1][:-4]  # Loại bỏ đuôi .txt
            if number.isdigit():
                grouped_files[group].append((int(number), file))
    
    # Đọc và ghép nội dung từng nhóm
    merged_texts = []
    for group in sorted(grouped_files.keys()):
        grouped_files[group].sort()  # Sắp xếp theo số thứ tự
        merged_content = "\n".join(open(file, encoding="utf-8").read() for _, file in grouped_files[group])
        merged_texts.append(merged_content)
    
    return merged_texts
def describe_image(description, detail_level="short", perspective="neutral", emotion=None, time_setting=None, art_style=None):
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
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return ""
def generate_image(prompt, output_path, model="stabilityai/stable-diffusion-3.5-large", style=None, color_palette=None):
    """
    Tạo hình ảnh từ mô tả văn bản với các tùy chỉnh linh hoạt.
    
    :param prompt: Mô tả hình ảnh đầu vào.
    :param output_path: Đường dẫn lưu ảnh đầu ra.
    :param model: Mô hình AI sử dụng để tạo ảnh.
    :param style: Phong cách hình ảnh (nếu có, ví dụ: 'realistic', 'anime', 'cyberpunk').
    :param color_palette: Bảng màu ưu tiên (nếu có, ví dụ: 'vibrant', 'monochrome').
    """
    
    custom_prompt = prompt
    
    if style:
        custom_prompt += f" in {style} style"
    if color_palette:
        custom_prompt += f" with {color_palette} color scheme"
    
    image = client.text_to_image(custom_prompt, model=model)
    image.save(output_path)
def image_gen(detail_level="short", perspective="neutral", emotion=None, time_setting=None, art_style=None, resolution=(512, 512), style=None, color_palette=None):
    text_folder = "./data/text"
    merged_texts = merge_grouped_texts(text_folder)
    index = 0
    for merged_text in tqdm(merged_texts, desc="Processing", unit="image"):
        output_path = f"./data/image/{index}.png"
        prompt = describe_image(merged_text, detail_level=detail_level, perspective=perspective, emotion=emotion, time_setting=time_setting, art_style=art_style)
        print(prompt)
        print(f"Image saved at {output_path}")
        # Cơ chế retry với backoff
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            try:
                generate_image(prompt, output_path, style=style, color_palette=color_palette)
                time.sleep(60)  # Chờ sau khi tạo ảnh thành công
                break  # Nếu thành công thì thoát khỏi vòng lặp retry
            except HfHubHTTPError as e:
                print(f"Lỗi khi gọi API: {e}")
                retry_count += 1
                wait_time = 2 ** retry_count + random.uniform(0, 1)  # Exponential backoff
                print(f"Thử lại sau {wait_time:.2f} giây...")
                time.sleep(wait_time)

        index += 1
if __name__ == "__main__":
    image_gen(detail_level="short", perspective="neutral", emotion="sad", time_setting="classic", art_style="realistic", style="anime", color_palette="monochrome")