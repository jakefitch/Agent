import os
from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage
from typing import Optional
from .member_search_page import MemberSearch
from .claim_page import ClaimPage
from dotenv import load_dotenv

class VspSession(BasePage):
    """Class for managing VSP session and page interactions."""
    
    class _Pages:
        """Internal class for managing page objects."""
        
        def __init__(self, page: Page, logger: Logger):
            self.page = page
            self.logger = logger
            self.member_search = MemberSearch(page, logger)
            self.claim_page = ClaimPage(page, logger)
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        """Initialize the VSP session.
        
        Args:
            page: Playwright page instance
            logger: Logger instance for logging operations
            context: Optional PatientContext for patient-specific operations
        """
        super().__init__(page, logger, context)
        self.pages = self._Pages(page, logger)
        self.base_url = "https://eyefinity.com"  # Update with actual VSP login URL
    
    def __getattr__(self, name):
        """Delegate attribute access to self.pages.
        
        This allows direct access to page objects through the session instance.
        For example: vsp.claim_page instead of vsp.pages.claim_page
        """
        return getattr(self.pages, name)

    def login(self, location: str = "ama") -> bool:
        """Login to VSP portal.
        
        Args:
            location: Location to login to ('ama' for Amarillo or 'bgr' for Borger)
            
        Returns:
            bool: True if login was successful
        """
        try:
            self.logger.log("Starting VSP login process...")
            # Load credentials
            load_dotenv("/home/jake/Code/.env")
            ama_username = os.getenv("vsp_username")
            bgr_username = os.getenv("vsp_borger_username")
            vsp_password = os.getenv("vsp_password")
            
            if not all([ama_username, bgr_username, vsp_password]):
                raise ValueError("Missing VSP credentials")
            
            # Navigate to eyefinity and click login
            self.logger.log("Navigating to eyefinity...")
            self.page.goto("https://www.eyefinity.com")
            self.page.evaluate("document.querySelector('#eyefinity-lgn').click();")
            self.page.wait_for_timeout(3000)
            
            # Stop page loading
            self.page.evaluate("window.stop();")
            self.page.wait_for_timeout(2000)
            
            # Fill login form
            username = ama_username if location.lower() == "ama" else bgr_username
            self.logger.log(f"Logging in as {username}...")
            self.page.locator("#username").fill(username)
            self.page.locator("#password").fill(vsp_password)
            self.page.locator("#btnLogin").click()
            
            # Wait for login to complete
            self.page.wait_for_timeout(2000)
            
            # Navigate to member search
            self.logger.log("Navigating to member search...")
            self.page.goto("https://eclaim.eyefinity.com/secure/eInsurance/member-search")
            
            self.logger.log("Login successful")
            return True
            
        except Exception as e:
            self.logger.log(f"Login failed: {str(e)}")
            self.take_screenshot("VSP login error")
            return False 