from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient
from typing import Optional, List, Dict
from time import sleep

class AuthorizationPage(BasePage):
    """Page object for interacting with VSP's authorization page."""

    SERVICE_NAMES = {
        0: "exam",
        1: "contact_service",
        2: "lens",
        3: "frame",
        4: "contacts",
    }

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
                auth_number_cell = row.locator('[id^="auth-search-result-auth-number-data"]')
                current_name = name_cell.inner_text().strip().upper()
                self.logger.log(f"Checking row {i+1}: {current_name}")

                if current_name == target_name:
                    self.logger.log(f"Found matching authorization for {target_name}")
                    auth_number_cell.click()
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

            self.logger.log(
                f"No patient match for name {target_name} with DOB {target_dob}. Trying DOB only."
            )

            for i in range(row_count):
                row = rows.nth(i)
                name_cell = row.locator('#patient-selection-result-name-data')
                dob_cell = row.locator('[id^="patient-selection-result-city-dob-data"]')

                current_dob = dob_cell.inner_text().strip()
                self.logger.log(f"Checking row {i+1} for DOB only: DOB={current_dob}")

                if current_dob == target_dob:
                    self.logger.log(f"Found patient by DOB: {current_dob}")
                    name_cell.click()
                    return True

            self.logger.log(f"No matching patient found with DOB {target_dob}")
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
        # Use attribute selector instead of ID selector to handle numeric IDs
        return self.page.locator(f'[id="{package_index}-service-checkbox-{service_index}"]')

    def _service_availability(self, package_index: int, service_index: int):
        """Return locator for a service availability cell."""
        return self.page.locator(f'[id="{package_index}-availability-{service_index}"]')

    def _parse_service_status(self, text: str) -> str:
        """Return standardized service status based on availability cell text."""
        value = text.strip()
        lower = value.lower()
        if lower in {"yes", "available"}:
            return "available"
        if "authorized" in lower:
            return "authorized"
        return value  # assume a date string or unknown text

    def get_service_statuses(self, package_index: int = 0) -> Dict[int, str]:
        """Return availability status for each service in a package."""
        statuses: Dict[int, str] = {}
        idx = 0
        while True:
            locator = self._service_availability(package_index, idx)
            if locator.count() == 0:
                break
            try:
                text = locator.inner_text().strip()
            except Exception:
                text = ""
            statuses[idx] = self._parse_service_status(text)
            idx += 1
        return statuses

    def _services_from_claims(self, patient: Patient) -> List[int]:
        """Determine which service checkboxes to select based on claim codes.

        Exam                     -> index 0
        Contact Lens Service     -> index 1
        Lens                     -> index 2
        Frame                    -> index 3
        Contact Lens             -> index 4

        Args:
            patient: ``Patient`` instance containing claim information.

        Returns:
            List of checkbox indices corresponding to required services.
        """
        if not patient.claims:
            return []

        select_exam = False
        select_cl_service = False
        select_lens = False
        select_frame = False
        select_contacts = False

        for claim in patient.claims:
            code = (claim.vcode or claim.code or "").upper()

            # Exam codes
            if code in {"92004", "92014"} or code.startswith("99") or \
               code.startswith("S062") or code.startswith("S602"):
                select_exam = True

            # Contact lens material codes
            if code.startswith("V252"):
                select_contacts = True

            # Frame codes
            if code in {"V2020", "V2025"}:
                select_frame = True

            # Lens codes
            if code.startswith(("V21", "V22", "V23")) or code.startswith("V2781"):
                select_lens = True

            # Contact lens service codes
            if code.startswith("9231"):
                select_cl_service = True

        service_indices = []
        if select_exam:
            service_indices.append(0)
        if select_cl_service:
            service_indices.append(1)
        if select_lens:
            service_indices.append(2)
        if select_frame:
            service_indices.append(3)
        if select_contacts:
            service_indices.append(4)

        return service_indices

    def select_services_for_patient(self, patient: Patient, package_index: int = 0) -> str:
        """Determine and select services for a patient based on claim data.

        The method combines the claim-derived service list with the current
        availability statuses on the page to decide the next action.

        Returns a string describing the workflow decision:
            ``"issue"``          - select services and issue a new authorization
            ``"use_existing"``   - services already authorized exactly match
            ``"delete_existing"``- existing authorization does not match claims
            ``"unavailable"``    - a required service is unavailable or not
                                   offered on the plan
            ``"no_services"``    - no billable services were found
        """

        indices = self._services_from_claims(patient)
        if not indices:
            self.logger.log("No billable services found in claims")
            return "no_services"

        statuses = self.get_service_statuses(package_index)
        desired_set = set(indices)
        authorized_set = {i for i, s in statuses.items() if s == "authorized"}

        available = []
        authorized = []
        unavailable = []

        for idx in indices:
            # If the status for a desired service is missing, the plan does not
            # support it. Treat this the same as any other unavailable status.
            status = statuses.get(idx, "unavailable")
            if status == "available":
                available.append(idx)
            elif status == "authorized":
                authorized.append(idx)
            else:
                unavailable.append(idx)

        if unavailable:
            names = ", ".join(self.SERVICE_NAMES.get(i, str(i)) for i in unavailable)
            self.logger.log(f"Services unavailable for authorization: {names}")
            return "unavailable"

        if authorized_set == desired_set:
            self.logger.log("Desired services already authorized - using existing authorization")
            return "use_existing"

        if authorized:
            self.logger.log("Authorized services do not match desired - will delete authorization")
            return "delete_existing"

        # All required services are available
        self.logger.log("All required services available - selecting for authorization")
        self.select_services(indices, package_index)
        return "issue"

    def select_services(self, service_indices: List[int], package_index: int = 0) -> None:
        """Select one or more service checkboxes by index if available."""
        statuses = self.get_service_statuses(package_index)
        for idx in service_indices:
            # Missing status indicates the service is not offered on the plan
            status = statuses.get(idx, "unavailable")
            if status != "available":
                self.logger.log(f"Skipping service {idx} due to status: {status}")
                continue
            try:
                checkbox = self._service_checkbox(package_index, idx)
                checkbox.click()
                self.logger.log(f"Selected service checkbox {idx}")
            except Exception as e:
                self.logger.log_error(f"Failed to select service {idx}: {str(e)}")

    def select_all_services(self, package_index: int = 0) -> None:
        """Select the 'all available services' checkbox."""
        try:
            self.page.locator(f'[id="{package_index}-all-available-services-checkbox"]').click()
        except Exception as e:
            self.logger.log_error(f"Failed to select all services: {str(e)}")

    def issue_authorization(self, package_index: int = 0) -> bool:
        """Click the Issue Authorization button."""
        try:
            button = self.page.locator(f'[id="{package_index}-issue-authorization-button"]')
            button.wait_for(state="visible", timeout=5000)
            button.click()
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to issue authorization: {str(e)}")
            self.take_screenshot("auth_issue_error")
            return False

    def get_confirmation_number(self) -> Optional[str]:
        """Return the authorization confirmation number if visible and store it in the patient object."""
        try:
            elem = self.page.locator('#auth-confirmation-number')
            elem.wait_for(state='visible', timeout=5000)
            confirmation_number = elem.inner_text().strip()
            
            if confirmation_number and self.context and self.context.patient:
                self.context.patient.authorization_number = confirmation_number
                self.logger.log(f"Stored authorization number {confirmation_number} in patient object")
            
            return confirmation_number
        except Exception as e:
            self.logger.log_error(f"Failed to get confirmation number: {str(e)}")
            return None

    def navigate_to_claim(self) -> bool:
        """Click the View CMS 1500 Form button to navigate to the claim form."""
        try:
            button = self.page.locator('[id="authorization-confirmation-go-to-claim-form-button"]')
            button.wait_for(state="visible", timeout=5000)
            button.click()
            self.logger.log("Clicked View CMS 1500 Form button")
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to claim form: {str(e)}")
            self.take_screenshot("claim_nav_error")
            return False
