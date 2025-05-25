from core.playwright_handler import get_handler, close_handler
from core.stats_analyzer import get_analyzer
from core.base import Patient
from dotenv import load_dotenv
from datetime import datetime
import os
#HI 
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

# Example of how to use the Patient class during debugging
def example_patient_usage():
    # Create a patient
    patient = Patient(
        first_name="John",
        last_name="Doe",
        date_of_birth=datetime(1990, 1, 1)
    )
    
    # When you're at a breakpoint and have scraped some data:
    # Add insurance data
    patient.add_insurance_data("policy_number", "123456789")
    patient.add_insurance_data("insurance_company", "Blue Cross")
    
    # Add demographic data
    patient.add_demographic_data("address", "123 Main St")
    patient.add_demographic_data("phone", "555-0123")
    
    # Add medical data
    patient.add_medical_data("allergies", ["Penicillin", "Peanuts"])
    
    # Print all data to verify
    patient.print_data()
    
    # Access specific data
    policy_number = patient.get_insurance_data("policy_number")
    print(f"Policy Number: {policy_number}")

initialize_session()
    
    
    
