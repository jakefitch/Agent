from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext
from typing import Optional
from .auth_page import AuthPage
from .claim_page import ClaimPage

class VspSession:
    """Class for managing VSP session and page interactions."""
    
    class _Pages:
        """Internal class for managing page objects."""
        
        def __init__(self, page: Page, logger: Logger):
            self.page = page
            self.logger = logger
            self.auth_page = AuthPage(page, logger)
            self.claim_page = ClaimPage(page, logger)
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        """Initialize the VSP session.
        
        Args:
            page: Playwright page instance
            logger: Logger instance for logging operations
            context: Optional PatientContext for patient-specific operations
        """
        self.page = page
        self.logger = logger
        self.context = context
        self.pages = self._Pages(page, logger)
    
    def __getattr__(self, name):
        """Delegate attribute access to self.pages.
        
        This allows direct access to page objects through the session instance.
        For example: vsp.claim_page instead of vsp.pages.claim_page
        """
        return getattr(self.pages, name) 