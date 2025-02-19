import os
import fitz  
from docx import Document
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

####################### - TEXT EXTRACTION - #######################
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
####################### - SEMANTIC CHUNKING - #######################
def split_text_by_semantics(text, number_of_chunks):
    prompt = f"""
    Bạn là một chuyên gia xử lý văn bản. Hãy chia văn bản sau thành {number_of_chunks} đoạn có ý nghĩa sao cho mỗi đoạn vừa đủ để giải thích trong khoảng 3 đến 5 câu.

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

####################### - CONTENT GENERATION - #######################
def generate_explaination_for_chunks(chunks, analysis_level='basic', style='academic', word_limit=100):
    """
    Phân tích nội dung của văn bản theo mức độ và phong cách mong muốn.
    
    :param chunks: Danh sách các đoạn văn bản cần phân tích.
    :param text: Toàn bộ văn bản gốc.
    :param analysis_level: Mức độ phân tích ('basic' hoặc 'detailed').
    :param style: Phong cách phân tích ('academic', 'popular', 'creative', 'humorous').
    :param word_limit: Số từ ước lượng cho mỗi phần tóm tắt.
    :return: Danh sách các phân tích tương ứng với từng đoạn.
    """
    
    level_prompts = {
        'basic': "Hãy đưa ra một bản tóm tắt ngắn gọn, tập trung vào nội dung chính.",
        'detailed': "Hãy phân tích chuyên sâu từng phần, làm rõ ý nghĩa, ngữ cảnh và các yếu tố quan trọng."
    }
    
    style_prompts = {
        'academic': "Phân tích theo phong cách học thuật, sử dụng ngôn ngữ chuyên sâu và lập luận chặt chẽ.",
        'popular': "Trình bày theo phong cách phổ thông, dễ hiểu và phù hợp với nhiều đối tượng.",
        'creative': "Giải thích một cách sáng tạo, sử dụng hình ảnh ẩn dụ và cách diễn đạt thú vị.",
        'humorous': "Phân tích theo phong cách hài hước, thêm vào yếu tố vui nhộn và bất ngờ."
    }
    
    overview_prompt = f"""
    Đây là một văn bản có nội dung quan trọng. Bạn sẽ phân tích từng phần theo mức độ '{analysis_level}' và phong cách '{style}'.
    Văn bản gồm các phần sau: {', '.join([f'Phần {i+1}' for i in range(len(chunks))])}.
    {level_prompts[analysis_level]}
    {style_prompts[style]}
    Mỗi phần không vượt quá {word_limit} từ.
    """
    
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(overview_prompt)
        overview_text = response.text.strip()
        
        explanations = []
        for idx, chunk in enumerate(chunks, start=1):
            part_prompt = f"""
            Phân tích phần {idx} của văn bản.
            {level_prompts[analysis_level]}
            {style_prompts[style]}
            Nội dung phần này:
            {chunk}
            Hãy đảm bảo phần tóm tắt không vượt quá {word_limit} từ.
            """
            
            part_response = model.generate_content(part_prompt)
            explanations.append(part_response.text.strip())
        
        return explanations
    
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return [] 
def text_processing(file_path, number_of_chunks = 3, analysis_level='basic', style='academic', word_limit=100):
    # Trích xuất văn bản từ file PDF
    text = extract_text_from_file(file_path = file_path)

    # Tách văn bản theo ngữ nghĩa
    semantic_chunks = split_text_by_semantics(text,number_of_chunks = number_of_chunks)

    # Tạo thuyết minh cho từng phần semantic chunk
    explainations = generate_explaination_for_chunks(semantic_chunks, analysis_level = analysis_level, style = style, word_limit = word_limit)

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
####################### - MAIN CODE - #######################
if __name__ == "__main__":
    text_processing(file_path = "./data/input/sample.pdf",number_of_chunks=3)