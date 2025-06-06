from playwright.sync_api import Page
from core.logger import Logger
from core.base import BasePage, PatientContext, PatientManager
from typing import Optional
from .patient_page import PatientPage
from .invoice_page import InvoicePage
from .optical_order import OpticalOrder
from .products import Products
from .insurance_tab import InsuranceTab
from .claims_page import ClaimsPage
import os
import time

class RevSession:
    """Class for managing Revolution EHR session and page interactions."""
    
    class _Pages:
        """Internal class for managing page objects."""
        
        def __init__(
            self,
            page: Page,
            logger: Logger,
            patient_manager: PatientManager,
            context: Optional[PatientContext] = None,
        ):
            self.page = page
            self.logger = logger
            self.patient_page = PatientPage(page, logger, context)
            self.invoice_page = InvoicePage(
                page,
                logger,
                context,
                patient_manager,
            )
            self.optical_order = OpticalOrder(page, logger, context)
            self.products = Products(page, logger, context)
            self.insurance_tab = InsuranceTab(page, logger, context)
            self.claims_page = ClaimsPage(page, logger, context)
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        """Initialize the Revolution EHR session.
        
        Args:
            page: Playwright page instance
            logger: Logger instance for logging operations
            context: Optional PatientContext for patient-specific operations
        """
        self.page = page
        self.logger = logger
        self.context = context
        self.patient_manager = PatientManager()
        self.pages = self._Pages(page, logger, self.patient_manager, context)
    
    def login(self) -> None:
        """Log in to Revolution EHR using credentials from environment variables.
        
        Raises:
            Exception: If login fails at any step
        """
        # Get credentials from environment variables
        username = os.getenv('rev_username')
        password = os.getenv('rev_password')
        
        if not username or not password:
            raise Exception("Missing Revolution EHR credentials in environment variables")
        
        # Navigate to the login page
        self.page.goto("https://revolutionehr.com/static/")
        
        # Wait for and fill in the login form
        self.page.locator('[data-test-id="loginUsername"]').fill(username)
        self.page.locator('[data-test-id="loginPassword"]').fill(password)
        
        # Click the login button
        self.page.locator('[data-test-id="loginBtn"]').click()
        
        # Wait for navigation to complete
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)  # Additional small delay to ensure page is fully loaded
        
        self.logger.log("✅ Logged into RevolutionEHR")
    
    def __getattr__(self, name):
        """Delegate attribute access to self.pages.
        
        This allows direct access to page objects through the session instance.
        For example: rev.patient_page instead of rev.pages.patient_page
        """
        return getattr(self.pages, name) 