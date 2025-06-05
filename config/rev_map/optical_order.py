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
        """Check if the orders page is fully loaded.

        Returns:
            bool: True if the page is loaded, False otherwise
        """
        try:
            self.logger.log("Checking if orders page is loaded...")
            # Wait for the main dashboard container
            self.page.wait_for_selector('[data-test-id="ordersEnhancedDashboard"]', timeout=15000)
            # Ensure at least one row of the orders table is visible
            self.page.wait_for_selector("//table[@role='presentation']/tbody/tr", timeout=15000)
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
            
            # Wait for the products table to be visible
            products_table = self.page.locator('[data-test-id="productsTable"]').is_visible(timeout=5000)
            if not products_table:
                raise Exception("Products page failed to load")
                
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
            frame_tab = self.page.locator('[data-test-id="frameInformationTab"]')
            for _ in range(5):  # Try up to 5 times
                try:
                    frame_tab.click()
                    break
                except:
                    self.page.wait_for_timeout(1000)
                    continue
            
            self.page.wait_for_timeout(1000)

            # Initialize frames dictionary if it doesn't exist
            if not hasattr(patient, 'frames'):
                patient.frames = {}

            # Scrape model
            try:
                frame = self.page.locator("//div[@data-test-id='frameProductSelectionStyleSection']//p[@class='form-control-static']")
                patient.frames['model'] = frame.text_content() or 'unknown'
            except:
                patient.frames['model'] = 'unknown'

            # Scrape manufacturer
            try:
                manufacturer = self.page.locator("//div[@data-test-id='frameProductSelectionManufacturerSection']//p[@class='form-control-static']")
                patient.frames['manufacturer'] = manufacturer.text_content() or 'unknown'
            except:
                patient.frames['manufacturer'] = 'unknown'

            # Scrape collection
            try:
                collection = self.page.locator("//div[@data-test-id='frameProductSelectionCollectionSection']//p[@class='form-control-static']")
                patient.frames['collection'] = collection.text_content() or patient.frames['manufacturer']
            except:
                patient.frames['collection'] = patient.frames['manufacturer']

            # Scrape color
            try:
                frame_color = self.page.locator("//div[@data-test-id='frameColorSection']//p[@class='form-control-static']")
                patient.frames['color'] = frame_color.text_content() or 'unknown'
            except:
                patient.frames['color'] = 'unknown'

            # Scrape temple
            try:
                temple = self.page.locator("//label[text()='Temple']/following-sibling::div/p[@class='form-control-static']")
                temple_text = temple.text_content()[:3] if temple.text_content() else '135'
                patient.frames['temple'] = '135' if int(temple_text) < 100 else temple_text
            except:
                patient.frames['temple'] = '135'

            # Set material randomly
            patient.frames['material'] = random.choice(['zyl', 'metal'])

            # Scrape eyesize
            try:
                eyesize = self.page.locator("//label[text()='Eye']/following-sibling::div/p[@class='form-control-static']")
                patient.frames['eyesize'] = eyesize.text_content()[:2] if eyesize.text_content() else '54'
            except:
                patient.frames['eyesize'] = '54'

            # Scrape dbl
            try:
                dbl = self.page.locator("//label[text()='Bridge']/following-sibling::div/p[@class='form-control-static']")
                patient.frames['dbl'] = dbl.text_content()[:2] if dbl.text_content() else '17'
            except:
                patient.frames['dbl'] = '17'

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
            
            # Helper function to get values from table cells
            def get_table_values(selector):
                element = self.page.locator(selector)
                inner_html = element.inner_html()
                parts = inner_html.split("<br>")
                return {
                    'right': parts[0].strip() if parts[0].strip() else '',
                    'left': parts[1].strip() if len(parts) > 1 and parts[1].strip() else ''
                }
            
            # Get prescription data
            sph = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(3)")
            cyl = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4)")
            axis = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(5)")
            add = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(6)")
            h_prism = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(8)")
            h_base = get_table_values("td.nostretch:nth-child(9)")
            v_prism = get_table_values("table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(10)")
            v_base = get_table_values("td.nostretch:nth-child(11)")
            
            # Store prescription data in medical_data
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
            dpd = self.page.locator("//*[@data-test-id='eyeglassLensMeasurementsBinocularSection']//input[@type='text' and @placeholder='']").input_value()
            seg_height = self.page.locator("//*[@formcontrolname='segHeight']//input[@type='text' and @placeholder='']").input_value()
            
            # Store measurements in medical_data
            patient.medical_data.update({
                'od_pd': od_pd,
                'os_pd': os_pd,
                'dpd': dpd,
                'seg_height': seg_height
            })
            
            # Try to get lens details from estimator first
            try:
                lens_element = self.page.locator('//*[@placeholder="Select Lens Style"]')
                lens_value = lens_element.inner_html()
                match = re.search(r'<option[^>]*>([^<]+)</option>', lens_value)
                lens_description = match.group(1) if match else ''
                
                material = self.page.locator('//*[@placeholder="Select Material"]').input_value()
                ar = self.page.locator('//*[@placeholder="Select AR"]').input_value()
                lens_type = self.page.locator('//*[@placeholder="Select Type"]').input_value()
                
            except:
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
                lens_type_element = self.page.locator('//*[@data-test-id="lensDetailsManufacturerModelSection"]')
                lens_type_data = lens_type_element.text_content()
                lens_type = 'Single Vision' if 'sv' in lens_type_data.lower() else 'PAL'
                lens_description = "SV Poly W/ AR"
            
            # Store lens details in lenses dictionary
            patient.lenses.update({
                'type': lens_type,
                'ar': ar,
                'material': material,
                'description': lens_description
            })
            
            # Check for photochromatic in billed items
            patient.lenses['photochromatic'] = any(
                item['code'].upper().startswith('V2744') 
                for item in patient.billed_items
            )
            
            # Check for lens material in billed items
            for item in patient.billed_items:
                code = item['code'].upper()
                if code.startswith('V2784'):
                    patient.lenses['material'] = 'Polycarbonate'
                    break
                elif code.startswith('V2783'):
                    patient.lenses['material'] = 'High Index'
                    break
            else:
                patient.lenses['material'] = 'CR-39'
            
            self.logger.log("Successfully scraped lens data")
            
        except Exception as e:
            self.logger.log_error(f"Failed to scrape lens data: {str(e)}")
            self.take_screenshot("Failed to scrape lens data")
            raise 

    def scrape_copay(self, patient: Patient):
        """Scrape copay data from the billing tab and update the patient's claims dictionary.
        
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
            
            # Update patient's claims dictionary with copay
            if not hasattr(patient, 'claims'):
                patient.claims = []
            
            # Add copay to the first claim if it exists, otherwise create a new claim
            if patient.claims:
                current_copay = float(patient.claims[0].get('copay', 0))
                new_copay = float(copay_value)
                patient.claims[0]['copay'] = str(current_copay + new_copay)
            else:
                patient.claims.append({'copay': copay_value})
            
            self.logger.log(f"Successfully updated copay in claims to: {patient.claims[0]['copay']}")
            
        except Exception as e:
            self.logger.log_error(f"Failed to scrape copay data: {str(e)}")
            self.take_screenshot("Failed to scrape copay data")
            raise 

    def close_all_orders(self):
        """Closes all open optical order tabs by finding and clicking all close icons."""
        try:
            self.logger.log("Attempting to close all optical order tabs...")
            
            # Switch to the first tab
            self.page.bring_to_front()
            
            # Find all close icons for optical order tabs
            close_icons = self.page.locator("span.e-close-icon").all()
            
            if not close_icons:
                self.logger.log("No optical order tabs found to close")
                return
                
            self.logger.log(f"Found {len(close_icons)} optical order tabs to close")
            
            # Click each close icon
            for icon in close_icons:
                try:
                    icon.click()
                    self.page.wait_for_timeout(500)  # Small delay between clicks
                except Exception as e:
                    self.logger.log_error(f"Failed to close a tab: {str(e)}")
                    continue
                    
            self.logger.log("Finished attempting to close all optical order tabs")
            
        except Exception as e:
            self.logger.log_error(f"Error while closing optical order tabs: {str(e)}")
            self.take_screenshot("Failed to close optical order tabs")
            raise 