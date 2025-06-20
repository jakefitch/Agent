# pdf_tools.py

from abc import ABC, abstractmethod

# --- Abstract Base Tool ---

class AbstractPDFTool(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> dict:
        pass


# --- Tool 1: Fast Raw Text with PyMuPDF ---

class PyMuPDFTool(AbstractPDFTool):
    def parse(self, file_path):
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])
        return {"text": text}


# --- Tool 2: OCR Scan Reader with Tesseract ---

class TesseractTool(AbstractPDFTool):
    def parse(self, file_path):
        import fitz
        from PIL import Image
        import pytesseract

        doc = fitz.open(file_path)
        images = [
            Image.frombytes("RGB", page.get_pixmap().size, page.get_pixmap().samples)
            for page in doc
        ]
        ocr_text = "\n".join([pytesseract.image_to_string(img) for img in images])
        return {"text": ocr_text}


# --- Tool 3: LLM-Assisted Reasoner (Ollama, Local Model) ---

class OllamaLLMTool(AbstractPDFTool):
    def __init__(self, ollama_client):
        self.client = ollama_client

    def parse(self, file_path):
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        full_text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()

        if not full_text:
            return {"error": "No text extracted from PDF"}

        prompt = f"Extract structured benefits information from this VSP document:\n\n{full_text}"
        response = self.client.chat(prompt)
        return response


# --- Reader Wrapper ---

class PDFReader:
    def __init__(self, tool: AbstractPDFTool):
        self.tool = tool

    def parse(self, file_path):
        return self.tool.parse(file_path)
