from core.playwright_handler import get_handler, close_handler
from dotenv import load_dotenv
import os

# Initialize rev as None
rev = None

def initialize_session():
    """Initialize the Playwright session and return the handler"""
    global rev
    
    print("🔧 Initializing EMR Session")
    print("-------------------------")
    
    # Load environment variables from the specific .env file
    load_dotenv("/home/jake/Code/.env")
    
    # Get credentials from environment variables
    username = os.getenv("rev_username")
    password = os.getenv("rev_password")
    
    if not username or not password:
        print("❌ Error: Username or password not found in .env file")
        exit(1)
    
    rev = get_handler(headless=False)
    rev.goto("https://revolutionehr.com/static/")
    
    rev.login(
        username_selector='[data-test-id="loginUsername"]',
        password_selector='[data-test-id="loginPassword"]',
        username=username,
        password=password,
        login_button_selector='[data-test-id="loginBtn"]'
    )
    
    print("\n✅ Session started successfully!")
    return rev

def close_session():
    """Close the Playwright session and print statistics"""
    global rev
    if rev:
        print("\n👋 Closing session...")
        close_handler()
        rev = None

if __name__ == "__main__":
    try:
        # Initialize the session
        initialize_session()
        
        # Just test navigation to patient page
        print("Attempting to navigate to patient page...")
        rev.pages.patient_page.navigate_to_patient_page()
        print("Successfully navigated to patient page")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if hasattr(rev, 'take_screenshot'):
            rev.take_screenshot("error_screenshot")
    finally:
        # Always close the session
        close_session()
    
    
    
