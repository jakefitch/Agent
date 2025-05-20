from core.playwright_handler import get_handler, close_handler
from core.stats_analyzer import get_analyzer
from dotenv import load_dotenv
import os

# Initialize handler as None
handler = None

def initialize_session():
    """Initialize the Playwright session and return the handler"""
    global handler
    
    print("🔧 Interactive Playwright Development Environment")
    print("----------------------------------------------")
    
    # Load environment variables from the specific .env file
    load_dotenv("/home/jake/Code/.env")
    
    # Get credentials from environment variables
    username = os.getenv("rev_username")
    password = os.getenv("rev_password")
    
    if not username or not password:
        print("❌ Error: Username or password not found in .env file")
        exit(1)
    
    handler = get_handler(headless=False)
    handler.goto("https://revolutionehr.com/static/")
    
    handler.login(
        username_selector='[data-test-id="loginUsername"]',
        password_selector='[data-test-id="loginPassword"]',
        username=username,
        password=password,
        login_button_selector='[data-test-id="loginBtn"]'
    )
    
    print("\n✅ Session started successfully!")
    print("Available commands:")
    print("  - handler.pages.invoice_page.navigate_to_invoices()")
    print("  - handler.pages.invoice_page.search_invoice(...)")
    print("  - handler.print_stats()")
    print("  - exit (to close the session)")
    
    return handler

def close_session():
    """Close the Playwright session and print statistics"""
    global handler
    if handler:
        print("\n📊 Printing final statistics...")
        handler.print_stats()
        print("\n📈 Analyzing long-term trends...")
        analyzer = get_analyzer()
        analyzer.print_analysis()
        print("\n👋 Closing session...")
        close_handler()
        handler = None

def check_for_document(self):
    """Check if any document exists in the Documents and Images tab.
    
    Returns:
        tuple: (exists (bool), document_info (dict))
    """
    try:
        print("Checking for documents in table")
        
        # Wait for the documents table to be present
        self.handler.wait_for_selector('[data-test-id="patientDocumentsComponentTable"]', timeout=10000)
        
        # Look for any document row in the table
        document_row = self.handler.page.locator('[data-test-id="patientDocumentsComponentTable"] div').filter(has_text='.').first
        
        # Check if any document row exists
        exists = document_row.is_visible(timeout=5000)
        
        document_info = {
            'exists': exists,
            'name': None,
            'date': None
        }
        
        if exists:
            # Get the text of the document row
            full_name = document_row.inner_text()
            document_info['name'] = full_name
            print(f"Found document: {full_name}")
            
            # Try to extract date if present
            try:
                # Assuming date is in the format MM/DD/YYYY
                date_parts = full_name.split()
                if len(date_parts) > 1:
                    date_str = date_parts[-1]
                    document_info['date'] = date_str
                    print(f"Extracted date: {date_str}")
            except Exception as e:
                print(f"Could not parse date from document name: {str(e)}")
        
        print(f"Document check result: {document_info}")
        return exists, document_info
        
    except Exception as e:
        self.handler.logger.log_error(f"Failed to check document: {str(e)}")
        self.handler.take_screenshot("Failed to check document")
        return False, {'exists': False, 'name': None, 'date': None}

initialize_session()
    
    
    