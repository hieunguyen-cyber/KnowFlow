# Load file PDF, DOCX, TXT
import pdfplumber
import docx
import pymupdf

def load_text_from_pdf(pdf_path):
    """Trích xuất văn bản từ file PDF."""
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text())
    return "\n".join(text).strip()

def load_text_from_docx(docx_path):
    """Trích xuất văn bản từ file DOCX."""
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def load_text_from_txt(txt_path):
    """Đọc văn bản từ file TXT."""
    with open(txt_path, "r", encoding="utf-8") as file:
        return file.read().strip()

def load_text(file_path):
    """Xác định định dạng file và load nội dung phù hợp."""
    if file_path.endswith(".pdf"):
        return load_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return load_text_from_docx(file_path)
    elif file_path.endswith(".txt"):
        return load_text_from_txt(file_path)
    else:
        raise ValueError("Định dạng file không được hỗ trợ!")

# Kiểm tra thử
if __name__ == "__main__":
    file_path = "../data/sample.pdf"
    print(load_text(file_path))