from core.playwright_handler import get_handler, close_handler
from dotenv import load_dotenv
from core.base import PatientManager
from datetime import datetime
import os
import json

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

    initialize_session()
    
    # Create a patient manager
    patient_manager = PatientManager()
    
    # Navigate to patient page first
    print("Attempting to navigate to patient page...")
    rev.pages.patient_page.navigate_to_patient_page()
    print("Successfully navigated to patient page")
    
    # Now create a new patient
    print("\nCreating new patient...")
    patient = patient_manager.create_patient(
        first_name="Jacob",
        last_name="Fitch",
        dob="11/24/1982"
    )
    print(f"Created patient: {patient.first_name} {patient.last_name}")
    
    # Print patient data
    patient.print_data()
    
    # Search for the patient
    print("\nSearching for patient...")
    rev.pages.patient_page.search_patient(patient)
    
    # Select the patient from results
    if rev.pages.patient_page.select_patient_from_results(patient):
        print("Successfully selected patient from results")
    else:
        print("No matching patient found in results")
    
    # Update the patient in the manager
    patient_manager.add_patient(patient) 
    print("Patient data updated in manager")
    #select VSP from insurance tab
    #rev.pages.patient_page.expand_insurance()
    #rev.pages.insurance_tab.select_insurance("VSP")
    import code
    code.interact(local=locals())

        

    
    
    
