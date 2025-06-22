#!/usr/bin/env python3
"""
Test script for the Playwright selector analysis function.
"""

from ollama import OllamaClient

def test_selector_analysis():
    """Test the selector analysis function with a sample HTML snippet."""
    
    # Initialize the client
    client = OllamaClient()
    
    # Sample HTML snippet (this would be the actual HTML from your page)
    html_snippet = """
    <div class="patient-container">
        <div class="header">
            <h2>Patient Information</h2>
        </div>
        <div class="content">
            <button data-test-id="patient.navigationTab" class="nav-tab">
                <span>John Doe</span>
                <span class="close-icon" title="Close">×</span>
            </button>
            <div class="patient-details">
                <p>Age: 35</p>
                <p>DOB: 1988-05-15</p>
            </div>
        </div>
    </div>
    """
    
    # Default selector that was already set
    default_selector = '[data-test-id="patient.navigationTab"]'
    
    print("🧪 Testing Playwright Selector Analysis...")
    print(f"HTML Snippet: {html_snippet.strip()}")
    print(f"Default Selector: {default_selector}")
    print("-" * 50)
    
    # Run the analysis
    results = client.analyze_playwright_selector(default_selector, html_snippet)
    
    # Display results
    if "error" in results:
        print(f"❌ Analysis failed: {results['error']}")
        return
    
    print(f"\n📊 Analysis Results:")
    print(f"Models tested: {results['models_tested']}")
    print(f"Successful models: {results['successful_models']}")
    print(f"Ranking model: {results['ranking_model']}")
    
    print(f"\n🏆 Ranked Selectors:")
    for ranked in results['ranked_selectors']:
        print(f"{ranked['rank']}. {ranked['model']}: {ranked['selector']}")
    
    print(f"\n📝 Full results saved to logs directory")

if __name__ == "__main__":
    test_selector_analysis() 