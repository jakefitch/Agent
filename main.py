from core.playwright_handler import get_handler, close_handler
from core.stats_analyzer import get_analyzer
from dotenv import load_dotenv
import os
#HI JAKE!!!!!!!
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



initialize_session()
    
    
    