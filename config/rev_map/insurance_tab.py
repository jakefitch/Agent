from core.playwright_handler import get_handler
import random

class InsuranceTab:
    def __init__(self, handler):
        self.handler = handler

    def close_insurance_tab(self):
        """Close the Insurance tab in the patient menu."""
        try:
            self.handler.page.locator('[data-test-id="insuranceCloseButton"]').click()
            self.handler.logger.log("Closed Insurance tab")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to close Insurance tab: {str(e)}")
            self.handler.take_screenshot("Failed to close Insurance tab")
            raise

    def select_insurance(self, insurance_name, select_mode='random'):
        """
        Select an insurance entry by (partial) name. By default, selects a random match if multiple are found.
        Args:
            insurance_name (str): The (partial) name of the insurance to match.
            select_mode (str): 'random' (default) to select one at random, 'all' to process all matches (calls process_insurance_row for each).
        Returns:
            bool: True if at least one match was found and clicked/processed, False otherwise.
        """
        try:
            # Find all insurance name cells in the first column of the insurance table
            rows = self.handler.page.locator('.ag-center-cols-container .ag-row')
            matches = []
            for i in range(rows.count()):
                row = rows.nth(i)
                # The company name is in the first gridcell (col-id="0")
                name_cell = row.locator('[col-id="0"] span')
                cell_text = name_cell.inner_text().strip()
                if insurance_name.lower() in cell_text.lower():
                    matches.append(row)
            
            if not matches:
                self.handler.logger.log(f"No insurance found matching: {insurance_name}")
                return False
            
            self.handler.logger.log(f"Found {len(matches)} insurance(s) matching: {insurance_name}")
            
            if select_mode == 'all':
                for row in matches:
                    row.click()
                    self.handler.logger.log(f"Clicked insurance: {row.locator('[col-id=\"0\"] span').inner_text().strip()}")
                return True
            else:  # default: random
                chosen_row = random.choice(matches)
                chosen_row.click()
                self.handler.logger.log(f"Clicked insurance: {chosen_row.locator('[col-id=\"0\"] span').inner_text().strip()}")
                return True
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select insurance by name: {str(e)}")
            self.handler.take_screenshot("Failed to select insurance by name")
            raise

    def click_back_to_all_insurances(self):
        """Click the 'Back to All Insurances' button."""
        try:
            self.handler.page.locator('[data-test-id="allPatientInsurancesButton"]').click()
            self.handler.logger.log("Clicked 'Back to All Insurances' button")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click 'Back to All Insurances' button: {str(e)}")
            self.handler.take_screenshot("Failed to click 'Back to All Insurances' button")
            raise

    def click_add_insurance(self):
        """Click the 'Add Insurance' button."""
        try:
            self.handler.page.locator('[data-test-id="insuranceAddButton"]').click()
            self.handler.logger.log("Clicked 'Add Insurance' button")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to click 'Add Insurance' button: {str(e)}")
            self.handler.take_screenshot("Failed to click 'Add Insurance' button")
            raise

    def select_insurance_company_in_dialog(self, company_name, dialog_name='ej2_dropdownlist_50'):
        """
        Select an insurance company from the dropdown in the add insurance dialog.
        Args:
            company_name (str): The name (or partial name) of the insurance company to select.
            dialog_name (str): The accessible name of the dialog (default: 'ej2_dropdownlist_50').
        """
        try:
            dialog = self.handler.page.get_by_role('dialog', name=dialog_name)
            combobox = dialog.get_by_role('combobox')
            combobox.click()
            combobox.fill(company_name)
            combobox.press('Enter')
            self.handler.logger.log(f"Selected insurance company '{company_name}' in dialog '{dialog_name}'")
        except Exception as e:
            self.handler.logger.log_error(f"Failed to select insurance company '{company_name}' in dialog '{dialog_name}': {str(e)}")
            self.handler.take_screenshot(f"Failed to select insurance company in dialog {dialog_name}")
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
            if company_name:
                dialog = self.handler.page.get_by_role('dialog', name=dialog_name)
                combobox = dialog.get_by_role('combobox')
                combobox.click()
                combobox.fill(company_name)
                combobox.press('Enter')
                self.handler.logger.log(f"Selected insurance company '{company_name}' in dialog '{dialog_name}'")
            else:
                dialog = self.handler.page.get_by_role('dialog', name=dialog_name)
                combobox = dialog.get_by_role('combobox')
                scraped['company_name'] = combobox.input_value() if hasattr(combobox, 'input_value') else combobox.inner_text()

            # Priority (Primary/Secondary)
            if priority:
                cb = self.handler.page.get_by_role('combobox', name='Primary')
                cb.click()
                self.handler.page.get_by_role('option', name=priority).click()
                self.handler.logger.log(f"Set priority to {priority}")
            else:
                cb = self.handler.page.get_by_role('combobox', name='Primary')
                scraped['priority'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()

            # Insurance Type
            if insurance_type:
                cb = self.handler.page.locator('[data-test-id="basicInformationTypeFormGroup"]').get_by_role('combobox')
                cb.click()
                self.handler.page.get_by_role('option', name=insurance_type).click()
                self.handler.logger.log(f"Set insurance type to {insurance_type}")
            else:
                cb = self.handler.page.locator('[data-test-id="basicInformationTypeFormGroup"]').get_by_role('combobox')
                scraped['insurance_type'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()

            # Plan Name
            if plan_name:
                tb = self.handler.page.locator('[data-test-id="basicInformationPlanFormGroup"]').get_by_role('textbox')
                tb.click()
                tb.fill(plan_name)
                self.handler.logger.log(f"Filled plan name: {plan_name}")
            else:
                tb = self.handler.page.locator('[data-test-id="basicInformationPlanFormGroup"]').get_by_role('textbox')
                scraped['plan_name'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            # Policy Holder
            if policy_holder:
                holder = self.handler.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"]').get_by_text(policy_holder)
                holder.click()
                self.handler.logger.log(f"Selected policy holder: {policy_holder}")
            else:
                holder = self.handler.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"]')
                scraped['policy_holder'] = holder.inner_text()

            # DOB
            if dob:
                dob_field = self.handler.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"]')
                dob_field.click()
                dob_field.fill(dob)
                self.handler.logger.log(f"Filled DOB: {dob}")
            else:
                dob_field = self.handler.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"]')
                scraped['dob'] = dob_field.input_value() if hasattr(dob_field, 'input_value') else dob_field.inner_text()

            # Policy Number
            if policy_number:
                tb = self.handler.page.locator('[data-test-id="basicInformationPolicyNumberFormGroup"]').get_by_role('textbox')
                tb.click()
                tb.fill(policy_number)
                self.handler.logger.log(f"Filled policy number: {policy_number}")
            else:
                tb = self.handler.page.locator('[data-test-id="basicInformationPolicyNumberFormGroup"]').get_by_role('textbox')
                scraped['policy_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            # Group Number
            if group_number:
                tb = self.handler.page.locator('[data-test-id="basicInformationGroupNumberFormGroup"]').get_by_role('textbox')
                tb.click()
                tb.fill(group_number)
                self.handler.logger.log(f"Filled group number: {group_number}")
            else:
                tb = self.handler.page.locator('[data-test-id="basicInformationGroupNumberFormGroup"]').get_by_role('textbox')
                scraped['group_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            # Authorization
            if authorization:
                tb = self.handler.page.locator('[data-test-id="individualBenefitsAuthorizationNumberFormGroup"]').get_by_role('textbox')
                tb.click()
                tb.fill(authorization)
                self.handler.logger.log(f"Filled authorization: {authorization}")
            else:
                tb = self.handler.page.locator('[data-test-id="individualBenefitsAuthorizationNumberFormGroup"]').get_by_role('textbox')
                scraped['authorization'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            self.handler.logger.log("Filled/scraped insurance dialog fields")
            return scraped
        except Exception as e:
            self.handler.logger.log_error(f"Failed to fill/scrape insurance dialog: {str(e)}")
            self.handler.take_screenshot("Failed to fill/scrape insurance dialog")
            raise 

    def scrape_insurance(self):
        """
        Scrape all insurance dialog fields (except company name) and return their values as a dictionary.
        Returns:
            dict: All field values as text (excluding company_name).
        """
        scraped = {}
        try:
            # Priority
            cb = self.handler.page.get_by_role('combobox', name='Primary')
            scraped['priority'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()

            # Insurance Type
            cb = self.handler.page.locator('[data-test-id="basicInformationTypeFormGroup"]').get_by_role('combobox')
            scraped['insurance_type'] = cb.input_value() if hasattr(cb, 'input_value') else cb.inner_text()

            # Plan Name
            tb = self.handler.page.locator('[data-test-id="basicInformationPlanFormGroup"]').get_by_role('textbox')
            scraped['plan_name'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            # Policy Holder
            holder = self.handler.page.locator('[data-test-id="basicInformationPolicyHolderFormGroup"]')
            scraped['policy_holder'] = holder.inner_text()

            # DOB
            dob_field = self.handler.page.locator('[data-test-id="basicInformationPolicyDateOfBirthFormGroup"]')
            scraped['dob'] = dob_field.input_value() if hasattr(dob_field, 'input_value') else dob_field.inner_text()

            # Policy Number
            tb = self.handler.page.locator('[data-test-id="basicInformationPolicyNumberFormGroup"]').get_by_role('textbox')
            scraped['policy_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            # Group Number
            tb = self.handler.page.locator('[data-test-id="basicInformationGroupNumberFormGroup"]').get_by_role('textbox')
            scraped['group_number'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            # Authorization
            tb = self.handler.page.locator('[data-test-id="individualBenefitsAuthorizationNumberFormGroup"]').get_by_role('textbox')
            scraped['authorization'] = tb.input_value() if hasattr(tb, 'input_value') else tb.inner_text()

            self.handler.logger.log("Scraped insurance dialog fields (excluding company name)")
            return scraped
        except Exception as e:
            self.handler.logger.log_error(f"Failed to scrape insurance dialog: {str(e)}")
            self.handler.take_screenshot("Failed to scrape insurance dialog")
            raise 