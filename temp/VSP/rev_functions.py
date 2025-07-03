# Description: This file contains the functions that are used in the test cases
from selenium.webdriver.common.by import By
from time import sleep
from selenium.common.exceptions import StaleElementReferenceException




# create a function that finds the element where row-index="0" by using the MyAutomation class
def loop_rows(automation,eob_data):
    count = 0
    while True:
        next_element = None
        next_element = automation.wait_for_element(By.XPATH, f'//*[@row-index="{count}"]')      
        if next_element is None:
            print("No more patients")
            print_remaining_items(eob_data)
            break
        #look through data to find potential matches
        find_matches(automation,eob_data,count)

        #tab down to bring new elements into view
        payment_amount_element = automation.wait_for_element(By.XPATH, f'//*[@row-index="{count}"]//*[@col-id="paymentAmount"]')
        payment_amount_element.click()
        automation.press_tab()
        count +=1



def find_matches(automation, eob_data, count):

    name_element = automation.wait_for_element(By.XPATH, f'//*[@row-index="{count}"]//*[@col-id="patientName"]')
    date_element = automation.wait_for_element(By.XPATH, f'//*[@row-index="{count}"]//*[@col-id="serviceDate"]')

    # Loop through the eob_data and try to find a matching name
    for patient_data in eob_data:
        name_element = automation.wait_for_element(By.XPATH, f'//*[@row-index="{count}"]//*[@col-id="patientName"]')
        name, dos, billed_items, total = patient_data
        if ", " not in name:
            continue
        last_name, first_name = name.split(", ")
        last_name = last_name.strip().capitalize()
        first_name = first_name.strip().capitalize()
        #make the first and last name all upper
        last_name = last_name.upper()
        first_name = first_name.upper()
        


    

        # Strip any text after the first 4 characters of the first name
        first_name = first_name[:4]
        last_name = last_name[:4]
        
        #add 20 to the year of service date and a 0 if the month is only one digit so the string matches the date format in the table from 1/01/21 to 01/01/2021 when searching dates
        #dos = dos.split("/")
        #dos[2] = "20" + dos[2]
        #if len(dos[0]) == 1:
            #dos[0] = "0" + dos[0]
        #if len(dos[1]) == 1:
            #dos[1] = "0" + dos[1]
        #dos = "/".join(dos)
        
        
    
        
        #print(f'looking for {first_name} {last_name} for dos {dos}')
        
        #ignore case when searching for the name by converting the name element text to uppercase
        name_element_text = name_element.text.upper()
        #remove hyphens from the name element text
        name_element_text = name_element_text.replace("-", "")
        #remove spaces from the name element text
        name_element_text = name_element_text.replace(" ", "")
        #remove commas from the name element text
        name_element_text = name_element_text.replace(",", "")
        #remove periods from the name element text
        name_element_text = name_element_text.replace(".", "")
        #remove spaces from the name element text
        
        if last_name in name_element_text and first_name in name_element_text:
            # If the date does not match, continue on -- I removed this temporarily. I'm not sure I need it anymore. 
            #if dos != date_element.text:
                #found_date = date_element.text
                #print (f"Found a match for {name} but the date of service, {found_date} does not match")
                #continue

            print(f'found a match for {name} with dos {dos}')

            invoice_opened_successfully = False
            trys = 0
            while not invoice_opened_successfully:
                try:
                    open_invoice(automation, patient_data, count)
                    invoice_opened_successfully = True
                except:
                    print("Invoice did not open successfully, retrying...")
                    trys += 1
                    if trys >= 3:
                        print("Failed to open invoice after 3 attempts, moving on to the next patient.")
                        break
                    continue
            
            #break
        else:
            # Keep going through the data
            continue


    


def open_invoice(automation,patient_data,count):
    name, dos, billed_items, total = patient_data

    #click on the payment amount to open the invoice
    open_invoice_xpath = f'//*[@row-index="{count}"]//*[@col-id="itemsTotal"]//rev-template-cell-renderer//a'
    open_invoice_element = automation.wait_for_element(By.XPATH, open_invoice_xpath)
    open_invoice_element.click()
    reconcile_invoice(automation,patient_data)


    #pass in invoice logic function here
    sleep(2)

    #click on the back button to return to the EOB
    back_button = automation.wait_for_element(By.XPATH, '//*[@data-test-id="receivePaymentModalSaveButton"]')
    back_button.click()
    

