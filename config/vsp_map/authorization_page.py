from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient, ClaimItem
from typing import Optional, List, Dict, Set
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

    # Mapping of various header labels to canonical service names
    SERVICE_ALIASES = {
        "exam": "exam",
        "examination": "exam",
        "exam_service": "exam",
        "contact_lens_service": "contact_service",
        "contact_lens_exam": "contact_service",
        "contact_lens_exam_service": "contact_service",
        "contact_lens": "contacts",
        "contacts": "contacts",
        "contact_lens_material": "contacts",
        "contact_lens_materials": "contacts",
        "lens": "lens",
        "lenses": "lens",
        "spectacle_lens": "lens",
        "frame": "frame",
        "frame_service": "frame",
        "frame_services": "frame",
    }

    # Service code mappings
    _exam_codes = {"92004", "92014", "92015"}  # Common exam codes
    _lens_codes = {"V21", "V22", "V23", "V2781"}  # Lens code prefixes
    _frame_codes = {"V2020", "V2025"} #Frame code prefixes
    _contacts_codes = {"V25"} #Contact code prefixes
    _contact_services = {"92310"} #Contact lens code prefix

    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://eclaim.eyefinity.com/secure/eInsurance/member-search/patient-selection"

    # ------------------------------------------------------------------
    # Utilities
    def is_loaded(self, timeout: int = 5000) -> bool:
        """Verify the authorization page has loaded."""
        try:
            return_link = self.page.locator('#return-to-classic-mode-link')
            return_link.wait_for(state='visible', timeout=timeout)
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

    def _canonical_service_name(self, header_text: str) -> Optional[str]:
        """Normalize a header label to a canonical service name.

        This method attempts to standardize the various ways VSP labels the
        service columns. The original implementation performed only very basic
        replacements which meant that headers such as "Contact Lens Exam/Service"
        or "Frame Services" were not recognised. As a result the mapping between
        service names and column indices would be empty and the subsequent
        authorization logic would fail to select any services.

        The updated logic normalises the text by removing punctuation, collapsing
        whitespace and handling common variants. It then performs a series of
        substring checks to determine the canonical service name.
        """
        if not header_text:
            return None

        text = header_text.strip().lower()

        # Replace common punctuation with spaces
        for ch in ["/", "-", "\n", "\t"]:
            text = text.replace(ch, " ")

        # Collapse multiple spaces and convert to underscore format
        text = "_".join(text.split())

        # Handle plural/singular forms
        text = text.replace("services", "service")
        text = text.replace("lenses", "lens")
        text = text.replace("frames", "frame")

        # Direct alias lookup
        if text in self.SERVICE_ALIASES:
            return self.SERVICE_ALIASES[text]

        # Fallbacks based on keywords
        if "exam" in text and "contact" not in text:
            return "exam"
        if "contact" in text and ("service" in text or "exam" in text):
            return "contact_service"
        if "contact" in text:
            return "contacts"
        if "frame" in text:
            return "frame"
        if "lens" in text:
            return "lens"

        return None

    def get_service_index_map(self, package_index: int = 0) -> Dict[str, int]:
        """Return a mapping of canonical service names to their indices."""
        headers = self.page.locator(f'[id="{package_index}-service-header"] label')
        mapping: Dict[str, int] = {}
        count = headers.count()
        for i in range(count):
            text = headers.nth(i).inner_text().strip()
            canonical = self._canonical_service_name(text)
            if canonical is not None:
                mapping[canonical] = i
        self.logger.log(f"[get_service_index_map] Service index map: {mapping}")
        return mapping

    def _parse_service_status(self, text: str) -> str:
        """Return standardized service status based on availability cell text."""
        value = text.strip()
        self.logger.log(f"[_parse_service_status] Parsing text: '{value}'")
        if not value:
            self.logger.log("[_parse_service_status] Empty text, returning 'unavailable'")
            return "unavailable"
        lower = value.lower()
        if lower in {"yes", "available"}:
            self.logger.log("[_parse_service_status] Found 'available' status")
            return "available"
        if lower in {"no", "unavailable"}:
            self.logger.log("[_parse_service_status] Found 'unavailable' status")
            return "unavailable"
        if lower in {"authorized", "auth"}:
            self.logger.log("[_parse_service_status] Found 'authorized' status")
            return "authorized"
        self.logger.log(f"[_parse_service_status] Unknown status '{value}', returning as is")
        return value

    def get_service_statuses(self, package_index: int = 0, max_services: Optional[int] = None) -> Dict[int, str]:
        """Return availability status for each service in a package."""
        statuses: Dict[int, str] = {}
        self.logger.log(f"[get_service_statuses] Checking statuses for package {package_index}")
        if max_services is None:
            headers = self.page.locator(f'[id="{package_index}-service-header"] label')
            max_services = headers.count()
        for idx in range(max_services):
            self.logger.log(f"[get_service_statuses] Checking service index {idx}")
            locator = self._service_availability(package_index, idx)
            if locator.count() == 0:
                self.logger.log(f"[get_service_statuses] No element found for service {idx}")
                continue
            try:
                text = locator.inner_text().strip()
                self.logger.log(f"[get_service_statuses] Raw text for service {idx}: '{text}'")
                status = self._parse_service_status(text)
                self.logger.log(f"[get_service_statuses] Parsed status for service {idx}: {status}")
                statuses[idx] = status
            except Exception as e:
                self.logger.log_error(f"[get_service_statuses] Error getting status for service {idx}: {str(e)}")
                text = ""
                statuses[idx] = self._parse_service_status(text)
        self.logger.log(f"[get_service_statuses] Final statuses: {statuses}")
        return statuses

    def _services_from_claims(self, claims: List[ClaimItem]) -> Set[str]:
        """Return set of canonical service names from claims."""
        services = set()
        self.logger.log(f"[_services_from_claims] Processing {len(claims)} claims")
        for claim in claims:
            self.logger.log(f"[_services_from_claims] Checking claim: {claim.vcode} - {claim.description}")
            if claim.vcode in self._exam_codes:
                self.logger.log(f"[_services_from_claims] Found exam code {claim.vcode}, adding service 'exam'")
                services.add("exam")
            elif any(claim.vcode.startswith(code) for code in self._lens_codes):
                self.logger.log(f"[_services_from_claims] Found lens code {claim.vcode}, adding service 'lens'")
                services.add("lens")
            elif claim.vcode in self._frame_codes:
                self.logger.log(f"[_services_from_claims] Found frame code {claim.vcode}, adding service 'frame'")
                services.add("frame")
            elif any(claim.vcode.startswith(code) for code in self._contacts_codes):
                self.logger.log(f"[_services_from_claims] Found contact lens code {claim.vcode}, adding service 'contacts'")
                services.add("contacts")
            elif any(claim.vcode.startswith(code) for code in self._contact_services):
                self.logger.log(f"[_services_from_claims] Found contact service code {claim.vcode}, adding service 'contact_service'")
                services.add("contact_service")
            else:
                self.logger.log(f"[_services_from_claims] Code {claim.vcode} not mapped to any service")
        self.logger.log(f"[_services_from_claims] Final services: {services}")
        return services

    def is_exam_authorized(self, package_index: int = 0) -> bool:
        """Check if the exam service is already authorized.
        
        Args:
            package_index: The index of the package to check.
            
        Returns:
            bool: True if exam service is authorized, False otherwise.
        """
        try:
            status = self.get_service_statuses(package_index).get(0, "unavailable")
            self.logger.log(f"[is_exam_authorized] Exam service status: {status}")
            return status == "authorized"
        except Exception as e:
            self.logger.log_error(f"[is_exam_authorized] Failed to check exam authorization: {str(e)}")
            return False

    def select_services_for_patient(self, patient: Patient) -> str:
        """Select all available services for a patient based on their claims.
        
        Returns:
            str: One of:
                "unavailable" - if any required service is unavailable
                "use_existing" - if authorized services exactly match billed services
                "delete_existing" - if there are authorized services but they don't match billed services
                "issue" - if all billed services are available for authorization
                "exam_authorized" - if exam is already authorized but materials are unavailable
        """
        self.logger.log(f"[select_services_for_patient] Called for patient: {patient.first_name} {patient.last_name}")
        self.logger.log(f"[select_services_for_patient] Claims: {patient.claims}")
        
        # Determine mapping of service names to indices from the page
        index_map = self.get_service_index_map()

        # Map claim codes to service names
        sleep(1)
        service_names = self._services_from_claims(patient.claims)
        self.logger.log(f"[select_services_for_patient] Services from claims: {sorted(list(service_names))}")

        # Convert service names to indices using the page map
        service_indices = {index_map[name] for name in service_names if name in index_map}
        self.logger.log(f"[select_services_for_patient] Service indices from claims: {sorted(list(service_indices))}")

        # Get current service statuses
        statuses = self.get_service_statuses(max_services=None)
        self.logger.log(f"[select_services_for_patient] Service statuses for package 0: {statuses}")
        
        # Track which services we can and cannot authorize
        desired = service_indices
        authorized = {idx for idx, status in statuses.items() if status == "authorized"}
        self.logger.log(f"[select_services_for_patient] Desired set: {desired}")
        self.logger.log(f"[select_services_for_patient] Authorized set: {authorized}")
        
        # Check each service's status
        available = []
        unavailable = []
        for idx in desired:
            status = statuses.get(idx, "unavailable")
            self.logger.log(f"[select_services_for_patient] Service idx {idx} has status: {status}")
            if status == "available":
                available.append(idx)
            elif status == "unavailable":
                unavailable.append(idx)
        
        self.logger.log(f"[select_services_for_patient] Available: {available}, Authorized: {sorted(list(authorized))}, Unavailable: {unavailable}")

        # Log which services are unavailable
        if unavailable:
            unavailable_services = []
            reverse_map = {v: k for k, v in index_map.items()}
            for idx in unavailable:
                name = reverse_map.get(idx, str(idx))
                unavailable_services.append(name)
            self.logger.log(f"[select_services_for_patient] Services unavailable for authorization: {', '.join(unavailable_services)}")
            
            # Check if exam is already authorized when materials are unavailable
            if 0 not in unavailable and self.is_exam_authorized():
                self.logger.log("[select_services_for_patient] Exam is already authorized but materials are unavailable")
                return "exam_authorized"
            return "unavailable"
        
        # Check if authorized services exactly match desired services
        if authorized == desired:
            self.logger.log("[select_services_for_patient] Authorized services exactly match desired services")
            return "use_existing"
        
        # If there are any authorized services but they don't match desired services
        if authorized:
            self.logger.log("[select_services_for_patient] Authorized services exist but don't match desired services")
            return "delete_existing"
        
        # If we get here, all services are available and none are authorized
        self.logger.log("[select_services_for_patient] All services available for authorization")
        if self.select_services(0, set(available)):
            return "issue"
        return "unavailable"  # Fallback if selection fails

    def select_services(self, package_index: int, service_indices: Set[int]) -> bool:
        """Select services in a package by clicking their checkboxes."""
        self.logger.log(f"[select_services] Selecting services {service_indices} in package {package_index}")
        try:
            for idx in service_indices:
                self.logger.log(f"[select_services] Attempting to select service {idx}")
                checkbox = self.page.locator(f'[id="{package_index}-service-checkbox-{idx}"]')
                if checkbox.is_visible():
                    self.logger.log(f"[select_services] Found visible checkbox for service {idx}")
                    checkbox.click()
                    self.logger.log(f"[select_services] Clicked checkbox for service {idx}")
                else:
                    self.logger.log(f"[select_services] Checkbox for service {idx} not visible")
            return True
        except Exception as e:
            self.logger.log_error(f"[select_services] Failed to select services: {str(e)}")
            return False

    def select_all_services(self, package_index: int = 0) -> None:
        """Select the 'all available services' checkbox."""
        try:
            self.page.locator(f'[id="{package_index}-all-available-services-checkbox"]').click()
        except Exception as e:
            self.logger.log_error(f"Failed to select all services: {str(e)}")

    def issue_authorization(self, package_index: int = 0) -> bool:
        """Click the Issue Authorization button.

        The button may be visible but disabled (grayed out). In that case the
        click should be skipped and ``False`` returned.
        """
        try:
            button = self.page.locator(f'[id="0-issue-authorization-button"]')
            button.wait_for(state="visible", timeout=5000)

            if not button.is_enabled():
                self.logger.log_error("Issue Authorization button is disabled")
                return False

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

    def get_plan_name(self, patient: Patient) -> bool:
        """Find the plan name and see if it is a plan that doesn't cover a product we tried to create a claim for
        or if it was unavailable for the patient for any other reason. Log a note in the patient account to suggest looking for an
        alternate plan.
        """
        try:
            plan_name = self.page.locator('#coverage-summary-product-package-title-index-0').inner_text().strip()
            self.logger.log(f"Plan name: {plan_name}")
            #add the plan name to the patients insurance data   
            patient.insurance_data['plan_name'] = plan_name
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to research authorization: {str(e)}")
            return False

    def get_exam_service(self, package_index: int = 0) -> bool:
        """Check if exam service is available and click it if it is.

        Args:
            package_index: The index of the package to check.

        Returns:
            bool: True if exam service was available and clicked, False otherwise.
        """
        try:
            # Directly check the exam service checkbox
            checkbox = self.page.locator(f'[id="{package_index}-service-checkbox-0"]')
            if checkbox.is_visible():
                checkbox.click()
                return True
            return False
        except Exception as e:
            self.logger.log_error(f"Failed to check exam service: {str(e)}")
            return False