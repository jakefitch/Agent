from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage
from typing import Optional, List, Dict

class AuthorizationPage(BasePage):
    """Page object for interacting with VSP's authorization page."""

    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://eclaim.eyefinity.com/secure/eInsurance/authorization"

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

    def select_authorization(self, auth_number: str) -> bool:
        """Select an authorization by its number."""
        try:
            rows = self._get_authorization_rows()
            for i in range(rows.count()):
                row = rows.nth(i)
                cell = row.locator('[id^="auth-search-result-auth-number-data"]')
                if cell.inner_text().strip() == str(auth_number):
                    cell.click()
                    return True
            return False
        except Exception as e:
            self.logger.log_error(f"Failed to select authorization {auth_number}: {str(e)}")
            self.take_screenshot("auth_select_error")
            return False

    def delete_authorization(self, auth_number: str) -> bool:
        """Click the delete icon for the authorization matching ``auth_number``."""
        try:
            rows = self._get_authorization_rows()
            for i in range(rows.count()):
                row = rows.nth(i)
                num_cell = row.locator('[id^="auth-search-result-auth-number-data"]')
                if num_cell.inner_text().strip() == str(auth_number):
                    delete_cell = row.locator('[id^="auth-search-result-delete-data"] mat-icon')
                    delete_cell.click()
                    return True
            return False
        except Exception as e:
            self.logger.log_error(f"Failed to delete authorization {auth_number}: {str(e)}")
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

    def select_patient(self, name: str) -> bool:
        """Select a patient row by exact name."""
        try:
            rows = self._get_patient_rows()
            for i in range(rows.count()):
                row = rows.nth(i)
                name_cell = row.locator('#patient-selection-result-name-data')
                if name_cell.inner_text().strip().upper() == name.upper():
                    name_cell.click()
                    return True
            return False
        except Exception as e:
            self.logger.log_error(f"Failed to select patient {name}: {str(e)}")
            self.take_screenshot("auth_select_patient_error")
            return False
