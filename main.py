from src.text_processing import text_processing
from src.text_to_speech import text_to_speech
from src.image_gen import image_gen
from src.text_to_video import text_to_video
import os
def remove_cache(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):  # Kiểm tra nếu là file
            os.remove(file_path)
def main(file_path = "./data/input/sample.pdf", analysis_level='basic', writting_style='academic', word_lower_limit=100, word_upper_limit = 150, gender = "female", speed = "fast",detail_level="short", perspective="neutral", emotion="sad", time_setting="classic", art_style="realistic", style="anime", color_palette="monochrome"):
    remove_cache("./data/audio")
    remove_cache("./data/image")
    remove_cache("./data/text")
    text_processing(file_path = file_path, analysis_level=analysis_level, writting_style=writting_style, word_lower_limit = word_lower_limit, word_upper_limit=word_upper_limit )
    text_to_speech(gender = gender, speed = speed)
    image_gen(detail_level=detail_level, perspective=perspective, emotion=emotion, time_setting=time_setting, art_style=art_style, style=style, color_palette=color_palette)
    text_to_video()
    remove_cache("./data/audio")
    remove_cache("./data/image")
    remove_cache("./data/text")

if __name__ == "__main__":
    main(file_path="./data/input/sample_1.pdf")