import fitz  # PyMuPDF
import os
from docx import Document
import google.generativeai as genai
import re

def extract_text_from_pdf(pdf_path):
    """Trích xuất văn bản từ file PDF"""
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(doc.page_count):
        text += doc.load_page(page_num).get_text()
    return text

def extract_text_from_docx(docx_path):
    """Trích xuất văn bản từ file DOCX"""
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_file(file_path):
    """Kiểm tra loại file và gọi hàm trích xuất tương ứng"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")

def filter_sensitive_with_gemini(text):
    """Lọc nội dung nhạy cảm bằng Gemini"""
    prompt = f"""
    Bạn là chuyên gia xử lý văn bản. Hãy phân tích văn bản sau và thay thế các từ nhạy cảm bằng dấu sao (*).

    Văn bản:
    {text}

    Đầu ra:
    - Văn bản đã được lọc với các từ nhạy cảm thay thế bằng dấu (*).
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return text

def split_text_by_length(text, max_length=300):
    """Chia văn bản thành các đoạn theo độ dài tối đa"""
    sentences = re.split(r'(?<=\.)\s+', text)
    chunks, current_chunk = [], ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def split_text_by_semantics(text):
    """Chia văn bản thành các đoạn có ý nghĩa bằng Gemini"""
    prompt = f"""
    Bạn là chuyên gia xử lý văn bản. Hãy chia văn bản sau thành các đoạn có ý nghĩa, mỗi đoạn khoảng 150-300 từ.

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
        return [chunk.strip() for chunk in response.text.strip().split("- Phần ") if chunk]
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return []

def generate_explanation_for_chunks(chunks):
    """Tạo lời giải thích cho từng phần văn bản"""
    overview_prompt = f"""
    Đây là một văn bản quan trọng. Bạn sẽ phân tích và giải thích từng phần:
    {', '.join([f"Phần {i+1}" for i in range(len(chunks))])}.

    Hãy mô tả tổng quan trước khi giải thích chi tiết từng phần.
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        overview_text = model.generate_content(overview_prompt).text.strip()

        explanations = []
        for idx, chunk in enumerate(chunks, start=1):
            part_prompt = f"""
            Hãy phân tích và giải thích phần {idx} sau:

            {chunk}
            """
            explanations.append(model.generate_content(part_prompt).text.strip())

        return [overview_text] + explanations
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return []

if __name__ == "__main__":
    file_path = '../data/sample.pdf'  # Thay đổi theo file cần xử lý
    extracted_text = extract_text_from_file(file_path)

    # Lọc nội dung nhạy cảm
    filtered_text = filter_sensitive_with_gemini(extracted_text)

    # Tách văn bản theo độ dài
    chunks_by_length = split_text_by_length(filtered_text)

    # Tách văn bản theo ngữ nghĩa
    semantic_chunks = split_text_by_semantics(filtered_text)

    # Tạo lời giải thích cho từng phần
    explanations = generate_explanation_for_chunks(semantic_chunks)

    # In kết quả
    for idx, explanation in enumerate(explanations, start=0):
        section = "Tổng quan" if idx == 0 else f"Giải thích cho Phần {idx}"
        print(f"{section}:\n{explanation}\n")