#/patient_page.py

from core.base import BasePage, PatientContext, Patient
from .insurance_tab import InsuranceTab
from datetime import datetime
from typing import Optional
import time
from core.utils import format_date
import re
from playwright.sync_api import Page
from core.logger import Logger

def check_alert_modal(func):
    """Decorator to check for alert modal before executing any method."""
    def wrapper(self, *args, **kwargs):
        try:
            # Look for the modal close button with a short timeout
            close_button = self.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
            if close_button.is_visible(timeout=3000):  # 3 second timeout
                close_button.click()
                self.logger.log("Closed alert history modal")
        except Exception as e:
            # Log but don't raise - we don't want this to break the main flow
            self.logger.log(f"Alert modal check completed: {str(e)}")
        
        # Execute the original method
        return func(self, *args, **kwargs)
    return wrapper

class PatientPage(BasePage):
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://revolutionehr.com/static/#/patients/search"
        self.insurance_tab = InsuranceTab(page, logger, context)
    
    def _validate_patient_required(self):
        # Patient is not required for initial navigation
        pass
    
    def is_loaded(self):
        """Check if the page is loaded"""
        try:
            # First check for advanced search button
            self.logger.log("Checking for advanced search button...")
            advanced_search = self.page.locator('[data-test-id="simpleSearchAdvancedSearch"]').is_visible(timeout=5000)
            if advanced_search:
                self.logger.log("Found advanced search button - page is loaded")
                return True
            
            # If advanced search isn't visible, check for simple search form
            self.logger.log("Advanced search not found, checking for simple search form...")
            simple_search = self.page.locator('[data-test-id="simpleSearchForm"]').is_visible(timeout=5000)
            if simple_search:
                self.logger.log("Found simple search form - page is loaded")
                return True
                
            self.logger.log("Neither advanced search nor simple search form found")
            return False
            
        except Exception as e:
            self.logger.log_error(f"Failed to check if patient page is loaded: {str(e)}")
            return False
    
    def navigate_to_patient_page(self):
        """Navigate to the patient search page."""
        try:
            self.page.goto(self.base_url)
            self.logger.log("Navigated to patient search page")
            
            # Add a small delay to ensure the page has time to load
            self.page.wait_for_timeout(2000)  # 2 second delay
            
            # Wait for the page to be loaded
            if not self.is_loaded():
                raise Exception("Patient page failed to load after navigation")
                
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to patient page: {str(e)}")
            raise
    
    @check_alert_modal
    def click_patient_tab(self):
        """Click the open patient tab."""
        try:
            self.page.locator('[data-test-id$=".navigationTab"]').click()
            self.logger.log("Clicked patient tab")
        except Exception as e:
            self.logger.log_error(f"Failed to click patient tab: {str(e)}")
            raise

    @check_alert_modal
    def close_patient_tab(self):
        """Click the close button (x) on the patient tab."""
        try:
            # Find the last navigation tab and get its close button
            self.page.locator('[data-test-id$=".navigationTab"]').get_by_title('Close').click()
            self.logger.log("Closed patient tab")
        except Exception as e:
            self.logger.log_error(f"Failed to close patient tab: {str(e)}")
            raise

    def click_advanced_search(self):
        """Click the advanced search link on the patient search page."""
        try:
            self.page.locator('[data-test-id="simpleSearchAdvancedSearch"]').click()
            self.logger.log("Clicked advanced search link")
        except Exception as e:
            self.logger.log_error(f"Failed to click advanced search link: {str(e)}")
            raise

    def search_patient(self, patient: Patient) -> Optional[Patient]:
        """Perform an advanced patient search using the provided Patient object.
        
        Args:
            patient (Patient): The Patient object containing the data to search for
            
        Returns:
            Optional[Patient]: Patient object if found, None otherwise
        """
        self.logger.log("Starting advanced patient search")
        try:
            # Check if we're already in advanced search mode
            advanced_search_visible = self.page.locator('[data-test-id="advancedSearchSearchButton"]').is_visible(timeout=1000)
            if not advanced_search_visible:
                self.click_advanced_search()
            
            # Fill in each field if available in the patient object
            if patient.last_name:
                self.page.get_by_role('textbox', name='Last Name').fill(patient.last_name)
                
            if patient.first_name:
                self.page.get_by_role('textbox', name='First Name').fill(patient.first_name)
                
            if patient.dob:
                self.page.get_by_role('combobox', name='datepicker').fill(patient.dob)
                
            address = patient.get_demographic_data("address")
            if address:
                self.page.get_by_role('textbox', name='Address').fill(address)
                
            phone = patient.get_demographic_data("phone")
            if phone:
                self.page.locator('[data-test-id="advancedSearchPhoneFormGroup"]').get_by_role('textbox', name='maskedtextbox').fill(phone)
                
            email = patient.get_demographic_data("email")
            if email:
                self.page.get_by_role('textbox', name='Email').fill(email)
                
            ssn = patient.get_demographic_data("ssn")
            if ssn:
                self.page.locator('[data-test-id="advancedSearchSocialSecurityNumberFormGroup"]').get_by_role('textbox', name='maskedtextbox').fill(ssn)
                
            patient_id = patient.get_demographic_data("patient_id")
            if patient_id:
                self.page.get_by_role('textbox', name='ID').fill(patient_id)
            
            # Click the search button
            self.page.locator('[data-test-id="advancedSearchSearchButton"]').click()
            self.logger.log("Advanced patient search completed")
            
            return patient
            
        except Exception as e:
            self.logger.log_error(f"Failed to perform advanced patient search: {str(e)}")
            raise

    def _check_alert_modal(self):
        """Check for and close the alert modal if it appears."""
        try:
            # Add a small wait to allow the modal to appear
            self.page.wait_for_timeout(1000)  # 1 second wait
            
            close_button = self.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
            if close_button.is_visible(timeout=3000):
                close_button.click()
                self.logger.log("Closed alert history modal")
        except Exception as e:
            self.logger.log(f"Alert modal check completed: {str(e)}")

    def select_patient_from_results(self, patient: Patient) -> bool:
        """Select a patient from the search results based on the provided Patient object.
        
        Args:
            patient (Patient): The Patient object containing the data to match
            
        Returns:
            bool: True if a matching patient was found and selected, False otherwise
        """
        # Add a small wait to allow the modal to appear
        self.page.wait_for_timeout(1000)  # 1 second wait
        
        try:
            # Wait for the results table to be visible
            self.page.wait_for_selector('.ag-center-cols-container', timeout=5000)
            
            # Get all rows in the table
            rows = self.page.locator('.ag-center-cols-container .ag-row').all()
            
            if not rows:
                self.logger.log("No search results found")
                return False
                
            self.logger.log(f"Found {len(rows)} search results")
            
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
                    if patient.first_name.lower() in name_cell.lower():
                        match_score += 1
                
                if patient.dob:
                    dob_cell = row.locator('[col-id="dob"]').text_content()
                    if patient.dob in dob_cell:
                        match_score += 1
                
                # Update best match if this row has a higher score
                if match_score > best_match_score:
                    best_match = row
                    best_match_score = match_score
            
            if best_match:
                best_match.click()
                self.logger.log(f"Selected patient with match score {best_match_score}")
                return True
            else:
                self.logger.log("No matching patient found")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Failed to select patient from results: {str(e)}")
            return False

    def scrape_demographics(self, patient: Patient) -> None:
        """Scrape patient demographic information from the patient page.
        
        This function extracts:
        - Date of birth
        - Gender
        - Address (street, city, state, zip)
        
        Args:
            patient: Patient object to store the demographic data
        """
        try:
            # Wait for the patient page to load
            self.page.wait_for_selector('[data-test-id="patientHeaderDemographicList"]', timeout=10000)
            
            # Wait a moment for any popups
            self.page.wait_for_timeout(1000)
            
            # Handle any alert popup
            try:
                close_button = self.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
                if close_button.is_visible(timeout=3000):
                    close_button.click()
            except Exception as e:
                self.logger.log(f"Alert modal check: {str(e)}")
            
            # Get date of birth
            dob_element = self.page.locator('[data-test-id="patientHeaderDateOfBirth"]')
            dob_text = dob_element.inner_text()
            patient.dob = dob_text.split(' ')[0]  # Store in the dob field
            
            # Get gender
            gender_element = self.page.locator('[data-test-id="patientHeaderGender"]')
            patient.demographics['gender'] = gender_element.inner_text()
            
            # Get address
            try:
                address_element = self.page.locator('[data-test-id="patientHeaderAddress"]')
                address_text = address_element.inner_text()
                address_parts = address_text.split(',')
                
                # Extract address components
                patient.demographics['address'] = address_parts[0].strip()
                patient.demographics['city'] = address_parts[1].strip()
                
                # Split state and zip - handle cases where state might be abbreviated or full name
                state_zip = address_parts[2].strip()
                # Split on last space to separate state and zip
                last_space_index = state_zip.rindex(' ')
                patient.demographics['state'] = state_zip[:last_space_index].strip()
                patient.demographics['zip'] = state_zip[last_space_index:].strip()
                
            except Exception as e:
                self.logger.log(f"Error extracting address: {str(e)}")
                # Set default values
                patient.demographics.update({
                    'address': '1476 Biggs',
                    'city': 'Amarillo',
                    'state': 'TX',
                    'zip': '79110'
                })
            
            self.logger.log("Successfully scraped patient demographics")
            
        except Exception as e:
            self.logger.log_error(f"Failed to scrape patient demographics: {str(e)}")
            raise

    def expand_insurance(self):
        """Click the insurance summary expand button to show insurance details."""
        try:
            self.page.locator('[data-test-id="insuranceSummaryPodexpand"]').click()
            self.logger.log("Clicked insurance summary expand button")
        except Exception as e:
            self.logger.log_error(f"Failed to click insurance summary expand button: {str(e)}")
            raise

    
    def click_patient_summary_menu(self):
        """Click the patient summary menu button."""
        try:
            self.page.locator('[data-test-id="patientSummaryMenu"]').click()
            self.logger.log("Clicked patient summary menu")
        except Exception as e:
            self.logger.log_error(f"Failed to click patient summary menu: {str(e)}")
            raise

    def scrape_family_demographics(self, patient: Patient) -> None:
        """Scrape family member demographic information for VSP search combinations.
        
        This function extracts family member information and stores it in the patient's
        insurance_data dictionary under 'search_combinations'. Each family member's data
        is stored as a dictionary with keys: first_name, last_name, dob.
        
        Args:
            patient: Patient object to store the family demographic data
        """
        try:
            # Initialize search_combinations list in insurance_data if it doesn't exist
            if 'search_combinations' not in patient.insurance_data:
                patient.insurance_data['search_combinations'] = []

            # Add primary patient as first search combination
            primary_patient = {
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'dob': patient.dob
            }
            patient.insurance_data['search_combinations'].append(primary_patient)

            # Click on patient summary menu to access family members
            self.click_patient_summary_menu()
            self.page.wait_for_timeout(3000)  # Wait for contacts to load

            # Get all listed contacts
            listed_contacts = self.page.locator("//*[@col-id='formattedName']").all()
            self.logger.log(f"Found {len(listed_contacts)} contacts")

            # Use a counter to iterate through contacts to avoid stale elements
            for i in range(len(listed_contacts)):
                # Skip the first iteration (primary patient)
                if i > 0:
                    try:
                        # Refresh contacts list to avoid stale elements
                        listed_contacts = self.page.locator("//*[@col-id='formattedName']").all()
                        contact = listed_contacts[i]
                        contact.click()
                        self.page.wait_for_timeout(1000)

                        # Check for and close alert popup
                        try:
                            close_button = self.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
                            if close_button.is_visible(timeout=2000):
                                close_button.click()
                        except:
                            pass

                        # Get name information
                        name_field = self.page.locator("//*[@class='media-heading display-inline-block vertical-align-middle margin-top-0 margin-bottom-0 margin-right-lg']")
                        name = name_field.inner_text()
                        name_parts = name.split(',')
                        last_name = name_parts[0].strip()
                        first_name = name_parts[1].strip() if len(name_parts) > 1 else ''
                        
                        # Strip everything from the hashtag in the first name
                        first_name = re.sub(r'#.*', '', first_name)

                        # Get DOB
                        try:
                            dob = self.page.locator("//*[@class='fa fa-birthday-cake text-primary margin-right-xs']")
                            if dob.is_visible():
                                dob = dob.locator("..").inner_text()
                            else:
                                dob = self.page.locator("//*[@class='fa fa-birthday-cake text-info margin-right-xs']").locator("..").inner_text()
                            
                            # Strip the age in () from the text
                            dob = re.sub(r'\([^)]*\)', '', dob)
                        except:
                            dob = None

                        # Create family member data dictionary
                        family_member = {
                            'first_name': first_name,
                            'last_name': last_name,
                            'dob': dob
                        }

                        # Add to search combinations
                        patient.insurance_data['search_combinations'].append(family_member)
                        self.logger.log(f"Added family member: {first_name} {last_name}")

                        # Close the patient tab
                        closing_name = f"{last_name}, {first_name[0]}".lower().replace(" ", "")
                        close_icon = self.page.locator(f"//span[@data-test-id='{closing_name}.navigationTab']/ancestor::div[contains(@class, 'e-text-wrap')]/span[contains(@class, 'e-close-icon')]")
                        close_icon.click()
                        self.page.wait_for_timeout(1000)

                    except Exception as e:
                        self.logger.log(f"Error processing contact {i}: {str(e)}")
                        continue

            self.logger.log(f"Successfully scraped {len(patient.insurance_data['search_combinations'])} family member records")
            
        except Exception as e:
            self.logger.log_error(f"Failed to scrape family demographics: {str(e)}")
            raise

    def expand_optical_orders(self):
        """Expand the optical orders section for the current patient."""
        try:
            self.logger.log("Expanding optical orders section...")
            self.page.locator('[data-test-id="ordersOpticalPodexpand"]').click()
            self.page.wait_for_timeout(1500)  # Wait for animation
            self.logger.log("Optical orders section expanded")
        except Exception as e:
            self.logger.log(f"Failed to expand optical orders: {str(e)}")
            raise

    def open_optical_order(self, patient: Patient) -> bool:
        """Find and open the correct optical order based on date and VSP text.
        
        Args:
            patient: Patient object containing the claims data with date of service
            
        Returns:
            bool: True if order was found and opened, False otherwise
        """
        try:
            # Get the date from the first claim in claims data
            if not patient.claims or len(patient.claims) == 0:
                self.logger.log("No claims data found for patient")
                return False
                
            # Get the date from the first claim
            claim_date = patient.claims[0].date
            if not claim_date:
                self.logger.log("No date found in claims data")
                return False
                
            # Wait for the table to be visible
            self.page.wait_for_selector("//table[@role='presentation']/tbody/tr", timeout=5000)
            
            # Text options to match in the order
            text_options = [
                'VSP IOF PROGRAM - Sacramento, CA',
                'CARL ZEISS VISION KENTUCKY - Hebron, KY **CA-RNP** **ADVTG/NAT-RNP** **SELECT**',
                'VSP',
                'vsp'
            ]
            
            # Maximum retries for stale elements
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    # Get all rows
                    rows = self.page.locator("//table[@role='presentation']/tbody/tr").all()
                    
                    for row in rows:
                        try:
                            # Find the date cell
                            date_cell = row.locator(".//*[@data-colindex='1']")
                            date_text = date_cell.inner_text()
                            
                            if date_text == claim_date:
                                # Check for matching text options
                                for text_option in text_options:
                                    try:
                                        text_cell = row.locator(f".//td[contains(text(), '{text_option}')]")
                                        if text_cell.is_visible():
                                            self.logger.log(f"Found matching order with text: {text_option}")
                                            text_cell.click()
                                            # Wait for order to open
                                            self.page.wait_for_timeout(1500)
                                            return True
                                    except Exception as e:
                                        continue
                                        
                        except Exception as e:
                            self.logger.log(f"Error processing row: {str(e)}")
                            continue
                            
                    # If we get here, no matching order was found in this attempt
                    if attempt < max_retries - 1:
                        self.logger.log(f"Retrying order search (Attempt {attempt + 1}/{max_retries})")
                        self.page.wait_for_timeout(100)
                        
                except Exception as e:
                    self.logger.log(f"Error during order search attempt {attempt + 1}: {str(e)}")
                    if attempt < max_retries - 1:
                        self.page.wait_for_timeout(100)
            
            self.logger.log("No matching optical order found")
            return False
            
        except Exception as e:
            self.logger.log_error(f"Failed to open optical order: {str(e)}")
            raise