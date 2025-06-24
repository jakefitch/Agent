from typing import Optional, List
import re
from playwright.sync_api import Page
from core.logger import Logger
from core.base import PatientContext, BasePage, Patient
from time import sleep
from config.debug.vsp_error_tracker import save_vsp_error_message
import time


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

            refraction_checkbox = self.page.locator('#exam-refraction-performed-checkbox')

            # Only click if not already checked
            if refraction_checkbox.is_visible(timeout=5000):
                is_checked = refraction_checkbox.get_attribute("class")
                if "mat-checkbox-checked" not in is_checked:
                    # Click the inner box (where the check toggle actually happens)
                    click_target = refraction_checkbox
                    click_target.click()
                    self.logger.log("Checked refraction performed checkbox")
                else:
                    self.logger.log("Refraction checkbox already checked")
            else:
                self.logger.log_error("Refraction checkbox not visible")


        except Exception as e:
            self.logger.log_error(f"Failed to select exam type: {str(e)}")
            self.take_screenshot("exam_type_select_error")
            raise

    def set_doctor(self, patient: Patient) -> None:
        """Set the rendering provider with validation and retry logic."""
        max_attempts = 3
        doctor_name = patient.insurance_data.get('doctor', '')
        
        # Determine provider ID based on doctor name
        if "Fitch" in doctor_name:
            provider_id = "1740293919"
        elif "Hollingsworth" in doctor_name:
            provider_id = "1639335516"
        else:
            provider_id = "1891366597"  # Default to Schaeffer
        
        self.logger.log(f"Attempting to set doctor: {doctor_name} (provider_id: {provider_id})")
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.log(f"Set doctor attempt {attempt}/{max_attempts}")
                
                # Wait a moment for the dropdown to be ready
                self.page.wait_for_timeout(1000)
                
                # Use select_option to select the provider
                provider_dropdown = self.page.locator('#exam-rendering-provider-group')
                provider_dropdown.select_option(value=provider_id)
                self.logger.log(f"Selected provider {provider_id} for doctor {doctor_name}")
                
                # Validate the selection was successful
                self.page.wait_for_timeout(500)  # Wait for selection to register
                
                # Check if the dropdown now shows the selected value
                selected_value = provider_dropdown.evaluate("el => el.value")
                if selected_value == provider_id:
                    self.logger.log(f"Doctor selection validated successfully on attempt {attempt}")
                    return
                else:
                    self.logger.log_error(f"Validation failed - expected {provider_id}, got {selected_value}")
                    if attempt < max_attempts:
                        self.logger.log(f"Retrying doctor selection...")
                        continue
                    else:
                        raise Exception(f"Failed to validate doctor selection after {max_attempts} attempts")
                        
            except Exception as e:
                self.logger.log_error(f"Set doctor attempt {attempt} failed: {str(e)}")
                if attempt < max_attempts:
                    self.logger.log(f"Retrying doctor selection...")
                    self.page.wait_for_timeout(1000)  # Wait before retry
                else:
                    self.logger.log_error(f"All {max_attempts} attempts to set doctor failed")
                    self.take_screenshot("claim_set_doctor_error")
                    raise Exception(f"Failed to set doctor after {max_attempts} attempts: {str(e)}")
        
        # This should never be reached due to the raise above, but just in case
        raise Exception(f"Failed to set doctor after {max_attempts} attempts")

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
            

            field.fill(diagnosis)
            self.logger.log(f"Filled diagnosis code: {diagnosis}")
        except Exception as e:
            self.logger.log_error(f"Failed disease reporting: {str(e)}")
            self.take_screenshot("claim_disease_report_error")

    def calculate(self, patient: Patient) -> None:
        """Click the Calculate button and handle alerts."""
        try:
            self.page.locator('#claim-tracker-calculate').click()
            self.wait_for_network_idle(timeout=10000)
            
            # Check for warning popup that may appear after calculation
            try:
                warning_container = self.page.locator('#warning-message-container')
                if warning_container.is_visible(timeout=2000):  # Reduced from 5000ms to 2000ms
                    self.logger.log("Warning popup detected after calculation")
                    
                    # Try to click the Acknowledge button
                    acknowledge_button = self.page.locator('#soft-edit-ackn-1')
                    if acknowledge_button.is_visible(timeout=1000):  # Reduced from 2000ms to 1000ms
                        acknowledge_button.click()
                        self.logger.log("Clicked Acknowledge button in warning popup")
                        self.page.wait_for_timeout(500)
                        self.page.locator('#claim-tracker-calculate').click()
                        self.wait_for_network_idle(timeout=10000)
                          # Reduced from 1000ms to 500ms
                    else:
                        # Fallback: try to find any acknowledge button in the warning container
                        acknowledge_buttons = warning_container.locator('button:has-text("Acknowledge")')
                        if acknowledge_buttons.count() > 0:
                            acknowledge_buttons.first.click()
                            self.logger.log("Clicked Acknowledge button using text selector")
                            self.page.wait_for_timeout(500)  # Reduced from 1000ms to 500ms
                        else:
                            self.logger.log("Warning popup found but no Acknowledge button located")
                            
            except Exception as e:
                self.logger.log(f"No warning popup appeared or error handling it: {str(e)}")
                
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
                    fsa_locator = self.page.locator("#services-fsa-paid-input")
                    if fsa_locator.is_visible(timeout=1000):
                        fsa_locator.fill(copay)

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
        """Fill out the lens information based on ``patient.lenses`` data.

        The lens form is highly sequential: each dropdown reloads the next one
        when a selection is made.  We therefore step through the form in order,
        waiting briefly after each choice.  ``patient.lenses`` is a dictionary
        populated during scraping with keys like ``type``, ``material``, ``ar``
        and ``photochromatic``.
        """

        lens_data = getattr(patient, "lenses", {}) or {}
        lens_type = lens_data.get("type")
        if not lens_type:
            return  # nothing to submit

        material = lens_data.get("material", "")
        ar = lens_data.get("ar", "")
        photo = lens_data.get("photochromatic", False)

        # Map lens info to the specific design string used in the final dropdown
        design = None
        if ar == "" and material == "CR-39" and lens_type == "Single Vision":
            design = "Stock Spherical - Clear"
        elif ar == "" and material == "Polycarbonate" and lens_type == "Single Vision" and not photo:
            design = "Stock Spherical - Clear"
        elif ar == "Other (AR Coating A)" and material == "Polycarbonate" and lens_type == "Single Vision":
            design = "Stock Aspheric w/ Standard AR (A) - Clear"
        elif ar == "Lab Choice (AR Coating C) (AR Coating C)" and material == "Polycarbonate" and lens_type == "Single Vision" and photo:
            design = "Stock Aspheric w/ Premium AR (C) - Photochromic Other"
        elif ar == "Lab Choice (AR Coating C) (AR Coating C)" and material == "Polycarbonate" and lens_type == "Single Vision":
            design = "Stock Spherical w/ Premium AR (C) - Clear"
        elif ar == "" and material == "Polycarbonate" and lens_type == "Single Vision" and photo:
            design = "Stock Spherical - Photochromic Other"
        elif ar =="Lab Choice (AR Coating D) (AR Coating D)" and material == "Polycarbonate" and lens_type == "Single Vision" and photo:
            design = "Stock Spherical w/ Premium AR (D) - Photochromic Other"
        elif ar =="Lab Choice (AR Coating D) (AR Coating D)" and material == "Polycarbonate" and lens_type == "Single Vision":
            design = "Stock Spherical w/ Premium AR (D) - Clear"
    

        try:
            # Scroll to the start of the lens section
            self.page.evaluate("window.scrollTo(0, 500)")
            self.page.wait_for_timeout(500)

            # --- Finishing type dropdown ---
            finishing = self.page.locator('#lens-finishing-dropdown')
            if finishing.count() > 0:
                # Use select_option instead of click to avoid visibility issues
                finishing.select_option(value="IN_OFFICE_STOCK_LENS")
                self.page.wait_for_timeout(500)

            # --- Vision type dropdown ---
            self.page.locator('#lens-vision-dropdown').select_option(label=lens_type)
            self.page.wait_for_timeout(500)

            # --- Material dropdown ---
            if material:
                self.page.locator('#lens-material-dropdown').select_option(label=material)
                self.page.wait_for_timeout(500)

            # --- Lens design dropdown ---
            if design:
                lens_dd = self.page.locator('#lens-lens-dropdown')
                lens_dd.click()
                # Wait for the dropdown to open
                self.page.wait_for_timeout(500)
                
                # For ng-select, we need to type into the search input that appears
                try:
                    # Look for the search input that appears when ng-select is opened
                    search_input = self.page.locator('.ng-dropdown-panel input[type="text"]')
                    if search_input.is_visible(timeout=2000):
                        search_input.fill(design)
                        self.page.wait_for_timeout(500)
                        search_input.press('Enter')
                    else:
                        # Fallback: try typing directly into the ng-select
                        lens_dd.type(design)
                        self.page.wait_for_timeout(500)
                        lens_dd.press('Enter')
                except Exception as e:
                    self.logger.log(f"Failed to fill ng-select with {design}: {str(e)}")
                    # Try alternative approach - click on the option directly
                    try:
                        option = self.page.locator(f'.ng-dropdown-panel .ng-option:has-text("{design}")')
                        if option.is_visible(timeout=2000):
                            option.click()
                        else:
                            # Last resort: try pressing Tab to close dropdown
                            lens_dd.press('Tab')
                    except Exception as e2:
                        self.logger.log(f"Failed alternative approach: {str(e2)}")
                        lens_dd.press('Tab')  # Close dropdown
                
                self.page.wait_for_timeout(500)

            # --- Lab ID ---
            self.page.evaluate("window.scrollTo(0, 1900)")
            self.page.locator('#lab-lab-textbox').fill('0557')
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

    def handle_popup_window(self) -> bool:
        """Handle popup window that may open after claim submission.
        
        Returns:
            bool: True if popup was handled successfully, False otherwise
        """
        try:
            # Get the browser context from the page for popup handling
            browser_context = self.page.context
            
            # Wait for a new page to open (popup window)
            popup_page = browser_context.wait_for_event('page', timeout=5000)
            self.logger.log("Popup window detected, switching to it...")
            
            # Switch to the popup page
            popup_page.wait_for_load_state()
            self.logger.log(f"Popup page loaded: {popup_page.url}")
            
            # Perform actions in the popup window
            success = self.perform_popup_actions(popup_page)
            
            # Close the popup window
            popup_page.close()
            self.logger.log("Popup window closed")
            
            return success
            
        except Exception as e:
            self.logger.log(f"No popup window opened or popup handling failed: {str(e)}")
            return False

    def perform_popup_actions(self, popup_page) -> bool:
        """Perform specific actions in the popup window.
        
        This handles the frameset-based report popup with:
        - rptTop frame (contains tab bar with "Service Report")
        - rptPage frame (main preview panel)
        - rptPrint frame (hidden/printing)
        
        Args:
            popup_page: The popup page object to interact with
            
        Returns:
            bool: True if actions were successful, False otherwise
        """
        try:
            self.logger.log("Performing actions in popup window...")
            
            # Wait for the popup to fully load
            popup_page.wait_for_load_state("domcontentloaded")
            self.logger.log("Popup page loaded, accessing frames...")
            
            # Step 1: Access the rptTop frame (contains the tab bar)
            try:
                rpt_top = popup_page.frame(name="rptTop")
                if not rpt_top:
                    self.logger.log_error("Could not find rptTop frame")
                    return False
                self.logger.log("Successfully accessed rptTop frame")
            except Exception as e:
                self.logger.log_error(f"Failed to access rptTop frame: {str(e)}")
                return False
            
            # Step 2: Click the "Service Report" tab in rptTop frame
            try:
                # Try multiple approaches to find and click the Service Report tab
                service_report_clicked = False
                
                # Approach 1: Try role-based locator
                try:
                    service_report_link = rpt_top.get_by_role("link", name="Service Report")
                    if service_report_link.is_visible(timeout=3000):
                        service_report_link.click()
                        service_report_clicked = True
                        self.logger.log("Clicked Service Report tab using role-based locator")
                except Exception as e1:
                    self.logger.log(f"Role-based locator failed: {str(e1)}")
                
                # Approach 2: Try text-based locator
                if not service_report_clicked:
                    try:
                        service_report_link = rpt_top.locator("a", has_text="Service Report")
                        if service_report_link.is_visible(timeout=3000):
                            service_report_link.click()
                            service_report_clicked = True
                            self.logger.log("Clicked Service Report tab using text-based locator")
                    except Exception as e2:
                        self.logger.log(f"Text-based locator failed: {str(e2)}")
                
                # Approach 3: Try more generic selector
                if not service_report_clicked:
                    try:
                        service_report_link = rpt_top.locator("a:has-text('Service Report')")
                        if service_report_link.is_visible(timeout=3000):
                            service_report_link.click()
                            service_report_clicked = True
                            self.logger.log("Clicked Service Report tab using generic selector")
                    except Exception as e3:
                        self.logger.log(f"Generic selector failed: {str(e3)}")
                
                if not service_report_clicked:
                    self.logger.log_error("Could not find or click Service Report tab")
                    return False
                    
            except Exception as e:
                self.logger.log_error(f"Failed to click Service Report tab: {str(e)}")
                return False
            
            # Step 3: Wait for rptPage frame to load new content
            try:
                rpt_page = popup_page.frame(name="rptPage")
                if not rpt_page:
                    self.logger.log_error("Could not find rptPage frame")
                    return False
                
                # Wait for the frame content to load
                rpt_page.wait_for_load_state("domcontentloaded")
                self.logger.log("Successfully accessed rptPage frame and waited for content")
                
                # Optional: Take a screenshot of the report
                try:
                    screenshot_path = f"logs/screenshots/service_report_{int(time.time())}.png"
                    rpt_page.screenshot(path=screenshot_path)
                    self.logger.log(f"Service report screenshot saved: {screenshot_path}")
                except Exception as screenshot_error:
                    self.logger.log(f"Failed to take screenshot: {str(screenshot_error)}")
                
                # Optional: Try to find and click download/print button
                self.try_download_report(rpt_page)
                
            except Exception as e:
                self.logger.log_error(f"Failed to access rptPage frame: {str(e)}")
                return False
            
            self.logger.log("Popup actions completed successfully")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Failed to perform popup actions: {str(e)}")
            return False

    def try_download_report(self, rpt_page) -> bool:
        """Try to download or print the report from the rptPage frame.
        
        Args:
            rpt_page: The rptPage frame object
            
        Returns:
            bool: True if download/print was successful, False otherwise
        """
        try:
            self.logger.log("Attempting to download/print report...")
            
            # Try multiple approaches to find download/print button
            download_clicked = False
            
            # Approach 1: Try role-based download button
            try:
                download_button = rpt_page.get_by_role("button", name="Download")
                if download_button.is_visible(timeout=2000):
                    download_button.click()
                    download_clicked = True
                    self.logger.log("Clicked download button using role-based locator")
            except Exception as e1:
                self.logger.log(f"Role-based download button not found: {str(e1)}")
            
            # Approach 2: Try title-based download button
            if not download_clicked:
                try:
                    download_button = rpt_page.get_by_title("Download")
                    if download_button.is_visible(timeout=2000):
                        download_button.click()
                        download_clicked = True
                        self.logger.log("Clicked download button using title-based locator")
                except Exception as e2:
                    self.logger.log(f"Title-based download button not found: {str(e2)}")
            
            # Approach 3: Try aria-label-based download button
            if not download_clicked:
                try:
                    download_button = rpt_page.locator("button[aria-label='Download']")
                    if download_button.is_visible(timeout=2000):
                        download_button.click()
                        download_clicked = True
                        self.logger.log("Clicked download button using aria-label selector")
                except Exception as e3:
                    self.logger.log(f"Aria-label download button not found: {str(e3)}")
            
            # Approach 4: Try print button
            if not download_clicked:
                try:
                    print_button = rpt_page.get_by_role("button", name="Print")
                    if print_button.is_visible(timeout=2000):
                        print_button.click()
                        download_clicked = True
                        self.logger.log("Clicked print button")
                except Exception as e4:
                    self.logger.log(f"Print button not found: {str(e4)}")
            
            # Approach 5: Try to trigger browser print dialog
            if not download_clicked:
                try:
                    rpt_page.evaluate("window.print()")
                    self.logger.log("Triggered browser print dialog")
                    download_clicked = True
                except Exception as e5:
                    self.logger.log(f"Failed to trigger print dialog: {str(e5)}")
            
            if download_clicked:
                self.logger.log("Report download/print action completed")
                return True
            else:
                self.logger.log("No download/print button found, report is viewable in popup")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Failed to download/print report: {str(e)}")
            return False

    def click_submit_claim(self) -> bool:
        """Submit the claim and handle all post-submission flows.
        
        This is the master method that handles the complete claim submission process:
        1. Clicks the submit claim button
        2. Handles the confirmation popup
        3. Waits for processing
        4. Handles the success modal if it appears
        5. Handles any popup windows that may open
        6. Handles any errors or warnings
        
        Returns:
            bool: True if claim was submitted successfully, False if blocked by errors
        """
        try:
            self.logger.log("Starting claim submission process...")
            previous_url = self.page.url

            # Step 1: Click the initial submit claim button
            self.page.locator('#claimTracker-submitClaim').click()
            self.logger.log("Clicked submit claim button")
            
            # Step 2: Handle the confirmation popup
            self.page.wait_for_timeout(1000)
            confirm_button = self.page.locator('#submit-claim-modal-ok-button')
            if confirm_button.is_visible(timeout=5000):
                confirm_button.click()
                self.logger.log("Clicked confirmation button in popup")
                self.wait_for_network_idle(timeout=10000)
            else:
                self.logger.log("No confirmation popup found, proceeding...")

            # Step 3: Check if we navigated away (success)
            if self.page.url != previous_url:
                self.logger.log("Claim submitted successfully - page navigated away")
                return True

            # Step 4: Handle success modal if it appears
            try:
                success_button = self.page.locator('#successfully-submitted-claim-modal-yes-button')
                if success_button.is_visible(timeout=3000):
                    success_button.click()
                    self.logger.log("Clicked yes button in success modal")
                    self.wait_for_network_idle(timeout=5000)
                    
                    # Step 5: Handle popup window if it opens
                    popup_success = self.handle_popup_window()
                    if popup_success:
                        return True
                    
            except Exception as e:
                self.logger.log(f"Success modal not found or not clickable: {str(e)}")

            # Step 6: Check for errors or warnings
            errors = []
            warnings = []

            error_panel = self.page.locator("#error-message-container")
            if error_panel.count() > 0 and error_panel.first.is_visible():
                msg = error_panel.first.inner_text().strip()
                errors.append(msg)
                self.logger.log_error(f"Error found: {msg}")

            warning_panel = self.page.locator("#warning-message-container")
            if warning_panel.count() > 0 and warning_panel.first.is_visible():
                msg = warning_panel.first.inner_text().strip()
                warnings.append(msg)
                self.logger.log(f"Warning found: {msg}")
                
                # Attempt to acknowledge/resolve the warning
                try:
                    buttons = warning_panel.first.locator("button")
                    for i in range(buttons.count()):
                        btn = buttons.nth(i)
                        btn.click()
                        self.page.wait_for_timeout(500)
                    self.logger.log("Attempted to resolve warnings")
                except Exception as e:
                    self.logger.log_error(f"Failed to handle warning buttons: {str(e)}")

            if errors or warnings:
                for msg in errors + warnings:
                    try:
                        save_vsp_error_message(msg)
                    except Exception as e2:
                        self.logger.log_error(f"Failed to save VSP error message: {str(e2)}")
                self.take_screenshot("claim_submit_blocked")
                self.logger.log_error(f"Claim submission blocked. Errors: {errors}, Warnings: {warnings}")
                return False

            self.logger.log_error("Claim did not redirect and no error banner detected.")
            self.take_screenshot("claim_submit_unknown")
            return False

        except Exception as e:
            self.logger.log_error(f"Submit claim threw exception: {str(e)}")
            self.take_screenshot("claim_submit_exception")
            return False

