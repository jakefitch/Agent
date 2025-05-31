from core.base import BasePage, PatientContext, Patient
from typing import Optional
from playwright.sync_api import Page
from core.logger import Logger

class Products(BasePage):
    """Class for handling product operations in Revolution EHR."""
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        """Initialize the Products class.
        
        Args:
            page: Playwright page instance
            logger: Logger instance for logging operations
            context: Optional PatientContext for patient-specific operations
        """
        super().__init__(page, logger, context)
        self.base_url = "https://revolutionehr.com/static/#/legacy/inventory/products"
    
    def is_loaded(self) -> bool:
        """Check if the products page is loaded.
        
        Returns:
            bool: True if the page is loaded, False otherwise
        """
        try:
            self.logger.log("Checking if products page is loaded...")
            products_table = self.page.locator('[data-test-id="productsTable"]').is_visible(timeout=5000)
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
            if not self.is_loaded():
                raise Exception("Products page failed to load")
                
            self.logger.log("Successfully navigated to products page")
            
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to products page: {str(e)}")
            self.take_screenshot("Failed to navigate to products page")
            raise

    def get_wholesale_price(self, frame_name: str) -> str:
        """Get the wholesale price for a specific frame.
        
        Args:
            frame_name: The name of the frame to search for
            
        Returns:
            str: The wholesale price of the frame, or '64.95' if not found
        """
        try:
            self.logger.log(f"Searching for wholesale price of frame: {frame_name}")
            
            # Clear any existing search
            clear_search = self.page.locator('form.mrgn-btm:nth-child(1) > div:nth-child(4) > button:nth-child(2)')
            clear_search.click()
            self.page.wait_for_timeout(1000)
            
            # Enter frame name in search field
            search_field = self.page.locator("[name='productSimpleSearch']")
            search_field.fill(frame_name)
            search_field.press('Enter')
            self.page.wait_for_timeout(2000)
            
            # Click on the frame link
            frame_link = self.page.locator(f"[uib-popover='{frame_name}']")
            frame_link.click()
            self.page.wait_for_timeout(1000)
            
            # Get the wholesale price
            wholesale_field = self.page.locator('/html/body/div[2]/div/div/div[8]/rev-inventory-dashboard/div/div/div/rev-inventory-products-dashboard/div/div[2]/div[2]/rev-inventory-product-tab-container/div[2]/div/div[1]/rev-inventory-product-details/form/div[1]/div/div[2]/div/rev-currency[2]/rev-form-control/div/div/rev-currency-input/div/input')
            wholesale = wholesale_field.input_value()
            
            if wholesale:
                self.logger.log(f"Found wholesale price: {wholesale}")
                return wholesale
            else:
                self.logger.log("No wholesale price found, using default")
                return '64.95'
                
        except Exception as e:
            self.logger.log_error(f"Failed to get wholesale price: {str(e)}")
            self.take_screenshot("Failed to get wholesale price")
            return '64.95'  # Return default price if anything fails 