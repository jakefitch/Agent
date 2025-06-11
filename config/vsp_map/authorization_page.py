from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient
from typing import Optional, List, Dict
from time import sleep

class AuthorizationPage(BasePage):
    """Page object for interacting with VSP's authorization page."""

    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://eclaim.eyefinity.com/secure/eInsurance/member-search/patient-selection"

    # ------------------------------------------------------------------
    # Utilities
    def is_loaded(self, timeout: int = 5000) -> bool:
        """Verify the authorization page has loaded."""
        try:
            header = self.page.locator('#list-of-authorizations-header')
            header.wait_for(state='visible', timeout=timeout)
            return True
        except Exception as e:
            self.logger.log_error(f"Authorization page not loaded: {str(e)}")
            return False

    def navigate_to_authorizations(self) -> None:
        """Navigate to the authorization page."""
        try:
            self.logger.log("Navigating to authorization page ...")
            self.page.goto(self.base_url)
            self.wait_for_network_idle(timeout=10000)
            if not self.is_loaded(timeout=10000):
                raise Exception("Authorization page failed to load")
            self.logger.log("Authorization page loaded")
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to authorization page: {str(e)}")
            self.take_screenshot("authorization_nav_error")
            raise

    # ------------------------------------------------------------------
    # Existing authorization table utilities
    def _get_authorization_rows(self):
        return self.page.locator('#auth-selection-table mat-row')

    def list_authorizations(self) -> List[Dict[str, str]]:
        """Return a list of existing authorizations on the page."""
        rows = self._get_authorization_rows()
        data = []
        try:
            for i in range(rows.count()):
                row = rows.nth(i)
                auth_number = row.locator('[id^="auth-search-result-auth-number-data"]').inner_text().strip()
                name = row.locator('#auth-search-result-name-data').inner_text().strip()
                product = row.locator('#auth-search-result-product-data').inner_text().strip()
                expires = row.locator('#auth-search-result-expires-data').inner_text().strip()
                data.append({
                    'auth_number': auth_number,
                    'name': name,
                    'product': product,
                    'expires': expires,
                })
            return data
        except Exception as e:
            self.logger.log_error(f"Failed to parse authorization list: {str(e)}")
            self.take_screenshot("auth_list_parse_error")
            return []

    def _fix_name_order(self, first_name: str, last_name: str) -> tuple[str, str]:
        """Fix swapped first and last names if they appear to be in the wrong order."""
        # If first_name contains a comma, it's likely the last name was put in the first_name field
        if ',' in first_name:
            return last_name, first_name.replace(',', '').strip()
        # If last_name contains a comma, it's likely the first name was put in the last_name field
        if ',' in last_name:
            return last_name.replace(',', '').strip(), first_name
        return first_name, last_name

    def select_authorization(self, patient: Patient) -> bool:
        """Select an authorization for the given patient by name."""
        try:
            first_name, last_name = self._fix_name_order(patient.first_name, patient.last_name)
            self.logger.log(f"Raw patient data - First Name: '{first_name}', Last Name: '{last_name}'")
            target_name = f"{last_name}, {first_name}".upper().strip()
            self.logger.log(f"Searching for authorization with name: {target_name}")
            
            rows = self._get_authorization_rows()
            row_count = rows.count()
            self.logger.log(f"Found {row_count} authorization rows to search through")
            
            for i in range(row_count):
                row = rows.nth(i)
                name_cell = row.locator('#auth-search-result-name-data')
                current_name = name_cell.inner_text().strip().upper()
                self.logger.log(f"Checking row {i+1}: {current_name}")
                
                if current_name == target_name:
                    self.logger.log(f"Found matching authorization for {target_name}")
                    name_cell.click()
                    return True
                    
            self.logger.log(f"No matching authorization found for {target_name}")
            return False
        except Exception as e:
            self.logger.log_error(
                f"Failed to select authorization for {patient.first_name} {patient.last_name}: {str(e)}"
            )
            self.take_screenshot("auth_select_error")
            return False

    def delete_authorization(self, patient: Patient) -> bool:
        """Delete an authorization for the given patient."""
        try:
            first_name, last_name = self._fix_name_order(patient.first_name, patient.last_name)
            self.logger.log(f"Raw patient data - First Name: '{first_name}', Last Name: '{last_name}'")
            target_name = f"{last_name}, {first_name}".upper().strip()
            self.logger.log(f"Searching for authorization to delete with name: {target_name}")
            
            rows = self._get_authorization_rows()
            row_count = rows.count()
            self.logger.log(f"Found {row_count} authorization rows to search through")
            
            for i in range(row_count):
                row = rows.nth(i)
                name_cell = row.locator('#auth-search-result-name-data')
                current_name = name_cell.inner_text().strip().upper()
                self.logger.log(f"Checking row {i+1}: {current_name}")
                
                if current_name == target_name:
                    self.logger.log(f"Found matching authorization to delete: {target_name}")
                    delete_cell = row.locator('[id^="auth-search-result-delete-data"] mat-icon')
                    delete_cell.click()
                    self.logger.log("Clicked delete icon")
                    
                    sleep(0.5)
                    try:
                        ok_button = self.page.locator('#okButton')
                        ok_button.wait_for(state='visible', timeout=5000)
                        ok_button.click()
                        self.logger.log(
                            f"Successfully deleted authorization for {patient.first_name} {patient.last_name}"
                        )
                        return True
                    except Exception as e:
                        self.logger.log_error(f"Failed to click OK button: {str(e)}")
                        return False
                        
            self.logger.log(f"No matching authorization found to delete for {target_name}")
            return False
        except Exception as e:
            self.logger.log_error(
                f"Failed to delete authorization for {patient.first_name} {patient.last_name}: {str(e)}"
            )
            self.take_screenshot("auth_delete_error")
            return False

    def refresh_authorizations(self) -> None:
        """Click the refresh button on the authorization page."""
        try:
            self.page.locator('#patientSelection-refreshButton').click()
            self.wait_for_network_idle(timeout=10000)
        except Exception as e:
            self.logger.log_error(f"Failed to refresh authorizations: {str(e)}")
            self.take_screenshot("auth_refresh_error")

    # ------------------------------------------------------------------
    # Patient selection utilities
    def _get_patient_rows(self):
        return self.page.locator('#patient-selection-member-result-table mat-row')

    def list_patients(self) -> List[Dict[str, str]]:
        """Return a list of patients displayed for issuing authorizations."""
        rows = self._get_patient_rows()
        data = []
        try:
            for i in range(rows.count()):
                row = rows.nth(i)
                name = row.locator('#patient-selection-result-name-data').inner_text().strip()
                relation = row.locator('#patient-selection-result-relation-data').inner_text().strip()
                dob = row.locator('[id^="patient-selection-result-city-dob-data"]').inner_text().strip()
                data.append({'name': name, 'relation': relation, 'dob': dob})
            return data
        except Exception as e:
            self.logger.log_error(f"Failed to parse patient list: {str(e)}")
            self.take_screenshot("auth_patient_list_error")
            return []

    def select_patient(self, patient: Patient) -> bool:
        """Select a patient row by name and date of birth."""
        try:
            first_name, last_name = self._fix_name_order(patient.first_name, patient.last_name)
            self.logger.log(f"Raw patient data - First Name: '{first_name}', Last Name: '{last_name}'")
            target_name = f"{last_name}, {first_name}".upper().strip()
            target_dob = (patient.dob or "").strip()
            self.logger.log(f"Searching for patient with name: {target_name} and DOB: {target_dob}")
            
            rows = self._get_patient_rows()
            row_count = rows.count()
            self.logger.log(f"Found {row_count} patient rows to search through")
            
            for i in range(row_count):
                row = rows.nth(i)
                name_cell = row.locator('#patient-selection-result-name-data')
                dob_cell = row.locator('[id^="patient-selection-result-city-dob-data"]')
                
                current_name = name_cell.inner_text().strip().upper()
                current_dob = dob_cell.inner_text().strip()
                self.logger.log(f"Checking row {i+1}: Name={current_name}, DOB={current_dob}")
                
                if current_name == target_name and current_dob == target_dob:
                    self.logger.log(f"Found matching patient: {target_name}")
                    name_cell.click()
                    return True
                    
            self.logger.log(f"No matching patient found for {target_name} with DOB {target_dob}")
            return False
        except Exception as e:
            self.logger.log_error(
                f"Failed to select patient {patient.first_name} {patient.last_name}: {str(e)}"
            )
            self.take_screenshot("auth_select_patient_error")
            return False

    # ------------------------------------------------------------------
    # Coverage selection utilities
    def _service_checkbox(self, package_index: int, service_index: int):
        """Return locator for a service checkbox."""
        return self.page.locator(f"#{package_index}-service-checkbox-{service_index}")

    def select_services(self, service_indices: List[int], package_index: int = 0) -> None:
        """Select one or more service checkboxes by index."""
        for idx in service_indices:
            try:
                checkbox = self._service_checkbox(package_index, idx)
                checkbox.click()
            except Exception as e:
                self.logger.log_error(f"Failed to select service {idx}: {str(e)}")

    def select_all_services(self, package_index: int = 0) -> None:
        """Select the 'all available services' checkbox."""
        try:
            self.page.locator(f"#{package_index}-all-available-services-checkbox").click()
        except Exception as e:
            self.logger.log_error(f"Failed to select all services: {str(e)}")

    def issue_authorization(self, package_index: int = 0) -> bool:
        """Click the Issue Authorization button."""
        try:
            button = self.page.locator(f"#{package_index}-issue-authorization-button")
            button.wait_for(state="visible", timeout=5000)
            button.click()
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to issue authorization: {str(e)}")
            self.take_screenshot("auth_issue_error")
            return False

    def get_confirmation_number(self) -> Optional[str]:
        """Return the authorization confirmation number if visible."""
        try:
            elem = self.page.locator('#auth-confirmation-number')
            elem.wait_for(state='visible', timeout=5000)
            return elem.inner_text().strip()
        except Exception:
            return None