#this function can be removed once the combined write off function is working
def reconcile_invoice(automation, patient_data):
    name, dos, billed_items, total = patient_data
    print('Reconciling claim')
    sleep(2)  # Ensure sleep is from time module
    
    paid_invoice_codes = []

    try:
        # Dynamically fetch the count of line items to process them individually
        line_items_count = len(automation.wait_for_elements(By.XPATH, '//*[@role="row"]'))
        
        for i in range(line_items_count):
            # Refetch the item on each iteration to prevent stale references
            item = automation.wait_for_elements(By.XPATH, '//*[@role="row"]')[i]
            
            # Now, find the code element within this item context to avoid stale elements
            try:
                code_elements_count = len(item.find_elements(By.XPATH, './/*[@col-id="invoiceItem.code"]'))
                for j in range(code_elements_count):
                    # Refetch code element by index within the current item context
                    code_element = item.find_elements(By.XPATH, './/*[@col-id="invoiceItem.code"]')[j]
                    code_text = code_element.text
                    
                    
                    
                    
                    #make V2740 and V2745 match no matter which one is found
                    if code_text == 'V2740':
                        code_text = 'V2745'
            
                        
                    
                    #capitolize the code text that is not a number
                    if not code_text.isdigit():
                        code_text = code_text.upper()
                        #print(f'capilolized code text: {code_text}')
                    
                    # Check if the code matches your criteria
                    if not code_text.startswith('9') and not code_text.startswith('V'):
                        continue
                    
                    #if the code text starts with V21, or V22, match all the codes that start with v21 or v22 --- needs testing!!!
    
                    if code_text.startswith('V21') or code_text.startswith('V22') or code_text.startswith('V23'):
                        code_text = 'base_lens'
                        

                    print(f"Found code: {code_text}")

                    # Find and clear the payment amount input
                    payment_amount_element = item.find_element(By.XPATH, './/*[@col-id="paymentAmount"]//input')
                    payment_amount_element.clear()

                
                    
                    # Find the matching billed item and input the payment amount
                    for billed_item in billed_items:
                        
                        #if the billed item starts with V21 or V22, match all the codes that start with V21 or V22,adjust billed item to only be the first three strings
                        if billed_item[0].startswith('V21') or billed_item[0].startswith('V22') or billed_item[0].startswith('V23'):
                            billed_item[0] = 'base_lens'
                            #print(f"Found billed item: {billed_item[0]}") 
                
                        if billed_item[0] == code_text:
                            
                            
                            payment_amount_element.send_keys(billed_item[1])
                            

                            #press tab to move to the next element
                            automation.press_tab()
                            sleep(.5)

                            #balance_element = item.find_element(By.XPATH, './/*[@col-id="balance"]')
                            #balance_text = balance_element.text.replace('$', '')  # Remove '$' if present
                            #transfer_element = item.find_element(By.XPATH, './/*[@col-id="transferAmount1"]//input')
                            #transfer_element.clear()
                            #transfer_element.send_keys(balance_text)
                            #sleep(.5)
                            print(f"Payment amount for {billed_item[1]} has been sent to {code_text}")
                            #append the code text to the invoice codes list
                            paid_invoice_codes.append(code_text)

                            break
                
                    
                    
                        
                    
                        
                    #if billed items were found, remove them from the billed items list
                    for billed_item in billed_items:
                            if billed_item[0] == code_text:
                                billed_items.remove(billed_item)
                                break

                            #break  # Break once the matching billed item is processed
            except StaleElementReferenceException:
                print("Encountered a stale element while processing code elements, moving to next item.")
                continue  # Optionally handle or log the exception as needed
        print(f"Remaining billed items for {name}: {billed_items}")
        
    
                
        
    except StaleElementReferenceException:
        print("Encountered a stale element while fetching line items.")
        # Handle or log as needed, perhaps retry the whole operation if it's critical


    
    check_for_duplicates(automation,paid_invoice_codes)

    

def print_remaining_items(patient_data):
    #only print patient data that still has items in the billed items list
    for patient in patient_data:
        name, dos, billed_items, total = patient
        if billed_items:
            print(name)
            print(dos)
            print(billed_items)
            print(total)
            print("\n")
            
            
def check_for_duplicates(automation,paid_incoice_codes):
    print(f'Checking for duplicates')

    #if paid invoice codes contains 92015, add 92310 to the list
    if '92015' in paid_incoice_codes:
        paid_incoice_codes.append('92310')

    
    
    
  

    try:
        # Dynamically fetch the count of line items to process them individually
        line_items_count = len(automation.wait_for_elements(By.XPATH, '//*[@role="row"]'))
        
        for i in range(line_items_count):
            # Refetch the item on each iteration to prevent stale references
            item = automation.wait_for_elements(By.XPATH, '//*[@role="row"]')[i]
            
            # Now, find the code element within this item context to avoid stale elements
            try:
                code_elements_count = len(item.find_elements(By.XPATH, './/*[@col-id="invoiceItem.code"]'))
                for j in range(code_elements_count):
                    # Refetch code element by index within the current item context
                    code_element = item.find_elements(By.XPATH, './/*[@col-id="invoiceItem.code"]')[j]
                    code_text = code_element.text
                    

                    #capitolize the code text that is not a number
                    if not code_text.isdigit():
                        code_text = code_text.upper()
                        #print(f'capilolized code text: {code_text}')
                    
                    # Check if the code matches your criteria
                    if not code_text.startswith('9') and not code_text.startswith('V'):
                        continue
                    
                    #if the code text starts with V21, or V22, match all the codes that start with v21 or v22 --- needs testing!!!

                    if code_text.startswith('V21') or code_text.startswith('V22') or code_text.startswith('V23'):
                        code_text = 'base_lens'

                    # look for the code text in the paid invoice codes list
                    if code_text in paid_incoice_codes:
                        print(f'Found a duplicate for {code_text}')
                        #find out if there is a zero balance left on the item
                        balance_element = item.find_element(By.XPATH, './/*[@col-id="balance"]')
                        balance_text = balance_element.text.replace('$', '')
                        if balance_text != '0.00':
                            print(f'Balance is {balance_text} for {code_text}')
                            #find the transfer amount input and clear it
                            transfer_element = item.find_element(By.XPATH, './/*[@col-id="transferAmount1"]//input')
                            transfer_element.clear()
                            #send the balance text to the transfer amount input
                            transfer_element.send_keys(balance_text)
                            sleep(.5)
                            #press tab to move to the next element
                            automation.press_tab()
                            print(f"Transfer amount for {code_text} has been set to {balance_text}")
                        else:
                            print(f'Balance is not 0.00 for {code_text}')
                            continue




            except StaleElementReferenceException:
                print("Encountered a stale element while processing code elements, moving to next item.")
                continue

    except StaleElementReferenceException:
        print("Encountered a stale element while fetching line items.")
        # Handle or log as needed, perhaps retry the whole operation if it's critical







  