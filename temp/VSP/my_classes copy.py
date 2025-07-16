
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import pyperclip
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import random
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import os
import shutil
from dotenv import load_dotenv

#set the .env path
env_path = '/home/jake/Code/.env'
load_dotenv(env_path, override=True)


class MyAutomation:
    def __init__(self, location, headless=False, page_load_timeout=15):
        # Create Firefox options
        options = Options()
        
        # Set headless mode dynamically based on the argument
        if headless:
            options.add_argument("--headless")
        
        # Set the browser to start maximized
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1920")  # Ensure proper window size in headless mode
        
        # Initialize the Firefox driver with the specified options
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_page_load_timeout(page_load_timeout)
        
        # Set location and file paths
        self.location = location
        self.driver.set_window_size(1920,1920)
        self.base_pdf_file_path = "/home/jake/Documents/file.pdf"

    def save_pdf(self, print_button_xpath, new_file_name):
        try:
            # Find the print button using the provided xpath and click it
            print_button = self.wait_for_element(By.XPATH, print_button_xpath)
            print_button.click()
            
            # Add a delay to ensure the print action completes
            sleep(5)  # Adjust this time as necessary

            # Define the new file path based on the provided name
            new_file_path = f"/home/jake/Documents/{new_file_name}.pdf"

            # Rename the file to the desired name
            shutil.move(self.base_pdf_file_path, new_file_path)
            
            print(f"PDF saved and renamed to {new_file_path}.")
        except NoSuchElementException:
            print(f"Print button not found with xpath: {print_button_xpath}")
        except Exception as e:
            print(f"An error occurred while saving the PDF: {str(e)}")

    def execute_script(self, script, *args):
        return self.driver.execute_script(script, *args)


    def get_pdf_file_path_by_location(self):
        if self.location == "Amarillo":
            return "/home/optibot/patient_benefits"
        elif self.location == "Borger":
            return "/home/optibot/GoogleDrive/Patient Benefits"
        else:
            return None
        
    def press_tab(self):
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.TAB).perform()


    def send_keys(self, keys):
        actions = ActionChains(self.driver)
        actions.send_keys(keys).perform()


    def open_new_tab(self, url=None):
        self.driver.execute_script("window.open('','_blank');")
        # Switch to the new tab (it will be the last one)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        if url:
            self.navigate_to_site(url)

    def execute_script(self, script):
        self.driver.execute_script(script)


    def switch_to_tab(self, tab_index):
        self.driver.switch_to.window(self.driver.window_handles[tab_index])

    def close_tab(self):
        self.driver.close()


    def navigate_to_site(self, url):
        self.driver.get(url)

    def wait_for_element(self, by_method, value, timeout=10):
        try:
            element_located = EC.presence_of_element_located((by_method, value))
            return WebDriverWait(self.driver, timeout).until(element_located)
        except TimeoutException:
            print(f"Timed out waiting for element with {by_method} = {value}")
            return None

    def short_wait_for_element(self, by_method, value, timeout=4):
        try:
            element_located = EC.presence_of_element_located((by_method, value))
            return WebDriverWait(self.driver, timeout).until(element_located)
        except TimeoutException:
            print(f"Timed out waiting for element with {by_method} = {value}")
            return None

    def find_element(self, by_method, value):
        return self.driver.find_element(by_method, value)

    def login(self, username_locator, password_locator, username, password):
        try:
            username_element = self.wait_for_element(*username_locator)
            password_element = self.wait_for_element(*password_locator)

            if username_element and password_element:
                username_element.send_keys(username)
                password_element.send_keys(password)
                password_element.send_keys(Keys.RETURN)
            else:
                print("Failed to find the required elements for login.")
        except Exception as e:
            print(f"An error occurred during login: {str(e)}")

    def close_browser(self):
        self.driver.quit()

    def number_of_tabs(self):
        return len(self.driver.window_handles)

    def wait_for_clickable(self, by_method, value, timeout=10):
        try:
            element_located = EC.element_to_be_clickable((by_method, value))
            return WebDriverWait(self.driver, timeout).until(element_located)
        except TimeoutException:
            print(f"Timed out waiting for element with {by_method} = {value} to become clickable")
            return None
    def extended_wait_for_clickable(self, by_method, value, timeout=120):
        try:
            element_located = EC.element_to_be_clickable((by_method, value))
            return WebDriverWait(self.driver, timeout).until(element_located)
        except TimeoutException:
            print(f"Timed out waiting for element with {by_method} = {value} to become clickable")
            return None
    def short_wait_for_clickable(self, by_method, value, timeout=3):
        try:
            element_located = EC.element_to_be_clickable((by_method, value))
            return WebDriverWait(self.driver, timeout).until(element_located)
        except TimeoutException:
            print(f"Timed out waiting for element with {by_method} = {value} to become clickable")
            return None

    def wait_for_elements(self, by_method, value, timeout=10):
        try:
            elements_located = EC.presence_of_all_elements_located((by_method, value))
            return WebDriverWait(self.driver, timeout).until(elements_located)
        except TimeoutException:
            print(f"Timed out waiting for elements with {by_method} = {value}")
            return []
        
    #def short wait for elements
    def short_wait_for_elements(self, by_method, value, timeout=4):
        try:
            elements_located = EC.presence_of_all_elements_located((by_method, value))
            return WebDriverWait(self.driver, timeout).until(elements_located)
        except TimeoutException:
            print(f"Timed out waiting for elements with {by_method} = {value}")
            return []
        

    

    def click_until_successful(self, element, max_attempts=5):
        attempts = 0
        while attempts < max_attempts:
            try:
                # Check if the element is clickable
                if element.is_enabled() and element.is_displayed():
                    element.click()
                    break  # Exit the loop if the click was successful
                else:
                    print("Element not clickable, retrying...")
                    time.sleep(1)  # Optional: Wait a second before retrying
            except StaleElementReferenceException:
                print("Element has become stale, retrying...")
                attempts += 1
                continue
        else:  # This block runs if the loop ends without a break (i.e., all attempts failed)
            print("Failed to click the element after all attempts")

    def wait_for_page_to_be_still(self, timeout=10):
        old_page = self.driver.page_source
        try:
            WebDriverWait(self.driver, timeout).until(lambda driver: driver.page_source != old_page)
        except TimeoutException:
            print('timed out waiting for page to be still')

    def get_page_source(self):
        return self.driver.page_source


    def scroll_until_element_found(self, element_locator, max_attempts=10):
        attempts = 0
        while attempts < max_attempts:
            try:
                # Check if the element is present using expected conditions
                element_present = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(element_locator)
                )

                # If element is found, return it
                return element_present

            except Exception as e:
                # Scroll down the page using JavaScript
                self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
                attempts += 1

        # If the element is not found after the maximum attempts, return None
        return None

    def scroll_element_into_view(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            print("Element scrolled into view.")
        except Exception as e:
            print(f"An error occurred while scrolling: {e}")

    def switch_to_frame(self, by_method=None, value=None, frame_element=None):
        try:
            if frame_element:
                # If an element is passed directly, switch to it
                self.driver.switch_to.frame(frame_element)
            elif by_method and value:
                # If a locator is provided, find the frame first and then switch to it
                frame_element = self.wait_for_element(by_method, value)
                if frame_element:
                    self.driver.switch_to.frame(frame_element)
                else:
                    print(f"Unable to locate the frame with {by_method} = {value}")
            else:
                print("You must provide either a frame element or a locator.")
        except NoSuchElementException as e:
            print(f"An error occurred while switching to the frame: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")

    def switch_to_default_content(self):
        try:
            self.driver.switch_to.default_content()
        except Exception as e:
            print(f"An error occurred while switching to the default content: {str(e)}")



    def load_pages_vsp(self):
        #load revolution
        rev_username = os.environ.get("rev_username")
        rev_password = os.environ.get("rev_password")
        self.navigate_to_site("https://revolutionehr.com/static/")
        username_locator = (By.CSS_SELECTOR, '[placeholder="Username"]')
        password_locator = (By.CSS_SELECTOR, "div.form-group:nth-child(2) > div:nth-child(1) > input:nth-child(2)")
        self.wait_for_element(*username_locator)
        self.wait_for_element(*password_locator)
        self.login(username_locator, password_locator, rev_username, rev_password)
        self.switch_to_tab(0)


        #load vsp in amarillo
        self.open_new_tab("https://www.eyefinity.com")
        vsp_login_button = self.wait_for_element(By.CSS_SELECTOR, "#eyefinity-lgn")
        selector = "#eyefinity-lgn"
        script = f"document.querySelector('{selector}').click();"
        self.execute_script(script)
        sleep(3)
        self.execute_script("window.stop();")
        sleep(2)

        vsp_username = os.environ.get("vsp_username")
        vsp_password = os.environ.get("vsp_password")
        send_vsp_user = self.wait_for_element(By.ID, "username")
        send_vsp_user.send_keys(vsp_username)
        send_vsp_pwd = self.wait_for_element(By.ID, "password")
        send_vsp_pwd.send_keys(vsp_password)
        vsp_login_button = self.wait_for_element(By.ID, "btnLogin")
        vsp_login_button.click()
        sleep(2)
        self.navigate_to_site('https://eclaim.eyefinity.com/secure/eInsurance/member-search')
        

    def load_pages_vsp_borger(self):
        #load revolution
        rev_username = os.environ.get("rev_username")
        rev_password = os.environ.get("rev_password")
        self.navigate_to_site("https://revolutionehr.com/static/")
        username_locator = (By.CSS_SELECTOR, '[placeholder="Username"]')
        password_locator = (By.CSS_SELECTOR, "div.form-group:nth-child(2) > div:nth-child(1) > input:nth-child(2)")
        self.wait_for_element(*username_locator)
        self.wait_for_element(*password_locator)
        self.login(username_locator, password_locator, rev_username, rev_password)
        self.switch_to_tab(0)


        #load vsp in amarillo
        self.open_new_tab("https://www.eyefinity.com")
        vsp_login_button = self.wait_for_element(By.CSS_SELECTOR, "#eyefinity-lgn")
        selector = "#eyefinity-lgn"
        script = f"document.querySelector('{selector}').click();"
        self.execute_script(script)
        sleep(3)
        self.execute_script("window.stop();")
        sleep(2)


        send_vsp_user = self.wait_for_element(By.ID, "username")
        send_vsp_user.send_keys("8062742020")
        send_vsp_pwd = self.wait_for_element(By.ID, "password")
        send_vsp_pwd.send_keys("32655")
        vsp_login_button = self.wait_for_element(By.ID, "btnLogin")
        vsp_login_button.click()
        sleep(2)
        self.navigate_to_site('https://eclaim.eyefinity.com/secure/eInsurance/member-search')




    def get_value(self, by_method, value):
        element = self.wait_for_element(by_method, value)
        if element:
            return element.get_attribute('value')
        else:
            print("Failed to find the element.")
            return None

    def switch_to_new_tab(self):
        try:
            # Wait for the new tab to open
            WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > 1)
            # Switch to the new tab (it will be the last one in the window handles list)
            self.driver.switch_to.window(self.driver.window_handles[-1])
        except TimeoutException:
            print("New tab did not open in time")

    def close_tab_and_switch_back(self):
        # Close the current tab
        self.driver.close()
        # Switch back to the original tab
        self.driver.switch_to.window(self.driver.window_handles[0])

    def capture_frame_content(self, frame_locator):
        try:
            # Switch to the frame
            self.driver.switch_to.frame(self.driver.find_element(*frame_locator))
            # Get the frame's content
            frame_content = self.driver.page_source
            # Switch back to the default content
            self.driver.switch_to.default_content()
            return frame_content
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def random_sleep(self, base_time=1):
        sleep_time = base_time + random.uniform(0, 2)  # Adjust the 1 to change the maximum random addition
        import time
        time.sleep(sleep_time)
        
    def print_frame_to_pdf(self, frame_element, pdf_filename):
        try:
            # Switch to the frame
            self.driver.switch_to.frame(frame_element)
            # Get the frame's content
            frame_content = self.driver.page_source
            # Switch back to the default content
            self.driver.switch_to.default_content()
            # Create PDF from the frame's content
            #HTML(string=frame_content).write_pdf(pdf_filename)
            print(f'PDF saved as {pdf_filename}')
        except Exception as e:
            print(f"An error occurred: {e}")
            
    def copy_text_from_element(self, by_method, value):
        try:
            # Find the element
            element = self.wait_for_element(by_method, value)
            if element:
                # Create an ActionChain for keyboard actions
                actions = ActionChains(self.driver)

                # Move to the element, click to focus, select all text, and copy
                actions.move_to_element(element).click().key_down(Keys.CONTROL).send_keys('a').send_keys('c').key_up(Keys.CONTROL).perform()

                # Get the copied text from the clipboard
                copied_text = pyperclip.paste()
                return copied_text
            else:
                print("Element not found for copying text.")
                return None
        except Exception as e:
            print(f"An error occurred while copying text from element: {e}")
            return None


