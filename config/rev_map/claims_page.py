from playwright.sync_api import Page
from core.logger import Logger
from core.base import BasePage, PatientContext
from typing import Optional

class ClaimsPage(BasePage):
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)

    def is_loaded(self):
        return self.page.locator("#claims_table").is_visible()

    def get_results_table(self):
        return self.page.locator("#claims_table")
