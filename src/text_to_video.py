from moviepy.video.io.VideoFileClip import VideoFileClip, AudioFileClip
from moviepy.video.VideoClip import TextClip, ImageClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips, CompositeVideoClip
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import ColorClip
import os
from itertools import accumulate
import pysrt


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
        font = "./BeVietnamPro-Light.ttf"
        # Tạo clip phụ đề
        txt_clip = TextClip(font=font, text=wrap_text(sub.text, max_width=75), font_size=20, stroke_color="black", stroke_width=3, color="#fff")
         
        # Đặt vị trí hiển thị (giữa phía dưới video)
        txt_clip = txt_clip.with_position(('center', 'bottom')).with_duration(end_time - start_time).with_start(start_time)
        
        subtitle_clips.append(txt_clip)

    # Ghép phụ đề vào video
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # Xuất video với phụ đề
    final_video.write_videofile(output_video_path, fps=video.fps, codec='libx264', threads=4)

    print(f"Video với phụ đề đã được lưu tại: {output_video_path}")
if __name__ == "__main__":
    duration_time = get_audio_duration("./data/audio")
    create_srt_from_time_and_text(duration_time, './data/text', 'subtitle.srt')
    concatenate_audio_files("./data/audio","final_audio.wav")
    create_video_from_images("./data/image","final_audio.wav","output.mp4")
    add_subtitles_to_video("output.mp4", "subtitle.srt", "final_output.mp4")