import torch
from transformers import VitsModel, AutoTokenizer
import torchaudio
import os
from gtts import gTTS

def generate_audio(text, filename="output.mp3", gender="female", speed="normal"):
    """
    Convert text to speech and save it as an audio file.
    
    Parameters:
        text (str): The text to convert.
        filename (str): The output file name.
        gender (str): "male" (use MMS-TTS) or "female" (use gTTS).
        speed (str): "slow", "normal", or "fast" (only for gTTS).
    """
    lang = "vi"
    
    if gender.lower() == "female":
        # gTTS chỉ có giọng nữ
        speed_mapping = {"slow": True, "normal": False, "fast": False}
        slow = speed_mapping.get(speed.lower(), False)
        
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save(filename)
        print(f"✅ Audio saved as {filename}")
    
    elif gender.lower() == "male":
        # MMS-TTS cho giọng nam
        model = VitsModel.from_pretrained("facebook/mms-tts-vie")
        tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-vie")
        
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = model(**inputs).waveform
        
        # Lưu file âm thanh
        torchaudio.save(filename, output, 24000, backend="sox_io")
        print(f"✅ Audio saved as {filename}")
    
    else:
        print("⚠️ Giọng không hợp lệ! Chỉ hỗ trợ 'male' hoặc 'female'.")
def text_to_speech(gender, speed):
    text_folder = "./"
    text_files = sorted([f for f in os.listdir(text_folder) if f.endswith('.txt') and f != "text.txt" and f != "requirements.txt"])
    for text_file in text_files:
        with open(f"{text_file}", "r", encoding="utf-8") as file:
            content = file.read()
        audio_file = text_file.replace("txt","mp3")
        generate_audio(content, f"{audio_file}", gender=gender, speed=speed) 
