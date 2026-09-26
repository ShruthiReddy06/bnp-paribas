import os
from pypdf import PdfReader
import docx

class UnsupportedFileError(Exception):
    """Raised when the file format is not supported."""
    pass

class EmptyDocumentError(Exception):
    """Raised when the document is empty or text extraction yields no result."""
    pass

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")
    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to read DOCX: {e}")
    return text.strip()

def extract_text_from_doc(file_path: str) -> str:
    # Legacy .doc file support is limited on Windows without system-level COM tools (like MS Word)
    # or third-party binaries (like antiword). We provide a clean rejection here.
    raise UnsupportedFileError(
        "Legacy .doc files require system-level dependencies (like Antiword or MS Word COM) "
        "which are not reliably available in this environment. Please convert the file to .docx or .pdf."
    )

def parse_document(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    elif ext == ".doc":
        text = extract_text_from_doc(file_path)
    else:
        raise UnsupportedFileError(f"Unsupported file extension: {ext}. Only .pdf and .docx are supported.")
        
    if not text:
        raise EmptyDocumentError("The document is empty or unreadable.")
        
    return text