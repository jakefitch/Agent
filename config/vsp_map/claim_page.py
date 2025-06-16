from typing import Optional, List
import re
from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient
from time import sleep
from config.debug.vsp_error_tracker import save_vsp_error_message


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
        sleep(1)
        try:
            dos = patient.insurance_data.get('dos')
            if not dos:
                self.logger.log_error("No date of service provided for patient")
                return False

            # Check for COB link and click if present, but don't delay too long
            cob_link = self.page.locator('#cob-coverage-navigate-to-claim-link')
            try:
                if cob_link.wait_for(state='visible', timeout=500):
                    cob_link.click()
                    self.page.wait_for_timeout(500)  # Optional: short wait for UI update
            except Exception:
                pass  # COB link not present or not visible, continue as normal

            dos_field = self.page.locator('#date-of-service')
            dos_field.wait_for(state='visible', timeout=15000)
            dos_field.click()
            dos_field.fill(dos)
            self.logger.log(f"Set date of service to {dos}")
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to set date of service: {str(e)}")
            self.take_screenshot("dos_set_error")
            raise Exception("Failed to set date of service")

    def _extract_exam_code(self, patient: Patient) -> Optional[str]:
        """Return the exam code from ``patient.claims`` if present."""
        exam_codes = {
            "92002",
            "92004",
            "92012",
            "92014",
            "S0620",
            "S0621",
            "99202",
            "99203",
            "99204",
            "99205",
            "99211",
            "99212",
            "99213",
            "99214",
            "99215",
        }

        for item in getattr(patient, "claims", []):
            code = (getattr(item, "vcode", "") or getattr(item, "code", "")).upper()
            if code in exam_codes:
                return code
        return None

    def submit_exam(self, patient: Patient) -> None:
        """Select the exam type for the claim based on patient data."""
        try:
            exam_code = self._extract_exam_code(patient)
            if not exam_code:
                self.logger.log_error("No exam code found to select")
                return

            dropdown = self.page.locator('#exam-type-group')
            dropdown.wait_for(state='visible', timeout=5000)
            dropdown.select_option(value=exam_code)
            self.logger.log(f"Selected exam type {exam_code}")

        except Exception as e:
            self.logger.log_error(f"Failed to select exam type: {str(e)}")
            self.take_screenshot("exam_type_select_error")
            raise

    def set_doctor(self, patient: Patient) -> None:
        """Set the rendering provider."""
        try:
            # First click the dropdown to open it
            
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
        sleep(1)
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
            self.logger.log("Starting fill_pricing function...")
            self.logger.log(f"Patient claims count: {len(patient.claims) if patient.claims else 0}")
            
            # Scroll to pricing section
            self.logger.log("Scrolling to pricing section...")
            self.page.evaluate("window.scrollTo(0, 4000)")
            self.page.wait_for_timeout(2000)

            inputs = self.page.locator("//input[@formcontrolname='cptHcpcsCode']")
            input_count = inputs.count()
            self.logger.log(f"Found {input_count} CPT/HCPCS code inputs on page")

            def calculate_units(desc: str, qty: int) -> int:
                self.logger.log(f"Calculating units for description: {desc}, quantity: {qty}")
                pack_sizes = re.findall(r"\b(6|90|30|60|12|24)\b", desc or "")
                result = int(pack_sizes[0]) * int(qty) if pack_sizes else 0
                self.logger.log(f"Calculated units: {result}")
                return result

            for item in patient.claims:
                self.logger.log(f"\nProcessing claim item: {item}")
                
                code = getattr(item, "code", "")
                price = str(getattr(item, "billed_amount", ""))
                description = getattr(item, "description", "")
                qty = getattr(item, "quantity", 1)
                
                self.logger.log(f"Item details - Code: {code}, Price: {price}, Description: {description}, Quantity: {qty}")

                if description == "Coopervision Inc. Biofinity":
                    description = "CooperVision Biofinity 6 pack"
                    self.logger.log("Updated description for Biofinity")

                for i in range(input_count):
                    inp = inputs.nth(i)
                    # Try multiple methods to get the input value
                    current_value = None
                    try:
                        # Method 1: Try input.value
                        current_value = inp.input_value()
                    except Exception as e1:
                        self.logger.log(f"Method 1 failed: {str(e1)}")
                        try:
                            # Method 2: Try evaluating the element's value property
                            current_value = inp.evaluate("el => el.value")
                        except Exception as e2:
                            self.logger.log(f"Method 2 failed: {str(e2)}")
                            try:
                                # Method 3: Try getting the text content
                                current_value = inp.text_content()
                            except Exception as e3:
                                self.logger.log(f"Method 3 failed: {str(e3)}")
                    
                    self.logger.log(f"Checking input {i+1}: value={current_value}")
                    
                    if current_value == code:
                        line_num = inp.get_attribute("id").split("-")[2]
                        self.logger.log(f"Found matching code {code} on line {line_num}")
                        
                        if code.startswith("V25"):
                            self.logger.log("Processing V25 code - calculating units")
                            unit_count = calculate_units(description, qty)
                            unit_input = self.page.locator(
                                f"#service-line-{line_num}-unit-count-input"
                            )
                            self.logger.log(f"Setting unit count to {unit_count}")
                            unit_input.fill(str(unit_count))

                        price_input = self.page.locator(
                            f"#service-line-{line_num}-billed-amount-input"
                        )
                        self.logger.log(f"Setting billed amount to {price}")
                        price_input.fill(price)
                        break
                    else:
                        self.logger.log(f"No match found for code {code} in input {i+1}")

            # FSA and patient paid amounts
            self.logger.log("\nProcessing FSA and patient paid amounts...")
            copay = str(patient.insurance_data.get("copay", ""))
            self.logger.log(f"Patient copay amount: {copay}")

            self.logger.log("Scrolling to FSA section...")
            self.page.evaluate("window.scrollTo(0, 4400)")
            self.page.wait_for_timeout(1000)
            
            try:
                if copay:
                    self.logger.log("Setting FSA paid amount...")
                    self.page.locator("#services-fsa-paid-input").fill(copay)
            except Exception as e:
                self.logger.log_error(f"Error setting FSA paid amount: {str(e)}")

            self.logger.log("Scrolling to patient paid section...")
            self.page.evaluate("window.scrollTo(0, 4400)")
            self.page.wait_for_timeout(3000)
            
            try:
                paid = self.page.locator("#services-patient-paid-amount-input")
                if copay:
                    self.logger.log("Setting patient paid amount...")
                    paid.click()
                    paid.fill(copay)
            except Exception as e:
                self.logger.log_error(f"Error setting patient paid amount: {str(e)}")

            self.logger.log("Successfully completed fill_pricing function")

        except Exception as e:
            self.logger.log_error(f"Failed to fill pricing: {str(e)}")
            self.logger.log_error(f"Error type: {type(e).__name__}")
            self.logger.log_error(f"Error details: {str(e)}")
            self.take_screenshot("claim_price_error")
            raise

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
            # Click the initial submit claim button
            self.page.locator('#claimTracker-submitClaim').click()
            
            # Wait briefly for the confirmation popup
            self.page.wait_for_timeout(1000)
            
            # Click the confirmation button in the popup
            confirm_button = self.page.locator('#submit-claim-modal-ok-button')
            if confirm_button.is_visible(timeout=5000):
                confirm_button.click()
                self.wait_for_network_idle(timeout=10000)
            else:
                self.logger.log_error("Confirmation popup not found after clicking submit claim")
                self.take_screenshot("claim_submit_no_popup")
                
        except Exception as e:
            self.logger.log_error(f"Submit claim failed: {str(e)}")
            self.take_screenshot("claim_submit_error")

    def submit_claim_and_handle_errors(self) -> bool:
        """Submit the claim and check for potential error banners."""
        try:
            previous_url = self.page.url
            self.page.locator('#claimTracker-submitClaim').click()
            self.wait_for_network_idle(timeout=10000)

            if self.page.url != previous_url:
                self.logger.log("Claim submitted successfully.")
                return True

            banner = self.page.locator('div.error-message, .alert-banner, .vsp-error')
            if banner.count() > 0 and banner.first.is_visible():
                error_text = banner.first.inner_text().strip()
                self.logger.log_error(f"Claim submission blocked: {error_text}")
                try:
                    save_vsp_error_message(error_text)
                except Exception as e2:
                    self.logger.log_error(f"Failed to save VSP error message: {str(e2)}")
                self.take_screenshot("claim_submit_blocked")
                return False

            self.logger.log_error("Claim did not redirect and no error banner detected.")
            self.take_screenshot("claim_submit_unknown")
            return False

        except Exception as e:
            self.logger.log_error(f"Submit claim threw exception: {str(e)}")
            self.take_screenshot("claim_submit_exception")
            return False

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
        if not patient.has_optical_order:
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
        """Submit frame information to the claim form.
        
        Args:
            patient: Patient object containing frame and insurance data
        """
        if not patient.has_optical_order:
            return
        try:
            # Select the frame supplier
            supplier_value = "DOCTOR" if patient.has_frame else "PATIENT"
            self.page.locator('#frames-frame-supplier-dropdown').select_option(value=supplier_value)

            # Trigger manual frame entry popup
            self.page.locator('#frame-search-textbox').fill('1234')
            self.page.locator('#frame-search-button').click()
            sleep(1)
            manual = self.page.locator('#search-manual-frames')
            if manual.is_visible(timeout=3000):
                manual.click()

            # Wait for the manual entry form
            self.page.locator('#frame-details-fields').wait_for(state='visible', timeout=10000)

            frames = getattr(patient, 'frames', {})

            def fill(selector: str, value: str) -> None:
                if value is None:
                    value = ''
                field = self.page.locator(selector)
                if field.count() > 0:
                    field.fill(value)

            fill('#frame-display-form-manufacturer', frames.get('manufacturer', ''))
            fill('#frame-display-form-collection', frames.get('collection', ''))
            fill('#frame-display-form-model', frames.get('model', 'unknown'))
            fill('#frame-display-form-color', frames.get('color', ''))
            fill('#frame-display-form-temple', frames.get('temple', ''))
            
            # Handle material dropdown with case-insensitive matching
            material = frames.get('material', '')
            if material:
                material = material.lower()
                # Get all options from the dropdown
                options = self.page.locator('#frame-display-form-materialType option').all()
                # Find matching option (case-insensitive)
                for option in options:
                    if option.inner_text().lower().replace(' ', '') == material.replace(' ', ''):
                        self.page.locator('#frame-display-form-materialType').select_option(value=option.get_attribute('value'))
                        break
            
            fill('#frame-display-form-eyesize', frames.get('eyesize', ''))
            fill('#frame-display-form-dbl', frames.get('dbl', ''))

            wholesale = frames.get('wholesale_price')
            if wholesale:
                if wholesale == '0.00':
                    wholesale = '64.95'
                fill('#frame-display-form-wholesale-cost', wholesale)

            # Save the details
            self.page.locator("[title='Click to save your edits']").click()

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

    def fill_copay_and_fsa(self, patient: Patient) -> None:
        """Fill out the copay amount and FSA paid amount fields if available.
        
        Args:
            patient: Patient object containing the copay amount in insurance_data
        """
        try:
            copay = str(patient.insurance_data.get("copay", ""))
            if not copay:
                self.logger.log("No copay amount found in patient data")
                raise Exception("No copay amount found in patient data")

            # Scroll to the patient paid section
            self.page.evaluate("window.scrollTo(0, 4400)")
            self.page.wait_for_timeout(1000)

            # Fill copay amount
            copay_field = self.page.locator("#services-patient-paid-amount-input")
            if copay_field.is_visible(timeout=5000):
                copay_field.click()
                copay_field.fill(copay)
                self.logger.log(f"Set patient paid amount to {copay}")
            else:
                self.logger.log_error("Could not find patient paid amount field")

            # Try to fill FSA amount if field exists
            try:
                fsa_field = self.page.locator("#services-fsa-paid-input")
                if fsa_field.is_visible(timeout=1000):  # Short timeout since this field is optional
                    fsa_field.click()
                    fsa_field.fill(copay)
                    self.logger.log(f"Set FSA paid amount to {copay}")
            except Exception as e:
                self.logger.log("FSA paid field not found or not visible - this is expected in some cases")

        except Exception as e:
            self.logger.log_error(f"Failed to fill copay and FSA amounts: {str(e)}")
            self.take_screenshot("claim_copay_fsa_error")
            raise

