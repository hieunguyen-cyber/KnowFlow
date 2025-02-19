import os
import fitz  # PyMuPDF
from docx import Document
import random
import time
import pysrt
import torch
import torchaudio
import numpy as np
import glob
from collections import defaultdict
from tqdm import tqdm
import google.generativeai as genai
from moviepy.video.io.VideoFileClip import VideoFileClip, AudioFileClip
from moviepy.video.VideoClip import TextClip, ImageClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips, CompositeVideoClip
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import ColorClip
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from itertools import accumulate
from transformers import VitsModel, AutoTokenizer
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

# Lấy API keys từ file .env
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Sử dụng API key mà không hardcode
genai.configure(api_key=GOOGLE_API_KEY)
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)

def extract_text_from_pdf(pdf_path):
    # Mở file PDF
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

def extract_text_from_docx(docx_path):
    # Mở file DOCX
    doc = Document(docx_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_text_from_file(file_path):
    # Kiểm tra loại file và gọi hàm tương ứng
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")
def split_text_by_semantics(text):
    prompt = f"""
    Bạn là một chuyên gia xử lý văn bản. Hãy chia văn bản sau thành các đoạn có ý nghĩa sao cho mỗi đoạn vừa đủ để giải thích trong khoảng 3 đến 5 câu.

    Văn bản:
    {text}

    Định dạng đầu ra:
    - Phần 1: [Nội dung]
    - Phần 2: [Nội dung]
    - Phần 3: [Nội dung]
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        chunks = result_text.split("- Phần ")
        chunks = [chunk.strip() for chunk in chunks if chunk]
        return chunks
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return []

def generate_explaination_for_chunks(chunks):
    # Tạo một mô tả ngữ nghĩa tổng quan về văn bản
    overview_prompt = f"""
    Đây là một văn bản có nội dung liên quan đến các chủ đề quan trọng. Bạn sẽ được yêu cầu phân tích và thuyết minh cho từng phần của văn bản sau.
    Văn bản gồm các phần sau:
    {', '.join([f"Phần {i+1}" for i in range(len(chunks))])}.
    
    Xin vui lòng mô tả và giải thích nội dung từng phần theo ngữ nghĩa của nó. Mỗi phần hãy phân tích khoảng 5 câu.
    """

    try:
        # Gọi Gemini để tạo mô tả tổng quan
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(overview_prompt, safety_settings={
                                                                            'HATE': 'BLOCK_NONE',
                                                                            'HARASSMENT': 'BLOCK_NONE',
                                                                            'SEXUAL' : 'BLOCK_NONE',
                                                                            'DANGEROUS' : 'BLOCK_NONE'
                                                                            })
        overview_text = response.text.strip()

        explainations = []
        for idx, chunk in enumerate(chunks, start=1):
            part_prompt = f"""
                            Bạn là một nhà phân tích văn bản tài ba. Dựa trên phần {idx} của một chủ đề lớn, hãy phân tích và giải thích ý nghĩa sâu sắc của đoạn văn sau:  
                            {chunk}

                            Hãy trình bày phân tích một cách rõ ràng, chi tiết và mạch lạc. Đảm bảo rằng:  
                            - Bạn làm rõ những ý tưởng chính và thông điệp quan trọng trong đoạn văn.  
                            - Giải thích bối cảnh và những yếu tố quan trọng như nhân vật (nếu có), tình huống, hoặc các sự kiện xảy ra trong đoạn văn.  
                            - Các câu phải liền mạch, không xuống dòng, không liệt kê. (Quan trọng)
                            - Phân tích các yếu tố văn phong, cách sử dụng ngôn từ, và cách mà chúng góp phần vào việc truyền tải thông điệp của tác giả.  
                            - Làm rõ mối liên hệ giữa các phần trong đoạn văn, đảm bảo sự liên kết chặt chẽ giữa các ý tưởng.  
                            - Sử dụng các ví dụ trong văn bản để minh họa cho các phân tích của bạn một cách thuyết phục.
                            """

            part_response = model.generate_content(part_prompt)
            part_explaination = part_response.text.strip()
            explainations.append(part_explaination)

        return explainations

    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return []  
def generate_audio(line):
    #Tạo input cho mô hình
    model = VitsModel.from_pretrained("facebook/mms-tts-vie")
    tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-vie")
    inputs = tokenizer(line, return_tensors="pt")

    with torch.no_grad():
        # Sinh âm thanh từ mô hình
        output = model(**inputs).waveform

    # Đảm bảo output có dạng 2D [1, samples]
    output = output.unsqueeze(0) if output.ndimension() == 1 else output
    return model, output
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
    Bạn là chuyên gia mô tả hình ảnh. Hãy đọc đoạn mô tả dưới đây và rút gọn thành một câu cực ngắn, chỉ giữ lại các yếu tố quan trọng nhất.

    Đoạn mô tả:
    {description}

    Hãy trả về đúng một câu ngắn nhất bằng Tiếng Anh có thể nhưng vẫn đầy đủ ý chính.
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
def format_time(seconds):
    """Chuyển đổi thời gian (giây) thành định dạng SRT hh:mm:ss,ms"""
    mins, sec = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{int(hours):02}:{int(mins):02}:{int(sec):02},{int((sec % 1) * 1000):03}"
def get_audio_duration(audio_path):
    # Lọc các file có đuôi .wav
    audio_paths = os.listdir(audio_path)
    audio_list = [file for file in audio_paths if file.endswith(".wav")]
    
    # Khởi tạo danh sách audio duration
    duration_list = []
    
    for audio_path in audio_list:
        # Mở file âm thanh và lấy thời gian
        with AudioFileClip(f"./data/audio/{audio_path}") as audio:
            duration_list.append(audio.duration)
    # Tính tổng tích lũy thời gian
    duration_list = [format_time(time) for time in list(accumulate(duration_list))]
    return [format_time(0.0)] + duration_list
def create_srt_from_time_and_text(duration_time, text_folder, output_srt):
    subtitle = ""
    subtitle_index = 1
    text_list = sorted([file for file in os.listdir(text_folder) if file.endswith('txt')])
    # Duyệt qua các mốc thời gian và file text
    for i in range(len(duration_time) - 1):
        start_time = duration_time[i]
        end_time = duration_time[i + 1]
        
        # Lấy tên file text tương ứng
        text_file = text_list[i]  
        
        text_path = os.path.join(text_folder, text_file)
        
        if os.path.exists(text_path):
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                # Thêm phần subtitle vào chuỗi kết quả
                subtitle += f"{subtitle_index}\n{start_time} --> {end_time}\n{text}\n\n"
                subtitle_index += 1
        else:
            print(f"File {text_file} không tồn tại!")
    
    # Lưu vào file SRT
    with open(output_srt, 'w', encoding='utf-8') as f:
        f.write(subtitle)
def concatenate_audio_files(audio_folder, output_audio_path):
    # Lọc tất cả các file âm thanh .wav trong thư mục
    audio_clips = []
    
    for file in sorted(os.listdir(audio_folder)):
        if file.endswith('.wav'):
            audio_path = os.path.join(audio_folder, file)
            audio_clip = AudioFileClip(audio_path)
            audio_clips.append(audio_clip)
    
    # Ghép tất cả các audio clip lại với nhau
    final_audio = concatenate_audioclips(audio_clips)
    
    # Lưu kết quả vào file output
    final_audio.write_audiofile(output_audio_path, codec = 'pcm_s16le')

    print(f"File audio đã được lưu tại: {output_audio_path}")
def create_video_from_images(image_folder, audio_path, output_video_path):
    # Đọc file âm thanh để lấy thời lượng
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration  # Tổng thời lượng video bằng thời lượng audio

    # Đọc tất cả các file ảnh trong thư mục và sắp xếp theo tên
    image_files = [file for file in sorted(os.listdir(image_folder)) if file.endswith("png")]
    
    if not image_files:
        raise ValueError("Không tìm thấy ảnh nào trong thư mục!")

    # Tính thời lượng hiển thị cho mỗi ảnh
    duration_per_image = total_duration / len(image_files)

    # Tạo danh sách các clip ảnh
    clips = [ImageClip(f"./data/image/{img}").with_duration(duration_per_image).resized(width=1280) for img in image_files]

    # Ghép các clip ảnh lại với nhau
    final_video = concatenate_videoclips(clips, method="chain")
    
    # Gán âm thanh vào video
    final_video .audio = audio

    # Xuất video
    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="pcm_s16le", fps=24)

    print(f"Video đã được lưu tại: {output_video_path}")
def wrap_text(text, max_width):
    """
    Tự động xuống dòng để vừa với chiều rộng max_width.
    """
    import textwrap
    return "\n".join(textwrap.wrap(text, width=max_width))
def add_subtitles_to_video(video_path, subtitle_path, output_video_path):
    """
    Thêm phụ đề từ file .srt trực tiếp vào video.
    
    :param video_path: Đường dẫn video gốc
    :param subtitle_path: Đường dẫn file .srt
    :param output_video_path: Đường dẫn lưu video đầu ra
    """
    
    # Đọc file video
    video = VideoFileClip(video_path)

    # Đọc file .srt
    subs = pysrt.open(subtitle_path)

    subtitle_clips = []  # Danh sách các đoạn phụ đề

    # Xử lý từng dòng phụ đề
    for sub in subs:
        # Chuyển thời gian thành giây
        start_time = sub.start.ordinal / 1000  # Chuyển từ milliseconds sang giây
        end_time = sub.end.ordinal / 1000
        font = "./data/BeVietnamPro-Light.ttf"
        # Tạo clip phụ đề
        txt_clip = TextClip(font=font, text=wrap_text(sub.text, max_width=85), font_size=30, stroke_color="black", stroke_width=3, color="#fff")
         
        # Đặt vị trí hiển thị (giữa phía dưới video)
        txt_clip = txt_clip.with_position(('center', 'bottom')).with_duration(end_time - start_time).with_start(start_time)
        
        subtitle_clips.append(txt_clip)

    # Ghép phụ đề vào video
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # Xuất video với phụ đề
    final_video.write_videofile(output_video_path, fps=video.fps, codec='libx264', threads=4)

    print(f"Video với phụ đề đã được lưu tại: {output_video_path}")
def main(file_path):
    # Trích xuất văn bản từ file PDF
    text = extract_text_from_file(file_path)

    # Tách văn bản theo ngữ nghĩa
    semantic_chunks = split_text_by_semantics(text)

    # Tạo thuyết minh cho từng phần semantic chunk
    explainations = generate_explaination_for_chunks(semantic_chunks)

    # Lưu từng câu vào tệp riêng biệt
    for idx, explaination in enumerate(explainations, start=1):
        # Tách đoạn văn bản thành các câu dựa trên dấu chấm
        sentences = explaination.split('.')
        
        # Lưu từng câu vào tệp riêng biệt
        for sentence_idx, sentence in enumerate(sentences, start=1):
            sentence = sentence.strip()  # Loại bỏ khoảng trắng thừa
            if sentence:  # Kiểm tra nếu câu không rỗng
                output_file = f"./data/text/{idx}_{sentence_idx}.txt"  # Tên tệp theo định dạng x_y.txt
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"'{sentence}'")  # Ghi câu trong dấu nháy đơn
                print(f"Đã lưu: {output_file}")
    text_folder = "./data/text"
    text_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]  
    for text_file in text_files:
        with open(f"./data/text/{text_file}", "r", encoding="utf-8") as file:
            content = file.read()
        audio_file = text_file.replace("txt","wav")
        model, audio = generate_audio(content)
        torchaudio.save(f"./data/audio/{audio_file}", audio, model.config.sampling_rate)
        print(f"Đã lưu {audio_file}")
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
    duration_time = get_audio_duration("./data/audio")
    create_srt_from_time_and_text(duration_time, './data/text', './data/output/subtitle.srt')
    concatenate_audio_files("./data/audio","./data/output/final_audio.wav")
    create_video_from_images("./data/image","./data/output/final_audio.wav","./data/output/output.mp4")
    add_subtitles_to_video("./data/output/output.mp4", "./data/output/subtitle.srt", "./data/output/final_output.mp4")
if __name__ == "__main__":
    main("../data/sample.pdf")