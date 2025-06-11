from typing import Optional, List
import re
from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient
from time import sleep
import re


class ClaimPage(BasePage):
    """Page object for interacting with VSP's claim form."""

    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://eclaim.eyefinity.com/secure/eInsurance/claim-form"

    # ------------------------------------------------------------------
    # Utilities
    def is_loaded(self, timeout: int = 5000) -> bool:
        """Verify the claim form page has loaded."""
        try:
            header = self.page.locator('#claim-form-header')
            header.wait_for(state='visible', timeout=timeout)
            return True
        except Exception as e:
            self.logger.log_error(f"Claim form page not loaded: {str(e)}")
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
    def set_dos(self, patient: Patient) -> bool:
        """Set the date of service on the claim form."""
        try:
            if not patient.dos:
                self.logger.log_error("No date of service provided for patient")
                return False

            dos_field = self.page.locator('[id="dos-field"]')
            dos_field.wait_for(state='visible', timeout=5000)
            dos_field.fill(patient.dos)
            self.logger.log(f"Set date of service to {patient.dos}")
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to set date of service: {str(e)}")
            self.take_screenshot("dos_set_error")
            return False

    def submit_exam(self, patient: Patient) -> None:
        """Submit the exam claim."""
        try:
            self.logger.log("Submitting exam claim...")
            self.page.locator('#submit-claim-button').click()
            self.logger.log("Successfully submitted exam claim")
        except Exception as e:
            self.logger.log_error(f"Failed to submit exam claim: {str(e)}")
            self.take_screenshot("claim_submit_error")
            raise

    def set_doctor(self, patient: Patient) -> None:
        """Set the rendering provider."""
        try:
            # First click the dropdown to open it
            self.page.locator('#exam-rendering-provider-group').click()
            self.logger.log("Clicked provider dropdown")
            
            # Wait a moment for the dropdown to fully open
            self.page.wait_for_timeout(1000)
            
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
        """Submit the contact lens claim."""
        try:
            self.logger.log("Submitting contact lens claim...")
            self.page.locator('#submit-cl-claim-button').click()
            self.logger.log("Successfully submitted contact lens claim")
        except Exception as e:
            self.logger.log_error(f"Failed to submit contact lens claim: {str(e)}")
            self.take_screenshot("claim_submit_cl_error")
            raise

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
       
        """Fill billed amounts and patient payment information."""
        try:
            # Scroll to pricing section
            self.page.evaluate("window.scrollTo(0, 4000)")
            self.page.wait_for_timeout(2000)

            inputs = self.page.locator("//input[@formcontrolname='cptHcpcsCode']")
            input_count = inputs.count()

            def calculate_units(desc: str, qty: int) -> int:
                pack_sizes = re.findall(r"\b(6|90|30|60|12|24)\b", desc or "")
                return int(pack_sizes[0]) * int(qty) if pack_sizes else 0

            for item in patient.claims:

                code = getattr(item, "code", "")
                price = str(getattr(item, "billed_amount", ""))
                description = getattr(item, "description", "")
                if description == "Coopervision Inc. Biofinity":
                    description = "CooperVision Biofinity 6 pack"
                qty = getattr(item, "quantity", 1)

                for i in range(input_count):
                    inp = inputs.nth(i)
                    
                    if inp.get_attribute("value") == code:
                        line_num = inp.get_attribute("id").split("-")[2]
                        if code.startswith("V25"):
                            unit_count = calculate_units(description, qty)
                            unit_input = self.page.locator(
                                f"#service-line-{line_num}-unit-count-input"
                            )
                            unit_input.fill(str(unit_count))

                        price_input = self.page.locator(
                            f"#service-line-{line_num}-billed-amount-input"
                        )
                        price_input.fill(price)
                        break

            # FSA and patient paid amounts
            copay = str(patient.insurance_data.get("copay", ""))

            self.page.evaluate("window.scrollTo(0, 4400)")
            self.page.wait_for_timeout(1000)
            try:
                if copay:
                    self.page.locator("#services-fsa-paid-input").fill(copay)
            except Exception:
                pass

            self.page.evaluate("window.scrollTo(0, 4400)")
            self.page.wait_for_timeout(3000)
            try:
                paid = self.page.locator("#services-patient-paid-amount-input")
                if copay:
                    paid.click()
                    paid.fill(copay)
            except Exception:
                pass

        except Exception as e:
            
            self.logger.log_error(f"Failed to fill pricing: {str(e)}")
            self.take_screenshot("claim_price_error")

    def set_gender(self, patient: Patient) -> None:
        """Set the patient's gender."""
        try:
            if not patient.gender:
                self.logger.log_error("No gender provided for patient")
                return

            self.logger.log(f"Setting gender to {patient.gender}")
            self.page.locator('#exam-gender').select_option(value=patient.gender)
            
        except Exception as e:
            self.logger.log_error(f"Failed to set gender: {str(e)}")
            self.take_screenshot("claim_set_gender_error")
            raise

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

