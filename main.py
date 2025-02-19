from src.text_processing import text_processing
from src.text_to_speech import text_to_speech
from src.image_gen import image_gen
from src.text_to_video import text_to_video

def main(file_path = "./data/input/sample.pdf",number_of_chunks=3, gender = "female", speed = "fast",detail_level="short", perspective="neutral", emotion="sad", time_setting="classic", art_style="realistic", style="anime", color_palette="monochrome"):
    text_processing(file_path = file_path, number_of_chunks=number_of_chunks)
    text_to_speech(gender = gender, speed = speed)
    image_gen(detail_level=detail_level, perspective=perspective, emotion=emotion, time_setting=time_setting, art_style=art_style, style=style, color_palette=color_palette)
    text_to_video()
if __name__ == "__main__":
    main()