import torch
from transformers import VitsModel, AutoTokenizer
import torchaudio
import numpy as np
import os

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

if __name__ == "__main__":
    text_folder = "./data/text"
    text_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]  
    for text_file in text_files:
        with open(f"./data/text/{text_file}", "r", encoding="utf-8") as file:
            content = file.read()
        audio_file = text_file.replace("txt","wav")
        model, audio = generate_audio(content)
        torchaudio.save(f"./data/audio/{audio_file}", audio, model.config.sampling_rate)
        print(f"Đã lưu {audio_file}")
