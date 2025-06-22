#!/usr/bin/env python3
"""
Example of using save_element_context with AI selector analysis.
"""

from core.ai_tools import OllamaClient
from core.base import BasePage
from playwright.sync_api import Page

def debug_failed_selector(page: Page, failed_selector: str, context_name: str = None):
    """
    Debug a failed selector by capturing context and analyzing with AI.
    
    Args:
        page: Playwright page object
        failed_selector: The selector that failed
        context_name: Optional name for the context files
    """
    
    # Create a BasePage instance to use the save_element_context method
    from core.logger import Logger
    logger = Logger()
    base_page = BasePage(page, logger)
    
    print(f"🔍 Debugging failed selector: {failed_selector}")
    
    # Step 1: Save element context
    print("📸 Capturing element context...")
    context_data = base_page.save_element_context(failed_selector, context_name)
    
    if "error" in context_data:
        print(f"❌ Failed to capture context: {context_data['error']}")
        return None
    
    # Step 2: Analyze with AI if we have HTML context
    if context_data.get('element_html') or context_data.get('full_page_html'):
        print("🤖 Analyzing with AI...")
        
        # Initialize AI client
        ai_client = OllamaClient()
        
        # Prepare HTML snippet for analysis
        html_snippet = ""
        if context_data.get('element_html'):
            html_snippet = f"""
{context_data.get('parent_context', '')}
{context_data.get('element_html', '')}
{context_data.get('sibling_context', '')}
"""
        else:
            # Use full page HTML if element not found
            html_snippet = context_data.get('full_page_html', '')
        
        # Run AI analysis
        ai_results = ai_client.analyze_playwright_selector(failed_selector, html_snippet)
        
        if "error" not in ai_results:
            print("✅ AI analysis complete!")
            print(f"🏆 Top selector suggestion: {ai_results['ranked_selectors'][0]['selector'] if ai_results['ranked_selectors'] else 'None'}")
            
            # Add AI results to context data
            context_data['ai_analysis'] = ai_results
        else:
            print(f"❌ AI analysis failed: {ai_results['error']}")
    
    return context_data

def example_usage():
    """
    Example of how to use the debug function in a real scenario.
    """
    
    # This would be used in your actual page classes
    # For example, in patient_page.py when a selector fails:
    
    example_code = '''
    # In your page class method:
    def click_patient_tab(self):
        """Click the open patient tab."""
        try:
            self.page.locator('[data-test-id$=".navigationTab"]').click()
            self.logger.log("Clicked patient tab")
        except Exception as e:
            self.logger.log_error(f"Failed to click patient tab: {str(e)}")
            
            # Debug the failed selector
            context_data = debug_failed_selector(
                self.page, 
                '[data-test-id$=".navigationTab"]', 
                'patient_tab_selector_failure'
            )
            
            # You can now use the context_data for further analysis
            if context_data and 'ai_analysis' in context_data:
                best_selector = context_data['ai_analysis']['ranked_selectors'][0]['selector']
                self.logger.log(f"AI suggests trying: {best_selector}")
            
            raise
    '''
    
    print("📝 Example usage code:")
    print(example_code)

if __name__ == "__main__":
    example_usage() 