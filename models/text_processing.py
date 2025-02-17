import pdfplumber
from docx import Document
import os
from langdetect import detect  # For language detection
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.text_rank import TextRankSummarizer
from pyvi import ViTokenizer  # Tokenizer for Vietnamese
from sumy.nlp.tokenizers import Tokenizer  # Tokenizer for English

def extract_text_from_pdf(pdf_path):
    """Extract content from a PDF file."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text

def extract_text_from_docx(docx_path):
    """Extract content from a DOCX file."""
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_txt(txt_path):
    """Extract content from a TXT file."""
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text

def extract_text(file_path):
    """Determine the file format and extract text accordingly."""
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError("Unsupported file format")

def split_text_into_sections(text, max_length=500):
    """Split the text into sections based on sentence length."""
    sentences = text.split(".")
    sections = []
    current_section = ""
    for sentence in sentences:
        if len(current_section) + len(sentence) < max_length:
            current_section += sentence + "."
        else:
            sections.append(current_section.strip())
            current_section = sentence + "."
    if current_section:
        sections.append(current_section.strip())
    return sections

def detect_language(text):
    """Detect the language of the given text."""
    try:
        return detect(text)
    except:
        return "en"  # Default to English if detection fails

def summarize_text(text, num_sentences=2):
    """Summarize text using TextRank, with language-specific tokenization."""
    # Detect the language of the text
    language = detect_language(text)
    
    if language == "vi":  # If the language is Vietnamese
        # Tokenize using ViTokenizer for Vietnamese
        tokenized_text = ViTokenizer.tokenize(text)
        parser = PlaintextParser.from_string(tokenized_text, Tokenizer("english"))
    else:  # If the language is English
        # Use default English tokenizer from sumy
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
    
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join(str(sentence) for sentence in summary)

if __name__ == "__main__":
    test_file = "data/sample.pdf"  # Change the file path for testing
    content = extract_text(test_file)
    sections = split_text_into_sections(content)
    for i, section in enumerate(sections[:3]):
        summary = summarize_text(section)
        print(f"[Section {i+1}]: {summary}")  # Print summary for the first 3 sections