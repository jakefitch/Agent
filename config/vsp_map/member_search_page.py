from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient
from typing import Optional, Dict, List, Set
from datetime import datetime
import re
from time import sleep
import time
import os
import json
from pathlib import Path
from core.ai_tools import OllamaClient

class MemberSearch(BasePage):
    """Class for handling VSP member search operations."""
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        """Initialize the member search page.
        
        Args:
            page: Playwright page instance
            logger: Logger instance for logging operations
            context: Optional PatientContext for patient-specific operations
        """
        super().__init__(page, logger, context)
        self.base_url = "https://eclaim.eyefinity.com/secure/eInsurance/member-search"
    
    def is_loaded(self, timeout: int = 5000) -> bool:
        """Check if the member search page is loaded.

        Args:
            timeout: Maximum time in milliseconds to wait for the page element.

        Returns:
            bool: ``True`` if the page is loaded, otherwise ``False``.
        """
        try:
            self.logger.log("Checking if member search page is loaded...")
            link = self.page.locator('#member-search-valid-search-combinations-link')
            link.wait_for(state='visible', timeout=timeout)
            return True
        except Exception as e:
            self.logger.log_error(f"Error checking if member search page is loaded: {str(e)}")
            return False
        
    def navigate_to_member_search(self) -> None:
        """Navigate to the member search page.
        
        This function will:
        1. Navigate to the member search page using the base URL
        2. Wait for the page to load
        3. Verify we're on the correct page using is_loaded
        """
        try:

            # Navigate to the member search page
            self.logger.log("Navigating to member search...")
            self.page.goto("https://eclaim.eyefinity.com/secure/eInsurance/member-search")

            # Give the page a moment to settle before checking
            self.wait_for_network_idle(timeout=10000)

            # Verify the page has loaded
            if not self.is_loaded(timeout=10000):
                raise Exception("Member search page failed to load properly")
            
            self.logger.log("Successfully navigated to member search page")
            
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to member search page: {str(e)}")
            self.take_screenshot("Failed to navigate to member search page")
            raise
    
    def _enter_dos(self, dos: str) -> bool:
        """Enter the date of service.
        
        Args:
            dos: Date of service in MM/DD/YYYY format
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.log(f"Entering date of service: {dos}")
            dos_field = self.page.locator("#member-search-dos")
            if not dos_field.is_visible():
                self.logger.log("DOS field not visible")
                return False
                
            dos_field.fill(dos)
            return True
        except Exception as e:
            self.logger.log(f"Error entering DOS: {str(e)}")
            self.take_screenshot("dos_entry_error")
            return False
    
    def _clear_search_fields(self) -> None:
        """Clear all search fields."""
        try:
            self.logger.log("Clearing all search fields...")
            selectors = [
                "#member-search-first-name",
                "#member-search-last-name", 
                "#member-search-dob",
                "#member-search-last-four",
                "#member-search-full-id"
            ]
            for selector in selectors:
                field = self.page.locator(selector)
                if field.is_visible():
                    # Clear the field and verify it's empty
                    field.clear()
                    # Wait a moment for the clear to take effect
                    self.page.wait_for_timeout(100)
                    # Double-check by filling with empty string
                    field.fill("")
                    self.logger.log(f"Cleared field: {selector}")
                else:
                    self.logger.log(f"Field not visible, skipping: {selector}")
            
            # Verify all fields are empty
            for selector in selectors:
                field = self.page.locator(selector)
                if field.is_visible():
                    value = field.input_value()
                    if value.strip():
                        self.logger.log(f"Warning: Field {selector} still has value: '{value}'")
                        # Force clear again
                        field.clear()
                        field.fill("")
            
            self.logger.log("Search fields cleared successfully")
        except Exception as e:
            self.logger.log(f"Error clearing search fields: {str(e)}")
            self.take_screenshot("clear_fields_error")
    
    def _click_search_and_evaluate(self) -> bool:
        """Click search button and evaluate results.

        Returns:
            bool: True if member was found and selected, False otherwise
        """
        try:
            self.logger.log("Clicking search button...")
            self.page.locator("#member-search-search-button").click()
            self.page.wait_for_timeout(500)  # Let DOM settle

            selector = "#member-search-result-name-data"
            start = time.time()
            timeout_seconds = 5

            while time.time() - start < timeout_seconds:
                locator = self.page.locator(selector).first
                if locator.is_visible() and locator.inner_text().strip():
                    self.logger.log(f"Member found after {round(time.time() - start, 2)}s, selecting result...")
                    locator.click()
                    return True
                self.page.wait_for_timeout(200)  # brief poll delay

            self.logger.log(f"Member not found after {round(time.time() - start, 2)}s")
            return False

        except Exception as e:
            self.logger.log(f"Error during search: {str(e)}")
            self.take_screenshot("search_error")
            return False


    
    def search_member_data(self, search_data: Dict) -> bool:
        """Search for a member using the provided search criteria.
        
        Args:
            search_data: Dictionary containing search criteria:
                - dos: Date of service (required)
                - first_name: First name (optional)
                - last_name: Last name (optional)
                - dob: Date of birth (optional)
                - ssn_last4: Last 4 of SSN (optional)
                - memberid: Member ID (optional)
                
        Returns:
            bool: True if member was found and selected, False otherwise
        """
        try:
            self.logger.log(f"Starting member search with data: {search_data}")

            self._clear_search_fields()

            if not self._enter_dos(search_data["dos"]):
                self.logger.log("Failed to enter date of service")
                return False
            
            if search_data.get('first_name'):
                self.page.locator("#member-search-first-name").fill(search_data['first_name'].strip())

            if search_data.get('last_name'):
                self.page.locator("#member-search-last-name").fill(search_data['last_name'].strip())

            if search_data.get('dob'):
                self.page.locator("#member-search-dob").fill(search_data['dob'].strip())

            if search_data.get('ssn_last4'):
                self.page.locator("#member-search-last-four").fill(search_data['ssn_last4'].strip())

            if search_data.get('memberid') and len(search_data['memberid']) >= 9:
                self.page.locator("#member-search-full-id").fill(search_data['memberid'].strip())

            return self._click_search_and_evaluate()
            
        except Exception as e:
            self.logger.log(f"Error during member search: {str(e)}")
            self.take_screenshot("member_search_error")
            return False
    
    def search_member(self, patient: Optional[Patient] = None) -> bool:
        """Search for a member using all combinations from :func:`build_search_data`.

        Args:
            patient: ``Patient`` instance to build search data from. If ``None``,
                the patient from the current context will be used.

        Returns:
            bool: ``True`` if a matching member was found, otherwise ``False``.
        """
        try:
            if patient is None:
                if self.context and getattr(self.context, "patient", None):
                    patient = self.context.patient
                else:
                    raise ValueError("No patient provided for member search")

            # Build the list of search combinations
            search_data_list = self.build_search_data(patient)
            self.logger.log(
                f"Starting member search with {len(search_data_list)} combinations..."
            )

            # Navigate to the search page first
            self.navigate_to_member_search()

            for i, search_data in enumerate(search_data_list, 1):
                self.logger.log(
                    f"Trying search combination {i} of {len(search_data_list)}..."
                )
                if self.search_member_data(search_data):
                    self.logger.log(f"Member found on attempt {i}")
                    return True
                self.logger.log(f"Search combination {i} did not find a match")
                sleep(1)

            self.logger.log("All search combinations failed to find a match")
            return False

        except Exception as e:
            self.logger.log_error(f"Error during member search: {str(e)}")
            self.take_screenshot("member_search_list_error")
            return False

    def build_search_data(self, patient: Patient) -> List[Dict]:
        """Create an ordered list of search dictionaries for a patient.

        The order is:
            1. Full member IDs
            2. Name and DOB (oldest to youngest)
            3. Name and last 4 of SSN/member ID

        Args:
            patient: ``Patient`` object containing scraped data. ``patient.insurance_data``
                must contain a ``dos`` key with the date of service.

        Returns:
            List of search dictionaries in preferred order.
        Raises:
            ValueError: If the date of service is missing from ``patient.insurance_data``.

        """
        search_data_list: List[Dict] = []

        dos = patient.insurance_data.get("dos")
        if not dos:
            raise ValueError("Date of service not found in patient.insurance_data")

        # Helper to normalize DOB strings
        def _normalize_dob(dob_str: Optional[str]) -> Optional[str]:
            if not dob_str:
                return None
            dob_str = dob_str.strip()
            try:
                dt = datetime.strptime(dob_str, "%m/%d/%Y")
                return dt.strftime("%m/%d/%Y")
            except ValueError:
                if re.fullmatch(r"\d{8}", dob_str):
                    try:
                        dt = datetime.strptime(dob_str, "%m%d%Y")
                        return dt.strftime("%m/%d/%Y")
                    except ValueError:
                        return None
            return None

        # Helper to clean name strings
        def _clean_name(name: Optional[str]) -> str:
            if not name:
                return ""
            # Remove punctuation and any leading/trailing non-letter characters
            name = re.sub(r"[;,]", "", name)
            name = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", name)
            return name.strip()

        # Helper to parse potential names from arbitrary text fields
        def _parse_name(text: Optional[str]):
            if not text or re.search(r"\d", text):
                return None
            txt = text.replace(";", ",").strip()
            if "," in txt:
                parts = [p.strip() for p in txt.split(",", 1)]
                if len(parts) >= 2:
                    last, first = parts[0], parts[1].split()[0]
                    return _clean_name(first), _clean_name(last)
            parts = txt.split()
            if len(parts) == 2:
                first, last = parts
                return _clean_name(first), _clean_name(last)
            return None

        # Collect unique name/DOB combinations
        combo_set = set()

        def add_combo(first: Optional[str], last: Optional[str], dob: Optional[str]):
            fn, ln = _clean_name(first), _clean_name(last)
            if fn and ln:
                combo_set.add((fn, ln, dob))

        # From provided search combinations
        for c in patient.insurance_data.get("search_combinations", []):
            add_combo(c.get("first_name"), c.get("last_name"), c.get("dob"))

        # Primary patient information
        add_combo(patient.first_name, patient.last_name, patient.dob)

        # Policy holder information
        holder = patient.insurance_data.get("policy_holder")
        holder_dob = patient.insurance_data.get("dob")
        if holder:
            if "," in holder:
                last, first = [part.strip() for part in holder.split(",", 1)]
            else:
                parts = holder.split()
                first = parts[0]
                last = parts[-1]
            add_combo(first, last, holder_dob)

        # Plan name may contain a person's name
        plan_name = patient.insurance_data.get("plan_name")
        parsed = _parse_name(plan_name)
        if parsed:
            add_combo(parsed[0], parsed[1], holder_dob)

        combos = [
            {"first_name": fn, "last_name": ln, "dob": dob}
            for fn, ln, dob in combo_set
        ]

        # ------------------------------------
        # Collect IDs for memberid/last4 searches
        ids: Set[str] = set()

        for value in patient.insurance_data.values():
            if isinstance(value, str):
                for digits in re.findall(r"\d{4,}", value):
                    ids.add(digits)

        full_ids = sorted({d for d in ids if len(d) >= 9})
        last4_list = sorted({d[-4:] for d in ids if len(d) >= 4})

        # 1. Full member ID searches
        for mid in full_ids:
            search_data_list.append({"dos": dos, "memberid": mid})

        # 2. Name + DOB (sorted oldest to youngest)
        dated_combos = []
        for combo in combos:
            dob_norm = _normalize_dob(combo.get("dob"))
            if dob_norm:
                try:
                    dt = datetime.strptime(dob_norm, "%m/%d/%Y")
                except ValueError:
                    dt = datetime.max
            else:
                dt = datetime.max
            dated_combos.append((dt, combo["first_name"], combo["last_name"], dob_norm))

        dated_combos.sort(key=lambda t: t[0])

        for _, fn, ln, dob_str in dated_combos:
            if dob_str:
                search_item = {
                    "dos": dos,
                    "first_name": fn,
                    "last_name": ln,
                    "dob": dob_str,
                }
                self.logger.log(f"Adding name+DOB search combination: {search_item}")
                search_data_list.append(search_item)

        # 3. Name + last4 searches
        for combo in combos:
            for last4 in last4_list:
                search_data_list.append(
                    {
                        "dos": dos,
                        "first_name": combo.get("first_name", ""),
                        "last_name": combo.get("last_name", ""),
                        "ssn_last4": last4,
                    }
                )

        # Remove duplicates while preserving order
        unique_data = []
        seen = set()
        for item in search_data_list:
            key = tuple(sorted(item.items()))
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        # --- LLM post-processing step ---
        instruction_file = Path(__file__).resolve().parents[2] / "core" / "ai_tools" / "agent_instructions" / "instruction.txt"
        if instruction_file.exists():
            try:
                with open(instruction_file, "r") as f:
                    instruction = f.read()

                self.logger.log(f"Dataset before LLM cleaning: {json.dumps(unique_data, indent=2)}")
                client = OllamaClient()
                prompt = f"{instruction}\n\n{json.dumps(unique_data)}"
                start_time = time.time()
                response = client.generate(prompt)
                elapsed = time.time() - start_time
                self.logger.log(f"Ollama model execution time: {elapsed:.2f} seconds")

                if response:
                    cleaned = json.loads(response)
                    if isinstance(cleaned, list):
                        unique_data = cleaned
                self.logger.log(f"Dataset after LLM cleaning: {json.dumps(unique_data, indent=2)}")
            except Exception as e:
                self.logger.log(f"LLM processing failed: {e}")
        self.logger.log('LLM post-processing complete')
        self.logger.log(str(unique_data))
        return unique_data

    


