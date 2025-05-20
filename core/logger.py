import logging
from datetime import datetime
import os
from pathlib import Path

class Logger:
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.screenshots_dir = self.logs_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger('playwright')
        self.logger.setLevel(logging.INFO)
        
        # Create today's log file
        self.setup_log_file()
    
    def setup_log_file(self):
        """Create a new log file for today's date"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_dir / f"playwright_{today}.log"
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
    def log(self, message, level='info'):
        """Log a message with the specified level"""
        log_func = getattr(self.logger, level.lower())
        log_func(message)
    
    def log_error(self, message, screenshot_path=None):
        """Log an error with optional screenshot reference"""
        if screenshot_path:
            self.logger.error(f"{message} [Screenshot: {screenshot_path}]")
        else:
            self.logger.error(message)
    
    def get_screenshot_path(self):
        """Generate a unique screenshot path"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return self.screenshots_dir / f"error_{timestamp}.png"

# Global logger instance
_logger = None

def get_logger():
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger 