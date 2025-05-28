#/patient_page.py

from core.playwright_handler import get_handler
import random
from core.base import BasePage, PatientContext, Patient
from .insurance_tab import InsuranceTab
from datetime import datetime
from typing import Optional
import time

def check_alert_modal(func):
    """Decorator to check for alert modal before executing any method."""
    def wrapper(self, *args, **kwargs):
        try:
            # Look for the modal close button with a short timeout
            close_button = self.handler.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
            if close_button.is_visible(timeout=3000):  # 3 second timeout
                close_button.click()
                self.handler.logger.log("Closed alert history modal")
        except Exception as e:
            # Log but don't raise - we don't want this to break the main flow
            self.handler.logger.log(f"Alert modal check completed: {str(e)}")
        
        # Execute the original method
        return func(self, *args, **kwargs)
    return wrapper

class PatientPage(BasePage):
    def __init__(self, handler, context: Optional[PatientContext] = None):
        super().__init__(handler, context)
        self.base_url = "https://revolutionehr.com/static/#/patients/search"
        self.insurance_tab = InsuranceTab(handler, context)
    
    def _validate_patient_required(self):
        # Patient is not required for initial navigation
        pass
    
    def is_loaded(self):
        """Check if the page is loaded"""
        try:
            # First check for advanced search button
            self.handler.logger.log("Checking for advanced search button...")
            advanced_search = self.handler.page.locator('[data-test-id="simpleSearchAdvancedSearch"]').is_visible(timeout=5000)
            if advanced_search:
                self.handler.logger.log("Found advanced search button - page is loaded")
                return True
            
            # If advanced search isn't visible, check for simple search form
            self.handler.logger.log("Advanced search not found, checking for simple search form...")
            simple_search = self.handler.page.locator('[data-test-id="simpleSearchForm"]').is_visible(timeout=5000)
            if simple_search:
                self.handler.logger.log("Found simple search form - page is loaded")
                return True
                
            self.handler.logger.log("Neither advanced search nor simple search form found")
            return False
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to check if patient page is loaded: {str(e)}")
            return False
    
    def navigate_to_patient_page(self):
        """Navigate to the patient search page."""
        try:
            self.handler.page.goto(self.base_url)
            self.handler.logger.log("Navigated to patient search page")
            
            # Add a small delay to ensure the page has time to load
            self.handler.page.wait_for_timeout(2000)  # 2 second delay
            
            # Wait for the page to be loaded
            if not self.is_loaded():
                raise Exception("Patient page failed to load after navigation")
                
        except Exception as e:
            self.handler.logger.log_error(f"Failed to navigate to patient page: {str(e)}")
            self.handler.take_screenshot("Failed to navigate to patient page")
            raise
    
    @check_alert_modal
    def click_patient_tab(self):
        """Click the open patient tab."""
        try:
            self.handler.page.locator('[data-test-id$=".navigationTab"]').click()
            self.handler.logger.log("Clicked patient tab")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click patient tab: {str(e)}")
            self.handler.take_screenshot("Failed to click patient tab")
            raise

    @check_alert_modal
    def close_patient_tab(self):
        """Click the close button (x) on the patient tab."""
        try:
            # Find the last navigation tab and get its close button
            self.handler.page.locator('[data-test-id$=".navigationTab"]').get_by_title('Close').click()
            self.handler.logger.log("Closed patient tab")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to close patient tab: {str(e)}")
            self.handler.take_screenshot("Failed to close patient tab")
            raise

    def click_advanced_search(self):
        """Click the advanced search link on the patient search page."""
        try:
            self.handler.page.locator('[data-test-id="simpleSearchAdvancedSearch"]').click()
            self.handler.logger.log("Clicked advanced search link")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click advanced search link: {str(e)}")
            self.handler.take_screenshot("Failed to click advanced search link")
            raise

    def search_patient(self, patient: Patient) -> Optional[Patient]:
        """Perform an advanced patient search using the provided Patient object.
        
        Args:
            patient (Patient): The Patient object containing the data to search for
            
        Returns:
            Optional[Patient]: Patient object if found, None otherwise
        """
        self.handler.logger.log("Starting advanced patient search")
        try:
            # Check if we're already in advanced search mode
            advanced_search_visible = self.handler.page.locator('[data-test-id="advancedSearchSearchButton"]').is_visible(timeout=1000)
            if not advanced_search_visible:
                self.click_advanced_search()
            
            # Fill in each field if available in the patient object
            if patient.last_name:
                self.handler.page.get_by_role('textbox', name='Last Name').fill(patient.last_name)
                
            if patient.first_name:
                self.handler.page.get_by_role('textbox', name='First Name').fill(patient.first_name)
                
            if patient.dob:
                self.handler.page.get_by_role('combobox', name='datepicker').fill(patient.dob)
                
            address = patient.get_demographic_data("address")
            if address:
                self.handler.page.get_by_role('textbox', name='Address').fill(address)
                
            phone = patient.get_demographic_data("phone")
            if phone:
                self.handler.page.locator('[data-test-id="advancedSearchPhoneFormGroup"]').get_by_role('textbox', name='maskedtextbox').fill(phone)
                
            email = patient.get_demographic_data("email")
            if email:
                self.handler.page.get_by_role('textbox', name='Email').fill(email)
                
            ssn = patient.get_demographic_data("ssn")
            if ssn:
                self.handler.page.locator('[data-test-id="advancedSearchSocialSecurityNumberFormGroup"]').get_by_role('textbox', name='maskedtextbox').fill(ssn)
                
            patient_id = patient.get_demographic_data("patient_id")
            if patient_id:
                self.handler.page.get_by_role('textbox', name='ID').fill(patient_id)
            
            # Click the search button
            self.handler.page.locator('[data-test-id="advancedSearchSearchButton"]').click()
            self.handler.logger.log("Advanced patient search completed")
            
            return patient
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to perform advanced patient search: {str(e)}")
            self.handler.take_screenshot("Failed to perform advanced patient search")
            raise

    def _check_alert_modal(self):
        """Check for and close the alert modal if it appears."""
        try:
            # Add a small wait to allow the modal to appear
            self.handler.page.wait_for_timeout(1000)  # 1 second wait
            
            close_button = self.handler.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
            if close_button.is_visible(timeout=3000):
                close_button.click()
                self.handler.logger.log("Closed alert history modal")
        except Exception as e:
            self.handler.logger.log(f"Alert modal check completed: {str(e)}")

   
    def select_patient_from_results(self, patient: Patient) -> bool:
        """Select a patient from the search results based on the provided Patient object.
        
        Args:
            patient (Patient): The Patient object containing the data to match
            
        Returns:
            bool: True if a matching patient was found and selected, False otherwise
        """
        # Add a small wait to allow the modal to appear
        self.handler.page.wait_for_timeout(1000)  # 1 second wait
        
        try:
            # Wait for the results table to be visible
            self.handler.page.wait_for_selector('.ag-center-cols-container', timeout=5000)
            
            # Get all rows in the table
            rows = self.handler.page.locator('.ag-center-cols-container .ag-row').all()
            
            if not rows:
                self.handler.logger.log("No search results found")
                return False
                
            self.handler.logger.log(f"Found {len(rows)} search results")
            
            # Find the best matching row
            best_match = None
            best_match_score = 0
            
            for row in rows:
                match_score = 0
                
                # Check each criterion if available in the patient object
                if patient.last_name:
                    name_cell = row.locator('[col-id="name"]').text_content()
                    if patient.last_name.lower() in name_cell.lower():
                        match_score += 1
                        
                if patient.first_name:
                    name_cell = row.locator('[col-id="name"]').text_content()
                    if patient.first_name.lower() in name_cell.lower():
                        match_score += 1
                        
                if patient.dob:
                    dob_cell = row.locator('[col-id="dateOfBirth"]').text_content()
                    if patient.dob in dob_cell:
                        match_score += 1
                        
                # Use get_demographic_data for optional fields
                address = patient.get_demographic_data("address")
                if address:
                    address_cell = row.locator('[col-id="addressResponse"]').text_content()
                    if address.lower() in address_cell.lower():
                        match_score += 1
                        
                phone = patient.get_demographic_data("phone")
                if phone:
                    phone_cell = row.locator('[col-id="preferredPhoneNumber"]').text_content()
                    if phone in phone_cell:
                        match_score += 1
                        
                patient_id = patient.get_demographic_data("patient_id")
                if patient_id:
                    id_cell = row.locator('[col-id="patientId"]').text_content()
                    if patient_id in id_cell:
                        match_score += 1
                
                # Update best match if this row has a higher score
                if match_score > best_match_score:
                    best_match = row
                    best_match_score = match_score
            
            # If we found a match, click it
            if best_match and best_match_score > 0:
                best_match.click()
                self.handler.logger.log(f"Selected patient with match score: {best_match_score}")
                self.handler.page.wait_for_timeout(2000)  # 2 second wait
                
                # Check for alert modal after clicking
                try:
                    close_button = self.handler.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
                    if close_button.is_visible(timeout=3000):  # 3 second timeout
                        close_button.click()
                        self.handler.logger.log("Closed alert history modal after patient selection")
                except Exception as e:
                    # Log but don't raise - we don't want this to break the main flow
                    self.handler.logger.log(f"Alert modal check after patient selection: {str(e)}")
                
                return True
            else:
                self.handler.logger.log("No matching patient found")
                return False
                
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select patient from results: {str(e)}")
            self.handler.take_screenshot("Failed to select patient from results")
            raise