class Member:
    def __init__(self,
        member_list=None,
        location=None,
        first_name=None,
        last_name=None,
        date_of_birth=None,
        group_number=None,
        active=None,
        memberid=None,
        authorization=None,
        exam_type=None,
        dos=None,
        doctor=None,
        diagnoses=None,
        copay="0",
        address=None,
        state=None,
        zipcode=None,
        gender=None,
        billed_items=None,
        seg_height=None,
        od_sph=None,
        od_cyl=None,
        od_axis=None,
        od_add=None,
        od_pd=None,
        od_h_prism=None,
        od_v_prism=None,
        od_h_base=None,
        od_v_base=None,
        os_h_prism=None,
        os_v_prism=None,
        os_h_base=None,
        os_v_base=None,
        os_sph=None,
        os_cyl=None,
        os_axis=None,
        os_add=None,
        os_pd=None,
        dpd=None,
        wholesale=None,
        manafacturer=None,
        collection=None,
        model=None,
        color=None,
        temple=None,
        material=None,
        eyesize=None,
        dbl=None,
        lens=None,
        lens_material=None,
        lens_ar=None,
        lens_type=None,
        photochromatic=None,
        sucess=False,
    ):
        self.seg_height = seg_height
        self.location = location 
        self.member_list = member_list
        self.wholesale = wholesale #done
        self.od_h_prism = od_h_prism #done 
        self.od_v_prism = od_v_prism #done
        self.od_h_base = od_h_base #done
        self.od_v_base = od_v_base #done
        self.os_h_prism = os_h_prism #done
        self.os_v_prism = os_v_prism #done
        self.os_h_base = os_h_base #done
        self.os_v_base = os_v_base #done
        self.od_sph = od_sph #done
        self.od_cyl = od_cyl #done
        self.od_axis = od_axis #done
        self.od_add = od_add #done
        self.od_pd = od_pd #done
        self.os_sph = os_sph #done     
        self.os_cyl = os_cyl #done
        self.os_axis = os_axis #done
        self.os_add = os_add #done
        self.os_pd = os_pd #done
        self.dpd = dpd #done
        self.first_name = first_name #done
        self.last_name = last_name #done
        self.date_of_birth = date_of_birth #done
        self.group_number = group_number
        self.active = active #done
        self.memberid = memberid #done
        self.authorization = authorization #done
        self.exam_type = exam_type #done
        self.dos = dos #done
        self.doctor = doctor #done
        self.diagnoses = diagnoses #done
        self.copay = copay #partially done -- may need to pull copay from optical order? 
        self.address = address 
        self.state = state  
        self.zipcode = zipcode
        self.gender = gender #done
        self.billed_items = billed_items #done
        self.manafacturer = manafacturer #done
        self.collection = collection #done
        self.model = model #done
        self.color = color #done
        self.temple = temple #done
        self.material = material #done
        self.eyesize = eyesize #done
        self.dbl = dbl #done
        self.lens = lens
        self.lens_material = lens_material #done    
        self.lens_ar = lens_ar #done
        self.lens_type = lens_type #done
        self.photochromatic = photochromatic
        self.sucess = sucess
    

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.date_of_birth})"










    