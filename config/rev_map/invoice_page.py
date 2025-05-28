#/invoice_page.py

from core.playwright_handler import get_handler
import re
from bs4 import BeautifulSoup
from core.base import ClaimItem

class InvoicePage:
    def __init__(self, handler):
        self.handler = handler
        self.base_url = "https://revolutionehr.com/static/#/accounting/invoices/dashboard"
    
    def navigate_to_invoices_page(self):
        """Navigate to the invoices dashboard page"""
        if not self.handler.is_running:
            self.handler.logger.log_error("Playwright session not running")
            return
        
        self.handler.logger.log("Navigating to invoices dashboard...")
        try:
            self.handler.goto(self.base_url)
            # Wait for the page to load completely
            self.handler.wait_for_selector('[data-test-id="invoiceDashboardReceiveCollectionsPaymentButton"]', timeout=10000)
            self.handler.logger.log("Successfully navigated to invoices dashboard")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to navigate to invoices dashboard: {str(e)}")
            self.handler.take_screenshot("Failed to navigate to invoices dashboard")
            raise

    def set_start_date(self, date_str):
        """Set the start date for invoice search"""
        self.handler.logger.log(f"Setting start date: {date_str}")
        try:
            self.handler.fill('#ej2-datepicker_8_input', date_str)
            self.handler.logger.log("Start date set successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to set start date: {str(e)}")
            self.handler.take_screenshot("Failed to set start date")
            raise

    def set_end_date(self, date_str):
        """Set the end date for invoice search"""
        self.handler.logger.log(f"Setting end date: {date_str}")
        try:
            self.handler.fill('#ej2-datepicker_9_input', date_str)
            self.handler.logger.log("End date set successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to set end date: {str(e)}")
            self.handler.take_screenshot("Failed to set end date")
            raise

    def enter_invoice_number(self, number):
        """Enter invoice number for search"""
        self.handler.logger.log(f"Entering invoice number: {number}")
        try:
            # First locate the form group, then filter for the div with 'Invoice #' text, then get the textbox
            form_group = self.handler.page.locator('[data-test-id="invoicesInvoiceNumberFormGroup"] div')
            filtered_div = form_group.filter(has_text='Invoice #')
            textbox = filtered_div.get_by_role('textbox')
            textbox.fill(number)
            self.handler.logger.log("Invoice number entered successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to enter invoice number: {str(e)}")
            self.handler.take_screenshot("Failed to enter invoice number")
            raise

    def enter_payor_name(self, name):
        """Enter payor name for search"""
        self.handler.logger.log(f"Entering payor name: {name}")
        try:
            # First locate the form group, then get the textbox within it
            form_group = self.handler.page.locator('[data-test-id="invoicesPayerNameFormGroup"]')
            textbox = form_group.get_by_role('textbox')
            textbox.fill(name)
            self.handler.logger.log("Payor name entered successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to enter payor name: {str(e)}")
            self.handler.take_screenshot("Failed to enter payor name")
            raise

    def select_location(self, office_location):
        """Select location from dropdown using keyboard simulation.
        
        This method uses a keyboard-based approach to handle complex dropdowns that may not
        respond well to direct element interaction. The approach is particularly useful for:
        - Syncfusion dropdowns
        - Dropdowns with complex JavaScript behavior
        - Dropdowns that require keyboard input for filtering/selection
        
        The sequence:
        1. Click the dropdown icon to focus the input
        2. Type the desired value using keyboard input
        3. Wait briefly for JavaScript to process the input
        4. Press Enter to confirm selection
        5. Tab out to trigger any blur events
        
        If you encounter similar issues with other dropdowns, try this pattern:
        - Use keyboard.type() instead of fill()
        - Add a small wait_for_timeout()
        - Include Enter and Tab for selection and focus management
        """
        self.handler.logger.log(f"Selecting location: {office_location}")
        try:
            # Click the dropdown to focus the input field
            self.handler.page.locator('[data-test-id="invoicesLocationFormGroup"] .e-input-group-icon').click()
            
            # Type location name
            self.handler.page.keyboard.type(office_location)
            
            # Wait a little for JS to register
            self.handler.page.wait_for_timeout(500)
            
            # Press Enter to "lock in" the selection
            self.handler.page.keyboard.press('Enter')
            
            # Tab to move out of the field
            self.handler.page.keyboard.press('Tab')
            
            self.handler.logger.log("Location selected successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select location: {str(e)}")
            self.handler.take_screenshot("Failed to select location")
            raise

    def select_payor_type(self, payor_type):
        
        self.handler.logger.log(f"Selecting payor type: {payor_type}")
        try:
            # Click the dropdown to focus the input field
            self.handler.page.locator('[data-test-id="invoicesPayerTypeFormGroup"] .e-input-group-icon').click()
            
            # Type payor type
            self.handler.page.keyboard.type(payor_type)
            
            # Wait a little for JS to register
            self.handler.page.wait_for_timeout(500)
            
            # Press Enter to "lock in" the selection
            self.handler.page.keyboard.press('Enter')
            
            # Tab to move out of the field
            self.handler.page.keyboard.press('Tab')
            
            self.handler.logger.log("Payor type selected successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select payor type: {str(e)}")
            self.handler.take_screenshot("Failed to select payor type")
            raise

    def click_search(self):
        """Click the search button"""
        self.handler.logger.log("Clicking search button")
        try:
            self.handler.click('[data-test-id="invoiceDashboardSearchButton"]')
            self.handler.logger.log("Search button clicked successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click search button: {str(e)}")
            self.handler.take_screenshot("Failed to click search button")
            raise

    def get_results_table(self): ## may not be useful anymore. 
        """Get the results table element"""
        self.handler.logger.log("Getting results table")
        try:
            # Get all table rows and filter for those that have text content
            table = self.handler.page.locator('[data-test-id="invoicesTable"] tr').filter(has_text='.')
            self.handler.logger.log("Results table found successfully")
            return table
        except Exception as e:
            self.handler.logger.log_error(f"Failed to get results table: {str(e)}")
            self.handler.take_screenshot("Failed to get results table")
            raise

    def is_loaded(self):
        """Check if the page is loaded"""
        try:
            return self.handler.page.locator('[data-test-id="invoiceDashboardSearchButton"]').is_visible()
        except Exception as e:
            self.handler.logger.log_error(f"Failed to check if page is loaded: {str(e)}")
            return False

    def search_invoice(self, invoice_number=None, start_date=None, end_date=None, payor=None, location=None):
        """Perform a complete invoice search with all parameters"""
        self.handler.logger.log("Starting invoice search")
        try:
            if start_date:
                self.set_start_date(start_date)
            if end_date:
                self.set_end_date(end_date)
            if invoice_number:
                self.enter_invoice_number(invoice_number)
            if payor:
                self.enter_payor_name(payor)
            if location:
                self.select_location(location)

            self.click_search()
            self.handler.logger.log("Invoice search completed successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to complete invoice search: {str(e)}")
            self.handler.take_screenshot("Failed to complete invoice search")
            raise

    def select_invoice_age(self, age_range):
        self.handler.logger.log(f"Selecting invoice age range: {age_range}")
        try:
            # Click the dropdown to focus the input field
            self.handler.page.locator('[data-test-id="invoicesInvoiceAgeFormGroup"] .e-input-group-icon').click()
            
            # Type age range
            self.handler.page.keyboard.type(age_range)
            
            # Wait a little for JS to register
            self.handler.page.wait_for_timeout(500)
            
            # Press Enter to "lock in" the selection
            self.handler.page.keyboard.press('Enter')
            
            # Tab to move out of the field
            self.handler.page.keyboard.press('Tab')
            
            self.handler.logger.log("Invoice age range selected successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select invoice age range: {str(e)}")
            self.handler.take_screenshot("Failed to select invoice age range")
            raise

    def set_approval_status(self, status):
        """Set approval status where status can be:
        "All" - clicks authorized-0
        "Authorized" - clicks authorized-1
        "Pending" - clicks authorized-2
        """
        status_map = {
            "All": "authorized-0",
            "Authorized": "authorized-1",
            "Pending": "authorized-2"
        }
        
        if status not in status_map:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(status_map.keys())}")
            
        self.handler.logger.log(f"Setting approval status: {status}")
        try:
            # Click the appropriate button based on status
            self.handler.page.locator(f'[data-test-id="{status_map[status]}"]').click()
            self.handler.logger.log("Approval status selected successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select approval status: {str(e)}")
            self.handler.take_screenshot("Failed to select approval status")
            raise

    def click_invoice_details_tab(self):
        """Click the Invoice Details tab"""
        self.handler.page.locator('[data-test-id="invoiceDetailsDetailTab"]').click()
        
    def click_additional_claim_info_tab(self):
        """Click the Additional Claim Info tab"""
        self.handler.page.locator('[data-test-id="invoiceDetailsAdditionalClaimInfoTab"]').click()
        
    def click_claim_history_tab(self):
        """Click the Claim History tab"""
        self.handler.page.locator('[data-test-id="invoiceDetailsClaimHistoryTab"]').click()
        
    def click_payment_history_tab(self):
        """Click the Payment History tab"""
        self.handler.page.locator('[data-test-id="invoiceDetailsPaymentHistoryTab"]').click()
        
    def click_statement_history_tab(self):
        """Click the Statement History tab"""
        self.handler.page.locator('[data-test-id="invoiceDetailsStatementHistoryTab"]').click()
        
    def click_docs_and_images_tab(self):
        """Click the Docs and Images tab"""
        self.handler.page.locator('[data-test-id="invoiceDetailsDocsAndImagesTab"]').click()
        
    def click_notes_tab(self):
        """Click the Notes tab"""
        self.handler.page.locator('[data-test-id="invoiceDetailsNotesTab"]').click()

    def click_pending_authorization(self):
        """Click the Pending authorization button"""
        self.handler.page.locator('[data-test-id="false"]').click()
        
    def click_authorized(self):
        """Click the Authorized button"""
        self.handler.page.locator('[data-test-id="true"]').click()

    def add_note(self, note_text):
        """Add a note to the current invoice.
        
        Args:
            note_text (str): The text of the note to add
        """
        print(f"Adding note: {note_text}")
        try:
            # Fill in the note text
            self.handler.page.get_by_role('textbox', name='textbox').fill(note_text)
            
            # Click the save button
            self.handler.page.locator('[data-test-id="saveAddEditNoteButton"]').click()
            
            print("Note saved successfully")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to add note: {str(e)}")
            self.handler.take_screenshot("Failed to add note")
            raise

    def process_patient_name(self, row):
        """Callback function to handle patient name in a row.
        Opens the patient details in a new tab, prints the name, and closes the tab.
        """
        print("Processing patient name")
        try:
            # Get the patient name cell using the specific col-id
            patient_cell = row.locator('[col-id="patientName"]')
            patient_name = patient_cell.inner_text()
            
            # Get the invoice ID
            invoice_id = row.locator('[col-id="id"]').inner_text()
            print(f"Processing patient: {patient_name} (Invoice: {invoice_id})")
            
            # Click to open new tab
            patient_cell.click()
            
            # Wait for new tab to be ready
            self.handler.wait_for_selector('[data-test-id="invoiceHeaderPreviewClaimButton"]')
            
            # Click through all tabs in sequence
            print("Clicking through all tabs...")
            self.click_invoice_details_tab()
            self.click_additional_claim_info_tab()
            self.click_claim_history_tab()
            self.click_payment_history_tab()
            self.click_statement_history_tab()
            self.click_docs_and_images_tab()
            self.click_notes_tab()
            
            # Add a note with the patient name and invoice ID
            note_text = f"Processed by automation - Patient: {patient_name}, Invoice: {invoice_id}"
            self.add_note(note_text)
            
            # Click authorization status buttons
            print("Clicking authorization status buttons...")
            self.click_pending_authorization()
            self.click_authorized()
            
            print(f"Completed processing tabs for: {patient_name}")
            
            # Close the tab by finding the specific tab with this invoice ID
            self.handler.page.get_by_role('tab', name=f"#{invoice_id}").get_by_title('Close').click()
            
            # Wait for main page to be ready
            self.handler.wait_for_selector('.ag-center-cols-container')
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to process patient: {str(e)}")
            self.handler.take_screenshot("Failed to process patient")
            raise

    def process_table_rows(self, action_callback=None):
        """Process all rows in the table across all pages.
        
        Args:
            action_callback: Function to execute on each row. If None, uses process_patient_name
        """
        try:
            page_num = 1
            while True:  # Loop until no more pages
                print(f"Processing page {page_num}")
                
                # Wait for AG Grid to be loaded
                self.handler.wait_for_selector('.ag-center-cols-container', timeout=10000)
                
                # Get current page rows using AG Grid selector
                rows = self.handler.page.locator('.ag-center-cols-container .ag-row').all()
                print(f"Found {len(rows)} rows on page {page_num}")
                
                if len(rows) == 0:
                    print("No rows found on page - waiting for content...")
                    self.handler.page.wait_for_timeout(2000)  # Give it a moment to load
                    rows = self.handler.page.locator('.ag-center-cols-container .ag-row').all()
                    print(f"After wait: Found {len(rows)} rows on page {page_num}")
                    
                    if len(rows) == 0:
                        print("Still no rows found - table may be empty or loading")
                        break
                
                # Process each row
                for i in range(len(rows)):
                    # Re-fetch the row to avoid stale elements
                    row = self.handler.page.locator('.ag-center-cols-container .ag-row').nth(i)
                    
                    # Use the provided callback if available, otherwise use default process_patient_name
                    if action_callback:
                        action_callback(row)
                    else:
                        self.process_patient_name(row)
                
                # Check for next page button with timeout
                try:
                    next_button = self.handler.page.get_by_role('navigation').get_by_title('Go to next page', exact=True)
                    
                    # Wait for button to be visible with timeout
                    if not next_button.is_visible(timeout=5000):
                        print("Next button not visible - reached last page")
                        break
                        
                    # Check if button is disabled
                    button_class = next_button.get_attribute('class', timeout=5000)
                    if 'e-disable' in button_class:
                        print("Next button is disabled - reached last page")
                        break
                        
                    print("Clicking next page button")
                    next_button.click()
                    
                    # Wait for table to reload
                    self.handler.wait_for_selector('.ag-center-cols-container', timeout=10000)
                    page_num += 1
                    
                except Exception as e:
                    print(f"Error checking next page button: {str(e)}")
                    print("Assuming we've reached the last page")
                    break
                
        except Exception as e:
            self.handler.logger.log_error(f"Failed to process table rows: {str(e)}")
            self.handler.take_screenshot("Failed to process table rows")
            raise

    def dummy_claim_review(self, row):
        """Dummy function to demonstrate callback functionality.
        Opens invoice, goes to notes tab, and adds a timestamped review note.
        
        Args:
            row: The row element to process
        """
        print("Starting dummy claim review")
        try:
            # Get the invoice ID before clicking
            invoice_id = row.locator('[col-id="id"]').inner_text()
            print(f"Processing invoice: {invoice_id}")
            
            # Click to open new tab
            row.locator('[col-id="patientName"]').click()
            
            # Wait for new tab to be ready
            self.handler.wait_for_selector('[data-test-id="invoiceHeaderPreviewClaimButton"]')
            
            # Go directly to notes tab
            self.click_notes_tab()
            
            # Click the Add Note button to open the textbox
            self.handler.page.locator('[data-test-id="notesAddButton"]').click()
            
            # Add timestamped note
            note_text = "reviewed claim"
            self.handler.page.get_by_role('textbox', name='textbox').fill(note_text)
            self.handler.page.locator('[data-test-id="saveAddEditNoteButton"]').click()
            
            print("Note added successfully")
            
            # Close the tab
            self.handler.page.get_by_role('tab', name=f"#{invoice_id}").get_by_title('Close').click()
            
            # Wait for main table to be ready
            self.handler.wait_for_selector('.ag-center-cols-container')
            
            print(f"Completed processing invoice: {invoice_id}")
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to process dummy claim review: {str(e)}")
            self.handler.take_screenshot("Failed to process dummy claim review")
            raise

    def check_for_document(self):
        """Check if any documents exist in the Documents and Images tab.
        
        Returns:
            bool: True if the document count badge exists (indicating documents are present)
        """
        try:
            # Wait for the documents tab to be present
            self.handler.wait_for_selector('[data-test-id="invoiceDetailsDocsAndImagesTab"]', timeout=10000)
            
            # Look for the badge that shows document count
            count_badge = self.handler.page.locator('[data-test-id="invoiceDetailsDocsAndImagesTab"] .badge.margin-left-xs')
            
            # Check if the badge exists
            if count_badge.is_visible(timeout=5000):
                return True
            else:
                return False
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to check document: {str(e)}")
            self.handler.take_screenshot("Failed to check document")
            return False

    def process_document_check(self, row):
        """Callback function to check for documents and handle workflow.
        If no document exists, it will execute a new function.
        If document exists, it will close and move to next invoice.
        
        Args:
            row: The row element to process
        """
        print("Starting document check workflow")
        try:
            # Get the invoice ID before clicking
            invoice_id = row.locator('[col-id="id"]').inner_text()
            print(f"Processing invoice: {invoice_id}")
            
            # Click to open new tab
            row.locator('[col-id="patientName"]').click()
            
            # Wait for new tab to be ready
            self.handler.wait_for_selector('[data-test-id="invoiceHeaderPreviewClaimButton"]')
            
            # Go to Documents and Images tab
            self.click_docs_and_images_tab()
            print('clicked docs and images tab')
            
            # Check for document preview
            exists = self.check_for_document()
            
            if not exists:
                print("No document found - executing additional processing")
                # Here you would call your new function
                # For example:
                # self.process_missing_document(invoice_id)
                # or
                # self.upload_required_document(invoice_id)
                print('no document found, submitting new claim!')
                
                
            else:
                print(f"Document found: {invoice_id} - proceeding to next invoice")
                # Add a note about the found document

            
            # Close the tab
            self.handler.page.get_by_role('tab', name=f"#{invoice_id}").get_by_title('Close').click()
            
            # Wait for main table to be ready
            self.handler.wait_for_selector('.ag-center-cols-container')
            
            print(f"Completed processing invoice: {invoice_id}")
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to process document check: {str(e)}")
            self.handler.take_screenshot("Failed to process document check")
            raise

    def click_patient_name_link(self):
        """Click the patient name link in the invoice header."""
        try:
            self.handler.page.locator('[data-test-id="invoiceHeaderPatientNameLink"]').click()
            self.handler.logger.log("Clicked patient name link successfully")
            # wait for the patient page to load
            self.handler.wait_for_selector('[data-test-id="patientHeaderDemographicList"]', timeout=10000)
            self.handler.logger.log("Patient page loaded successfully")
            #wait for a moment to allow a popup to have a chance to appear
            self.handler.page.wait_for_timeout(1000)
            
            #look for popup modal and close it
            try:
                close_button = self.handler.page.locator('[data-test-id="alertHistoryModalCloseButton"]')
                if close_button.is_visible(timeout=3000):  # 3 second timeout
                    close_button.click()
                    self.handler.logger.log("Closed alert history modal after patient selection")
            except Exception as e:
                self.handler.logger.log(f"Alert modal check after patient selection: {str(e)}")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click patient name link: {str(e)}")
            self.handler.take_screenshot("Failed to click patient name link")
            raise

    def click_invoice_tab(self, invoice_id):
        """Click the invoice tab for a specific invoice ID.
        
        Args:
            invoice_id (str): The invoice ID to identify the correct tab
        """
        try:
            self.handler.page.get_by_role('tab', name=f"#{invoice_id}").click()
            self.handler.logger.log(f"Clicked invoice tab for invoice: {invoice_id}")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click invoice tab: {str(e)}")
            self.handler.take_screenshot("Failed to click invoice tab")
            raise

    def scrape_invoice_details(self, patient, default_diagnosis='H52.223'):
        """Scrape invoice details from the current invoice page.
        
        Args:
            patient: Patient object to store the scraped data
            default_diagnosis: Default diagnosis code to use if none found (defaults to 'H52.223')
        """
        try:
            # Get the page content and parse with BeautifulSoup
            html_content = self.handler.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Locate the table
            table = soup.find('div', class_='e-gridcontent').find('table')

            # Initialize a list to store each row's data
            data_rows = []

            # Iterate through the table rows
            for row in table.find_all('tr', class_='e-row'):
                # Extract data from each cell in the row
                cells = row.find_all('td')
                row_data = {
                    'post_date': cells[1].get_text(strip=True),
                    'code': cells[2].get_text(strip=True),
                    'modifiers': cells[3].get_text(strip=True),
                    'diagnoses': cells[4].get_text(strip=True),
                    'description': cells[5].get_text(strip=True),
                    'Qty': cells[6].get_text(strip=True),
                    'Price': cells[10].get_text(strip=True),
                    'copay': cells[11].get_text(strip=True)
                }
                data_rows.append(row_data)

            # Merge duplicate codes
            from decimal import Decimal
            merged_data = {}

            for row in data_rows:
                code = row['code']
                if code in merged_data:
                    # Update existing entry
                    merged_data[code]['Qty'] = str(int(merged_data[code]['Qty']) + int(row['Qty']))
                    merged_data[code]['Price'] = str(Decimal(merged_data[code]['Price'].strip('$')) + Decimal(row['Price'].strip('$')))
                else:
                    # Add new entry
                    merged_data[code] = row
                    merged_data[code]['Price'] = row['Price'].strip('$')

            # Convert to ClaimItem objects and store in patient.claims
            patient.claims = []
            for row in merged_data.values():
                claim_item = ClaimItem(
                    vcode=row['code'],
                    description=row['description'],
                    billed_amount=float(row['Price'].strip('$')),
                    code=row['code'],
                    quantity=int(row['Qty']),
                    modifier=row['modifiers'] if row['modifiers'] else None
                )
                patient.claims.append(claim_item)

            # Store DOS in insurance_data
            if data_rows:
                patient.insurance_data['dos'] = data_rows[0]['post_date']

            # Get doctor name
            doctor_icon = soup.find('i', class_='fa-user-md')
            if doctor_icon:
                doctor_li = doctor_icon.find_parent('li')
                if doctor_li:
                    patient.medical_data['provider'] = doctor_li.get_text(strip=True)

            # Get location
            building_icon = soup.find('i', class_='fa-building')
            if building_icon:
                building_li = building_icon.find_parent('li')
                if building_li:
                    location = building_li.get_text(strip=True)
                    if location == "Borger":
                        patient.demographics['location'] = "Borger"
                    elif location == "Amarillo":
                        patient.demographics['location'] = "Amarillo"
                    else:
                        patient.demographics['location'] = location

            # Handle diagnoses
            if data_rows and data_rows[0]['diagnoses']:
                patient.medical_data['dx'] = data_rows[0]['diagnoses']
            else:
                patient.medical_data['dx'] = default_diagnosis
                # Click diagnosis button and search for H52. pattern
                self.handler.page.locator('[data-test-id="invoiceHeaderDiagnosisButton"]').click()
                
                # Wait for the diagnosis dialog to load
                self.handler.wait_for_selector('[data-test-id="selectADiagnosisCancelButton"]', timeout=10000)
                
                # Find diagnosis code
                diagnosis_elements = self.handler.page.locator('[revtooltip]').all()
                for element in diagnosis_elements:
                    text = element.inner_text()
                    if 'H52.' in text:
                        diagnosis_code_pattern = r'H\d{2}\.\d+'
                        match = re.search(diagnosis_code_pattern, text)
                        if match:
                            patient.medical_data['dx'] = match.group(0)
                            break
                
                # Close diagnosis dialog
                self.handler.page.locator('[data-test-id="selectADiagnosisCancelButton"]').click()

            self.handler.logger.log("Successfully scraped invoice details")
            
        except Exception as e:
            self.handler.logger.log_error(f"Failed to scrape invoice details: {str(e)}")
            self.handler.take_screenshot("Failed to scrape invoice details")
            raise


