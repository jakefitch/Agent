#/invoice_page.py

from core.base import BasePage, PatientContext
from playwright.sync_api import Page
from core.logger import Logger
from typing import Optional, List, Dict, Any
import time

class InvoicePage(BasePage):
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://revolutionehr.com/static/#/accounting/invoices/dashboard"

    def _validate_patient_required(self):
        if not self.context or not self.context.patient:
            self.logger.log("WARNING: Running without patient context.")

    def is_loaded(self):
        """Check if the invoice page is loaded."""
        try:
            # Check for the invoice table
            self.page.wait_for_selector('[data-test-id="invoiceDashboardReceiveInsurancePaymentButton"]', timeout=5000)
            self.logger.log("Invoice page is loaded")
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to verify invoice page load: {str(e)}")
            return False

    def navigate_to_invoices(self):
        """Navigate to the invoices page."""
        try:
            self.page.goto(self.base_url)
            self.logger.log("Navigated to invoices page")
            
            # Add a small delay to ensure the page has time to load
            self.page.wait_for_timeout(2000)  # 2 second delay
            
            # Wait for the page to be loaded
            if not self.is_loaded():
                raise Exception("Invoice page failed to load after navigation")
                
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to invoice page: {str(e)}")
            raise

    def search_invoice(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """Search for an invoice by its number."""
        try:
            # Enter invoice number
            self.page.locator('[data-test-id="invoiceId"]').fill(invoice_number)
            self.page.locator('[data-test-id="invoiceDashboardSearchButton"]').click()
            
            # Wait for results
            self.page.wait_for_selector('[data-test-id="invoiceTable"]', timeout=5000)
            
            # Check if invoice exists
            invoice_row = self.page.locator(f'[data-test-id="invoiceNumber"]:has-text("{invoice_number}")').first
            if not invoice_row.is_visible():
                self.logger.log(f"No invoice found with number: {invoice_number}")
                return None
            
            # Click on the invoice
            invoice_row.click()
            
            # Wait for details to load
            self.page.wait_for_selector('[data-test-id="invoiceDetails"]', timeout=5000)
            
            # Extract invoice details
            invoice = {
                'number': invoice_number,
                'date': self.page.locator('[data-test-id="invoiceDate"]').inner_text(),
                'amount': self.page.locator('[data-test-id="invoiceAmount"]').inner_text(),
                'status': self.page.locator('[data-test-id="invoiceStatus"]').inner_text(),
                'patient': self.page.locator('[data-test-id="invoicePatient"]').inner_text(),
                'items': []
            }
            
            # Get invoice items
            item_rows = self.page.locator('[data-test-id="invoiceItems"] tr').all()
            for row in item_rows:
                item = {
                    'description': row.locator('[data-test-id="itemDescription"]').inner_text(),
                    'quantity': row.locator('[data-test-id="itemQuantity"]').inner_text(),
                    'price': row.locator('[data-test-id="itemPrice"]').inner_text(),
                    'total': row.locator('[data-test-id="itemTotal"]').inner_text()
                }
                invoice['items'].append(item)
            
            self.logger.log(f"Retrieved details for invoice: {invoice_number}")
            return invoice
            
        except Exception as e:
            self.logger.log_error(f"Failed to search invoice: {str(e)}")
            raise

    def create_invoice(self, invoice_data: Dict[str, Any]) -> str:
        """Create a new invoice with the provided data."""
        try:
            # Click create invoice button
            self.page.locator('[data-test-id="createInvoice"]').click()
            
            # Wait for form to load
            self.page.wait_for_selector('[data-test-id="invoiceForm"]', timeout=5000)
            
            # Fill in invoice details
            self.page.locator('[data-test-id="invoiceDate"]').fill(invoice_data.get('date', ''))
            self.page.locator('[data-test-id="invoiceNotes"]').fill(invoice_data.get('notes', ''))
            
            # Add items
            for item in invoice_data.get('items', []):
                self.page.locator('[data-test-id="addItem"]').click()
                self.page.locator('[data-test-id="itemDescription"]').fill(item.get('description', ''))
                self.page.locator('[data-test-id="itemQuantity"]').fill(str(item.get('quantity', 1)))
                self.page.locator('[data-test-id="itemPrice"]').fill(str(item.get('price', 0)))
            
            # Save invoice
            self.page.locator('[data-test-id="saveInvoice"]').click()
            
            # Wait for save confirmation
            self.page.wait_for_selector('[data-test-id="saveConfirmation"]', timeout=5000)
            
            # Get the new invoice number
            invoice_number = self.page.locator('[data-test-id="invoiceNumber"]').inner_text()
            
            self.logger.log(f"Created new invoice: {invoice_number}")
            return invoice_number
            
        except Exception as e:
            self.logger.log_error(f"Failed to create invoice: {str(e)}")
            raise

    def delete_invoice(self, invoice_number: str) -> bool:
        """Delete an invoice by its number."""
        try:
            # Search for the invoice
            invoice = self.search_invoice(invoice_number)
            if not invoice:
                self.logger.log(f"Cannot delete non-existent invoice: {invoice_number}")
                return False
            
            # Click delete button
            self.page.locator('[data-test-id="deleteInvoice"]').click()
            
            # Confirm deletion
            self.page.locator('[data-test-id="confirmDelete"]').click()
            
            # Wait for deletion confirmation
            self.page.wait_for_selector('[data-test-id="deleteConfirmation"]', timeout=5000)
            
            self.logger.log(f"Deleted invoice: {invoice_number}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Failed to delete invoice: {str(e)}")
            raise

    def get_invoice_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all invoices."""
        try:
            # Wait for the invoice table
            self.page.wait_for_selector('[data-test-id="invoiceTable"]', timeout=5000)
            
            # Get all rows
            rows = self.page.locator('[data-test-id="invoiceTable"] tr').all()
            invoices = []
            
            for row in rows:
                try:
                    invoice = {
                        'number': row.locator('[data-test-id="invoiceNumber"]').inner_text(),
                        'date': row.locator('[data-test-id="invoiceDate"]').inner_text(),
                        'amount': row.locator('[data-test-id="invoiceAmount"]').inner_text(),
                        'status': row.locator('[data-test-id="invoiceStatus"]').inner_text(),
                        'patient': row.locator('[data-test-id="invoicePatient"]').inner_text()
                    }
                    invoices.append(invoice)
                except Exception as e:
                    self.logger.log_error(f"Failed to extract invoice details: {str(e)}")
                    continue
            
            self.logger.log(f"Retrieved summary of {len(invoices)} invoices")
            return invoices
            
        except Exception as e:
            self.logger.log_error(f"Failed to get invoice summary: {str(e)}")
            raise


