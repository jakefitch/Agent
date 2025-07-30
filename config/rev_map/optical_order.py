from playwright.sync_api import Page
from core.logger import Logger
from core.base import BasePage, PatientContext, Patient
from typing import Optional
import random
import re

class OpticalOrder(BasePage):
    """Class for handling optical order operations in Revolution EHR."""
    
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        super().__init__(page, logger, context)
        self.base_url = "https://revolutionehr.com/static/#/orders/ordersEnhanced/dashboard"
        self.products_url = "https://revolutionehr.com/static/#/legacy/inventory/products"
    
    def is_loaded(self) -> bool:
        """Check if the orders page is fully loaded by waiting for the badge-danger class.

        Returns:
            bool: True if the page is loaded, False otherwise
        """
        try:
            self.logger.log("Checking if orders page is loaded...")
            # Wait for the badge-danger class to be present
            self.page.wait_for_selector('.badge.badge-danger', timeout=15000)
            self.logger.log("Orders page is loaded")
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to check if orders page is loaded: {str(e)}")
            return False
    
    def navigate_to_orders(self):
        """Navigate to the orders dashboard page."""
        try:
            self.page.goto(self.base_url)
            self.logger.log("Navigated to orders dashboard")

            # Wait for network to settle and for the dashboard to appear
            self.wait_for_network_idle(timeout=20000)

            if not self.is_loaded():
                raise Exception("Orders page failed to load after navigation")
                
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to orders page: {str(e)}")
            self.take_screenshot("Failed to navigate to orders page")
            raise

    def navigate_to_products(self):
        """Navigate to the products inventory page."""
        try:
            self.logger.log("Navigating to products page...")
            self.page.goto(self.products_url)
            
            # Add a small delay to ensure the page has time to load
            self.page.wait_for_timeout(2000)  # 2 second delay
            
            # Wait for at least one danger button to be visible
            danger_buttons = self.page.locator('.btn.btn-xs.btn-danger.ng-scope').all()
            if not danger_buttons:
                raise Exception("Products page failed to load - no danger buttons found")
                
            self.logger.log("Successfully navigated to products page")
            
        except Exception as e:
            self.logger.log_error(f"Failed to navigate to products page: {str(e)}")
            self.take_screenshot("Failed to navigate to products page")
            raise

    def scrape_frame_data(self, patient: Patient):
        """Scrape frame data from the frame tab and store it in the patient's frames dictionary.
        
        Args:
            patient: Patient object to store the frame data in
        """
        try:
            self.logger.log("Scraping frame data...")

            # Click on the frame tab
            self.page.locator('[data-test-id="frameInformationTab"]').click()

            # Initialize frames dictionary if it doesn't exist
            if not hasattr(patient, 'frames'):
                patient.frames = {}

            def get_text(selector: str, default: str) -> str:
                loc = self.page.locator(selector)
                return (loc.text_content() or default).strip() if loc.count() > 0 else default

            patient.frames['model'] = get_text("//div[@data-test-id='frameProductSelectionStyleSection']//p[@class='form-control-static']", 'unknown')
            patient.frames['manufacturer'] = get_text("//div[@data-test-id='frameProductSelectionManufacturerSection']//p[@class='form-control-static']", 'unknown')
            patient.frames['collection'] = get_text("//div[@data-test-id='frameProductSelectionCollectionSection']//p[@class='form-control-static']", patient.frames['manufacturer'])
            patient.frames['color'] = get_text("//label[text()='Color']/following-sibling::div/p[@class='form-control-static']", 'unknown')

            temple_text = get_text("//label[text()='Temple']/following-sibling::div/p[@class='form-control-static']", '135')[:3]
            try:
                patient.frames['temple'] = temple_text if int(temple_text) >= 100 else '135'
            except ValueError:
                patient.frames['temple'] = '135'

            # Set material randomly
            patient.frames['material'] = random.choice(['zyl', 'metal'])

            patient.frames['eyesize'] = get_text("//label[text()='Eye']/following-sibling::div/p[@class='form-control-static']", '54')[:2]
            patient.frames['dbl'] = get_text("//label[text()='Bridge']/following-sibling::div/p[@class='form-control-static']", '17')[:2]

            self.logger.log("Successfully scraped frame data")
        except Exception as e:
            self.logger.log_error(f"Failed to scrape frame data: {str(e)}")
            self.take_screenshot("Failed to scrape frame data")
            raise

    def scrape_lens_data(self, patient: Patient):
        """Scrape lens data from the lens tab and store it in the patient's dictionaries.
        
        Args:
            patient: Patient object to store the lens data in
        """
        try:
            self.logger.log("Scraping lens data...")
            
            # Click on the lens tab
            lens_tab = self.page.locator('[data-test-id="rxLensInformationTab"]')
            lens_tab.click()
            self.page.wait_for_timeout(1000)
            
            # Initialize dictionaries if they don't exist
            if not hasattr(patient, 'lenses'):
                patient.lenses = {}
            if not hasattr(patient, 'medical_data'):
                patient.medical_data = {}
            
            # Parse prescription table using BeautifulSoup for faster access
            soup = self.get_page_soup()

            def parse_rx_table(table_soup):
                row = table_soup.find('tbody').find('tr')
                cells = row.find_all('td')

                def split_cell(idx):
                    if idx >= len(cells):
                        return '', ''
                    parts = cells[idx].decode_contents().split('<br/>')
                    right = parts[0].strip() if parts else ''
                    left = parts[1].strip() if len(parts) > 1 else ''
                    return right, left

                return {
                    'od_sph': split_cell(2)[0],
                    'os_sph': split_cell(2)[1],
                    'od_cyl': split_cell(3)[0],
                    'os_cyl': split_cell(3)[1],
                    'od_axis': split_cell(4)[0],
                    'os_axis': split_cell(4)[1],
                    'od_add': split_cell(5)[0],
                    'os_add': split_cell(5)[1],
                    'od_h_prism': split_cell(7)[0],
                    'os_h_prism': split_cell(7)[1],
                    'od_h_base': split_cell(8)[0],
                    'os_h_base': split_cell(8)[1],
                    'od_v_prism': split_cell(9)[0],
                    'os_v_prism': split_cell(9)[1],
                    'od_v_base': split_cell(10)[0],
                    'os_v_base': split_cell(10)[1],
                }

            table = soup.select_one("table[data-test-id='eyeglassPrescriptionTable']")
            if table:
                patient.medical_data.update(parse_rx_table(table))
            else:
                self.logger.log("Prescription table not found, falling back to locators")
                # Helper function to get values from table cells using locators
                def get_table_values(selector):
                    element = self.page.locator(selector)
                    inner_html = element.inner_html()
                    parts = inner_html.split("<br>")
                    return {
                        'right': parts[0].strip() if parts[0].strip() else '',
                        'left': parts[1].strip() if len(parts) > 1 and parts[1].strip() else ''
                    }

                sph = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(3)")
                cyl = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4)")
                axis = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(5)")
                add = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(6)")
                h_prism = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(8)")
                h_base = get_table_values("td.nostretch:nth-child(9)")
                v_prism = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(10)")
                v_base = get_table_values("td.nostretch:nth-child(11)")

                patient.medical_data.update({
                    'od_sph': sph['right'],
                    'os_sph': sph['left'],
                    'od_cyl': cyl['right'],
                    'os_cyl': cyl['left'],
                    'od_axis': axis['right'],
                    'os_axis': axis['left'],
                    'od_add': add['right'],
                    'os_add': add['left'],
                    'od_h_prism': h_prism['right'],
                    'os_h_prism': h_prism['left'],
                    'od_h_base': h_base['right'],
                    'os_h_base': h_base['left'],
                    'od_v_prism': v_prism['right'],
                    'os_v_prism': v_prism['left'],
                    'od_v_base': v_base['right'],
                    'os_v_base': v_base['left']
                })
            
            # Get PD measurements
            od_pd = self.page.locator("//*[@data-test-id='eyeglassLensMeasurementsOdSection']//input[@type='text' and @placeholder='MPD-D']").input_value()
            os_pd = self.page.locator("//*[@data-test-id='eyeglassLensMeasurementsOsSection']//input[@type='text' and @placeholder='MPD-D']").input_value()
            dpd = self.page.locator('[data-test-id="lensMeasurementsDistancePdStepper"] input[type="text"]').input_value()
            seg_height = self.page.locator("//*[@formcontrolname='segHeight']//input[@type='text' and @placeholder='']").first.input_value()
            
            # Store measurements in medical_data
            patient.medical_data.update({
                'od_pd': od_pd,
                'os_pd': os_pd,
                'dpd': dpd,
                'seg_height': seg_height
            })
            
            # Try to get lens details from estimator first ---THIS IS WHAT"S SLOWING US DOWN
            vsp_estimator_present = bool(soup.select_one('[data-test-id="EyefinityEyeglassListItemOptionFormGroup"]'))
            
            if vsp_estimator_present:
                # This is a VSP estimator order
                lens_element = self.page.locator('//*[@placeholder="Select Lens Style"]').first
                lens_value = lens_element.inner_html()
                match = re.search(r'<option[^>]*>([^<]+)</option>', lens_value)
                lens_description = match.group(1) if match else ''
                
                material_element = self.page.locator('//*[@placeholder="Select Material"]').first
                material = material_element.input_value()
                ar_element = self.page.locator('//*[@placeholder="Select AR"]').first
                ar = ar_element.input_value()
                lens_type_element = self.page.locator('//*[@placeholder="Select Type"]').first
                lens_type = lens_type_element.input_value()

            else:
                # Fall back to manual lens data
                material = self.page.locator('//*[@data-test-id="eyeglassLensOptionsMaterial"]').text_content()
                ar = self.page.locator('//*[@data-test-id="eyeglassLensCoatingsArCoatingsSection"]').text_content()
                
                # Process AR value
                if '(A)' in ar:
                    ar = "Other (AR Coating A)"
                elif '(C)' in ar or '(C, Teir 2)' in ar:
                    ar = "Lab Choice (AR Coating C) (AR Coating C)"
                elif ar == 'AR Coating':
                    ar = ''
                
                # Determine lens type
                lens_type_element = self.page.locator('//*[@data-test-id="lensDetailsManufacturerModelSection"]').first
                lens_type_data = lens_type_element.text_content()
                lens_type = 'Single Vision' if 'sv' in lens_type_data.lower() else 'PAL'
                lens_description = "SV Poly W/ AR"
            
            # Process material string - remove "Material" prefix if present
            if material.startswith('Material'):
                material = material[8:].strip()  # Remove "Material" and any extra spaces
            
            # Process lens description for AR information
            if lens_description:
                ar_match = re.search(r'w/?\s*/\s*ar\s*[:=]?\s*([^,]+)', lens_description.lower())
                if ar_match:
                    ar = ar_match.group(1).strip()
            
            # Store lens details in lenses dictionary
            patient.lenses.update({
                'type': lens_type,
                'ar': ar,
                'material': material,
                'description': lens_description
            })
            
            # Check for photochromatic in lens description and claims
            photochromatic = False
            
            # Check lens description for PhotoFusion or similar photochromatic indicators
            if lens_description and any(keyword in lens_description.lower() for keyword in ['photofusion', 'photochromic', 'photo']):
                photochromatic = True
                self.logger.log(f"Detected photochromatic from lens description: {lens_description}")
            
            # Check claims for V2744 code (photochromics)
            if hasattr(patient, 'claims') and patient.claims:
                for claim in patient.claims:
                    if claim.vcode and claim.vcode.upper().startswith('V2744'):
                        photochromatic = True
                        self.logger.log(f"Detected photochromatic from claim code: {claim.vcode}")
                        break
            
            # Check billed_items as fallback (for backward compatibility)
            if hasattr(patient, 'billed_items') and patient.billed_items:
                for item in patient.billed_items:
                    if item.get('code', '').upper().startswith('V2744'):
                        photochromatic = True
                        self.logger.log(f"Detected photochromatic from billed item: {item.get('code')}")
                        break
            
            patient.lenses['photochromatic'] = photochromatic
            
            # Check for lens material in claims and billed items
            if hasattr(patient, 'claims') and patient.claims:
                for claim in patient.claims:
                    code = claim.vcode.upper() if claim.vcode else ''
                    if code.startswith('V2784'):
                        patient.lenses['material'] = 'Polycarbonate'
                        self.logger.log(f"Set material to Polycarbonate from claim: {claim.vcode}")
                        break
                    elif code.startswith('V2783'):
                        patient.lenses['material'] = 'High Index'
                        self.logger.log(f"Set material to High Index from claim: {claim.vcode}")
                        break
                else:
                    if not patient.lenses.get('material'):
                        patient.lenses['material'] = 'CR-39'
                        self.logger.log("Set material to CR-39 (default)")
            
            # Check billed_items as fallback (for backward compatibility)
            elif hasattr(patient, 'billed_items') and patient.billed_items:
                for item in patient.billed_items:
                    code = item.get('code', '').upper()
                    if code.startswith('V2784'):
                        patient.lenses['material'] = 'Polycarbonate'
                        break
                    elif code.startswith('V2783'):
                        patient.lenses['material'] = 'High Index'
                        break
                else:
                    if not patient.lenses.get('material'):
                        patient.lenses['material'] = 'CR-39'
            
            self.logger.log("Successfully scraped lens data")
            
        except Exception as e:
            self.logger.log_error(f"Failed to scrape lens data: {str(e)}")
            self.take_screenshot("Failed to scrape lens data")
            raise 

    def scrape_optical_copay(self, patient: Patient):
        """Scrape copay data from the billing tab and update the patient's insurance data.
        
        Args:
            patient: Patient object to store the copay data in
        """
        try:
            self.logger.log("Scraping copay data...")
            
            # Click on the billing tab
            billing_tab = self.page.locator('[data-test-id="billingTab"]')
            billing_tab.click()
            self.page.wait_for_timeout(1000)
            
            # Try estimator method first
            try:
                copay_field = self.page.locator("(//*[@col-id='patientTotal'])[last()]")
                copay_value = copay_field.inner_html()
                copay_value = copay_value.replace("$", "")
                
            except:
                # Fall back to manual method
                self.logger.log("Estimator method failed, trying manual method...")
                
                # Click on billable items tab
                billable_items = self.page.locator('[data-test-id="assignedItemsTab"]')
                billable_items.click()
                self.page.wait_for_timeout(1000)
                
                # Get invoice ID
                invoice_id = self.page.locator("(//*[@col-id='invoiceId'])[2]").text_content()
                
                # Find and click invoice link
                invoice_link = self.page.locator(f"//*[@data-test-id='payersInvoicesTable']//a[contains(text(), '{invoice_id}')]")
                invoice_link.click()
                self.page.wait_for_timeout(2000)
                
                # Get copay value
                copay_field = self.page.locator('[data-test-id="invoiceDetailAggregateTableAdjustableTotalAmount"]')
                copay_value = copay_field.inner_html()
                copay_value = copay_value.replace("$", "").replace("-", "")
                
                # Close invoice modal
                close_button = self.page.locator('[data-test-id="invoiceDetailsModalCloseButton"]')
                close_button.click()
            
            # Update patient's insurance data with copay
            if not hasattr(patient, 'insurance_data'):
                patient.insurance_data = {}
            
            patient.insurance_data['copay'] = copay_value
            self.logger.log(f"Successfully updated copay in insurance data to: {copay_value}")
            
        except Exception as e:
            self.logger.log_error(f"Failed to scrape copay data: {str(e)}")
            self.take_screenshot("Failed to scrape copay data")
            raise 

    def close_order(
        self,
        order_number: Optional[str] = None,
        close_all: bool = False,
    ) -> int:
        """Close optical order tabs.

        In RevolutionEHR multiple order detail tabs may be open at the same
        time.  This helper will close a specific order, close all, or by
        default close the most recently opened tab.

        Args:
            order_number: Order number to close. Ignored if ``close_all`` is
                ``True``.
            close_all: If ``True`` close all open order tabs.

        Returns:
            int: Number of tabs closed.
        """

        try:
            self.logger.log(
                f"Closing order tabs - number={order_number}, all={close_all}"
            )

            tab_spans = self.page.locator(
                "[data-test-id^='#'][data-test-id$='.navigationTab']"
            )

            if close_all:
                count = tab_spans.count()
                for i in range(count - 1, -1, -1):
                    span = tab_spans.nth(i)
                    close_icon = span.locator(
                        "xpath=../../span[contains(@class,'e-close-icon')]"
                    )
                    close_icon.click()
                    span.wait_for(state="detached", timeout=5000)
                self.logger.log(f"Closed {count} order tab(s)")
                return count

            if order_number:
                span = self.page.locator(
                    f"[data-test-id='#{order_number}.navigationTab']"
                )
                if span.count() == 0:
                    self.logger.log(f"Order tab #{order_number} not found")
                    return 0
                close_icon = span.locator(
                    "xpath=../../span[contains(@class,'e-close-icon')]"
                )
                close_icon.click()
                span.wait_for(state="detached", timeout=5000)
                self.logger.log(f"Closed order tab #{order_number}")
                return 1

            count = tab_spans.count()
            if count == 0:
                self.logger.log("No order tabs found to close")
                return 0

            span = tab_spans.nth(count - 1)
            tab_name = span.inner_text().strip()
            close_icon = span.locator(
                "xpath=../../span[contains(@class,'e-close-icon')]"
            )
            close_icon.click()
            span.wait_for(state="detached", timeout=5000)
            self.logger.log(f"Closed last order tab {tab_name}")
            return 1

        except Exception as e:
            self.logger.log_error(f"Failed to close order tab(s): {str(e)}")
            self.take_screenshot("Failed to close order tab")
            raise
