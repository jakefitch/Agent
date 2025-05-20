from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv
from core.logger import get_logger
from core.stats_tracker import get_stats_tracker
from core.page_manager import PageManager
from functools import wraps

def track_function(func):
    """Decorator to track function success/failure"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            get_stats_tracker().track_function_call(func.__name__, True)
            return result
        except Exception as e:
            get_stats_tracker().track_function_call(func.__name__, False)
            raise
    return wrapper

class PlaywrightHandler:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.page = None
        self.context = None
        self._playwright = None
        self.is_running = False
        self.logger = get_logger()
        self.stats = get_stats_tracker()
        self.pages = None  # Will be initialized in start()

    @track_function
    def take_screenshot(self, error_message=None):
        """Take a screenshot and log it"""
        if not self.is_running:
            return None
        
        screenshot_path = self.logger.get_screenshot_path()
        self.page.screenshot(path=str(screenshot_path))
        
        if error_message:
            self.logger.log_error(error_message, screenshot_path)
        else:
            self.logger.log(f"Screenshot taken: {screenshot_path}")
        
        return screenshot_path

    @track_function
    def start(self):
        """Start the Playwright session with browser and page"""
        if self.is_running:
            self.logger.log("Playwright session already running", 'warning')
            return

        self.logger.log("Starting Playwright session...")
        try:
            self._playwright = sync_playwright().start()
            
            self.browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=['--start-maximized']
            )

            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080}
            )

            self.page = self.context.new_page()
            self.is_running = True
            
            # Initialize PageManager after session is running
            self.pages = PageManager(self)
            
            self.logger.log("Playwright session started successfully")
        except Exception as e:
            self.logger.log_error(f"Failed to start Playwright session: {str(e)}")
            self.take_screenshot("Failed to start Playwright session")
            raise

    @track_function
    def goto(self, url):
        """Navigate to a URL"""
        if not self.is_running:
            self.logger.log_error("Playwright session not running")
            return
        
        self.logger.log(f"Navigating to: {url}")
        try:
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
            self.logger.log("Navigation complete")
        except Exception as e:
            self.logger.log_error(f"Navigation failed: {str(e)}")
            self.take_screenshot("Navigation failed")
            raise

    @track_function
    def click(self, selector):
        """Click an element by selector"""
        if not self.is_running:
            self.logger.log_error("Playwright session not running")
            return
        
        self.logger.log(f"Clicking element: {selector}")
        try:
            self.page.locator(selector).click()
            self.logger.log("Click successful")
        except Exception as e:
            self.logger.log_error(f"Click failed: {str(e)}")
            self.take_screenshot("Click failed")
            raise

    @track_function
    def fill(self, selector, value):
        """Fill a form field by selector"""
        if not self.is_running:
            self.logger.log_error("Playwright session not running")
            return
        
        self.logger.log(f"Filling field: {selector}")
        try:
            self.page.locator(selector).fill(value)
            self.logger.log("Fill successful")
        except Exception as e:
            self.logger.log_error(f"Fill failed: {str(e)}")
            self.take_screenshot("Fill failed")
            raise

    @track_function
    def get_text(self, selector):
        """Get text content of an element"""
        if not self.is_running:
            self.logger.log_error("Playwright session not running")
            return None
        
        self.logger.log(f"Getting text from: {selector}")
        try:
            text = self.page.locator(selector).inner_text()
            self.logger.log("Text retrieved successfully")
            return text
        except Exception as e:
            self.logger.log_error(f"Failed to get text: {str(e)}")
            self.take_screenshot("Failed to get text")
            raise

    @track_function
    def wait_for_selector(self, selector, timeout=5000):
        """Wait for an element to appear"""
        if not self.is_running:
            self.logger.log_error("Playwright session not running")
            return
        
        self.logger.log(f"Waiting for element: {selector}")
        try:
            self.page.locator(selector).wait_for(timeout=timeout)
            self.logger.log("Element found")
        except Exception as e:
            self.logger.log_error(f"Element not found: {str(e)}")
            self.take_screenshot("Element not found")
            raise

    @track_function
    def login(self, username_selector, password_selector, username, password, login_button_selector):
        """
        Perform login action with the provided credentials and selectors
        
        Args:
            username_selector (str): CSS selector for the username input field
            password_selector (str): CSS selector for the password input field
            username (str): Username to enter
            password (str): Password to enter
            login_button_selector (str): CSS selector for the login button
        """
        if not self.is_running:
            self.logger.log_error("Playwright session not running")
            return
        
        self.logger.log("Attempting to log in...")
        try:
            # Wait for username field and enter username
            self.wait_for_selector(username_selector)
            self.fill(username_selector, username)
            self.logger.log("Username entered successfully")
            
            # Wait for password field and enter password
            self.wait_for_selector(password_selector)
            self.fill(password_selector, password)
            self.logger.log("Password entered successfully")
            
            # Wait for login button and click it
            self.wait_for_selector(login_button_selector)
            self.click(login_button_selector)
            self.logger.log("Login button clicked")
            
            # Wait for navigation to complete
            self.page.wait_for_load_state("networkidle")
            self.logger.log("Login process completed")
            
        except Exception as e:
            self.logger.log_error(f"Login failed: {str(e)}")
            self.take_screenshot("Login failed")
            raise

    @track_function
    def close(self):
        """Close the Playwright session"""
        if not self.is_running:
            self.logger.log("Playwright session not running", 'warning')
            return
        
        self.logger.log("Closing Playwright session...")
        try:
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()
            self.is_running = False
            self.logger.log("Playwright session closed")
        except Exception as e:
            self.logger.log_error(f"Failed to close session: {str(e)}")
            self.take_screenshot("Failed to close session")
            raise

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def print_stats(self):
        """Print current statistics"""
        overall_stats = self.stats.get_overall_stats()
        print("\n📊 Current Statistics:")
        print(f"Total Function Calls: {overall_stats['total_calls']}")
        print(f"Total Successes: {overall_stats['total_success']}")
        print(f"Total Failures: {overall_stats['total_failures']}")
        print(f"Overall Success Rate: {overall_stats['overall_success_rate']:.2f}%")
        
        print("\n🔍 Most Failed Functions:")
        for func_name, stats in self.stats.get_most_failed_functions():
            print(f"\n{func_name}:")
            print(f"  Calls: {stats['calls']}")
            print(f"  Success Rate: {stats['success_rate']:.2f}%")
            print(f"  Failures: {stats['failures']}")

# Global instance
_handler = None

def get_handler(headless=False):
    """Get or create a global Playwright handler instance"""
    global _handler
    if _handler is None:
        _handler = PlaywrightHandler(headless=headless)
        _handler.start()
    return _handler

def close_handler():
    """Close the global handler instance"""
    global _handler
    if _handler:
        _handler.close()
        _handler = None 