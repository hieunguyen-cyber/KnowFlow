import os
import fitz  
from docx import Document
from google import genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

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
def split_text_by_semantics(text):
    prompt = f"""
    Bạn là một chuyên gia xử lý văn bản. Hãy chia văn bản sau thành một số đoạn có ý nghĩa sao cho mỗi đoạn vừa đủ để giải thích trong khoảng 3 đến 5 câu.

    Văn bản:
    {text}

    Định dạng đầu ra:
    - Phần 1: [Nội dung]
    - Phần 2: [Nội dung]
    - Phần 3: [Nội dung]
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        result_text = response.text.strip()
        print(result_text)

        chunks = result_text.split("- Phần ")
        chunks = [chunk.strip() for chunk in chunks if chunk]
        return chunks
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return []

####################### - CONTENT GENERATION - #######################
def generate_explaination_for_chunks(chunks, analysis_level='basic', writting_style='academic', word_lower_limit=100, word_upper_limit=150):
    """
    Phân tích nội dung của văn bản theo mức độ và phong cách mong muốn.
    
    :param chunks: Danh sách các đoạn văn bản cần phân tích.
    :param text: Toàn bộ văn bản gốc.
    :param analysis_level: Mức độ phân tích ('basic' hoặc 'detailed').
    :param writting_style: Phong cách phân tích ('academic', 'popular', 'creative', 'humorous').
    :param word_limit: Số từ ước lượng cho mỗi phần tóm tắt.
    :return: Danh sách các phân tích tương ứng với từng đoạn.
    """
    
    level_prompts = {
        'basic': "Hãy đưa ra một bản tóm tắt ngắn gọn, tập trung vào nội dung chính.",
        'detailed': "Hãy phân tích chuyên sâu từng phần, làm rõ ý nghĩa, ngữ cảnh và các yếu tố quan trọng."
    }
    
    writting_style_prompts = {
        'academic': "Phân tích theo phong cách học thuật, sử dụng ngôn ngữ chuyên sâu và lập luận chặt chẽ.",
        'popular': "Trình bày theo phong cách phổ thông, dễ hiểu và phù hợp với nhiều đối tượng.",
        'creative': "Giải thích một cách sáng tạo, sử dụng hình ảnh ẩn dụ và cách diễn đạt thú vị.",
        'humorous': "Phân tích theo phong cách hài hước, thêm vào yếu tố vui nhộn và bất ngờ."
    }
    
    overview_prompt = f"""
    Đây là một văn bản có nội dung quan trọng. Bạn sẽ phân tích từng phần theo mức độ '{analysis_level}' và phong cách '{writting_style}'.
    Văn bản gồm các phần sau: {', '.join([f'Phần {i+1}' for i in range(len(chunks))])}.
    {level_prompts[analysis_level]}
    {writting_style_prompts[writting_style]}
    Mỗi phần không vượt quá {word_upper_limit} từ và không ít hơn {word_lower_limit} từ.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=overview_prompt
        )
        print(response)
        
        explanations = []
        for idx, chunk in enumerate(chunks, start=1):
            part_prompt = f"""
            Phân tích phần {idx} của văn bản.
            {level_prompts[analysis_level]}
            {writting_style_prompts[writting_style]}
            Nội dung phần này:
            {chunk}
            Hãy đảm bảo phần tóm tắt không vượt quá {word_upper_limit} từ và không ít hơn {word_lower_limit}.
            """
            
            part_response = response = client.models.generate_content(
                    model="gemini-2.0-flash", contents=part_prompt
                )
            explanations.append(part_response.text.strip())
        
        return explanations
    
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return [] 
def text_processing(file_path, analysis_level='basic', writting_style='academic', word_lower_limit = 100, word_upper_limit = 150):
    # Trích xuất văn bản từ file PDF
    text = extract_text_from_file(file_path=file_path)
    with open("./text.txt", "w", encoding="utf-8") as f:
        f.write(text)  
    # Tách văn bản theo ngữ nghĩa
    semantic_chunks = split_text_by_semantics(text)

    # Tạo thuyết minh cho từng phần semantic chunk
    explanations = generate_explaination_for_chunks(semantic_chunks, analysis_level=analysis_level, writting_style = writting_style, word_lower_limit = word_lower_limit, word_upper_limit=word_upper_limit)

    # Tạo thư mục nếu chưa tồn tại
    output_dir = "./"
    os.makedirs(output_dir, exist_ok=True)

    # Lưu từng câu vào file riêng biệt
    for chunk_idx, explanation in enumerate(explanations, start=1):
        # Tách đoạn phân tích thành các câu
        sentences = explanation.split('.')

        for sentence_idx, sentence in enumerate(sentences, start=1):
            sentence = sentence.strip()  # Loại bỏ khoảng trắng thừa
            if sentence:  # Kiểm tra nếu câu không rỗng
                output_file = os.path.join(output_dir, f"{chunk_idx}_{sentence_idx}.txt")  # Tên file dạng "chunkID_sentenceID.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(sentence.replace("*","") + ".")  # Giữ dấu chấm cuối câu
                print(f"Đã lưu: {output_file}")