from core.base import BasePage, PatientContext
from playwright.sync_api import Page
from core.logger import Logger
from typing import Optional

class ClaimsPage(BasePage):
    """Class for handling claims operations in Revolution EHR."""
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://revolutionehr.com/static/#/claims"
    
    def navigate_to_claims(self):
        """Navigate to the claims dashboard."""
        try:
            self.page.goto(self.base_url)
            self.logger.log("Navigated to claims dashboard")
            
            # Add a small delay to ensure the page has time to load
            self.page.wait_for_timeout(2000)  # 2 second delay
            
            # Wait for the page to be loaded
            if not self.is_loaded():
                raise Exception("Claims page failed to load after navigation")
                
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to claims page: {str(e)}")
            raise

    def is_loaded(self):
        """Check if the claims page is loaded."""
        try:
            # Check for the claims table
            self.page.wait_for_selector('[data-test-id="claimsTable"]', timeout=5000)
            self.logger.log("Claims page is loaded")
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to verify claims page load: {str(e)}")
            return False

    def get_results_table(self):
        return self.page.locator("#claims_table")