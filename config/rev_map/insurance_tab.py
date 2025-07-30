from playwright.sync_api import Page
from core.logger import Logger
from datetime import datetime
from core.base import BasePage, PatientContext, Patient
from typing import Optional
import random
from time import sleep


class InsuranceTab(BasePage):
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)

    def _validate_patient_required(self):
        if not self.context or not self.context.patient:
            raise ValueError("InsuranceTab requires a patient context to be set")

    def close_insurance_tab(self):
        """Close the Insurance tab in the patient menu."""
        try:
            self.page.locator('[data-test-id="insuranceCloseButton"]').click()
            self.logger.log("Closed Insurance tab")
        except Exception as e:
            self.logger.log_error(f"Failed to close Insurance tab: {str(e)}")
            self.take_screenshot("Failed to close Insurance tab")
            raise

    def select_insurance(self, insurance_name: str, select_mode: str = 'random', filters: Optional[dict] = None, wait_timeout: int = 2000) -> bool:
        """Select an insurance row in the grid.

        This method searches the insurance grid for rows whose company name
        contains ``insurance_name``.  Additional column values can be filtered
        by supplying a ``filters`` dictionary where the key is the ``col-id``
        attribute from the table and the value is the text that should be
        present in those columns.  When more than one row matches, the row is
        chosen based on ``select_mode`` which accepts ``'first'`` (default),
        ``'random'`` or ``'all'``.

        Parameters
        ----------
        insurance_name: str
            Partial name of the insurance company to look for.
        select_mode: str, optional
            How to choose between multiple matches: ``'first'`` (default),
            ``'random'`` or ``'all'``.
        filters: dict, optional
            Mapping of additional column ``col-id`` values to text that must be
            present in those columns.  For example ``{'priority.value': 'Primary'}``.
        wait_timeout: int, optional
            Time in milliseconds to wait for the grid to appear.

        Returns
        -------
        bool
            ``True`` if a matching row was clicked, ``False`` otherwise.
        """
        sleep(1)
        try:
            self.logger.log(f"Selecting insurance: {insurance_name} with filters {filters}")

            # Handle multiple containers by searching through all of them
            containers = self.page.locator('.ag-center-cols-container')
            container_count = containers.count()
            
            if container_count == 0:
                self.logger.log_error("No insurance grid containers found")
                return False
            
            self.logger.log(f"Found {container_count} insurance grid containers, searching through all of them")
            
            all_matches = []
            
            # Search through each container
            for container_index in range(container_count):
                try:
                    container = containers.nth(container_index)
                    self.logger.log(f"Searching container {container_index + 1} of {container_count}")
                    
                    self.logger.log(f"Waiting for container {container_index + 1} to be visible...")
                    container.wait_for(state="visible", timeout=wait_timeout)
                    self.logger.log(f"Container {container_index + 1} is now visible")

                    rows = container.locator('.ag-row')
                    row_count = rows.count()
                    self.logger.log(f"Found {row_count} insurance rows in container {container_index + 1}")
                    
                    for i in range(row_count):
                        try:
                            row = rows.nth(i)
                            
                            # Try multiple approaches to find the insurance name cell
                            name_cell = None
                            cell_text = ""
                            
                            # Approach 1: Try the original col-id="0" span
                            try:
                                name_cell = row.locator('[col-id="0"] span').first
                                if name_cell.count() > 0:
                                    cell_text = name_cell.inner_text().strip()
                                    self.logger.log(f"Container {container_index + 1}, Row {i+1}: Found name using col-id='0' span: '{cell_text}'")
                            except Exception as e:
                                self.logger.log(f"Container {container_index + 1}, Row {i+1}: Failed to find name using col-id='0' span: {str(e)}")
                            
                            # Approach 2: If first approach failed, try finding any span in the first column
                            if not cell_text:
                                try:
                                    name_cell = row.locator('span').first
                                    if name_cell.count() > 0:
                                        cell_text = name_cell.inner_text().strip()
                                        self.logger.log(f"Container {container_index + 1}, Row {i+1}: Found name using first span: '{cell_text}'")
                                except Exception as e:
                                    self.logger.log(f"Container {container_index + 1}, Row {i+1}: Failed to find name using first span: {str(e)}")
                            
                            # Approach 3: If still no text, try getting the entire row text
                            if not cell_text:
                                try:
                                    cell_text = row.inner_text().strip()
                                    self.logger.log(f"Container {container_index + 1}, Row {i+1}: Using entire row text: '{cell_text}'")
                                except Exception as e:
                                    self.logger.log(f"Container {container_index + 1}, Row {i+1}: Failed to get row text: {str(e)}")
                                    continue
                            
                            if not cell_text:
                                self.logger.log(f"Container {container_index + 1}, Row {i+1}: No text found, skipping")
                                continue
                                
                            if insurance_name.lower() not in cell_text.lower():
                                continue

                            # Skip rows that contain "New" as they are likely new/placeholder entries
                            if "New" in cell_text:
                                self.logger.log(f"Container {container_index + 1}, Row {i+1}: Skipping row containing 'New': '{cell_text}'")
                                continue

                            # Apply additional column filters if provided
                            if filters:
                                matched = True
                                for col_id, expected in filters.items():
                                    col = row.locator(f'[col-id="{col_id}"]').first
                                    if col.count() == 0:
                                        matched = False
                                        break
                                    value = col.inner_text().strip()
                                    if expected.lower() not in value.lower():
                                        matched = False
                                        break
                                if not matched:
                                    continue

                            all_matches.append(row)
                            self.logger.log(f"Found matching insurance in container {container_index + 1}, row {i+1}: {cell_text}")
                            
                        except Exception as e:
                            self.logger.log_error(f"Failed to process container {container_index + 1}, row {i+1}: {str(e)}")
                            continue
                            
                except Exception as e:
                    self.logger.log_error(f"Failed to process container {container_index + 1}: {str(e)}")
                    continue

            if not all_matches:
                self.logger.log(f"No insurance found matching: {insurance_name} with filters {filters}")
                return False

            self.logger.log(f"Found {len(all_matches)} insurance(s) matching: {insurance_name} across all containers")

            selected_rows = all_matches
            if select_mode == 'random':
                self.logger.log("Selecting random insurance")
                selected_rows = [random.choice(all_matches)]
            elif select_mode == 'first':
                selected_rows = [all_matches[0]]

            for row in selected_rows:
                row.click()
                
                self.logger.log(f"Clicked insurance: {insurance_name}")

                # Validate the selection was successful
                self.page.wait_for_timeout(2000)
                
                company_element = self.page.locator('[data-test-id="basicInformationCompanyFormGroup"]')
                if company_element.is_visible(timeout=3000):
                    self.logger.log("Insurance selection validated successfully")
                    return True
                else:
                    self.logger.log("Insurance selection validation failed, continuing to next option")
                    

            return False
        except Exception as e:
            self.logger.log_error(f"Failed to select insurance by name: {str(e)}")
            self.take_screenshot("Failed to select insurance by name")
            return False

    def click_back_to_all_insurances(self):
        """Click the 'Back to All Insurances' button."""
        try:
            self.page.locator('[data-test-id="allPatientInsurancesButton"]').click()
            self.logger.log("Clicked 'Back to All Insurances' button")
        except Exception as e:
            self.logger.log_error(f"Failed to click 'Back to All Insurances' button: {str(e)}")
            self.take_screenshot("Failed to click 'Back to All Insurances' button")
            raise

    def click_add_insurance(self):
        """Click the 'Add Insurance' button."""
        try:
            self.page.locator('[data-test-id="insuranceAddButton"]').click()
            self.logger.log("Clicked 'Add Insurance' button")
        except Exception as e:
            self.logger.log_error(f"Failed to click 'Add Insurance' button: {str(e)}")
            self.take_screenshot("Failed to click 'Add Insurance' button")
            raise

    def select_insurance_company_in_dialog(self, company_name, dialog_name='ej2_dropdownlist_50'):
        """
        Select an insurance company from the dropdown in the add insurance dialog.
        Args:
            company_name (str): The name (or partial name) of the insurance company to select.
            dialog_name (str): The accessible name of the dialog (default: 'ej2_dropdownlist_50').
        """
        try:
            dialog = self.page.get_by_role('dialog', name=dialog_name)
            combobox = dialog.get_by_role('combobox')
            combobox.click()
            combobox.fill(company_name)
            combobox.press('Enter')
            self.logger.log(f"Selected insurance company '{company_name}' in dialog '{dialog_name}'")
        except Exception as e:
            self.logger.log_error(f"Failed to select insurance company '{company_name}' in dialog '{dialog_name}': {str(e)}")
            self.take_screenshot(f"Failed to select insurance company in dialog {dialog_name}")
            raise 

    def fill_insurance(self, company_name=None, priority=None, insurance_type=None, plan_name=None, policy_holder=None, dob=None, policy_number=None, group_number=None, authorization=None, dialog_name='ej2_dropdownlist_50'):
        """
        Fill out the add insurance dialog, optionally scraping values if not provided.
        Args:
            company_name (str): Insurance company to select (partial match).
            priority (str): 'Primary' or 'Secondary'.
            insurance_type (str): 'Medical', 'Vision', or 'Medical & Vision'.
            plan_name (str): Plan name to fill.
            policy_holder (str): Policy holder name to select (partial match).
            dob (str): Date of birth to fill.
            policy_number (str): Policy number to fill.
            group_number (str): Group number to fill.
            authorization (str): Authorization number to fill.
            dialog_name (str): Dialog accessible name (default: 'ej2_dropdownlist_50').
        Returns:
            dict: Scraped values for any fields not filled.
        """
        scraped = {}
        try:
            # Company
            try:
                if company_name:
                    dialog = self.page.get_by_role('dialog', name=dialog_name)
                    combobox = dialog.get_by_role('combobox')
                    combobox.click()
                    combobox.fill(company_name)
                    combobox.press('Enter')
                    self.logger.log(f"Selected insurance company '{company_name}' in dialog '{dialog_name}'")
                else:
                    dialog = self.page.get_by_role('dialog', name=dialog_name)
                    combobox = dialog.get_by_role('combobox')
                    scraped['company_name'] = combobox.input_value() if hasattr(combobox, 'input_value') else combobox.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle company name field: {str(e)}")
                self.take_screenshot("Failed to handle company name field")
                raise

            # Priority (Primary/Secondary)
            try:
                if priority:
                    cb = self.page.get_by_role('combobox', name='Primary')
                    cb.click()
                    self.page.get_by_role('option', name=priority).click()
                    self.logger.log(f"Set priority to {priority}")
                else:
                    cb = self.page.get_by_role('combobox', name='Primary')
                    scraped['priority'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle priority field: {str(e)}")
                self.take_screenshot("Failed to handle priority field")
                raise

            # Insurance Type
            try:
                if insurance_type:
                    cb = self.page.locator('[data-test-id="basicInformationTypeFormGroup"]').get_by_role('combobox')
                    cb.click()
                    self.page.get_by_role('option', name=insurance_type).click()
                    self.logger.log(f"Set insurance type to {insurance_type}")
                else:
                    cb = self.page.locator('[data-test-id="basicInformationTypeFormGroup"]').get_by_role('combobox')
                    scraped['insurance_type'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle insurance type field: {str(e)}")
                self.take_screenshot("Failed to handle insurance type field")
                raise

            # Plan Name
            try:
                if plan_name:
                    tb = self.page.locator('[data-test-id="basicInformationPlanFormGroup"]').get_by_role('textbox')
                    tb.click()
                    tb.fill(plan_name)
                    self.logger.log(f"Filled plan name: {plan_name}")
                else:
                    tb = self.page.locator('[data-test-id="basicInformationPlanFormGroup"]').get_by_role('textbox')
                    scraped['plan_name'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle plan name field: {str(e)}")
                self.take_screenshot("Failed to handle plan name field")
                raise

            # Policy Holder
            try:
                if policy_holder:
                    holder = self.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"]').get_by_text(policy_holder)
                    holder.click()
                    self.logger.log(f"Selected policy holder: {policy_holder}")
                else:
                    holder_element = self.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"] .form-control-static')
                    raw_holder = holder_element.inner_text().strip()
                    scraped['policy_holder'] = ' '.join(reversed(raw_holder.split(', '))) if ', ' in raw_holder else raw_holder
                    self.logger.log(f"Successfully scraped policy holder: {scraped['policy_holder']}")
            except Exception as e:
                self.logger.log_error(f"Failed to handle policy holder field: {str(e)}")
                self.take_screenshot("Failed to handle policy holder field")
                raise

            # DOB
            try:
                if dob:
                    dob_field = self.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"]')
                    dob_field.click()
                    dob_field.fill(dob)
                    self.logger.log(f"Filled DOB: {dob}")
                else:
                    dob_field = self.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"]')
                    scraped['dob'] = dob_field.input_value() if hasattr(dob_field, 'input_value') else dob_field.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle DOB field: {str(e)}")
                self.take_screenshot("Failed to handle DOB field")
                raise

            # Policy Number
            try:
                if policy_number:
                    tb = self.page.locator('[data-test-id="basicInformationPolicyNumberFormGroup"]').get_by_role('textbox')
                    tb.click()
                    tb.fill(policy_number)
                    self.logger.log(f"Filled policy number: {policy_number}")
                else:
                    tb = self.page.locator('[data-test-id="basicInformationPolicyNumberFormGroup"]').get_by_role('textbox')
                    scraped['policy_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle policy number field: {str(e)}")
                self.take_screenshot("Failed to handle policy number field")
                raise

            # Group Number
            try:
                if group_number:
                    tb = self.page.locator('[data-test-id="basicInformationGroupNumberFormGroup"]').get_by_role('textbox')
                    tb.click()
                    tb.fill(group_number)
                    self.logger.log(f"Filled group number: {group_number}")
                else:
                    tb = self.page.locator('[data-test-id="basicInformationGroupNumberFormGroup"]').get_by_role('textbox')
                    scraped['group_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle group number field: {str(e)}")
                self.take_screenshot("Failed to handle group number field")
                raise

            # Authorization
            try:
                if authorization:
                    tb = self.page.locator('[data-test-id="individualBenefitsAuthorizationNumberFormGroup"]').get_by_role('textbox')
                    tb.click()
                    tb.fill(authorization)
                    self.logger.log(f"Filled authorization: {authorization}")
                else:
                    tb = self.page.locator('[data-test-id="individualBenefitsAuthorizationNumberFormGroup"]').get_by_role('textbox')
                    scraped['authorization'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()
            except Exception as e:
                self.logger.log_error(f"Failed to handle authorization field: {str(e)}")
                self.take_screenshot("Failed to handle authorization field")
                raise

            self.logger.log("Filled/scraped insurance dialog fields")
            return scraped
        except Exception as e:
            self.logger.log_error(f"Failed to fill/scrape insurance dialog: {str(e)}")
            self.take_screenshot("Failed to fill/scrape insurance dialog")
            raise 

    def scrape_insurance(self, patient: Optional[Patient] = None):
        """Scrape insurance information for a patient and store it.

        Args:
            patient: Optional patient object. If not provided, the method will
            attempt to use ``self.context.patient``. If neither is available,
            scraping will still proceed but the results will only be returned.
        """

        # Resolve the patient from arguments or context if available
        patient_obj = patient or getattr(self.context, "patient", None)
        if patient_obj:
            self.logger.log(
                f"Scraping insurance for {patient_obj.first_name} {patient_obj.last_name}"
            )
        else:
            self.logger.log(
                "Scraping insurance with no patient information provided"
            )
        scraped = {}
        try:
            # Check if we're on the insurance details page
            try:
                # Look for insurance details page indicators
                details_indicator = self.page.locator('[data-test-id="insuranceAddButton"]')
                if not details_indicator.is_visible(timeout=5000):
                    self.logger.log_error("Not on insurance details page. Please select an insurance first.")
                    self.take_screenshot("Not on insurance details page")
                    raise Exception("Not on insurance details page")
            except Exception as e:
                self.logger.log_error(f"Failed to verify insurance details page: {str(e)}")
                self.take_screenshot("Failed to verify insurance details page")
                raise
            sleep(2)
            # Priority (dropdown)
            try:
                priority_element = self.page.locator('[data-test-id="basicInformationPriorityFormGroup"] .e-input')
                if priority_element.count() > 0:
                    scraped['priority'] = priority_element.get_attribute('value')
                    self.logger.log(f"Successfully scraped priority: {scraped['priority']}")
                else:
                    self.logger.log_error("Priority element not found")
                    scraped['priority'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape priority field: {str(e)}")
                scraped['priority'] = None

            # Insurance Type (dropdown)
            try:
                type_element = self.page.locator('[data-test-id="basicInformationTypeFormGroup"] .e-input')
                if type_element.count() > 0:
                    scraped['insurance_type'] = type_element.get_attribute('value')
                    self.logger.log(f"Successfully scraped insurance type: {scraped['insurance_type']}")
                else:
                    self.logger.log_error("Insurance type element not found")
                    scraped['insurance_type'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape insurance type field: {str(e)}")
                scraped['insurance_type'] = None

            # Plan Name (text input)
            try:
                plan_element = self.page.locator('[formcontrolname="planName"]')
                if plan_element.count() > 0:
                    scraped['plan_name'] = plan_element.evaluate('el => el.value')
                    self.logger.log(f"Successfully scraped plan name: {scraped['plan_name']}")
                else:
                    self.logger.log_error("Plan name element not found")
                    scraped['plan_name'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape plan name field: {str(e)}")
                scraped['plan_name'] = None

            # Policy Holder (static text)
            try:
                holder_element = self.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"] .form-control-static')
                if holder_element.count() > 0:
                    raw_holder = holder_element.inner_text().strip()
                    scraped['policy_holder'] = ' '.join(reversed(raw_holder.split(', '))) if ', ' in raw_holder else raw_holder
                    self.logger.log(f"Successfully scraped policy holder: {scraped['policy_holder']}")
                else:
                    self.logger.log_error("Policy holder element not found")
                    scraped['policy_holder'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape policy holder field: {str(e)}")
                scraped['policy_holder'] = None

            # DOB (static text)
            try:
                dob_element = self.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"] .form-control-static')
                if dob_element.count() > 0:
                    scraped['dob'] = dob_element.inner_text().strip()
                    self.logger.log(f"Successfully scraped DOB: {scraped['dob']}")
                else:
                    self.logger.log_error("DOB element not found")
                    scraped['dob'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape DOB field: {str(e)}")
                scraped['dob'] = None

            # Policy Number (text input)
            try:
                policy_element = self.page.locator('[formcontrolname="policyNumber"]')
                if policy_element.count() > 0:
                    scraped['policy_number'] = policy_element.evaluate('el => el.value')
                    self.logger.log(f"Successfully scraped policy number: {scraped['policy_number']}")
                else:
                    self.logger.log_error("Policy number element not found")
                    scraped['policy_number'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape policy number field: {str(e)}")
                scraped['policy_number'] = None

            # Group Number (text input)
            try:
                group_element = self.page.locator('[formcontrolname="groupNumber"]')
                if group_element.count() > 0:
                    scraped['group_number'] = group_element.evaluate('el => el.value')
                    self.logger.log(f"Successfully scraped group number: {scraped['group_number']}")
                else:
                    self.logger.log_error("Group number element not found")
                    scraped['group_number'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape group number field: {str(e)}")
                scraped['group_number'] = None

            # Authorization (text input)
            try:
                auth_element = self.page.locator('[formcontrolname="authorizationNumber"]')
                if auth_element.count() > 0:
                    scraped['authorization'] = auth_element.evaluate('el => el.value')
                    self.logger.log(f"Successfully scraped authorization: {scraped['authorization']}")
                else:
                    self.logger.log_error("Authorization element not found")
                    scraped['authorization'] = None
            except Exception as e:
                self.logger.log_error(f"Failed to scrape authorization field: {str(e)}")
                scraped['authorization'] = None

            # Store scraped data in patient object if available
            if patient_obj:
                try:
                    # Filter out None values before updating
                    filtered_scraped = {k: v for k, v in scraped.items() if v is not None}
                    if filtered_scraped:
                        patient_obj.insurance_data.update(filtered_scraped)
                        self.logger.log(f"Updated patient insurance data with {len(filtered_scraped)} fields")
                    else:
                        self.logger.log("No valid insurance data to update")
                except Exception as e:
                    self.logger.log_error(f"Failed to update patient insurance data: {str(e)}")

            return scraped
        except Exception as e:
            self.logger.log_error(f"Failed to scrape insurance dialog: {str(e)}")
            self.take_screenshot("Failed to scrape insurance dialog")
            raise

    def upload_insurance_document(self, file_path):
        """
        Upload a document to the insurance tab.
        
        Args:
            file_path (str): Path to the file to upload
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            # Click the upload button
            upload_button = self.page.locator('[data-test-id="patientDocumentsUploadButton"]')
            upload_button.wait_for(state="visible", timeout=10000)
            upload_button.click()
            self.logger.log("Clicked upload button")
            
            # Wait for and click on Documents folder
            docs_folder = self.page.locator('[data-test-id="folder-1"] div').filter(has_text='Documents').locator('div')
            docs_folder.wait_for(state="visible", timeout=10000)
            docs_folder.click()
            self.logger.log("Clicked Documents folder")
            
            # Wait for and click on Insurance folder
            insurance_folder = self.page.locator('[data-test-id="folder-230a01acc0ae40b6fa53f63d990766f29bc51af7"] div').first
            insurance_folder.wait_for(state="visible", timeout=10000)
            insurance_folder.click()
            self.logger.log("Clicked Insurance folder")
            
            # Wait for the upload container to be ready
            upload_container = self.page.locator('[data-test-id="fileUpload"]')
            upload_container.wait_for(state="attached", timeout=10000)
            
            # Get the file input (it's intentionally hidden)
            file_input = upload_container.locator('input[type="file"]')
            
            # Set the file path
            file_input.set_input_files(file_path)
            self.logger.log(f"Selected file: {file_path}")
            
            # Wait for and click the upload/submit button
            submit_button = self.page.locator('[data-test-id="fileModalUploadButton"]')
            submit_button.wait_for(state="visible", timeout=10000)
            submit_button.click()
            self.logger.log("Clicked submit button")
            
            
                
        except Exception as e:
            self.logger.log_error(f"Failed to upload document: {str(e)}")
            self.take_screenshot("Failed to upload document")
            return False 

    def list_insurance_documents(self):
        """
        List all documents in the insurance documents table.
        
        Returns:
            list: List of dictionaries containing document details (name, date, description) and action buttons
        """
        try:
            # Wait for the documents table to be present
            self.page.wait_for_selector('[data-test-id="patientDocumentsComponentTable"]', timeout=10000)
            
            # Get all rows in the table
            rows = self.page.locator('.e-row').all()
            documents = []
            
            for row in rows:
                try:
                    # Extract document details from each column using data-colindex
                    doc = {
                        'name': row.locator('[data-colindex="0"]').inner_text().strip(),
                        'date': row.locator('[data-colindex="1"]').inner_text().strip(),
                        'description': row.locator('[data-colindex="2"]').inner_text().strip(),
                        'actions': {
                            'preview': row.locator('[data-test-id="patientDocumentPreviewButton"]').is_visible(),
                            'download': row.locator('[data-test-id="patientDocumentDownloadButton"]').is_visible(),
                            'delete': row.locator('[data-test-id="patientDocumentDeleteButton"]').is_visible()
                        }
                    }
                    documents.append(doc)
                except Exception as e:
                    self.logger.log_error(f"Failed to extract document details from row: {str(e)}")
                    continue
            
            self.logger.log(f"Found {len(documents)} documents in the table")
            return documents
            
        except Exception as e:
            self.logger.log_error(f"Failed to list insurance documents: {str(e)}")
            self.take_screenshot("Failed to list insurance documents")
            return [] 

    def delete_insurance_documents(self, cutoff_date):
        """
        Delete all insurance documents that are older than or equal to the cutoff date.
        
        Args:
            cutoff_date (str): Date in MM/DD/YYYY format to use as cutoff
            
        Returns:
            tuple: (int, int) - (number of documents deleted, number of documents skipped)
        """
        try:
            # Convert cutoff date string to datetime object
            cutoff = datetime.strptime(cutoff_date, '%m/%d/%Y')
            
            # Get all documents
            documents = self.list_insurance_documents()
            deleted_count = 0
            skipped_count = 0
            
            for doc in documents:
                try:
                    # Convert document date to datetime object
                    doc_date = datetime.strptime(doc['date'], '%m/%d/%Y')
                    
                    # Check if document is older than or equal to cutoff date
                    if doc_date <= cutoff:
                        # Find all rows that match this document's name and date
                        rows = self.page.locator('.e-row').filter(
                            has_text=doc['name']
                        ).filter(
                            has_text=doc['date']
                        ).all()
                        
                        if not rows:
                            self.logger.log_error(f"Could not find row for document: {doc['name']} from {doc['date']}")
                            skipped_count += 1
                            continue
                        
                        # Process each matching row
                        for row in rows:
                            try:
                                # Click the delete button for this row
                                delete_button = row.locator('[data-test-id="patientDocumentDeleteButton"]')
                                if not delete_button.is_visible(timeout=5000):
                                    self.logger.log_error(f"Delete button not visible for document: {doc['name']} from {doc['date']}")
                                    skipped_count += 1
                                    continue
                                    
                                delete_button.click()
                                
                                # Wait for and confirm the delete action using role and text
                                try:
                                    confirm_button = self.page.get_by_role('button', name='Yes')
                                    confirm_button.wait_for(state="visible", timeout=5000)
                                    confirm_button.click()
                                    
                                    # Wait for the confirmation dialog to disappear
                                    confirm_button.wait_for(state="hidden", timeout=5000)
                                    
                                    self.logger.log(f"Deleted document: {doc['name']} from {doc['date']}")
                                    deleted_count += 1
                                    
                                    # Wait for the table to stabilize
                                    self.page.wait_for_timeout(2000)
                                    
                                except Exception as e:
                                    self.logger.log_error(f"Failed to confirm deletion for {doc['name']} from {doc['date']}: {str(e)}")
                                    # Try to close the dialog if it's still open
                                    try:
                                        cancel_button = self.page.get_by_role('button', name='No')
                                        if cancel_button.is_visible(timeout=2000):
                                            cancel_button.click()
                                    except:
                                        pass
                                    skipped_count += 1
                                    continue
                            except Exception as e:
                                self.logger.log_error(f"Failed to process row for document {doc['name']} from {doc['date']}: {str(e)}")
                                skipped_count += 1
                                continue
                    else:
                        self.logger.log(f"Skipped document: {doc['name']} from {doc['date']} (newer than cutoff)")
                        skipped_count += 1
                        
                except Exception as e:
                    self.logger.log_error(f"Failed to process document {doc['name']}: {str(e)}")
                    skipped_count += 1
                    continue
            
            self.logger.log(f"Document cleanup complete. Deleted: {deleted_count}, Skipped: {skipped_count}")
            return deleted_count, skipped_count
            
        except Exception as e:
            self.logger.log_error(f"Failed to delete old documents: {str(e)}")
            self.take_screenshot("Failed to delete old documents")
            return 0, 0 

    def delete_auth(self):
        """
        Deletes teh authorization from insurance details page
        """
        try:
            # Get the authorization field
            auth_field = self.page.locator('[formcontrolname="authorizationNumber"]')
            auth_value = auth_field.input_value()
            
            # If the authorization doesn't contain numbers, return None
            if not any(char.isdigit() for char in auth_value):
                self.logger.log("No valid authorization number found")
                return None
            
            # Clear the authorization field and set it to '0'
            auth_field.click()
            auth_field.fill('0')
            self.logger.log(f"Cleared authorization number: {auth_value}")
            
            # Save the changes
            save_button = self.page.locator('[data-test-id="insuranceDetailsSaveButton"]')
            save_button.click()
            self.logger.log("Saved insurance details")

            
        except Exception as e:
            self.logger.log_error(f"Failed to delete authorization: {str(e)}")
            self.take_screenshot("Failed to delete authorization")
            return None 