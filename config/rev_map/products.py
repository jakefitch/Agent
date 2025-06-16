from playwright.sync_api import Page
from core.logger import Logger
from core.base import BasePage, PatientContext, Patient
from typing import Optional

class Products(BasePage):
    """Class for handling product operations in Revolution EHR."""
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://revolutionehr.com/static/#/legacy/inventory/products"
    
    def is_loaded(self) -> bool:
        """Check if the products page is loaded.
        
        Returns:
            bool: True if the page is loaded, False otherwise
        """
        try:
            self.logger.log("Checking if products page is loaded...")
            products_table = self.page.locator('[class="btn btn-xs btn-danger ng-scope"]').first.is_visible(timeout=5000)
            if products_table:
                self.logger.log("Products page is loaded")
                return True
                
            self.logger.log("Products page is not loaded")
            return False
            
        except Exception as e:
            self.logger.log_error(f"Failed to check if products page is loaded: {str(e)}")
            return False
    
    def navigate_to_products(self):
        """Navigate to the products inventory page."""
        try:
            self.logger.log("Navigating to products page...")
            self.page.goto(self.base_url)
            
            # Add a small delay to ensure the page has time to load
            self.page.wait_for_timeout(2000)  # 2 second delay
            
            # Wait for the products table to be visible
            
                
            self.logger.log("Successfully navigated to products page")
            
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to products page: {str(e)}")
            self.take_screenshot("Failed to navigate to products page")
            raise

    def get_wholesale_price(self, patient) -> str:
        """Get the wholesale price for a specific frame using patient data."""
        try:
            model = getattr(patient, 'frames', {}).get('model', None)
            if not model:
                self.logger.log("No model found in patient.frames, using default price")
                patient.frames['wholesale_price'] = '64.95'
                return '64.95'
            self.logger.log(f"Searching for wholesale price of frame model: {model}")

            # Clear any existing search
            clear_search = self.page.locator('form.mrgn-btm:nth-child(1) > div:nth-child(4) > button:nth-child(2)')
            clear_search.click()
            self.page.wait_for_timeout(1000)

            # Enter model in search field
            search_field = self.page.locator("[name='productSimpleSearch']")
            search_field.fill(model)
            search_field.press('Enter')
            self.page.wait_for_timeout(2000)

            # Click on the frame link
            frame_link = self.page.locator(f"[uib-popover='{model}']")
            frame_link.click()
            self.page.wait_for_timeout(1000)

            # Get the wholesale price
            wholesale_field = self.page.locator('rev-currency-input input.form-control[type="text"]').nth(2)
            wholesale = wholesale_field.input_value()

            if wholesale:
                self.logger.log(f"Found wholesale price: {wholesale}")
                patient.frames['wholesale_price'] = wholesale
                return wholesale
            else:
                self.logger.log("No wholesale price found, using default")
                patient.frames['wholesale_price'] = '64.95'
                return '64.95'

        except Exception as e:
            self.logger.log_error(f"Failed to get wholesale price: {str(e)}")
            self.take_screenshot("Failed to get wholesale price")
            patient.frames['wholesale_price'] = '64.95'
            return '64.95'
        finally:
            self.close_product_tabs(close_all=True)

    def close_product_tabs(
        self,
        tab_name: Optional[str] = None,
        close_all: bool = True,
    ) -> int:
        """Close product detail tabs.

        Multiple product tabs may be open simultaneously.  This helper can
        close a specific tab by name, close all tabs, or by default close the
        most recently opened tab when ``close_all`` is ``False``.

        Args:
            tab_name: The label of the tab to close. Ignored if ``close_all``
                is ``True``.
            close_all: If ``True`` close all open product tabs.

        Returns:
            int: Number of tabs closed.
        """

        try:
            self.logger.log(
                f"Closing product tabs - name={tab_name}, all={close_all}"
            )

            tab_spans = self.page.locator(
                "ul.nav-tabs li.uib-tab span.ng-binding"
            )

            if close_all:
                count = tab_spans.count()
                for i in range(count - 1, -1, -1):
                    span = tab_spans.nth(i)
                    close_icon = span.locator("i.fa-close.close")
                    if close_icon.count() > 0:
                        close_icon.click()
                        span.wait_for(state="detached", timeout=5000)
                self.logger.log(f"Closed {count} product tab(s)")
                return count

            if tab_name:
                span = tab_spans.filter(has_text=tab_name)
                if span.count() == 0:
                    self.logger.log(f"Product tab {tab_name} not found")
                    return 0
                close_icon = span.locator("i.fa-close.close")
                close_icon.click()
                span.wait_for(state="detached", timeout=5000)
                self.logger.log(f"Closed product tab {tab_name}")
                return 1

            count = tab_spans.count()
            if count == 0:
                self.logger.log("No product tabs found to close")
                return 0

            span = tab_spans.nth(count - 1)
            tab_label = span.inner_text().strip()
            close_icon = span.locator("i.fa-close.close")
            close_icon.click()
            span.wait_for(state="detached", timeout=5000)
            self.logger.log(f"Closed last product tab {tab_label}")
            return 1

        except Exception as e:
            self.logger.log_error(f"Failed to close product tab(s): {str(e)}")
            self.take_screenshot("Failed to close product tab")
            raise
