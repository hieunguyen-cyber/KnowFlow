from src.text_processing import text_processing
from src.text_to_speech import text_to_speech
from src.image_gen import image_gen
from src.text_to_video import text_to_video
import os
import glob

def main(file_path, analysis_level='basic', writting_style='academic', word_lower_limit=100, word_upper_limit = 150, gender = "female", speed = "fast", number_of_images = 3, detail_level="short", perspective="neutral", emotion="sad", time_setting="classic", art_style="realistic", style="anime", color_palette="monochrome"):
    # Lấy danh sách tất cả các tệp .txt và .mp3 trong thư mục hiện tại
    files_to_delete = glob.glob("*.txt") + glob.glob("*.mp3") + glob.glob("*.png")

    # Xóa tất cả các tệp trừ "requirements.txt"
    for file in files_to_delete:
        if file != "requirements.txt":
            os.remove(file)
            print(f"Deleted: {file}")
    text_processing(file_path = file_path, analysis_level=analysis_level, writting_style=writting_style, word_lower_limit = word_lower_limit, word_upper_limit=word_upper_limit )
    text_to_speech(gender = gender, speed = speed)
    image_gen(number_of_images = number_of_images, detail_level=detail_level, perspective=perspective, emotion=emotion, time_setting=time_setting, art_style=art_style, style=style, color_palette=color_palette)
    text_to_video()