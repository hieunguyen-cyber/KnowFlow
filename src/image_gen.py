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
def describe_image(description):
    """
    Nhận một đoạn văn mô tả chi tiết và trả về một câu mô tả cực ngắn gọn, chỉ nêu các yếu tố chính của hình ảnh.

    Args:
        description (str): Đoạn văn mô tả chi tiết.

    Returns:
        str: Một câu tóm tắt rất ngắn về hình ảnh.
    """
    prompt = f"""
    Bạn là chuyên gia mô tả hình ảnh. Hãy đọc đoạn mô tả dưới đây và rút gọn thành một câu cực ngắn mô tả khung cảnh được đề cập.

    Đoạn mô tả:
    {description}

    Hãy trả về đúng một câu ngắn nhất có thể bằng Tiếng Anh nhưng vẫn đầy đủ ý chính.
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return ""
def generate_image(prompt, output_path):
    image = client.text_to_image(prompt,model="stabilityai/stable-diffusion-3.5-large")
    image.save(output_path)
if __name__ == "__main__":
    text_folder = "./data/text"
    merged_texts = merge_grouped_texts(text_folder)
    index = 0
    for merged_text in tqdm(merged_texts, desc="Processing", unit="image"):
        output_path = f"./data/image/{index}.png"
        prompt = describe_image(merged_text)
        print(prompt)

        # Cơ chế retry với backoff
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            try:
                generate_image(prompt, output_path)
                time.sleep(60)  # Chờ sau khi tạo ảnh thành công
                break  # Nếu thành công thì thoát khỏi vòng lặp retry
            except HfHubHTTPError as e:
                print(f"Lỗi khi gọi API: {e}")
                retry_count += 1
                wait_time = 2 ** retry_count + random.uniform(0, 1)  # Exponential backoff
                print(f"Thử lại sau {wait_time:.2f} giây...")
                time.sleep(wait_time)

        index += 1