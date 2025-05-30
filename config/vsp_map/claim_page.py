from playwright.sync_api import Page
from core.base import Patient
from core.logger import Logger

class ClaimPage:
    """Handles claim-related operations in VSP portal."""
    
    def __init__(self, page: Page, logger: Logger):
        """Initialize claim page.
        
        Args:
            page: Playwright Page instance
            logger: Logger instance for logging operations
        """
        self.page = page
        self.logger = logger
    
    def submit_claim(self, patient: Patient) -> bool:
        """Submit a claim for a patient.
        
        Args:
            patient: Patient object containing claim data
            
        Returns:
            bool: True if claim was submitted successfully
        """
        try:
            self.logger.log("Submitting claim...")
            # Fill claim form with patient data
            self.page.locator('[data-test-id="firstName"]').fill(patient.first_name)
            self.page.locator('[data-test-id="lastName"]').fill(patient.last_name)
            self.page.locator('[data-test-id="dob"]').fill(patient.dob)
            
            # Submit claim
            self.page.locator('[data-test-id="submitClaim"]').click()
            
            # Wait for success message
            self.page.wait_for_selector('[data-test-id="claimSuccess"]', timeout=5000)
            self.logger.log("Claim submitted successfully")
            return True
            
        except Exception as e:
            self.logger.log(f"Failed to submit claim: {str(e)}")
            return False 