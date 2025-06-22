# AI Tools Package

This package contains AI-related tools and utilities for the Agent system.

## Components

### OllamaClient
The main AI client for interacting with Ollama models, providing:
- Text generation
- PDF analysis and text extraction
- **NEW**: Playwright selector analysis

### Agent Instructions
Contains instruction files for AI agents.

## Playwright Selector Analysis

The `analyze_playwright_selector` function helps you find better Playwright selectors by:

1. **Multi-Model Analysis**: Tests every available Ollama model
2. **Intelligent Ranking**: Uses AI to rank selectors from best to worst
3. **Comprehensive Logging**: Saves detailed results to JSON logs
4. **Robust Selection**: Prioritizes data-test-id, id, aria-label, and other reliable selectors

### Usage

```python
from core.ai_tools import OllamaClient

# Initialize client
client = OllamaClient()

# Analyze a selector
html_snippet = """
<div class="container">
    <button data-test-id="submitButton" class="btn btn-primary">
        Submit
    </button>
</div>
"""
default_selector = '[data-test-id="submitButton"]'

# Run analysis
results = client.analyze_playwright_selector(default_selector, html_snippet)

# Get top selector
top_selector = results['ranked_selectors'][0]['selector']
print(f"Best selector: {top_selector}")
```

### Function Parameters

- `default_selector` (str): The current selector being used
- `html_snippet` (str): HTML code containing the target element
- `ranking_model` (str, optional): Specific model for ranking (defaults to default_model)

### Returns

A dictionary containing:
- `ranked_selectors`: List of selectors ranked from best to worst
- `model_results`: Detailed results from each model
- `ranking`: Numerical ranking of selectors
- `timestamp`: Analysis timestamp
- Log file path for detailed results

### Log Files

Analysis results are automatically saved to `core/ai_tools/logs/selector_analysis_YYYYMMDD_HHMMSS.json`

## Element Context Capture

The `save_element_context` function (in `core/base.py`) captures HTML context around failed selectors:

### Features

- **Element Detection**: Finds the target element or similar elements
- **Context Capture**: Saves parent, sibling, and element HTML
- **Screenshot**: Takes screenshots of the element area
- **Similar Elements**: Identifies elements with similar attributes
- **Error Handling**: Graceful handling when elements aren't found

### Usage

```python
from core.base import BasePage

# In your page class
def click_element(self):
    try:
        self.page.locator('[data-test-id="myButton"]').click()
    except Exception as e:
        # Capture context when selector fails
        context_data = self.save_element_context(
            '[data-test-id="myButton"]', 
            'button_selector_failure'
        )
        
        # Use context data for debugging or AI analysis
        if context_data.get('element_html'):
            print(f"Element HTML: {context_data['element_html']}")
        
        raise
```

### Returns

A dictionary containing:
- `element_html`: The target element's HTML
- `parent_context`: Parent elements' HTML
- `sibling_context`: Sibling elements' HTML
- `similar_elements`: List of similar elements found
- `element_info`: Element attributes and properties
- `screenshot_path`: Path to element screenshot

## Combined Debugging Workflow

Combine both functions for comprehensive selector debugging:

```python
from core.ai_tools import OllamaClient
from core.base import BasePage

def debug_failed_selector(page, failed_selector, context_name=None):
    """Debug a failed selector with context capture and AI analysis."""
    
    # 1. Capture element context
    base_page = BasePage(page, logger)
    context_data = base_page.save_element_context(failed_selector, context_name)
    
    # 2. Analyze with AI if we have HTML
    if context_data.get('element_html'):
        ai_client = OllamaClient()
        html_snippet = f"""
{context_data.get('parent_context', '')}
{context_data.get('element_html', '')}
{context_data.get('sibling_context', '')}
"""
        ai_results = ai_client.analyze_playwright_selector(failed_selector, html_snippet)
        
        # 3. Get AI suggestions
        if ai_results.get('ranked_selectors'):
            best_selector = ai_results['ranked_selectors'][0]['selector']
            print(f"AI suggests: {best_selector}")
    
    return context_data
```

## Examples

See `example_usage.py`, `test_selector_analysis.py`, and `example_element_context.py` for complete examples.

## Installation

Ensure all required packages are installed:
```bash
pip install -r requirements.txt
```

## Dependencies

- numpy>=1.25.0,<3.0.0
- Pillow>=9.0.0
- PyMuPDF>=1.26.0
- pytesseract>=0.3.10
- requests
- PyPDF2 