import os
import fitz  # PyMuPDF
from docx import Document
import google.generativeai as genai

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

if __name__ == "__main__":
    genai.configure(api_key="AIzaSyBTBmiqMfF5KGFlZQULDtNP9n4GJgI0f6s")
    # Trích xuất văn bản từ file PDF
    text = extract_text_from_file("data/sample.pdf")

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