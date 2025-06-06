from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage
from typing import Optional, Dict, List
from time import sleep

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
    
    def is_loaded(self) -> bool:
        """Check if the member search page is loaded.
        
        Returns:
            bool: True if the page is loaded, False otherwise
        """
        try:
            # Check for the valid search combinations link with a 5-second timeout
            valid_search_link = self.page.locator('#member-search-valid-search-combinations-link')
            return valid_search_link.wait_for(state='visible', timeout=5000)
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
            
            # Wait for the page to load and verify
            if not self.is_loaded():
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
                
            dos_field.clear()
            for char in dos:
                dos_field.fill(char)
            return True
        except Exception as e:
            self.logger.log(f"Error entering DOS: {str(e)}")
            self.take_screenshot("dos_entry_error")
            return False
    
    def _clear_search_fields(self) -> None:
        """Clear all search fields."""
        try:
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
                    field.clear()
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
            
            # Wait for results
            result = self.page.locator("#member-search-result-name-data")
            if result.is_visible(timeout=5000):
                self.logger.log("Member found, selecting result...")
                result.click()
                return True
                
            self.logger.log("No member found")
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
            self.logger.log("Starting member search...")
            
            # Navigate to search page
            self.page.goto(self.base_url)
            if not self.is_loaded():
                self.logger.log("Member search page failed to load")
                return False
            
            # Enter DOS (required)
            if not self._enter_dos(search_data['dos']):
                self.logger.log("Failed to enter date of service")
                return False
            
            # Clear any existing values
            self._clear_search_fields()
            
            # Fill in available search fields
            if 'first_name' in search_data:
                self.page.locator("#member-search-first-name").fill(search_data['first_name'].strip())
            
            if 'last_name' in search_data:
                self.page.locator("#member-search-last-name").fill(search_data['last_name'].strip())
            
            if 'dob' in search_data:
                self.page.locator("#member-search-dob").fill(search_data['dob'].strip())
            
            if 'ssn_last4' in search_data:
                self.page.locator("#member-search-last-four").fill(search_data['ssn_last4'].strip())
            
            if 'memberid' in search_data and len(search_data['memberid']) >= 9:
                self.page.locator("#member-search-full-id").fill(search_data['memberid'].strip())
            
            # Attempt search
            return self._click_search_and_evaluate()
            
        except Exception as e:
            self.logger.log(f"Error during member search: {str(e)}")
            self.take_screenshot("member_search_error")
            return False
    
    def search_member(self, search_data_list: List[Dict]) -> bool:
        """Try multiple search combinations until a member is found.
        
        Args:
            search_data_list: List of dictionaries containing search criteria.
                Each dictionary should contain:
                - dos: Date of service (required)
                - first_name: First name (optional)
                - last_name: Last name (optional)
                - dob: Date of birth (optional)
                - ssn_last4: Last 4 of SSN (optional)
                - memberid: Member ID (optional)
                
        Returns:
            bool: True if member was found in any attempt, False if all attempts failed
        """
        try:
            self.logger.log(f"Starting member search with {len(search_data_list)} combinations...")
            
            for i, search_data in enumerate(search_data_list, 1):
                self.logger.log(f"Trying search combination {i} of {len(search_data_list)}...")
                
                if self.search_member_data(search_data):
                    self.logger.log(f"Member found on attempt {i}")
                    return True
                    
                self.logger.log(f"Search combination {i} did not find a match")
            
            self.logger.log("All search combinations failed to find a match")
            return False
            
        except Exception as e:
            self.logger.log(f"Error during member search list: {str(e)}")
            self.take_screenshot("member_search_list_error")
            return False
    
    