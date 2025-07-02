#!/usr/bin/env python3
"""
Test script for the new VSP popup handling functionality.

This script demonstrates how the new popup handling methods work
and can be used to test the functionality independently.
"""

import os
import sys
from playwright.sync_api import sync_playwright
from core.logger import Logger
from config.vsp_map.claim_page import ClaimPage

def test_popup_handling():
    """Test the popup handling functionality."""
    
    # Setup logging
    logger = Logger("test_popup_handling")
    logger.log("Starting popup handling test...")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to True for headless mode
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Create claim page instance
            claim_page = ClaimPage(page, logger)
            
            # Navigate to a test page (you would replace this with actual VSP page)
            logger.log("Navigating to test page...")
            page.goto("https://example.com")  # Replace with actual VSP page URL
            
            # Test the popup handling methods
            logger.log("Testing popup handling methods...")
            
            # Test 1: expect_popup method
            logger.log("=== Testing expect_popup method ===")
            try:
                result = claim_page.handle_popup_with_expect_popup()
                logger.log(f"expect_popup result: {result}")
            except Exception as e:
                logger.log_error(f"expect_popup test failed: {str(e)}")
            
            # Test 2: original popup method
            logger.log("=== Testing original popup method ===")
            try:
                result = claim_page.handle_popup_window()
                logger.log(f"original popup result: {result}")
            except Exception as e:
                logger.log_error(f"original popup test failed: {str(e)}")
            
            logger.log("Popup handling tests completed")
            
        except Exception as e:
            logger.log_error(f"Test failed: {str(e)}")
        
        finally:
            # Cleanup
            browser.close()
            logger.log("Browser closed")

def test_pdf_extraction():
    """Test the PDF extraction functionality."""
    
    logger = Logger("test_pdf_extraction")
    logger.log("Starting PDF extraction test...")
    
    # Create a mock rpt_page object for testing
    class MockRptPage:
        def __init__(self):
            self.mock_embed_src = "data:application/pdf;base64,JVBERi0xLjQKJcOkw7zDtsO8DQoxIDAgb2JqDQo8PA0KL1R5cGUgL0NhdGFsb2cNCi9QYWdlcyAyIDAgUg0KPj4NCmVuZG9iag0KMiAwIG9iag0KPDwNCi9UeXBlIC9QYWdlcw0KL0NvdW50IDENCi9LaWRzIFsgMyAwIFIgXQ0KPj4NCmVuZG9iag0KMyAwIG9iag0KPDwNCi9UeXBlIC9QYWdlDQovUGFyZW50IDIgMCBSDQovUmVzb3VyY2VzIDw8DQovRm9udCA8PA0KL0YxIDQgMCBSDQo+Pg0KPj4NCi9Db250ZW50cyA1IDAgUg0KL01lZGlhQm94IFsgMCAwIDYxMiA3OTIgXQ0KPj4NCmVuZG9iag0KNCAwIG9iag0KPDwNCi9UeXBlIC9Gb250DQovU3VidHlwZSAvVHlwZTENCi9CYXNlRm9udCAvSGVsdmV0aWNhDQovRW5jb2RpbmcgL1dpbkFuc2lFbmNvZGluZw0KPj4NCmVuZG9iag0KNSAwIG9iag0KPDwNCi9MZW5ndGggNDQNCj4+DQpzdHJlYW0NCkJUCjcwIDUwIFRECi9GMSAxMiBUZgooSGVsbG8gV29ybGQpIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoNCnhyZWYNCjAgNg0KMDAwMDAwMDAwMCA2NTUzNSBmDQowMDAwMDAwMDAxIDAwMDAwIG4NCjAwMDAwMDAwMDcgMDAwMDAgbg0KMDAwMDAwMDAxNyAwMDAwMCBuDQowMDAwMDAwMDMwIDAwMDAwIG4NCjAwMDAwMDAwMzggMDAwMDAgbg0KdHJhaWxlcg0KPDwNCi9TaXplIDYNCi9Sb290IDEgMCBSDQo+Pg0Kc3RhcnR4cmVmDQo0OQ0KJSVFT0Y="
        
        def locator(self, selector):
            class MockLocator:
                def __init__(self, src):
                    self.src = src
                
                def count(self):
                    return 1
                
                def get_attribute(self, attr):
                    if attr == "src":
                        return self.src
                    return None
            
            if selector == "embed[type='application/pdf']":
                return MockLocator(self.mock_embed_src)
            return MockLocator("")
    
    # Create a mock claim page for testing
    class MockClaimPage:
        def __init__(self, logger):
            self.logger = logger
        
        def _extract_pdf_from_embed(self, rpt_page):
            """Test version of PDF extraction."""
            try:
                self.logger.log("Attempting to extract PDF from embed element...")
                
                # Look for embed element with PDF
                embed = rpt_page.locator("embed[type='application/pdf']")
                if embed.count() == 0:
                    self.logger.log("No PDF embed element found")
                    return False
                
                # Get the src attribute
                src = embed.get_attribute("src")
                if not src:
                    self.logger.log("No src attribute found on embed element")
                    return False
                
                self.logger.log("Found PDF embed src attribute")
                
                # Check if it's a base64 PDF
                prefix = 'data:application/pdf;base64,'
                if not src.startswith(prefix):
                    self.logger.log("Embed src is not a Base64 PDF")
                    return False
                
                # Decode base64 PDF
                import base64
                base64_data = src[len(prefix):]
                try:
                    pdf_bytes = base64.b64decode(base64_data)
                    
                    # Generate filename with timestamp
                    import time
                    timestamp = int(time.time())
                    filename = f"test_pdf_{timestamp}.pdf"
                    
                    with open(filename, 'wb') as f:
                        f.write(pdf_bytes)
                    self.logger.log(f"✅ Test PDF saved as {filename}")
                    
                    # Clean up test file
                    os.remove(filename)
                    self.logger.log(f"Test file {filename} cleaned up")
                    
                    return True
                    
                except Exception as e:
                    self.logger.log_error(f"Base64 decode or file write failed: {str(e)}")
                    return False
                    
            except Exception as e:
                self.logger.log_error(f"Failed to extract PDF from embed: {str(e)}")
                return False
    
    # Run the test
    mock_claim_page = MockClaimPage(logger)
    mock_rpt_page = MockRptPage()
    
    result = mock_claim_page._extract_pdf_from_embed(mock_rpt_page)
    logger.log(f"PDF extraction test result: {result}")
    
    logger.log("PDF extraction test completed")

if __name__ == "__main__":
    print("VSP Popup Handling Test")
    print("=======================")
    
    # Test PDF extraction (this doesn't require browser)
    print("\n1. Testing PDF extraction...")
    test_pdf_extraction()
    
    # Test popup handling (requires browser)
    print("\n2. Testing popup handling...")
    print("Note: This requires a browser and actual VSP page access")
    print("Uncomment the line below to run the browser test:")
    # test_popup_handling()
    
    print("\nTest completed!") 