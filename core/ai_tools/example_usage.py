#!/usr/bin/env python3
"""
Example usage of the Playwright selector analysis function.
"""

from ollama import OllamaClient

def example_selector_analysis():
    """
    Example of how to use the analyze_playwright_selector function.
    """
    
    # Initialize the Ollama client
    client = OllamaClient()
    
    # Example 1: Patient tab selector
    html_snippet_1 = """
    <div class="tab-container">
        <span id="tabHeaderTextWrapper" data-test-id="patients.navigationTab" tab-id="c1d41e2e-fd71-4c5a-9668-3b016604ba27">
            Patients
        </span>
        <span id="tabHeaderTextWrapper" data-test-id="fitch,j.navigationTab" tab-id="7642f49e-c132-4a91-b6d4-e04ff08bfeca">
            Fitch, J
        </span>
    </div>
    """
    default_selector_1 = '[data-test-id$=".navigationTab"]'
    
    print("🔍 Example 1: Patient Tab Selector Analysis")
    print("=" * 50)
    results_1 = client.analyze_playwright_selector(default_selector_1, html_snippet_1)
    
    if "error" not in results_1:
        print(f"Top selector: {results_1['ranked_selectors'][0]['selector'] if results_1['ranked_selectors'] else 'None'}")
    
    print("\n" + "=" * 50)
    
    # Example 2: Button selector
    html_snippet_2 = """
    <div class="search-container">
        <button class="btn btn-primary" data-test-id="advancedSearchSearchButton" type="submit">
            <i class="fa fa-search"></i>
            Search
        </button>
        <button class="btn btn-secondary" data-test-id="resetButton">
            Reset
        </button>
    </div>
    """
    default_selector_2 = '[data-test-id="advancedSearchSearchButton"]'
    
    print("🔍 Example 2: Button Selector Analysis")
    print("=" * 50)
    results_2 = client.analyze_playwright_selector(default_selector_2, html_snippet_2)
    
    if "error" not in results_2:
        print(f"Top selector: {results_2['ranked_selectors'][0]['selector'] if results_2['ranked_selectors'] else 'None'}")

def analyze_specific_element(html_snippet: str, default_selector: str, ranking_model: str = None):
    """
    Analyze a specific HTML element for better Playwright selectors.
    
    Args:
        html_snippet: HTML code containing the target element
        default_selector: Current selector being used
        ranking_model: Optional specific model for ranking
    """
    client = OllamaClient()
    
    print(f"🔍 Analyzing selector: {default_selector}")
    print(f"📄 HTML snippet length: {len(html_snippet)} characters")
    
    results = client.analyze_playwright_selector(default_selector, html_snippet, ranking_model)
    
    if "error" in results:
        print(f"❌ Analysis failed: {results['error']}")
        return None
    
    print(f"\n📊 Results Summary:")
    print(f"   Models tested: {results['models_tested']}")
    print(f"   Successful: {results['successful_models']}")
    print(f"   Ranking model: {results['ranking_model']}")
    
    print(f"\n🏆 Top 3 Selectors:")
    for i, ranked in enumerate(results['ranked_selectors'][:3], 1):
        print(f"   {i}. {ranked['model']}: {ranked['selector']}")
    
    return results

if __name__ == "__main__":
    # Run the examples
    example_selector_analysis()
    
    # You can also analyze specific elements like this:
    # html = "<your HTML snippet here>"
    # selector = "your current selector"
    # results = analyze_specific_element(html, selector) 