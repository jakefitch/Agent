from time import sleep
from selenium.webdriver.common.by import By
from my_classes import MyAutomation
from vsp import submit_claim
from vsp import submit_steps
from vsp import open_new_claim
import tkinter as tk



place = "Amarillo"
automation = MyAutomation(location=place)
automation.load_pages_vsp()
automation.switch_to_tab(0)

def run():
    submit_claim(automation)

def loop(success_count, failed_claims):
    # Initial fetching of elements
    claims = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
    # Count the number of claims found
    count = len(claims)
    print(f'Found {count} claims')

    # Use a while loop instead of for loop to avoid stale elements
    index = 0
   
    while index < count:
        # Fetch elements fresh each time to avoid stale references
        sleep(1)
        for i in range(5):
            try:
                elements = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
                sleep(1)
                elements[index].click()
                break
            except Exception as e:
                print(f"Error fetching elements:{e}")
                sleep(1)
        #elements = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
        #sleep(1)
        # Click on the current element
        #elements[index].click()
        sleep(1)
        element = automation.wait_for_element(By.CSS_SELECTOR, 'span[data-test-id="invoiceDetailsDocsAndImagesTab"]')
        badge_span = element.find_element(By.CSS_SELECTOR, 'span.badge.margin-left-xs')
        needs_to_be_submitted = False
        if badge_span.text.strip():  # Check if it has content (remove leading/trailing spaces)
            decision = "Already Submitted"
            sleep(1)
        else:
            decision = "Needs to be Submitted"
            needs_to_be_submitted = True
        print(decision)
        sleep(1)
        if needs_to_be_submitted:
            try:
                submit_claim(automation)
                success_count += 1
            except Exception as e:
                print(f"Error submitting claim:{e}")
                # If there is an error, store the name and DOS
                automation.switch_to_tab(0)
                name = "John Doe"
                dos = "01/01/2024"
                try:
                    name = automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceHeaderPatientNameLink"]').text
                    dos = automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceDetailsServiceDate"]').text
                except Exception as e:
                    print(f"Error fetching name and DOS:{e}")
                failed_claims.append((name, dos))
                sleep(2)
                automation.switch_to_tab(0)
                automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerParentNavigateButtonaccounting']").click()
                sleep(1)
                automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerChildNavigateButtoninvoices']").click()
                sleep(1)
                automation.wait_for_element(By.XPATH, "//*[@data-test-id='invoiceDetailsDetailTab']").click()
        sleep(2)        
        # Click the back button element
        close = automation.wait_for_element(By.XPATH, '//*[substring(@id, string-length(@id) - string-length("1") + 1) = "1"]//span[@title="Close"]')
        close.click()
        
        # Increment the index to move to the next element
        index += 1

def submit_multiple_claims():
    success_count = 0
    failed_claims = []
    automation.switch_to_tab(0)
    while True:  
        # Wait for and find the "Go to next page" element
        next_page = automation.wait_for_element(By.XPATH, '//*[@title="Go to next page"]')
        next_page_class = next_page.get_attribute("class")
        
        # Check if the "next page" button is disabled
        if "e-disable" in next_page_class or "e-prevpagedisabled" in next_page_class:
            loop(success_count, failed_claims)
            print("No more pages")
            break  # Exit the loop if the next page button is disabled
        else:
            loop(success_count, failed_claims)
            sleep(2)
            next_page = automation.wait_for_element(By.XPATH, '//*[@title="Go to next page"]')  
            next_page.click()
            sleep(2)  # Click the next page button if not disabled

    # Now you can use the success_count and failed_claims in your new function
    print(f"Total successful claims submitted: {success_count}")
    print(f"Claims that failed to submit: {failed_claims}")
    # Call your function here to send a message with this information via Telegram
    #send_message(success_count, failed_claims)
    #close the automation browser
    automation.close_browser()

def open_second_window():
    submit_steps(automation)

def loop_claims_pages_for_success():
    automation.switch_to_tab(0)
    while True:  

        # Wait for and find the "Go to next page" element
        next_page = automation.wait_for_element(By.XPATH, '//*[@title="Go to next page"]')
        next_page_class = next_page.get_attribute("class")
        
        # Check if the "next page" button is disabled
        if "e-disable" in next_page_class or "e-prevpagedisabled" in next_page_class:
            check_for_success()
            break  # Exit the loop if the next page button is disabled
        else:
            check_for_success()
            sleep(2)
            next_page = automation.wait_for_element(By.XPATH, '//*[@title="Go to next page"]')  
            next_page.click() 
            sleep(2) # Click the next page button if not disabled
                
def new_claim():
    open_new_claim(automation)

def check_for_success():
    automation.switch_to_tab(0)
    claims = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
    # Count the number of claims found
    count = len(claims)   
    index = 0
    claim_count = 0
    
    while index < count:
        sleep(.5)
        elements = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
        sleep(.5)
        elements[index].click()
        sleep(.5)
        element = automation.wait_for_element(By.CSS_SELECTOR, 'span[data-test-id="invoiceDetailsDocsAndImagesTab"]')
        badge_span = element.find_element(By.CSS_SELECTOR, 'span.badge.margin-left-xs')

        if badge_span.text.strip():  # Check if it has content (remove leading/trailing spaces)
            sleep(.5)
        else:
            name = automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceHeaderPatientNameLink"]')  
            #print(f'Claim for {name.text} needs to be submitted')  
            claim_count += 1
        close = automation.wait_for_element(By.XPATH, '//*[substring(@id, string-length(@id) - string-length("1") + 1) = "1"]//span[@title="Close"]')
        close.click() 
        index += 1
    print(f'{claim_count} claims need to be submitted')

# Create the tkinter window
window = tk.Tk()
window.title("VSP Submitter")
window.attributes("-topmost", True)  # Make the window stay on top

# Create the buttons
go_button = tk.Button(window, text="Submit All", command=submit_multiple_claims)
go_button.pack(pady=10)

run_button = tk.Button(window, text="Submit One", command=run)
run_button.pack(pady=10)

# Create a button in the main window to open the second window
steps_button = tk.Button(window, text="Custom Lens", command=open_second_window)
steps_button.pack(pady=10)

#create a button to open a new vsp claim
new_claim_button = tk.Button(window, text="New Claim", command=new_claim)
new_claim_button.pack(pady=10)

# Create a button to check for success
success_button = tk.Button(window, text="Check for Success", command=loop_claims_pages_for_success)
success_button.pack(pady=10)

# Start the tkinter event loop
window.mainloop()
        
