import requests
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader
import os
import json
from datetime import datetime

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
    """Thin client for interacting with the local Ollama instance.

    The default timeout has been extended to two minutes to give the model
    additional time to respond.  The default model is also reduced to the 8B
    variant which is significantly faster than the previous 70B default.
    """

    def __init__(
        self,
        base_url: str = "http://100.120.49.120:11434",
        timeout: float = 120.0,
        default_model: str = "llama3:8b",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_model = default_model
        
        # Initialize PDF tools
        self.pdf_tools = {
            "fast": PyMuPDFTool(),
            "ocr": TesseractTool(),
        }

    def get_models(self) -> Optional[list[str]]:
        try:
            # Allow a short connect timeout but a longer read timeout so the model
            # has time to stream a response.
            response = requests.get(
                f"{self.base_url}/api/tags", timeout=(10, self.timeout)
            )
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
            if test_response and ("OK" in test_response or len(test_response.strip()) > 0):
                print(f"[✅] Model connection test successful")
                return True
            else:
                print(f"[❌] Model connection test failed - no response received")
                return False
        except Exception as e:
            print(f"[❌] Model connection test failed: {e}")
            return False

    def generate(self, prompt: str, model: Optional[str] = None, stream: bool = False) -> Optional[str]:
        try:
            # Use default model if none specified
            model_to_use = model or self.default_model
            payload = {"model": model_to_use, "prompt": prompt, "stream": stream}
            # Extend read timeout to give the LLM ample time to respond.
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=(10, self.timeout),
            )
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

    def analyze_playwright_selector(self, default_selector: str, html_snippet: str, ranking_model: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze HTML snippet to find Playwright selectors using multiple models.
        
        Args:
            default_selector: The default selector that was already set
            html_snippet: HTML code snippet containing the target element
            ranking_model: Model to use for ranking (defaults to self.default_model)
            
        Returns:
            Dict containing analysis results, rankings, and logs
        """
        try:
            print(f"[🔍] Starting Playwright selector analysis...")
            
            # Get all available models
            models = self.get_models()
            if not models:
                print("[❌] No models available for analysis")
                return {"error": "No models available"}
            
            print(f"[📋] Found {len(models)} models to test")
            
            # Create log directory if it doesn't exist
            log_dir = os.path.join(os.path.dirname(__file__), "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            # Create timestamp for this analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"selector_analysis_{timestamp}.json")
            
            # Prepare the analysis prompt
            analysis_prompt = f"""
You are an expert at creating Playwright selectors. Given this HTML snippet and a default selector, 
create the best possible Playwright selector for the target element.

HTML Snippet:
{html_snippet}

Default Selector: {default_selector}

Please create a Playwright selector that:
1. Is specific enough to target only the intended element
2. Is robust and won't break with minor HTML changes
3. Uses the most reliable selector strategy (data-test-id > id > aria-label > text content > CSS selectors)
4. Is human-readable and maintainable

Return ONLY the selector string, nothing else.
Do not include any other text or comments in your response
"""
            
            # Test each model and collect results
            model_results = {}
            successful_models = []
            
            for model in models:
                try:
                    print(f"[🧪] Testing model: {model}")
                    
                    # Generate selector with this model
                    selector = self.generate(analysis_prompt, model=model)
                    
                    if selector:
                        # Clean up the response (remove extra whitespace, quotes, etc.)
                        selector = selector.strip().strip('"').strip("'")
                        
                        model_results[model] = {
                            "selector": selector,
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        }
                        successful_models.append(model)
                        print(f"[✅] {model}: {selector}")
                    else:
                        model_results[model] = {
                            "selector": None,
                            "status": "failed",
                            "error": "No response generated",
                            "timestamp": datetime.now().isoformat()
                        }
                        print(f"[❌] {model}: No response")
                        
                except Exception as e:
                    model_results[model] = {
                        "selector": None,
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    print(f"[❌] {model}: Error - {str(e)}")
            
            # Create ranking prompt
            ranking_model_to_use = ranking_model or self.default_model
            ranking_prompt = f"""
You are an expert at evaluating Playwright selectors. Given these selectors for the same HTML element,
rank them from most likely to succeed (1) to least likely to succeed ({len(successful_models)}).

HTML Snippet:
{html_snippet}

Default Selector: {default_selector}

Generated Selectors:
"""
            
            # Add each successful selector to the ranking prompt
            for i, model in enumerate(successful_models, 1):
                selector = model_results[model]["selector"]
                ranking_prompt += f"{i}. {model}: {selector}\n"
            
            ranking_prompt += f"""
Please rank these selectors from 1 (best) to {len(successful_models)} (worst) based on:
1. Specificity and accuracy
2. Robustness against HTML changes
3. Readability and maintainability
4. Likelihood of success in Playwright

Return ONLY a JSON array with the ranking, like: [3, 1, 2, 4] where the numbers correspond to the selector numbers above.
"""
            
            # Get ranking from the ranking model
            ranking_response = self.generate(ranking_prompt, model=ranking_model_to_use)
            ranking = None
            
            if ranking_response:
                try:
                    # Try to parse the ranking response
                    ranking_text = ranking_response.strip()
                    if ranking_text.startswith('[') and ranking_text.endswith(']'):
                        ranking = json.loads(ranking_text)
                    else:
                        # Try to extract numbers from the response
                        import re
                        numbers = re.findall(r'\d+', ranking_text)
                        if numbers:
                            ranking = [int(n) for n in numbers[:len(successful_models)]]
                except Exception as e:
                    print(f"[⚠️] Could not parse ranking response: {e}")
                    ranking = list(range(1, len(successful_models) + 1))  # Default order
            
            # Create final results structure
            results = {
                "timestamp": timestamp,
                "html_snippet": html_snippet,
                "default_selector": default_selector,
                "models_tested": len(models),
                "successful_models": len(successful_models),
                "model_results": model_results,
                "ranking_model": ranking_model_to_use,
                "ranking": ranking,
                "ranked_selectors": []
            }
            
            # Create ranked selectors list
            if ranking and successful_models:
                for rank, selector_index in enumerate(ranking, 1):
                    if 1 <= selector_index <= len(successful_models):
                        model_name = successful_models[selector_index - 1]
                        results["ranked_selectors"].append({
                            "rank": rank,
                            "model": model_name,
                            "selector": model_results[model_name]["selector"]
                        })
            
            # Save results to log file
            with open(log_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"[📝] Analysis results saved to: {log_file}")
            print(f"[🏆] Top selector: {results['ranked_selectors'][0]['selector'] if results['ranked_selectors'] else 'None'}")
            
            return results
            
        except Exception as e:
            print(f"[❌] Playwright selector analysis failed: {e}")
            return {"error": str(e)}

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