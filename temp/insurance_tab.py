import random
from datetime import datetime
from core.base import BasePage, PatientContext
from typing import Optional
from playwright.sync_api import Page
from core.logger import Logger

class InsuranceTab(BasePage):
    """Class for handling insurance operations in Revolution EHR."""
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        """Initialize the InsuranceTab class.
        
        Args:
            page: Playwright page instance
            logger: Logger instance for logging operations
            context: Optional PatientContext for patient-specific operations
        """
        super().__init__(page, logger, context)

    def _validate_patient_required(self):
        if not self.context or not self.context.patient:
            raise ValueError("InsuranceTab requires a patient context to be set")

    def close_insurance_tab(self):
        try:
            self.page.locator('[data-test-id="insuranceCloseButton"]').click()
            self.logger.log("Closed Insurance tab")
        except Exception as e:
            self.logger.log_error(f"Failed to close Insurance tab: {str(e)}")
            self.take_screenshot("Failed to close Insurance tab")
            raise

    def click_back_to_all_insurances(self):
        try:
            self.page.locator('[data-test-id="allPatientInsurancesButton"]').click()
            self.logger.log("Clicked 'Back to All Insurances' button")
        except Exception as e:
            self.logger.log_error(f"Failed to click 'Back to All Insurances' button: {str(e)}")
            self.take_screenshot("Failed to click 'Back to All Insurances' button")
            raise

    def click_add_insurance(self):
        try:
            self.page.locator('[data-test-id="insuranceAddButton"]').click()
            self.logger.log("Clicked 'Add Insurance' button")
        except Exception as e:
            self.logger.log_error(f"Failed to click 'Add Insurance' button: {str(e)}")
            self.take_screenshot("Failed to click 'Add Insurance' button")
            raise

    def delete_auth(self):
        try:
            auth_field = self.page.locator('[formcontrolname="authorizationNumber"]')
            auth_value = auth_field.input_value()
            if not any(char.isdigit() for char in auth_value):
                self.logger.log("No valid authorization number found")
                return None

            auth_field.click()
            auth_field.fill('0')
            self.logger.log(f"Cleared authorization number: {auth_value}")

            save_button = self.page.locator('[data-test-id="insuranceDetailsSaveButton"]')
            save_button.click()
            self.logger.log("Saved insurance details")

        except Exception as e:
            self.logger.log_error(f"Failed to delete authorization: {str(e)}")
            self.take_screenshot("Failed to delete authorization")
            return None

    def select_insurance(self, insurance_name, select_mode='random'):
        try:
            self.logger.log(f"Selecting insurance: {insurance_name}")
            rows = self.page.locator('.ag-center-cols-container .ag-row')
            matches = []
            for i in range(rows.count()):
                row = rows.nth(i)
                name_cell = row.locator('[col-id="0"] span')
                cell_text = name_cell.inner_text().strip()
                if insurance_name.lower() in cell_text.lower():
                    matches.append(row)

            if not matches:
                self.logger.log(f"No insurance found matching: {insurance_name}")
                return False

            self.logger.log(f"Found {len(matches)} insurance(s) matching: {insurance_name}")

            if select_mode == 'all':
                for row in matches:
                    row.click()
                    locator_str = "[col-id='0'] span"
                    value = row.locator(locator_str).inner_text().strip()
                    self.logger.log(f"Clicked insurance: {value}")
                return True
            else:
                chosen_row = random.choice(matches)
                chosen_row.click()
                locator = "[col-id='0'] span"
                text = chosen_row.locator(locator).inner_text().strip()
                self.logger.log(f"Clicked insurance: {text}")
                return True
        except Exception as e:
            self.logger.log_error(f"Failed to select insurance by name: {str(e)}")
            self.take_screenshot("Failed to select insurance by name")
            return False

    def select_insurance_company_in_dialog(self, company_name, dialog_name='ej2_dropdownlist_50'):
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
        scraped = {}
        try:
            dialog = self.page.get_by_role('dialog', name=dialog_name)
            combobox = dialog.get_by_role('combobox')
            if company_name:
                combobox.click()
                combobox.fill(company_name)
                combobox.press('Enter')
                self.logger.log(f"Selected insurance company '{company_name}' in dialog '{dialog_name}'")
            else:
                scraped['company_name'] = combobox.input_value() if hasattr(combobox, 'input_value') else combobox.inner_text()

            cb = self.page.get_by_role('combobox', name='Primary')
            if priority:
                cb.click()
                self.page.get_by_role('option', name=priority).click()
                self.logger.log(f"Set priority to {priority}")
            else:
                scraped['priority'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()

            cb = self.page.locator('[data-test-id="basicInformationTypeFormGroup"]').get_by_role('combobox')
            if insurance_type:
                cb.click()
                self.page.get_by_role('option', name=insurance_type).click()
                self.logger.log(f"Set insurance type to {insurance_type}")
            else:
                scraped['insurance_type'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()

            tb = self.page.locator('[data-test-id="basicInformationPlanFormGroup"]').get_by_role('textbox')
            if plan_name:
                tb.click()
                tb.fill(plan_name)
                self.logger.log(f"Filled plan name: {plan_name}")
            else:
                scraped['plan_name'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            if policy_holder:
                holder = self.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"]').get_by_text(policy_holder)
                holder.click()
                self.logger.log(f"Selected policy holder: {policy_holder}")
            else:
                holder_element = self.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"] .form-control-static')
                scraped['policy_holder'] = holder_element.inner_text().strip()

            dob_field = self.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"]')
            if dob:
                dob_field.click()
                dob_field.fill(dob)
                self.logger.log(f"Filled DOB: {dob}")
            else:
                scraped['dob'] = dob_field.input_value() if hasattr(dob_field, 'input_value') else dob_field.inner_text()

            tb = self.page.locator('[data-test-id="basicInformationPolicyNumberFormGroup"]').get_by_role('textbox')
            if policy_number:
                tb.click()
                tb.fill(policy_number)
                self.logger.log(f"Filled policy number: {policy_number}")
            else:
                scraped['policy_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            tb = self.page.locator('[data-test-id="basicInformationGroupNumberFormGroup"]').get_by_role('textbox')
            if group_number:
                tb.click()
                tb.fill(group_number)
                self.logger.log(f"Filled group number: {group_number}")
            else:
                scraped['group_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            tb = self.page.locator('[data-test-id="individualBenefitsAuthorizationNumberFormGroup"]').get_by_role('textbox')
            if authorization:
                tb.click()
                tb.fill(authorization)
                self.logger.log(f"Filled authorization: {authorization}")
            else:
                scraped['authorization'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            self.logger.log("Filled/scraped insurance dialog fields")
            return scraped
        except Exception as e:
            self.logger.log_error(f"Failed to fill/scrape insurance dialog: {str(e)}")
            self.take_screenshot("Failed to fill/scrape insurance dialog")
            raise

    def upload_insurance_document(self, file_path):
        try:
            upload_button = self.page.locator('[data-test-id="patientDocumentsUploadButton"]')
            upload_button.wait_for(state="visible", timeout=10000)
            upload_button.click()
            self.logger.log("Clicked upload button")

            docs_folder = self.page.locator('[data-test-id="folder-1"] div').filter(has_text='Documents').locator('div')
            docs_folder.wait_for(state="visible", timeout=10000)
            docs_folder.click()
            self.logger.log("Clicked Documents folder")

            insurance_folder = self.page.locator('[data-test-id="folder-230a01acc0ae40b6fa53f63d990766f29bc51af7"] div').first
            insurance_folder.wait_for(state="visible", timeout=10000)
            insurance_folder.click()
            self.logger.log("Clicked Insurance folder")

            upload_container = self.page.locator('[data-test-id="fileUpload"]')
            upload_container.wait_for(state="attached", timeout=10000)
            file_input = upload_container.locator('input[type="file"]')
            file_input.set_input_files(file_path)
            self.logger.log(f"Selected file: {file_path}")

            submit_button = self.page.locator('[data-test-id="fileModalUploadButton"]')
            submit_button.wait_for(state="visible", timeout=10000)
            submit_button.click()
            self.logger.log("Clicked submit button")

        except Exception as e:
            self.logger.log_error(f"Failed to upload document: {str(e)}")
            self.take_screenshot("Failed to upload document")
            return False

    def list_insurance_documents(self):
        try:
            self.wait_for_selector('[data-test-id="patientDocumentsComponentTable"]', timeout=10000)
            rows = self.page.locator('.e-row').all()
            documents = []

            for row in rows:
                try:
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
        try:
            cutoff = datetime.strptime(cutoff_date, '%m/%d/%Y')
            documents = self.list_insurance_documents()
            deleted_count = 0
            skipped_count = 0

            for doc in documents:
                try:
                    doc_date = datetime.strptime(doc['date'], '%m/%d/%Y')
                    if doc_date <= cutoff:
                        rows = self.page.locator('.e-row').filter(has_text=doc['name']).filter(has_text=doc['date']).all()

                        if not rows:
                            self.logger.log_error(f"Could not find row for document: {doc['name']} from {doc['date']}")
                            skipped_count += 1
                            continue

                        for row in rows:
                            try:
                                delete_button = row.locator('[data-test-id="patientDocumentDeleteButton"]')
                                if not delete_button.is_visible(timeout=5000):
                                    self.logger.log_error(f"Delete button not visible for document: {doc['name']} from {doc['date']}")
                                    skipped_count += 1
                                    continue

                                delete_button.click()

                                try:
                                    confirm_button = self.page.get_by_role('button', name='Yes')
                                    confirm_button.wait_for(state="visible", timeout=5000)
                                    confirm_button.click()
                                    confirm_button.wait_for(state="hidden", timeout=5000)

                                    self.logger.log(f"Deleted document: {doc['name']} from {doc['date']}")
                                    deleted_count += 1
                                    self.page.wait_for_timeout(2000)

                                except Exception as e:
                                    self.logger.log_error(f"Failed to confirm deletion for {doc['name']} from {doc['date']}: {str(e)}")
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

    def scrape_insurance(self):
        if not self.context or not self.context.patient:
            raise ValueError("No patient context set for insurance scraping")

        self.logger.log(f"Scraping insurance for {self.context.patient.first_name} {self.context.patient.last_name}")
        scraped = {}
        try:
            try:
                priority_element = self.page.locator('[data-test-id="basicInformationPriorityFormGroup"] .e-input')
                scraped['priority'] = priority_element.get_attribute('value')
                self.logger.log(f"Successfully scraped priority: {scraped['priority']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape priority field: {str(e)}")
                self.take_screenshot("Failed to scrape priority field")
                raise

            try:
                type_element = self.page.locator('[data-test-id="basicInformationTypeFormGroup"] .e-input')
                scraped['insurance_type'] = type_element.get_attribute('value')
                self.logger.log(f"Successfully scraped insurance type: {scraped['insurance_type']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape insurance type field: {str(e)}")
                self.take_screenshot("Failed to scrape insurance type field")
                raise

            try:
                plan_element = self.page.locator('[formcontrolname="planName"]')
                scraped['plan_name'] = plan_element.evaluate('el => el.value')
                self.logger.log(f"Successfully scraped plan name: {scraped['plan_name']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape plan name field: {str(e)}")
                self.take_screenshot("Failed to scrape plan name field")
                raise

            try:
                holder_element = self.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"] .form-control-static')
                scraped['policy_holder'] = holder_element.inner_text().strip()
                self.logger.log(f"Successfully scraped policy holder: {scraped['policy_holder']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape policy holder field: {str(e)}")
                self.take_screenshot("Failed to scrape policy holder field")
                raise

            try:
                dob_element = self.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"] .form-control-static')
                scraped['dob'] = dob_element.inner_text().strip()
                self.logger.log(f"Successfully scraped DOB: {scraped['dob']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape DOB field: {str(e)}")
                self.take_screenshot("Failed to scrape DOB field")
                raise

            try:
                policy_element = self.page.locator('[formcontrolname="policyNumber"]')
                scraped['policy_number'] = policy_element.evaluate('el => el.value')
                self.logger.log(f"Successfully scraped policy number: {scraped['policy_number']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape policy number field: {str(e)}")
                self.take_screenshot("Failed to scrape policy number field")
                raise

            try:
                group_element = self.page.locator('[formcontrolname="groupNumber"]')
                scraped['group_number'] = group_element.evaluate('el => el.value')
                self.logger.log(f"Successfully scraped group number: {scraped['group_number']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape group number field: {str(e)}")
                self.take_screenshot("Failed to scrape group number field")
                raise

            try:
                auth_element = self.page.locator('[formcontrolname="authorizationNumber"]')
                scraped['authorization'] = auth_element.evaluate('el => el.value')
                self.logger.log(f"Successfully scraped authorization: {scraped['authorization']}")
            except Exception as e:
                self.logger.log_error(f"Failed to scrape authorization field: {str(e)}")
                self.take_screenshot("Failed to scrape authorization field")
                raise

            return scraped
        except Exception as e:
            self.logger.log_error(f"Failed to scrape insurance dialog: {str(e)}")
            self.take_screenshot("Failed to scrape insurance dialog")
            raise
