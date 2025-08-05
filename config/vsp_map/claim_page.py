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
        # Path to the most recent popup screenshot, if any
        self.last_screenshot_path: Optional[str] = None

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

    def _fill_with_verification(
        self,
        locator,
        value: str,
        field_name: str,
        max_attempts: int = 3,
    ) -> bool:
        """Fill a field and verify the value matches what was sent.

        Args:
            locator: Playwright locator for the input field.
            value: The value to set on the field.
            field_name: Name used for logging.
            max_attempts: Number of times to retry filling the field.

        Returns:
            bool: True if the field was set successfully, False otherwise.
        """
        for attempt in range(max_attempts):
            try:
                locator.click()
            except Exception:
                pass

            locator.fill(value)
            self.page.wait_for_timeout(500)

            current_value = ""
            try:
                current_value = locator.input_value()
            except Exception:
                try:
                    current_value = locator.evaluate("el => el.value")
                except Exception:
                    current_value = locator.text_content() or ""

            if current_value == value:
                self.logger.log(
                    f"{field_name} successfully set on attempt {attempt + 1}"
                )
                return True

            self.logger.log(
                f"{field_name} verification failed on attempt {attempt + 1}: "
                f"expected '{value}', got '{current_value}'"
            )
            self.page.wait_for_timeout(500)

        self.logger.log_error(
            f"Failed to set {field_name} after {max_attempts} attempts"
        )
        return False

    # ------------------------------------------------------------------
    # High level workflows
    def fill_rx(self, patient: Patient) -> None:
        """Fill the prescription and pricing information for the claim."""
        self.send_rx(patient)
        
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
            # First click of calculate button
            self.page.locator('#claim-tracker-calculate').click()
            sleep(2)
            
            # Check for acknowledge button and handle it
            try:
                acknowledge_button = self.page.locator('button.acknowledge-button')
                if acknowledge_button.is_visible(timeout=3000):
                    self.logger.log("Acknowledge button found, clicking it...")
                    acknowledge_button.click()
                    sleep(1)
                    
                    # Click calculate button again after acknowledging
                    self.logger.log("Clicking calculate button again after acknowledge...")
                    self.page.locator('#claim-tracker-calculate').click()
                    sleep(2)
                else:
                    self.logger.log("No acknowledge button found, proceeding...")
            except Exception as e:
                self.logger.log(f"Error checking for acknowledge button: {str(e)}")
            
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
                    fsa_locator = self.page.locator("#services-fsa-paid-input")
                    if fsa_locator.is_visible(timeout=1000):
                        self._fill_with_verification(
                            fsa_locator, copay, "FSA paid amount"
                        )

            except Exception as e:
                self.logger.log_error(f"Error setting FSA paid amount: {str(e)}")

            self.logger.log("Scrolling to patient paid section...")
            self.page.evaluate("window.scrollTo(0, 4400)")
            self.page.wait_for_timeout(3000)
            
            try:
                paid = self.page.locator("#services-patient-paid-amount-input")
                if copay:
                    self.logger.log("Setting patient paid amount...")
                    if not self._fill_with_verification(
                        paid, copay, "patient paid amount"
                    ):
                        raise Exception("Patient paid amount verification failed")
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
            
            # Get lens type from lenses dictionary, similar to submit_lens method
            lens_data = getattr(patient, "lenses", {}) or {}
            lens_type = lens_data.get("type", "Single Vision")
            if lens_type != 'Single Vision':
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
        if material =="High Index":
            material = "Plastic Hi Index"
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
        elif ar == "Lab Choice (AR Coating D) (AR Coating D)" and material == "Plastic Hi Index" and lens_type == "Single Vision":
            design = "Stock 1.67 Aspheric w/ Premium AR (D) - Clear"
        elif ar == "Other (AR Coating A)" and material == "Plastic Hi Index" and lens_type == "Single Vision":
            design = "Stock 1.67 Aspheric - Clear"
      
    
    

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
        
        The VSP reports page opens as a completely new browser window.
        We need to find this window and then process it.
        
        Returns:
            bool: True if popup was handled successfully, False otherwise
        """
        try:
            self.logger.log("=== POPUP WINDOW HANDLING START ===")
            
            # Get the browser context
            browser_context = self.page.context
            
            # Get all current pages and log them
            all_pages = browser_context.pages
            self.logger.log(f"Current page count: {len(all_pages)}")
            
            # Log details of all pages
            for i, page in enumerate(all_pages):
                try:
                    url = page.url
                    title = page.title()
                    self.logger.log(f"Page {i}: URL={url}, Title={title}")
                except Exception as e:
                    self.logger.log(f"Page {i}: Error getting details - {str(e)}")
            
            # First, try to find an existing VSP reports page
            vsp_reports_page = None
            
            for i, page in enumerate(all_pages):
                try:
                    url = page.url
                    title = page.title()
                    
                    # Look for VSP reports page or any page that's not the original
                    if (page != self.page and 
                        ("doctor.vsp.com/reports" in url or 
                         "vsp.com" in url or
                         "eyefinity.com" in url or
                         "reports" in url.lower() or
                         "benefit" in url.lower())):
                        vsp_reports_page = page
                        self.logger.log(f"Found VSP reports page at index {i}: {url}")
                        break
                except Exception as e:
                    self.logger.log(f"Error checking page {i}: {str(e)}")
                    continue
            
            # If we didn't find a specific VSP page, try to find any page that's not the original
            if not vsp_reports_page:
                self.logger.log("No specific VSP page found, looking for any non-original page...")
                for i, page in enumerate(all_pages):
                    if page != self.page:
                        try:
                            url = page.url
                            title = page.title()
                            self.logger.log(f"Found non-original page at index {i}: {url}")
                            vsp_reports_page = page
                            break
                        except Exception as e:
                            self.logger.log(f"Error checking non-original page {i}: {str(e)}")
                            continue
            
            # If still no page found, wait for a new page to appear
            if not vsp_reports_page:
                self.logger.log("No existing popup found, waiting for new popup window to open...")
                
                # Get initial page count
                initial_pages = len(browser_context.pages)
                self.logger.log(f"Initial page count: {initial_pages}")
                
                # Wait for a new page to appear (up to 10 seconds)
                max_wait_time = 10000  # 10 seconds
                wait_interval = 500    # Check every 500ms
                waited_time = 0
                
                while waited_time < max_wait_time:
                    current_pages = browser_context.pages
                    if len(current_pages) > initial_pages:
                        self.logger.log(f"New page detected! Current count: {len(current_pages)}")
                        break
                    
                    self.page.wait_for_timeout(wait_interval)
                    waited_time += wait_interval
                
                if len(browser_context.pages) > initial_pages:
                    # Find the new page (should be the last one)
                    all_pages = browser_context.pages
                    vsp_reports_page = all_pages[-1]  # Last page should be the popup
                    self.logger.log(f"Using new page as popup: {vsp_reports_page.url}")
                else:
                    self.logger.log_error("No new popup window detected within timeout")
                    return False
            
            if not vsp_reports_page:
                self.logger.log_error("No suitable popup page found")
                return False
            
            # Process the VSP reports page
            return self._process_vsp_reports_page(vsp_reports_page)
            
        except Exception as e:
            self.logger.log_error(f"Popup window handling failed: {str(e)}")
            return False

    def check_existing_popups(self) -> bool:
        """Check if there are any existing popup windows that we can process.
        
        This method looks for any existing pages that might be VSP reports
        and processes them directly.
        
        Returns:
            bool: True if an existing popup was found and processed, False otherwise
        """
        try:
            self.logger.log("=== CHECKING EXISTING POPUPS ===")
            
            # Get the browser context
            browser_context = self.page.context
            all_pages = browser_context.pages
            
            self.logger.log(f"Checking {len(all_pages)} existing pages...")
            
            # Log all pages for debugging
            for i, page in enumerate(all_pages):
                try:
                    url = page.url
                    title = page.title()
                    self.logger.log(f"Page {i}: URL={url}, Title={title}")
                    
                    # Check if this page is a VSP reports page
                    if (page != self.page and 
                        ("doctor.vsp.com/reports" in url or 
                         "vsp.com" in url or
                         "eyefinity.com" in url or
                         "reports" in url.lower() or
                         "benefit" in url.lower() or
                         "secure.eyefinity.com" in url)):
                        
                        self.logger.log(f"Found existing VSP reports page at index {i}: {url}")
                        return self._process_vsp_reports_page(page)
                        
                except Exception as e:
                    self.logger.log(f"Error checking page {i}: {str(e)}")
                    continue
            
            self.logger.log("No existing VSP reports pages found")
            return False
            
        except Exception as e:
            self.logger.log_error(f"Error checking existing popups: {str(e)}")
            return False

    def handle_popup_with_expect_popup(self) -> bool:
        """Handle the VSP report popup using Playwright's expect_popup().

        This is now the primary popup handler. It searches for common
        "View"/"Report" buttons, waits for the popup window, processes it,
        and closes the popup when finished.

        Returns:
            bool: True if popup was handled successfully, False otherwise
        """
        try:
            self.logger.log("=== EXPECT POPUP HANDLING START ===")
            
            # Look for the "View Doctor Reports" button or similar
            # This might be the button that triggers the popup
            report_buttons = [
                "//span[text()='View Doctor Reports']",
                "//button[contains(text(), 'View')]",
                "//button[contains(text(), 'Report')]",
                "//a[contains(text(), 'View')]",
                "//a[contains(text(), 'Report')]",
                "#view-reports-button",
                "[data-testid='view-reports']",
                "button:has-text('View')",
                "button:has-text('Report')",
                "a:has-text('View')",
                "a:has-text('Report')"
            ]
            
            self.logger.log(f"Searching for {len(report_buttons)} different button selectors...")
            
            button_found = False
            for i, button_selector in enumerate(report_buttons):
                try:
                    self.logger.log(f"Trying button selector {i+1}/{len(report_buttons)}: {button_selector}")
                    button = self.page.locator(button_selector)
                    
                    # Check if button exists and is visible
                    count = button.count()
                    self.logger.log(f"Button count: {count}")
                    
                    if count > 0:
                        is_visible = button.is_visible(timeout=2000)
                        self.logger.log(f"Button visible: {is_visible}")
                        
                        if is_visible:
                            button_text = button.text_content()
                            self.logger.log(f"Found report button: {button_selector} (text: '{button_text}')")
                            button_found = True
                            
                            # Use expect_popup to handle the popup
                            with self.page.expect_popup() as popup_info:
                                button.click()
                            
                            popup = popup_info.value
                            popup.wait_for_load_state()
                            self.logger.log("✅ Popup window opened successfully")
                            
                            # Process the popup
                            result = self._process_vsp_reports_page(popup)
                            
                            # Close the popup
                            popup.close()
                            self.logger.log("🧹 Popup window closed")
                            
                            return result
                    else:
                        self.logger.log(f"Button selector {button_selector} not found (count: 0)")
                        
                except Exception as e:
                    self.logger.log(f"Button {button_selector} error: {str(e)}")
                    continue
            
            if not button_found:
                self.logger.log("No report button found with known selectors")

            return button_found
            
        except Exception as e:
            self.logger.log_error(f"Expect popup handling failed: {str(e)}")
            return False

    def _process_vsp_reports_page(self, reports_page) -> bool:
        """Process the VSP reports page directly.
        
        This method handles the complete flow:
        1. Wait for the page to load
        2. Handle login if required
        3. Access the rptPage frame
        4. Extract PDF data
        5. Save and process the report
        
        Args:
            reports_page: The VSP reports page object
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            self.logger.log("=== PROCESSING VSP REPORTS PAGE ===")
            self.logger.log(f"Reports page URL: {reports_page.url}")
            self.logger.log(f"Reports page title: {reports_page.title()}")
            
            # Wait for the page to be fully loaded
            reports_page.wait_for_load_state("domcontentloaded")
            self.logger.log("Reports page loaded successfully")
            
            # Take a screenshot for debugging
            try:
                screenshot_path = f"logs/screenshots/vsp_reports_{int(time.time())}.png"
                reports_page.screenshot(path=screenshot_path)
                self.logger.log(f"Reports page screenshot saved: {screenshot_path}")
                # Store path for later retrieval
                self.last_screenshot_path = screenshot_path
            except Exception as e:
                self.logger.log(f"Failed to take screenshot: {str(e)}")
            
            # Check for login requirement
            try:
                username_input = reports_page.locator("#username")
                if username_input.is_visible(timeout=3000):
                    self.logger.log("🔐 Login required on VSP reports page")
                    
                    # Load VSP credentials from environment
                    try:
                        from dotenv import load_dotenv
                        import os
                        load_dotenv("/home/jake/Code/.env")
                        
                        # Try to use the same credentials as the main session
                        ama_username = os.getenv("vsp_username")
                        bgr_username = os.getenv("vsp_borger_username")
                        vsp_password = os.getenv("vsp_password")
                        
                        if not all([ama_username, bgr_username, vsp_password]):
                            self.logger.log_error("Missing VSP credentials in environment")
                            return False
                        
                        # Use AMA username as default (you might want to make this configurable)
                        username = ama_username
                        
                        username_input.fill(username)
                        reports_page.locator("#password").fill(vsp_password)
                        reports_page.locator("button[type='submit']").click()
                        reports_page.wait_for_load_state()
                        self.logger.log("🔓 Logged in successfully to VSP reports page")
                        
                    except Exception as login_error:
                        self.logger.log_error(f"Failed to login to VSP reports page: {str(login_error)}")
                        return False
            except Exception:
                self.logger.log("✅ No login required")
            
            # Wait for the rptPage frame to appear
            try:
                reports_page.wait_for_selector("#rptPage", timeout=10000)
                self.logger.log("Found rptPage frame selector")
            except Exception as e:
                self.logger.log(f"Could not find rptPage frame selector: {str(e)}")
                # Continue anyway, might be a different structure
            
            # Log all frames for debugging
            try:
                frames = reports_page.frames
                self.logger.log(f"Found {len(frames)} frames in reports page")
                for i, frame in enumerate(frames):
                    self.logger.log(f"  Frame {i}: name={frame.name}, url={frame.url}")
            except Exception as e:
                self.logger.log(f"Failed to enumerate frames: {str(e)}")
            
            # Try to access the rptPage frame (main content)
            rpt_page = None
            try:
                rpt_page = reports_page.frame(name="rptPage")
                if rpt_page:
                    self.logger.log("Successfully accessed rptPage frame")
                else:
                    self.logger.log_error("Could not find rptPage frame")
                    return False
            except Exception as e:
                self.logger.log_error(f"Failed to access rptPage frame: {str(e)}")
                return False
            
            # Wait for the frame content to load
            try:
                rpt_page.wait_for_load_state("domcontentloaded")
                self.logger.log("rptPage frame loaded successfully")
            except Exception as e:
                self.logger.log(f"Failed to wait for rptPage load: {str(e)}")
            
            # Take a screenshot of the report content
            try:
                screenshot_path = f"logs/screenshots/report_content_{int(time.time())}.png"
                rpt_page.screenshot(path=screenshot_path)
                self.logger.log(f"Report content screenshot saved: {screenshot_path}")
            except Exception as e:
                self.logger.log(f"Failed to take report screenshot: {str(e)}")

            # Enumerate toolbar/menu buttons for debugging
            try:
                toolbar_buttons = rpt_page.locator("button")
                btn_count = toolbar_buttons.count()
                self.logger.log(f"Found {btn_count} buttons in report frame")
                for i in range(min(btn_count, 10)):
                    btn = toolbar_buttons.nth(i)
                    label = btn.get_attribute("aria-label") or btn.text_content()
                    self.logger.log(f"  Button {i}: {label}")
            except Exception as e:
                self.logger.log(f"Failed to enumerate toolbar buttons: {str(e)}")

            # Log a small snippet of the frame HTML for debugging
            try:
                html_preview = rpt_page.content()[:500]
                self.logger.log(f"Frame HTML preview: {html_preview[:200]}...")
            except Exception as e:
                self.logger.log(f"Failed to get frame HTML preview: {str(e)}")
            
            # Try to extract PDF data from embed element
            pdf_extracted = self._extract_pdf_from_embed(rpt_page)
            
            # Try to download/print the report as fallback
            if not pdf_extracted:
                download_success = self.try_download_report(rpt_page)
            else:
                download_success = True
            
            # Close the reports page
            try:
                reports_page.close()
                self.logger.log("Reports page closed")
            except Exception as e:
                self.logger.log(f"Failed to close reports page: {str(e)}")
            
            self.logger.log("=== VSP REPORTS PAGE PROCESSING COMPLETED ===")
            return download_success or pdf_extracted
            
        except Exception as e:
            self.logger.log_error(f"Failed to process VSP reports page: {str(e)}")
            return False

    def _extract_pdf_from_embed(self, rpt_page) -> bool:
        """Extract PDF data from embed element in the rptPage frame.
        
        Args:
            rpt_page: The rptPage frame object
            
        Returns:
            bool: True if PDF was extracted successfully, False otherwise
        """
        try:
            self.logger.log("Attempting to extract PDF from embed element...")
            
            # Look for embed element with PDF
            embed = rpt_page.locator("embed[type='application/pdf']")
            if embed.count() == 0:
                self.logger.log("No PDF embed element found")
                return False
            
            # Get the src attribute
            src = embed.get_attribute("src")
            if not src:
                self.logger.log("No src attribute found on embed element")
                return False
            
            self.logger.log("Found PDF embed src attribute")
            
            # Check if it's a base64 PDF
            prefix = 'data:application/pdf;base64,'
            if not src.startswith(prefix):
                self.logger.log("Embed src is not a Base64 PDF")
                return False
            
            # Decode base64 PDF
            import base64
            base64_data = src[len(prefix):]
            try:
                pdf_bytes = base64.b64decode(base64_data)
                
                # Generate filename with timestamp
                timestamp = int(time.time())
                filename = f"logs/vsp_benefit_report_{timestamp}.pdf"
                
                # Ensure logs directory exists
                import os
                os.makedirs("logs", exist_ok=True)
                
                with open(filename, 'wb') as f:
                    f.write(pdf_bytes)
                self.logger.log(f"✅ PDF saved as {filename}")
                
                # Try to extract text from PDF
                self._extract_text_from_pdf(filename)
                
                return True
                
            except Exception as e:
                self.logger.log_error(f"Base64 decode or file write failed: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Failed to extract PDF from embed: {str(e)}")
            return False

    def _extract_text_from_pdf(self, pdf_filename: str) -> None:
        """Extract text from PDF and log key information.
        
        Args:
            pdf_filename: Path to the PDF file
        """
        try:
            # Try to import PyPDF2
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                self.logger.log("PyPDF2 not available, skipping text extraction")
                return
            
            reader = PdfReader(pdf_filename)
            text = ''.join([p.extract_text() or '' for p in reader.pages])
            
            # Extract key information using regex patterns
            import re
            patterns = {
                "Exam/ProfSvcs": r'Exam/ProfSvcs(.*?)Lens',
                "Lens": r'Lens(.*?)Frame',
                "Frame": r'Frame(.*?)$',
            }
            
            extracted = {}
            for label, pattern in patterns.items():
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    extracted[label] = match.group(1).strip()
                    self.logger.log(f"🧾 {label}: {extracted[label]}")
                else:
                    self.logger.log(f"🧾 {label}: Not found")
            
            self.logger.log("PDF text extraction completed")
            
        except Exception as e:
            self.logger.log_error(f"Failed to extract text from PDF: {str(e)}")

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
            # Reset stored screenshot path for this submission attempt
            self.last_screenshot_path = None
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
                    time.sleep(5)
                    self.logger.log("Clicked yes button in success modal")
                    self.wait_for_network_idle(timeout=5000)
                    
                    # Step 5: Handle popup window using expect_popup
                    self.logger.log("Attempting to handle popup window with expect_popup...")
                    popup_success = self.handle_popup_with_expect_popup()
                    if popup_success:
                        self.logger.log("Popup handling completed successfully with expect_popup")
                        return True
                    else:
                        self.logger.log("Popup handling failed using expect_popup")
                    
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

