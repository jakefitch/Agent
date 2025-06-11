from typing import Optional, List
import re
from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient


class ClaimPage(BasePage):
    """Page object for interacting with VSP's claim form."""

    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://eclaim.eyefinity.com/secure/eInsurance/claim-form"

    # ------------------------------------------------------------------
    # Utilities
    def is_loaded(self, timeout: int = 5000) -> bool:
        """Verify the claim page has loaded."""
        try:
            header = self.page.locator('#claim-form-container')
            header.wait_for(state='visible', timeout=timeout)
            return True
        except Exception as e:
            self.logger.log_error(f"Claim page not loaded: {str(e)}")
            return False

    def navigate_to_claim(self) -> None:
        """Navigate directly to the claim form page."""
        try:
            self.logger.log("Navigating to claim page ...")
            self.page.goto(self.base_url)
            self.wait_for_network_idle(timeout=10000)
            if not self.is_loaded(timeout=10000):
                raise Exception("Claim page failed to load")
            self.logger.log("Claim page loaded")
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to claim page: {str(e)}")
            self.take_screenshot("claim_nav_error")
            raise

    # ------------------------------------------------------------------
    # High level workflows
    def fill_rx(self, patient: Patient) -> None:
        """Fill the prescription and pricing information for the claim."""
        self.send_rx(patient)
        self.disease_reporting(patient)
        self.calculate(patient)
        self.fill_pricing(patient)
        self.set_gender(patient)

    def calculate_order(self) -> None:
        """Submit the claim and generate the report."""
        self.click_submit_claim()
        self.generate_report()

    # ------------------------------------------------------------------
    def set_dos(self, patient: Patient) -> None:
        """Set the date of service."""
        try:
            # --------------------------------------------------------------
            # Occasionally an intermediate COB page may appear before the
            # claim form loads. If so, click the link to continue to the
            # claim without interrupting execution.
            try:
                cob_link = self.page.locator('#cob-coverage-navigate-to-claim-link')
                cob_link.wait_for(state='visible', timeout=2000)
                cob_link.click()
                self.wait_for_network_idle(timeout=10000)
            except Exception:
                # If the element is not found or not clickable, simply ignore
                pass

            dos_field = self.page.locator('#date-of-service')
            dos_field.fill(patient.insurance_data.get("dos", ""))
        except Exception as e:
            self.logger.log_error(f"Failed to set DOS: {str(e)}")
            self.take_screenshot("claim_set_dos_error")
            raise

    def submit_exam(self, patient: Patient) -> None:
        
        """Select exam option based on the exam code being billed."""
        exam_code: Optional[str] = None
        for claim in patient.claims:
            code = (claim.code or "").upper()
            if code in {"92004", "92014", "92002", "92012"} or \
               code.startswith("99") or code.startswith("S062") or code.startswith("S602"):
                exam_code = code
                break

        if not exam_code:
            return

            
        group = "2" if exam_code.startswith("99") else "1"

        try:
            self.page.locator(f'#exam-type-group{group}-{exam_code}').click()
            refbox = self.page.locator('#exam-refraction-performed-checkbox-input')
            if not refbox.is_checked():
                self.page.locator('[formcontrolname="refractionTestPerformed"]').click()
        except Exception as e:
            self.logger.log_error(f"Failed to submit exam: {str(e)}")
            self.take_screenshot("claim_exam_error")

    def set_doctor(self, patient: Patient) -> None:
        """Set the rendering provider."""
        try:     
            # Determine provider ID based on doctor name
            doctor_name = patient.insurance_data.get('doctor', '')
            if "Fitch" in doctor_name:
                provider_id = "1740293919"
            elif "Hollingsworth" in doctor_name:
                provider_id = "1639335516"
            else:
                provider_id = "1891366597"  # Default to Schaeffer
            
            # Use select_option to select the provider
            self.page.locator('#exam-rendering-provider-group').select_option(value=provider_id)
            self.logger.log(f"Selected provider {provider_id} for doctor {doctor_name}")
            
        except Exception as e:
            self.logger.log_error(f"Failed to set doctor: {str(e)}")
            self.take_screenshot("claim_set_doctor_error")
            raise

    def submit_cl(self, patient: Patient) -> None:
        """Fill contact lens information if present."""
        contact_codes = {'V2500', 'V2501', 'V2502', 'V2503', 'V2520', 'V2521', 'V2522', 'V2523'}
        cl_items = [c for c in patient.claims if c.code in contact_codes]
        if not cl_items:
            return
        first = cl_items[0]
        try:
            self.page.locator('#contacts-material-type-dropdown').select_option(first.code)
            self.page.locator('#contacts-reason-dropdown').select_option("0")
            self.page.locator('#contacts-manufacturer-dropdown').select_option(patient.insurance_data.get('cl_manufacturer', 'Other'))
            self.page.locator('#contacts-brand-dropdown').select_option('Other')
            self.page.locator('#contacts-number-of-boxes-textbox').fill(str(first.quantity))
            self.page.locator('#additional-information-claim-input').fill(first.description)
        except Exception as e:
            self.logger.log_error(f"Failed to submit CL info: {str(e)}")
            self.take_screenshot("claim_cl_error")

    def disease_reporting(self, patient: Patient) -> None:
        """Enter diagnosis codes for services."""
        diagnosis = patient.medical_data.get('dx')
        if not diagnosis:
            diagnosis = 'H52.223'
        if not diagnosis.startswith('H52.'):
            diagnosis = 'H52.223'
        diagnosis = diagnosis.split(',')[0]
        try:
            field = self.page.locator('#services-diagnosis-code-A-textbox')
            field.click()
            field.fill(diagnosis)
        except Exception as e:
            self.logger.log_error(f"Failed disease reporting: {str(e)}")
            self.take_screenshot("claim_disease_report_error")

    def calculate(self, patient: Patient) -> None:
        """Click the Calculate button and handle alerts."""
        try:
            self.page.locator('#claim-tracker-calculate').click()
            self.wait_for_network_idle(timeout=10000)
        except Exception as e:
            self.logger.log_error(f"Calculation failed: {str(e)}")
            self.take_screenshot("claim_calculate_error")

    def fill_pricing(self, patient: Patient) -> None:
        """Fill billed amounts for each claim item."""
        try:
            for item in patient.claims:
                code = item.code
                price = str(item.billed_amount)
                inputs = self.page.locator("//input[@formcontrolname='cptHcpcsCode']")
                for i in range(inputs.count()):
                    inp = inputs.nth(i)
                    if inp.get_attribute('value') == code:
                        line_num = inp.get_attribute('id').split('-')[2]
                        price_input = self.page.locator(f"#service-line-{line_num}-billed-amount-input")
                        price_input.fill(price)
                        break
        except Exception as e:
            self.logger.log_error(f"Failed pricing fill: {str(e)}")
            self.take_screenshot("claim_price_error")

    def set_gender(self, patient: Patient) -> None:
        """Set patient gender switch."""
        try:
            self.page.locator('#patient-sex-male-toggle' if patient.demographics.get('gender') == 'Male' else '#patient-sex-female-toggle').click()
        except Exception as e:
            self.logger.log_error(f"Failed to set gender: {str(e)}")
            self.take_screenshot("claim_gender_error")

    def fill_address(self, patient: Patient) -> None:
        """Fill patient address if not already present."""
        try:
            addr = self.page.locator('#patient-address1')
            if addr.input_value() == "":
                addr.fill(patient.demographics.get('address', ''))
                self.page.locator('#patient-city-input').fill(patient.demographics.get('city', ''))
                state = patient.demographics.get('state', '')
                if state:
                    self.page.locator('#patient-state-input').click()
                    self.page.keyboard.type(state)
                    self.page.keyboard.press('Enter')
                self.page.locator('#patient-zip-code-input').fill(patient.demographics.get('zip', ''))
        except Exception as e:
            self.logger.log_error(f"Failed to fill address: {str(e)}")
            self.take_screenshot("claim_address_error")

    def click_submit_claim(self) -> None:
        try:
            self.page.locator('#claimTracker-submitClaim').click()
            self.wait_for_network_idle(timeout=10000)
        except Exception as e:
            self.logger.log_error(f"Submit claim failed: {str(e)}")
            self.take_screenshot("claim_submit_error")

    def generate_report(self) -> None:
        try:
            self.page.locator('#generate-report-button').click()
            self.wait_for_network_idle(timeout=10000)
        except Exception as e:
            self.logger.log_error(f"Generate report failed: {str(e)}")
            self.take_screenshot("claim_report_error")

    def send_add_and_seg_to_vsp(self, patient: Patient) -> None:
        try:
            self.page.locator('#prescriptionRightEyeAddInput').fill(patient.medical_data.get('od_add', ''))
            self.page.locator('#prescriptionLeftEyeAddInput').fill(patient.medical_data.get('os_add', ''))
            self.page.locator('#prescriptionLeftEyeSegmentHeightInput').fill(patient.medical_data.get('seg_height', ''))
            self.page.locator('#prescriptionRightEyeSegmentHeightInput').fill(patient.medical_data.get('seg_height', ''))
        except Exception as e:
            self.logger.log_error(f"Failed to send add/seg: {str(e)}")
            self.take_screenshot("claim_add_seg_error")

    def send_rx(self, patient: Patient) -> None:
        if patient.lens_type is None:
            return
        try:
            self.page.locator('#prescriptionRightEyeSphereInput').fill(patient.medical_data.get('od_sph', ''))
            self.page.locator('#prescriptionRightEyeCylinderInput').fill(patient.medical_data.get('od_cyl', ''))
            self.page.locator('#prescriptionRightEyeAxisInput').fill(patient.medical_data.get('od_axis', ''))
            self.page.locator('#prescriptionLeftEyeSphereInput').fill(patient.medical_data.get('os_sph', ''))
            self.page.locator('#prescriptionLeftEyeCylinderInput').fill(patient.medical_data.get('os_cyl', ''))
            self.page.locator('#prescriptionLeftEyeAxisInput').fill(patient.medical_data.get('os_axis', ''))
            if patient.medical_data.get('od_pd'):
                self.page.locator('#prescriptionBinocularMonocularSelect').select_option('MONOCULAR')
                self.page.locator('#prescriptionRightEyeDistanceInput').fill(patient.medical_data.get('od_pd', ''))
                self.page.locator('#prescriptionLeftEyeDistanceInput').fill(patient.medical_data.get('os_pd', ''))
            else:
                self.page.locator('#prescriptionBinocularMonocularSelect').select_option('BINOCULAR')
                self.page.locator('#prescriptionRightEyeDistanceInput').fill(patient.medical_data.get('dpd', ''))
            if patient.lens_type != 'Single Vision':
                self.send_add_and_seg_to_vsp(patient)
        except Exception as e:
            self.logger.log_error(f"Failed to send Rx: {str(e)}")
            self.take_screenshot("claim_send_rx_error")

    def submit_frame(self, patient: Patient) -> None:
        if patient.lens_type is None:
            return
        try:
            self.page.locator('#frames-frame-supplier-dropdown').click()
            if patient.insurance_data.get('wholesale'):
                self.page.locator('option[value="doctor"]').click()
            else:
                self.page.locator('option[value="patient"]').click()
            self.page.locator('#frame-search-textbox').fill('1234')
            self.page.locator('#frame-search-button').click()
        except Exception as e:
            self.logger.log_error(f"Failed to submit frame: {str(e)}")
            self.take_screenshot("claim_frame_error")

    def submit_lens(self, patient: Patient) -> None:
        if patient.lens_type is None:
            return
        try:
            self.page.locator('#lens-finishing-dropdown').click()
            self.page.locator('#lens-finishing-option-in-office-stock-lens').click()
        except Exception as e:
            self.logger.log_error(f"Failed to submit lens: {str(e)}")
            self.take_screenshot("claim_lens_error")

