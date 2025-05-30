from playwright.sync_api import Page
import os
from dotenv import load_dotenv
from core.logger import Logger

class AuthPage:
    """Handles authentication operations in VSP portal."""
    
    def __init__(self, page: Page, logger: Logger):
        """Initialize auth page.
        
        Args:
            page: Playwright Page instance
            logger: Logger instance for logging operations
        """
        self.page = page
        self.logger = logger
    
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
            return False 