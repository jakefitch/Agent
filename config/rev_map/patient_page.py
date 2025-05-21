#/patient_page.py

from core.playwright_handler import get_handler
import random

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

class PatientPage:
    def __init__(self, handler):
        self.handler = handler
        self.base_url = "https://revolutionehr.com/static/#/patients/search"
    
   
    def is_loaded(self):
        """Check if the page is loaded"""
        try:
            # We'll need to add the appropriate selector for the patient page
            return self.handler.page.locator('[data-test-id="patientPageIdentifier"]').is_visible()
        except Exception as e:
            self.handler.logger.log_error(f"Failed to check if patient page is loaded: {str(e)}")
            return False
    
    def navigate_to_patient_page(self):
        """Navigate to the patient search page."""
        try:
            self.handler.page.goto(self.base_url)
            self.handler.logger.log("Navigated to patient search page")
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

    
    def search_patient(self, last_name=None, first_name=None, dob=None, address=None, 
                      phone=None, email=None, ssn=None, patient_id=None):
        """Perform an advanced patient search with all available fields.
        
        Args:
            last_name (str, optional): Patient's last name
            first_name (str, optional): Patient's first name
            dob (str, optional): Date of birth
            address (str, optional): Patient's address
            phone (str, optional): Patient's phone number
            email (str, optional): Patient's email
            ssn (str, optional): Patient's social security number
            patient_id (str, optional): Patient's ID
        """
        self.handler.logger.log("Starting advanced patient search")
        try:
            # Check if we're already in advanced search mode
            advanced_search_visible = self.handler.page.locator('[data-test-id="advancedSearchSearchButton"]').is_visible(timeout=1000)  # 1 second timeout
            if not advanced_search_visible:
                self.click_advanced_search()
            
            # Fill in each field if provided
            if last_name:
                self.handler.page.get_by_role('textbox', name='Last Name').fill(last_name)
                
            if first_name:
                self.handler.page.get_by_role('textbox', name='First Name').fill(first_name)
                
            if dob:
                self.handler.page.get_by_role('combobox', name='datepicker').fill(dob)
                
            if address:
                self.handler.page.get_by_role('textbox', name='Address').fill(address)
                
            if phone:
                self.handler.page.locator('[data-test-id="advancedSearchPhoneFormGroup"]').get_by_role('textbox', name='maskedtextbox').fill(phone)
                
            if email:
                self.handler.page.get_by_role('textbox', name='Email').fill(email)
                
            if ssn:
                self.handler.page.locator('[data-test-id="advancedSearchSocialSecurityNumberFormGroup"]').get_by_role('textbox', name='maskedtextbox').fill(ssn)
                
            if patient_id:
                self.handler.page.get_by_role('textbox', name='ID').fill(patient_id)
            
            # Click the search button
            self.handler.page.locator('[data-test-id="advancedSearchSearchButton"]').click()
            self.handler.logger.log("Advanced patient search completed")
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to perform advanced patient search: {str(e)}")
            self.handler.take_screenshot("Failed to perform advanced patient search")
            raise

    def _check_alert_modal(self):
        """Check for and close the alert modal if it appears."""
        try:
            close_button = self.handler.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
            if close_button.is_visible(timeout=3000):
                close_button.click()
                self.handler.logger.log("Closed alert history modal")
        except Exception as e:
            self.handler.logger.log(f"Alert modal check completed: {str(e)}")

   
    def select_patient_from_results(self, last_name=None, first_name=None, dob=None, address=None, 
                                  phone=None, patient_id=None):
        """Select a patient from the search results based on matching criteria.
        
        Args:
            last_name (str, optional): Patient's last name
            first_name (str, optional): Patient's first name
            dob (str, optional): Date of birth
            address (str, optional): Patient's address
            phone (str, optional): Patient's phone number
            patient_id (str, optional): Patient's ID
            
        Returns:
            bool: True if a matching patient was found and selected, False otherwise
        """
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
                
                # Check each criterion if provided
                if last_name:
                    name_cell = row.locator('[col-id="name"]').text_content()
                    if last_name.lower() in name_cell.lower():
                        match_score += 1
                        
                if first_name:
                    name_cell = row.locator('[col-id="name"]').text_content()
                    if first_name.lower() in name_cell.lower():
                        match_score += 1
                        
                if dob:
                    dob_cell = row.locator('[col-id="dateOfBirth"]').text_content()
                    if dob in dob_cell:
                        match_score += 1
                        
                if address:
                    address_cell = row.locator('[col-id="addressResponse"]').text_content()
                    if address.lower() in address_cell.lower():
                        match_score += 1
                        
                if phone:
                    phone_cell = row.locator('[col-id="preferredPhoneNumber"]').text_content()
                    if phone in phone_cell:
                        match_score += 1
                        
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

                
                self._check_alert_modal()  # Check for modal after clicking
                return True
            else:
                self.handler.logger.log("No matching patient found")
                return False
                
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select patient from results: {str(e)}")
            self.handler.take_screenshot("Failed to select patient from results")
            raise

#################### these are the functions for insurance within the patient page.####################

    def click_insurance_tab(self):
        """Click the Insurance tab in the patient menu."""
        try:
            self.handler.page.locator('[data-test-id="insuranceMenu"]').click()
            self.handler.logger.log("Clicked Insurance tab")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click Insurance tab: {str(e)}")
            self.handler.take_screenshot("Failed to click Insurance tab")
            raise

    def close_insurance_tab(self):
        """Close the Insurance tab in the patient menu."""
        try:
            self.handler.page.locator('[data-test-id="insuranceCloseButton"]').click()
            self.handler.logger.log("Closed Insurance tab")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to close Insurance tab: {str(e)}")
            self.handler.take_screenshot("Failed to close Insurance tab")
            raise

    def select_insurance(self, insurance_name, select_mode='random'):
        """
        Select an insurance entry by (partial) name. By default, selects a random match if multiple are found.
        Args:
            insurance_name (str): The (partial) name of the insurance to match.
            select_mode (str): 'random' (default) to select one at random, 'all' to process all matches (calls process_insurance_row for each).
        Returns:
            bool: True if at least one match was found and clicked/processed, False otherwise.
        """
        try:
            # Find all insurance name cells in the first column of the insurance table
            rows = self.handler.page.locator('.ag-center-cols-container .ag-row')
            matches = []
            for i in range(rows.count()):
                row = rows.nth(i)
                # The company name is in the first gridcell (col-id="0")
                name_cell = row.locator('[col-id="0"] span')
                cell_text = name_cell.inner_text().strip()
                if insurance_name.lower() in cell_text.lower():
                    matches.append(row)
            
            if not matches:
                self.handler.logger.log(f"No insurance found matching: {insurance_name}")
                return False
            
            self.handler.logger.log(f"Found {len(matches)} insurance(s) matching: {insurance_name}")
            
            if select_mode == 'all':
                for row in matches:
                    row.click()
                    self.handler.logger.log(f"Clicked insurance: {row.locator('[col-id=\"0\"] span').inner_text().strip()}")
                return True
            else:  # default: random
                chosen_row = random.choice(matches)
                chosen_row.click()
                self.handler.logger.log(f"Clicked insurance: {chosen_row.locator('[col-id=\"0\"] span').inner_text().strip()}")
                return True
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select insurance by name: {str(e)}")
            self.handler.take_screenshot("Failed to select insurance by name")
            raise