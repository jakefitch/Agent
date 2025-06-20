import requests
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader
import os

class AbstractPDFTool(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> dict:
        pass

class PyMuPDFTool(AbstractPDFTool):
    def parse(self, file_path):
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])
        return {"text": text}

class TesseractTool(AbstractPDFTool):
    def parse(self, file_path):
        doc = fitz.open(file_path)
        images = [
            Image.frombytes("RGB", page.get_pixmap().size, page.get_pixmap().samples)
            for page in doc
        ]
        ocr_text = "\n".join([pytesseract.image_to_string(img) for img in images])
        return {"text": ocr_text}

class OllamaClient:
    def __init__(self, base_url: str = "http://100.120.49.120:11434", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_model = "llama3:70b"
        
        # Initialize PDF tools
        self.pdf_tools = {
            "fast": PyMuPDFTool(),
            "ocr": TesseractTool(),
        }

    def get_models(self) -> Optional[list[str]]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            # Extract just the model names
            model_names = [model['name'] for model in data.get('models', [])]
            return model_names
        except requests.exceptions.RequestException as e:
            print(f"[❌] GET /api/tags failed: {e}")
            return None

    def test_model_connection(self, model: Optional[str] = None) -> bool:
        """Test if the model is responding with a simple prompt."""
        try:
            print(f"[🧪] Testing model connection...")
            test_response = self.generate("Respond with 'OK' if you can hear me.", model=model)
            if test_response and "OK" in test_response:
                print(f"[✅] Model connection test successful")
                return True
            else:
                print(f"[❌] Model connection test failed - unexpected response: {test_response}")
                return False
        except Exception as e:
            print(f"[❌] Model connection test failed: {e}")
            return False

    def generate(self, prompt: str, model: Optional[str] = None, stream: bool = False) -> Optional[str]:
        try:
            # Use default model if none specified
            model_to_use = model or self.default_model
            payload = {"model": model_to_use, "prompt": prompt, "stream": stream}
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("response")
        except requests.exceptions.RequestException as e:
            print(f"[❌] POST /api/generate failed: {e}")
            return None

    # PDF Processing Methods
    def extract_text_fast(self, file_path: str) -> Optional[str]:
        """Extract text from PDF using PyMuPDF (fast, text-based PDFs)."""
        try:
            result = self.pdf_tools["fast"].parse(file_path)
            return result.get("text")
        except Exception as e:
            print(f"[❌] Fast text extraction failed: {e}")
            return None

    def extract_text_ocr(self, file_path: str) -> Optional[str]:
        """Extract text from PDF using OCR (slower, image-based PDFs)."""
        try:
            result = self.pdf_tools["ocr"].parse(file_path)
            return result.get("text")
        except Exception as e:
            print(f"[❌] OCR text extraction failed: {e}")
            return None

    def extract_text_auto(self, file_path: str) -> Optional[str]:
        """Automatically choose the best extraction method."""
        # Try fast extraction first
        text = self.extract_text_fast(file_path)
        if text and len(text.strip()) > 50:  # If we got substantial text
            return text
        
        # Fall back to OCR if fast extraction didn't work well
        print("[ℹ️] Fast extraction yielded little text, trying OCR...")
        return self.extract_text_ocr(file_path)

    def analyze_pdf_with_llm(self, file_path: str, prompt: str = None, model: Optional[str] = None) -> Optional[str]:
        """Extract text from PDF and analyze it with the LLM."""
        try:
            # Extract text from PDF
            text = self.extract_text_auto(file_path)
            if not text:
                print("[❌] Could not extract text from PDF")
                return None

            # Create analysis prompt
            if not prompt:
                prompt = f"Analyze this document and provide a structured summary:\n\n{text[:2000]}..."  # Limit text length
            
            # Use LLM to analyze
            return self.generate(prompt, model=model)
            
        except Exception as e:
            print(f"[❌] PDF analysis failed: {e}")
            return None

    def extract_structured_data(self, file_path: str, data_type: str = "benefits", model: Optional[str] = None) -> Optional[str]:
        """Extract specific structured data from PDF (e.g., benefits, claims, etc.)."""
        try:
            text = self.extract_text_auto(file_path)
            if not text:
                return None

            # Create specific prompts for different data types
            prompts = {
                "benefits": f"Extract structured benefits information from this VSP document. Return as JSON:\n\n{text[:2000]}...",
                "claims": f"Extract claim details and amounts from this document. Return as JSON:\n\n{text[:2000]}...",
                "patient": f"Extract patient demographic information from this document. Return as JSON:\n\n{text[:2000]}...",
                "summary": f"Provide a concise summary of this document:\n\n{text[:2000]}..."
            }
            
            prompt = prompts.get(data_type, prompts["summary"])
            return self.generate(prompt, model=model)
            
        except Exception as e:
            print(f"[❌] Structured data extraction failed: {e}")
            return None

    def analyze_pdf(self, file_path: str, data_type: str = "comprehensive", model: Optional[str] = None) -> Optional[str]:
        """Master PDF analysis method using 'three eyes' approach.
        
        This method combines:
        1. Raw text extraction (fast + OCR fallback)
        2. Structured data extraction (specific data types)
        3. LLM analysis (general document understanding)
        
        Args:
            file_path: Path to the PDF file
            data_type: Type of structured data to extract ("benefits", "claims", "patient", "summary", "comprehensive")
            model: Optional model to use for LLM analysis
            
        Returns:
            str: Comprehensive analysis combining all three approaches
        """
        try:
            print(f"[🔍] Starting comprehensive PDF analysis: {file_path}")
            
            # Test model connection first
            if not self.test_model_connection(model):
                print("[❌] Model connection test failed, aborting PDF analysis")
                return None
            
            # Eye 1: Extract raw text
            print("[👁️ Eye 1] Extracting raw text...")
            raw_text = self.extract_text_auto(file_path)
            if not raw_text:
                print("[❌] Could not extract any text from PDF")
                return None
            
            # Eye 2: Extract structured data
            print(f"[👁️ Eye 2] Extracting structured {data_type} data...")
            structured_data = self.extract_structured_data(file_path, data_type, model)
            
            # Eye 3: General LLM analysis
            print("[👁️ Eye 3] Performing general LLM analysis...")
            llm_analysis = self.analyze_pdf_with_llm(file_path, model=model)
            
            # Combine all three analyses into a comprehensive prompt
            print("[🧠] Combining all analyses...")
            combined_prompt = f"""
# COMPREHENSIVE PDF ANALYSIS REPORT

## RAW TEXT EXTRACTION (Eye 1)
{raw_text[:1500]}...

## STRUCTURED DATA EXTRACTION (Eye 2) - {data_type.upper()}
{structured_data if structured_data else "No structured data extracted"}

## GENERAL LLM ANALYSIS (Eye 3)
{llm_analysis if llm_analysis else "No LLM analysis available"}

## FINAL COMPREHENSIVE ANALYSIS
Please provide a final comprehensive analysis that synthesizes all three perspectives above. 
Focus on:
1. Key findings and insights
2. Important data points and values
3. Any discrepancies or conflicts between the three analyses
4. Recommendations or next steps
5. Confidence level in the analysis

Format your response in a clear, structured manner.
"""
            
            # Get final comprehensive analysis
            final_analysis = self.generate(combined_prompt, model=model)
            
            print("[✅] Comprehensive analysis complete!")
            return final_analysis
            
        except Exception as e:
            print(f"[❌] Comprehensive PDF analysis failed: {e}")
            return None

# Convenience function for backward compatibility
def create_pdf_reader(tool_type: str = "fast"):
    """Create a PDF reader with the specified tool type."""
    client = OllamaClient()
    if tool_type == "fast":
        return client.pdf_tools["fast"]
    elif tool_type == "ocr":
        return client.pdf_tools["ocr"]
    else:
        raise ValueError(f"Unknown tool type: {tool_type}")

# Example usage
if __name__ == "__main__":
    ollama = OllamaClient()
    
    # Test basic functionality
    models = ollama.get_models()
    #sample_output = ollama.generate("Explain HIPAA in two sentences.")
    print("Models:", models)
    #print("Sample output:", sample_output)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, "document.pdf")

    
    # Check if the PDF file exists
    if os.path.exists(pdf_path):
        print(f"[✅] Found PDF file: {pdf_path}")
        benefits_analysis = ollama.analyze_pdf(pdf_path, data_type="benefits", model="qwen2.5vl:7b")
        print(benefits_analysis)
    else:
        print(f"[❌] PDF file not found at: {pdf_path}")
        print(f"[ℹ️] Current working directory: {os.getcwd()}")
        print(f"[ℹ️] Script directory: {script_dir}")
        print(f"[ℹ️] Please place document.pdf in the same folder as ollama.py")
    
    # Test PDF functionality (if you have a PDF file)
    # pdf_text = ollama.extract_text_auto("path/to/your/document.pdf")
    # analysis = ollama.analyze_pdf_with_llm("path/to/your/document.pdf")
    # benefits = ollama.extract_structured_data("path/to/your/document.pdf", "benefits")