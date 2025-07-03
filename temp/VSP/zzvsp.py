from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from time import sleep
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
import re
import random
from my_classes import *
import tkinter as tk
import os
import pyautogui


#function that goes through the steps of submitting a claim

def open_new_claim(automation):
    member = Member()
    scrape_invoice(automation,member)
    set_copay(automation,member)
    open_vsp_benefit(automation,member)
    get_vsp_auth_from_rev(automation,member)
    look_for_member(automation,member)
    set_dos(automation,member)

def submit_claim(automation):
    
    member = Member()
    scrape_invoice(automation,member)

    #this part is for borger. It should be removed and tested for full automation
    #if member.location == 2:
        #for item in member.billed_items:
            #if item['code'].startswith('V21'):
                #print('optical order found, Borger will submit claim manually')
                #sleep(3)
                #return
            
    set_copay(automation,member)
    open_vsp_benefit(automation,member)
    get_vsp_auth_from_rev(automation,member)
    get_member_information_to_search_VSP(automation,member)
    

    optical_order = False
    for item in member.billed_items:
        if item['code'].startswith('V21'):
            optical_order = True
            break
    if optical_order == True:
        #print('glasses order found')
        get_eyewear_order(automation,member)
        get_wholesale(automation,member)
        get_frame_data(automation,member)
        get_lens_data(automation,member)
        get_optical_copay(automation,member)
    
    

    if member.authorization is not None:
       # print(f'found auth #: {member.authorization}')
        try:
            automation.switch_to_tab(1)
            automation.navigate_to_site('https://secureb.eyefinity.com/home/')
            sleep(1)
            auth_entry_page = automation.wait_for_element(By.XPATH,  "//a[text()='File Claims']")
            auth_entry_page.click()
            sleep(1)       
            for i in range(20):
                automation.press_tab()
            
            sleep(.5)
            automation.send_keys(member.authorization)
            automation.press_tab()
            automation.send_keys(Keys.ENTER)
        except:
            #print('using auth')
            pass
    
    else:
        #look_for_existing_auth(automation,member)
        look_for_member(automation,member)

    set_dos(automation,member)
    setDr(automation,member)
    submitexam(automation,member)
    submit_cl(automation,member)
    submit_frame(automation,member)
    submit_lens(automation,member)
    sendrx(automation,member)
    diseasereporting(automation,member)
    calculate(automation,member)
    fillpricing(automation,member)
    set_gender(automation,member)
    fill_address(automation,member)
    click_submit_claim(automation,member)
    generate_report(automation,member)
    mark_as_success(automation,member)  


#This function brings up the manual function window for submitting custom jobs not set up for automation

def submit_steps(automation):
    member = Member()
    
    scrape_invoice(automation,member)
    set_copay(automation,member)
    open_vsp_benefit(automation,member)
    get_vsp_auth_from_rev(automation,member)
    get_member_information_to_search_VSP(automation,member)

    

    optical_order = False
    for item in member.billed_items:
        if item['code'].startswith('V21') or item['code'].startswith('V22'):
            optical_order = True
            break
    if optical_order == True:
        #print('glasses order found')
        get_eyewear_order(automation,member)
        get_wholesale(automation,member)
        get_frame_data(automation,member)
        get_lens_data(automation,member)
        get_optical_copay(automation,member)
    
    

    if member.authorization is not None:
        #print(f'found auth #: {member.authorization}')
        try:
            automation.switch_to_tab(1)
            #print(f'switched to vsp tab')
            sleep(1)
            automation.navigate_to_site('https://secureb.eyefinity.com/home/')
            sleep(1)
            auth_entry_page = automation.wait_for_element(By.XPATH,  "//a[text()='File Claims']")
            auth_entry_page.click()
            sleep(1)

            for i in range(20):
                automation.press_tab()         
            sleep(.5)

            automation.send_keys(member.authorization)
            automation.press_tab()
            automation.send_keys(Keys.ENTER)
        except:
            #print('using auth')
            pass
    
    else:
        
        look_for_member(automation,member)
        
    set_dos(automation,member)

    setDr(automation,member)

    submitexam(automation,member)

    submit_cl(automation,member)

    submit_frame(automation,member)
    

    second_window = tk.Tk()  # Create a new top-level window
    second_window.title("Functions")
    second_window.attributes("-topmost", True)  # Make the window stay on top

    fill_rx_button = tk.Button(second_window, text="Add RX and Calculate", command=lambda: fill_rx(automation,member))
    fill_rx_button.pack(pady=10)

    calculate_order_button = tk.Button(second_window, text="Complete Order", command=lambda: calculate_order(automation,member,second_window))
    calculate_order_button.pack(pady=10)

    #position the window over the main window and make it stay on top
    #second_window.geometry("+%d+%d" % (automation.root.winfo_x() + 200, automation.root.winfo_y() + 200))

    second_window.mainloop()  # Start the main loop



#functions for pulling authorizations

def look_for_member(automation, member):
   
    #if member.active = true, skip this function
    if member.active == True:
        return

    search_vsp_by_name(automation,member)
    
    if member.active == False:
        #print(f'searching by name')
        search_vsp_by_id(automation,member)
        
    if member.active == False:
        #print('error finding active member.')
        look_for_existing_auth(automation,member)

    

    
    issue_new_auth_for_appropriate_services(automation,member)


def look_for_existing_auth(automation,member):
    automation.switch_to_tab(1)
    automation.navigate_to_site('https://eclaim.eyefinity.com/secure/eInsurance/auth-tracking')

    try:
    
        sleep(2)
        range_radial = automation.wait_for_clickable(By.XPATH, "//*[@id='auth-tracking-search-by-date-range-radio-button']")
        range_radial.click()
        sleep(1)
        from datetime import datetime, timedelta
        end_date = datetime.strptime(member.dos, '%m/%d/%Y')
        start_date = end_date - timedelta(days=7)
        start_date = start_date.strftime('%m/%d/%Y')
        end_date = end_date.strftime('%m/%d/%Y')
        #print(start_date)
        #print(end_date)
        
        sleep(1)
        auth_start_date = automation.wait_for_element(By.XPATH, "//*[@id='issue-date-start']")
        auth_start_date.clear()
        for char in start_date:
            auth_start_date.send_keys(char)
        
        sleep(1)
        auth_end_date = automation.wait_for_element(By.XPATH, "//*[@id='issue-date-end']")  
        auth_end_date.clear()
        for char in end_date:
            auth_end_date.send_keys(char)
        
        sleep(1)
        auth_search_button = automation.wait_for_element(By.XPATH, "//*[@id='auth-tracking-search-button']")
        auth_search_button.click()
        
        sleep(2)
        
        #scroll to the bottom of the page
        automation.execute_script("window.scrollTo(0, 10000)")
        
        
        authorizations = automation.wait_for_elements(By.XPATH, "//*[contains(@id, 'auth-tracking-result-patient-name-data-')]")
            #print the number of authorizations found
        #print(f'found {len(authorizations)} authorizations')
        #if the lenght is zero, return
        if len(authorizations) == 0:
            #print('no authorizations found')
            return
        
        for authorization in authorizations:
            #print(f'checking {authorization.text.lower()} for {member.last_name[:4].lower()} {member.first_name.lower()}')
            if member.last_name[:4].lower() in authorization.text.lower() and member.first_name[:4].lower() in authorization.text.lower():
                #print('found authorization')
                # Get the attribute 'id' from the authorization element
                xpath_id = authorization.get_attribute('id')
                # Split the id by hyphens and take the last part
                xpath_number = xpath_id.split('-')[-1]
                #print(xpath_number)
                break
        
    
    
        #click on the authorization  --- I can adjust this section of the code to double check DOB, and perhaps issue a new auth with only the service items
        sleep(1)
        auth_link = automation.wait_for_element(By.XPATH, f"//*[@id='auth-tracking-result-claim-number-data-span-{xpath_number}']")
        member.authorization = auth_link.text
        #print(f'auth #: {member.authorization}')
        auth_link.click()
        #set member auth to true
        member.authorization = True
    except:
        #print("error searching for auth in active authorizations")
        pass


def search_vsp_by_name(automation, member):
    try:
        # Log starting the function
        #print("Starting search_vsp_by_name")

        automation.switch_to_tab(1)
        automation.navigate_to_site('https://eclaim.eyefinity.com/secure/eInsurance/member-search')

        # Sending date of service
        vsp_dos_field = automation.wait_for_element(By.CSS_SELECTOR, "#member-search-dos")
        if vsp_dos_field:
            vsp_dos_field.clear()
            for char in member.dos:
                vsp_dos_field.send_keys(char)
            #print(f"Sent DOS: {member.dos}")
        else:
            #print("DOS field not found")
            return

        member.active = False

        for member_info in member.member_list:
            if member.active:
                break
            first_name = member_info['first_name'].strip()
            last_name = member_info['last_name'].strip()
            dob = member_info['dob'].strip()

            # Filling in the first name, last name, and DOB fields
            try:
                vsp_first_field = automation.wait_for_element(By.CSS_SELECTOR, "#member-search-first-name")
                vsp_first_field.clear()
                vsp_first_field.send_keys(first_name)
                #print(f"Sent first name: {first_name}")

                vsp_last_field = automation.wait_for_element(By.CSS_SELECTOR, "#member-search-last-name")
                vsp_last_field.clear()
                vsp_last_field.send_keys(last_name)
                #print(f"Sent last name: {last_name}")

                vsp_dob_field = automation.wait_for_element(By.CSS_SELECTOR, "#member-search-dob")
                vsp_dob_field.clear()
                for char in dob:
                    vsp_dob_field.send_keys(char)
                #print(f"Sent DOB: {dob}")

            except Exception as e:
               #print(f"Error entering member info: {e}")
                continue

            # Click Search
            vsp_search_button = automation.wait_for_element(By.XPATH, "//*[@id='member-search-search-button']")
            if vsp_search_button:
                vsp_search_button.click()
                #("Clicked search")
                sleep(2)
            else:
                #print("Search button not found")
                continue

            # Handle search results
            try:
                vsp_search_result = automation.short_wait_for_element(By.XPATH, "//*[@id='member-search-result-name-data']")
                if vsp_search_result:
                    #print(f"Primary located for {first_name} {last_name}")
                    vsp_search_result.click()
                    sleep(1)

                    # Try to delete old authorizations
                    delete_auth_buttons = automation.short_wait_for_elements(By.XPATH, "//*[@svgicon='eclaim-icons:trash']")
                    if delete_auth_buttons:
                        #print(f"Found {len(delete_auth_buttons)} authorizations")
                        for element in delete_auth_buttons:
                            try:
                                element.click()
                                sleep(1)
                                confirm_delete = automation.wait_for_element(By.XPATH, "//*[@id='okButton']")
                                if confirm_delete:
                                    confirm_delete.click()
                                    sleep(1)
                                    #print(f"Deleted old authorization for {first_name} {last_name}")
                            except Exception as e:
                                #print(f"Error during authorization deletion: {e}")
                                sleep(.1)
                    else:
                        #print("No authorizations found to delete.")
                        sleep(.1)

                    # Handle member selection
                    results = automation.wait_for_elements(By.XPATH, "//*[@id='patient-selection-result-name-data']")
                    for result in results:
                        name = member.first_name.lower()
                        if name in result.text.lower():
                            try:
                                dob_element = result.find_element(By.XPATH, "following-sibling::mat-cell[contains(@id, 'patient-selection-result-city-dob-data')]")
                                if member.date_of_birth in dob_element.text:
                                    #print(f"Found matching member: {member.first_name} {member.last_name}")
                                    member.active = True
                                    result.click()
                                    break
                            except Exception as e:
                                #print(f"Error finding DOB for member {member.first_name}: {e}")
                                continue
                        else:
                            #print(f"Name {member.first_name} not found in results")
                            continue

                    if not member.active:
                        #print(f"No match found for {first_name} {last_name}, returning to search")
                        automation.navigate_to_site('https://eclaim.eyefinity.com/secure/eInsurance/member-search')

                else:
                    #print(f"No results for {first_name} {last_name}")
                    continue
            except Exception as e:
                #print(f"Error during search result processing: {e}")
                continue

        #print("search_vsp_by_name completed")
    except Exception as e:
        #print(f"Error in search_vsp_by_name: {e}")
        sleep(.1)



def search_vsp_by_id(automation, member):
    try:
        #print("Starting search_vsp_by_id")
        sleep(.1)

        # Validate member ID
        if len(member.memberid) < 9 and not any(char.isalpha() for char in member.memberid):
            #print("Invalid member ID")
            member.active = False
            return

        automation.switch_to_tab(1)
        sleep(1)

        automation.navigate_to_site('https://eclaim.eyefinity.com/secure/eInsurance/member-search')

        # Sending date of service
        vsp_dos_field = automation.wait_for_element(By.CSS_SELECTOR, "#member-search-dos")
        if vsp_dos_field:
            vsp_dos_field.clear()
            for char in member.dos:
                vsp_dos_field.send_keys(char)
            #print(f"Sent DOS: {member.dos}")
        else:
            #print("DOS field not found")
            return

        # Enter Member ID
        vsp_full_id_field = automation.wait_for_element(By.CSS_SELECTOR, "#member-search-full-id")
        if vsp_full_id_field:
            vsp_full_id_field.send_keys(member.memberid)
            #print(f"Sent member ID: {member.memberid}")
        else:
            #print("Member ID field not found")
            return

        # Click Search
        vsp_search_button = automation.wait_for_element(By.XPATH, "//*[@id='member-search-search-button']")
        if vsp_search_button:
            vsp_search_button.click()
            #print("Clicked search")
        else:
            #print("Search button not found")
            return

        # Handle search results
        try:
            vsp_search_result = automation.short_wait_for_element(By.XPATH, "//*[@id='member-search-result-name-data']")
            if vsp_search_result:
                #print("Primary located")
                vsp_search_result.click()
                sleep(1)

                # Try to delete old authorizations
                delete_auth_buttons = automation.short_wait_for_elements(By.XPATH, "//*[@svgicon='eclaim-icons:trash']")
                if delete_auth_buttons:
                    #print(f"Found {len(delete_auth_buttons)} authorizations")
                    for element in delete_auth_buttons:
                        try:
                            element.click()
                            sleep(1)
                            confirm_delete = automation.wait_for_element(By.XPATH, "//*[@id='okButton']")
                            if confirm_delete:
                                confirm_delete.click()
                                sleep(1)
                                #print("Deleted old authorization")
                        except Exception as e:
                            #print(f"Error during authorization deletion: {e}")
                            sleep(.1)
                else:
                    #print("No authorizations found to delete.")
                    sleep(.1)
                # Handle member selection
                results = automation.wait_for_elements(By.XPATH, "//*[@id='patient-selection-result-name-data']")
                for result in results:
                    name = member.first_name.lower()
                    first_letter_of_name = member.first_name[0].lower()
                    if name in result.text.lower():
                        try:
                            dob_element = result.find_element(By.XPATH, "following-sibling::mat-cell[contains(@id, 'patient-selection-result-city-dob-data')]")
                            if member.date_of_birth in dob_element.text:
                                #print(f"Found matching member: {member.first_name} {member.last_name}")
                                member.active = True
                                result.click()
                                break
                        except Exception as e:
                            #print(f"Error finding DOB for member {member.first_name}: {e}")
                            sleep(.1)
                    #set name to the first letter of the first name
                    
                    elif first_letter_of_name in result.text.lower():
                        try:
                            dob_element = result.find_element(By.XPATH, "following-sibling::mat-cell[contains(@id, 'patient-selection-result-city-dob-data')]")
                            if member.date_of_birth in dob_element.text:
                                #print(f"Found matching member: {member.first_name} {member.last_name}")
                                member.active = True
                                result.click()
                                break
                        except Exception as e:
                            #print(f"Error finding DOB for member {member.first_name}: {e}")
                            sleep(.1)
                    else:
                        #print(f"Name {member.first_name} not found in results")
                        sleep(.1)

                if not member.active:
                    #print("No matching member found")
                    sleep(.1)

            else:
                #print("No primary search result found")
                sleep(.1)
        except Exception as e:
            #print(f"Error during search result processing: {e}")
            sleep(.1)

        #print("search_vsp_by_id completed")
        sleep(.1)
    except Exception as e:
        #print(f"Error in search_vsp_by_id: {e}")
        sleep(.1)


        

def click_on_primary(automation, member):
#search through the results for primary member
    vsp_search_results = automation.wait_for_elements(By.XPATH, "//*[@id=\"member-search-result-name-data\"]")
    #print('search results found')
    try:
        for element in vsp_search_results:
            name = element.text 
            if member.primary_last_name == None:
                member.primary_last_name = member.last_name
                #print(name)
                patient_lastname=(member.primary_last_name)
            else:
                patient_lastname = member.last_name
            if patient_lastname.lower() in name.lower():
                #print(f'found match for {member.last_name}')
                sleep(2)
                element.click()

                #print(f'clicked on {member.last_name}')
                break
    except:
       # print('last name didnt match')
        vsp_search_results = automation.wait_for_element(By.XPATH, "//mat-cell[contains(@class, 'action-link') and contains(@class, 'nested-column-3') and contains(@class, 'mat-cell') and contains(@class, 'cdk-column-name') and contains(@class, 'mat-column-name') and @role='gridcell']")
        vsp_search_results.click()
        #print('clicked on search result')


def click_on_authorization(automation,member):

    all_mat_rows = automation.wait_for_elements(By.XPATH, "//mat-row")

    # Loop through each row to find the one containing the name  in the specific cell ID
    for row in all_mat_rows:
        try:
            # Try to find the name cell within this row
           # print("searching")
            name_cell = row.find_element(By.XPATH, ".//mat-cell[@id='auth-search-result-name-data']")
            #print('found')
            name_cell_text = name_cell.text
            #print(name_cell_text)
            
            # Check if the name cell contains member information
            if member.first_name.lower() in name_cell_text.lower():
               # print(f'Found Member')
                # If it does, find the auth-number cell in the same row and click it
                auth_cell = row.find_element(By.XPATH, ".//mat-cell[starts-with(@id, 'auth-search-result-auth-number-data')]")
                auth_cell.click()
                member.ins_plan = "VSP"
                break  # Exit the loop, as we've found and clicked the relevant cell
                
        except NoSuchElementException:
            # If either cell is not found in this row, continue to the next row
            #print('no authorizations active' )
            pass


def issue_new_auth_for_appropriate_services(automation,member):  #-------------------------------------------------------- I think this function should say member.active not memeber.authorization

    #print(f'the member status is {member.authorization}. If it is true, the issue new auth function should not run.')
    #print(f'the member status is {member.active}. If it is false, the issue new auth function should not run.')
    if member.active == False:
        #print('no member to get authorization for. Returning')
        return
    #if member.active = true, skip this function
    if member.authorization == True:
        return

    #print(f'running new authorization function')
    new_exam = False
    existing_exam = False

    # Iterate through each dictionary in the list
    for item in member.billed_items:
        if item['code'] == '92004':
            new_exam = True
            #print('patient has new exam')
            break  # Exit the loop if the code is found

    # Iterate through each dictionary in the list
    for item in member.billed_items:
        if item['code'] == '92014':
            existing_exam = True
            #print('patient has existing exam')
            break  # Exit the loop if the code is found

    # Set of codes to check against
    exam_codes = {'92014', '92015', '92004', '92310'}

    # Initialize materials to False
    materials = False

    # Loop through each billed item
    for item in member.billed_items:
        # Check if the code is not in the set of exam codes
        if item['code'] not in exam_codes:
            materials = True
            #print('member has materials')
            break  # Break out of the loop as we found a non-exam code

    

    all_checkbox = automation.wait_for_clickable(By.XPATH, "//mat-checkbox[@id='0-all-available-services-checkbox']")
    exam_checkbox = automation.wait_for_clickable(By.XPATH, "//mat-checkbox[@id='0-service-checkbox-0']")
    lens_checkbox = automation.wait_for_clickable(By.XPATH, "//mat-checkbox[@id='0-service-checkbox-2']")
    frame_checkbox = automation.wait_for_clickable(By.XPATH, "//mat-checkbox[@id='0-service-checkbox-3']")
    contacts_checkbox = automation.wait_for_clickable(By.XPATH, "//mat-checkbox[@id='0-service-checkbox-4']")
    first_checkbox = automation.wait_for_clickable(By.XPATH, "//mat-checkbox[@id='0-service-checkbox-1']")

    if new_exam or existing_exam:
        exam_checkbox.click()
        exam_checkbox = automation.wait_for_clickable(By.XPATH, "//mat-checkbox[@id='0-service-checkbox-0']")


    if materials:
        try:
        #lens_checkbox.click()
        #frame_checkbox.click()
            contacts_checkbox.click()
        except:
            lens_checkbox.click()
            first_checkbox.click()
            #frame_checkbox.click()



    try:
        issue_auth_button = automation.wait_for_clickable(By.XPATH, "//*[@id='0-issue-authorization-button']")
        issue_auth_button.click()
        #print('auth button clicked')
        
        auth_element = automation.wait_for_element(By.ID, "auth-confirmation-number")
        #print('set auth element')
        member.authorization = auth_element.text.strip()
        #print(f'auth #: {member.authorization}')

        go_to_patient_record_button = automation.wait_for_clickable(By.XPATH, "//*[@id='authorization-confirmation-go-to-claim-form-button']")
        go_to_patient_record_button.click()
    except:
       # print(f'Unable to get authorization for {member.first_name} {member.last_name} ')
        pass



#EYEFINITY CLAIM FUNCTIONS

def fill_rx(automation,member):
    sendrx(automation,member)
    diseasereporting(automation,member)
    calculate(automation,member)
    fillpricing(automation,member)
    set_gender(automation,member)
    

def calculate_order(automation,member,second_window):
    click_submit_claim(automation,member)
    generate_report(automation,member)
    #close the second window
    second_window.destroy()
    

def set_dos(automation,member):

    #try looking for a link that has an id 'cob-coverage-navigate-to-claim-link'
    try:
        cob_link = automation.short_wait_for_element(By.ID, "cob-coverage-navigate-to-claim-link")
        cob_link.click()
    except Exception as e:
        pass

    try:
        dos_field = automation.wait_for_element(By.XPATH, "//*[@id='date-of-service']")
    except Exception as e:
        (f'error finding dos field: {e}. Authorization may not have been issued')
        
    date_string = member.dos
    for char in date_string:
        dos_field.send_keys(char)
    #print(f'sent dos: {member.dos}')


def submitexam(automation,member):

    new_exam = False
    existing_exam = False

    # Iterate through each dictionary in the list
    for item in member.billed_items:
        if item['code'] == '92004':
            new_exam = True
            break  # Exit the loop if the code is found

    # Iterate through each dictionary in the list
    for item in member.billed_items:
        if item['code'] == '92014':
            existing_exam = True
            break  # Exit the loop if the code is found


    #if doesn't have a new or existing exam code forget this function and move on
    submit_refraction = False

    if new_exam:
        automation.wait_for_element(By.XPATH, "//*[@id=\"exam-type-group1-92004\"]").click()
        submit_refraction = True
    elif existing_exam:
        automation.wait_for_element(By.XPATH, "//*[@id=\"exam-type-group1-92014\"]").click()
        submit_refraction = True

    sleep(.5)

    if submit_refraction:
        refractionbox = automation.wait_for_element(By.XPATH, "//*[@id='exam-refraction-performed-checkbox-input']")
        refractionticked = refractionbox.is_selected()

        if refractionticked == False:
            sleep(.5)
            refraction_tick = automation.wait_for_element(By.XPATH, "//*[@formcontrolname='refractionTestPerformed']")           
            refraction_tick.click()     




def setDr(automation,member):
    sleep(1)
    automation.execute_script("window.scrollTo(0, 50)")
    sleep(1)

    automation.wait_for_clickable(By.ID, "exam-rendering-provider-group").click()
    sleep(1)
    if "Fitch" in member.doctor:
            automation.wait_for_element(By.XPATH,"//*[@id=\"exam-rendering-provider-1740293919\"]").click()
    elif "Hollingsworth" in member.doctor:
        automation.wait_for_element(By.XPATH, "//*[@id=\"exam-rendering-provider-1639335516\"]").click()
    else:
        automation.wait_for_element(By.XPATH, "//*[@id=\"exam-rendering-provider-1891366597\"]").click()


def submit_cl(automation,member):
    #print('submitting cl')
    contact_codes = {'V2500', 'V2501', 'V2502', 'V2503', 'V2520', 'V2521', 'V2522', 'V2523'}

    # Initialize materials to False
    contacts = False

    # Loop through each billed item
    for item in member.billed_items:
        if item['code'] in contact_codes:
            contacts = True
            contact_code = item['code']
            break  # Break out of the loop as we found a non-exam code

    if not contacts:
        #print('no contacts found')
        return

    

    # Loop through each item
    cl_quantity = 0
    cl_price = 0
    for item in member.billed_items:
        code = item['code']
        if code in contact_codes:
            #add the intiger value of the quantity to the total quantity
            cl_quantity += int(item['Qty'])
            #add the float value of the price to the total price
            cl_price += float(item['Price'])
    
    #print(f'cl quantity: {cl_quantity}')
    #print(f'cl price: {cl_price}')

    for item in member.billed_items:
        if item['code'] in contact_codes:
            item['Qty'] = cl_quantity
            item['Price'] = cl_price
            break

    #print(f'I built this logic myself. Let us see how I did: {member.billed_items}')
    # Convert the aggregated data back to list
    
    









    automation.execute_script("window.scrollTo(0, 2500)")

    #set CL material
    sleep(1)
    contact_material_dropdown = automation.wait_for_element(By.XPATH, '//*[@id="contacts-material-type-dropdown"]')
    select = Select(contact_material_dropdown)
    select.select_by_value(contact_code)

    #set reason to elective
    sleep(1)
    cl_reason = automation.wait_for_element(By.XPATH, "//*[@id='contacts-reason-dropdown']")
    select = Select(cl_reason)
    select.select_by_value("0")

    #set manafacturer
  
    vistakon_list = {'Johnson', 'Vistakon', 'Acuvue', 'acuvue'}
    if any(brand in item['description'] for item in member.billed_items for brand in vistakon_list):
        manafacturer = 'Vistakon'

    
    alcon_list = {"Alcon", "Dailies", "Optix"}
    if any(brand in item['description'] for item in member.billed_items for brand in alcon_list):
        manafacturer = "Alcon"

   
    b_l_list = {'Bausch'}
    if any(brand in item['description'] for item in member.billed_items for brand in b_l_list):
        manafacturer = "Bausch & Lomb"

    coopervision_list = {'Cooper', 'Biofinity', 'Proclear'}
    if any(brand in item['description'] for item in member.billed_items for brand in coopervision_list):
        manafacturer = "CooperVision"

    #print(manafacturer)

    sleep(1)
    set_manafacturer = automation.wait_for_element(By.XPATH, "//*[@id='contacts-manufacturer-dropdown']")
    select = Select(set_manafacturer)
    select.select_by_value(manafacturer)

    #set brand to other. we'll be filling it out in box 19. 
    sleep(1)
    set_brand = automation.wait_for_element(By.XPATH, "//*[@id='contacts-brand-dropdown']")
    set_brand.click()
    sleep(1)
    set_brand.send_keys('ot')

    select = Select(set_brand)
    select.select_by_value("Other")


    #set box count
    sleep(1)
    for item in member.billed_items:
        if item['code'].startswith('V25'):
            quantity = item['Qty']
            break 
    boxes_field = automation.wait_for_element(By.XPATH, "//*[@id='contacts-number-of-boxes-textbox']")
    boxes_field.send_keys(quantity)

    

    #drop to box 19 and add brand
    sleep(1)
    for item in member.billed_items:
        if item['code'].startswith('V25'):
            cl_brand = item['description']
           # print(cl_brand)
            break

    automation.execute_script("window.scrollTo(0, 6000)")
    box_19 = automation.wait_for_element(By.XPATH, "//*[@id='additional-information-claim-input']")
    box_19.send_keys(cl_brand)


def diseasereporting(automation,member):
    automation.execute_script("window.scrollTo(0, 3600)")
    #nocondition = automation.wait_for_element(By.CSS_SELECTOR, "#known-conditions-none-checkbox > label:nth-child(1) > div:nth-child(1)")
    #noconditionselected = nocondition.is_selected()
    #if noconditionselected == False:

        #diseasereporting = automation.wait_for_element(By.CSS_SELECTOR, "#known-conditions-none-checkbox > label:nth-child(1) > div:nth-child(1)")
        #diseasereporting.click()
    
    #else:

        #pass
    
    if not member.diagnoses.startswith("H52."):
        member.diagnoses = "H52.223"
    
    #if the member diagnoses im multiple diagnoses, split them at the , and only use the first one
    if ',' in member.diagnoses:
        member.diagnoses = member.diagnoses.split(',')[0]

    diagnosisfield = automation.wait_for_element(By.XPATH, "//*[@id=\"services-diagnosis-code-A-textbox\"]")
    diagnosisfield.click()
    sleep(.5)
    diagnosisfield.clear()
    sleep(.5)
    diagnosisfield.click()
    diagnosisfield.send_keys(member.diagnoses)
    #actions.perform()
    sleep(.5)


def calculate(automation,member):
   # print('calculating')
    automation.wait_for_element(By.XPATH, "//*[@id='claim-tracker-calculate']").click()
    sleep(3)
    try:
        alert_box = automation.short_wait_for_element(By.XPATH, "//*[@id='warning-message-container']")
            #get all of the inner text of the alert box
        alert_message = alert_box.text
            #print(alert_message)
        if 'UPC and SKU' in alert_message:
            acknowledge = automation.wait_for_element(By.XPATH, "//*[@class='mat-focus-indicator acknowledge-button mat-stroked-button mat-button-base mat-primary']")
            acknowledge.click()
            automation.wait_for_element(By.XPATH, "//*[@id='claim-tracker-calculate']").click()
    except:
        pass


def fillpricing(automation,member):
   # print('filling pricing')
    automation.execute_script("window.scrollTo(0, 4000)")
    sleep(2)
    # Let's assume member.billed_items is initialized as below:
    billed_items = member.billed_items

    # Find all input elements with the form control name 'cptHcpcsCode'
    input_elements = automation.wait_for_elements(By.XPATH, "//input[@formcontrolname='cptHcpcsCode']")
   # print(f"Found {len(input_elements)} input elements.")
    #for element in input_elements:
       # print(element.get_attribute('value'))
    # Function to calculate unit count based on description and quantity
    def calculate_units(description, qty):
        # Look for pack size numbers in the description
        pack_sizes = re.findall(r'\b(6|90|30|60|12|24)\b', description)
        if pack_sizes:
            # Use the first found pack size to calculate units
            pack_size = int(pack_sizes[0])
            return pack_size * int(qty)
        return 0
    #print(f'set funtion for identifying conctacts')
    # Iterate over each billed item
    for item in billed_items:
        code_to_match = item['code']
        price_to_input = item['Price']
        description = item['description']
        if description == 'Coopervision Inc. Biofinity':
            description = 'CooperVision Biofinity 6 pack'
            #print(f'found {description}')
        qty = item['Qty']
        #print(f'code to match: {code_to_match}')
        # Loop through each input element to find the matching code
        #sleep(1)
        #input_elements = automation.wait_for_elements(By.XPATH, "//input[@formcontrolname='cptHcpcsCode']")
        #iterate over each input element while avoiding stale elements
        

        for input_element in input_elements:
            current_value = input_element.get_attribute('value')
            
            # If the current input element's value matches the code to match
            if current_value == code_to_match:
                #print(f"Found matching code: {code_to_match}")
                # Extract the line number from the element's ID
                match = re.search(r'service-line-(\d+)-hcpc-input', input_element.get_attribute('id'))
                if match:
                    line_number = match.group(1)
                    sleep(.5)
                    
                    # If the code starts with 'V25', calculate the units and find the unit count input
                    if code_to_match.startswith('V25'):
                        unit_count = calculate_units(description, qty)
                        #print(f'unit count: {unit_count}')
                        unit_count_input_id = f"service-line-{line_number}-unit-count-input"
                        unit_count_input_element = automation.wait_for_element(By.ID, unit_count_input_id)
                        unit_count_input_element.clear()
                        unit_count_input_element.send_keys(str(unit_count))
                        #print(f"Unit count for code {code_to_match} set to {unit_count} on line {line_number}.")

                    # Construct the ID for the corresponding 'Price' input field
                    price_input_id = f"service-line-{line_number}-billed-amount-input"
                    price_input_element = automation.wait_for_element(By.ID, price_input_id)
                    price_input_element.clear()
                    price_input_element.send_keys(price_to_input)
                    #print(f"Price for code {code_to_match} set to {price_to_input} on line {line_number}.")
                    break  # Stop checking once we've found and updated the right field



    #search for FSA box
    sleep(1)
    automation.execute_script("window.scrollTo(0, 4400)")
    #print(f'should be in the correct spot')
    sleep(1)
    try:
        automation.short_wait_for_element(By.XPATH, "//*[@id=\"services-fsa-paid-input\"]").send_keys(member.copay)
    except: 
       # print(f'no fsa found')
        sleep(1)
        pass

    #set patient payment
    sleep(1)
    #print('scrolling into view')
    automation.execute_script("window.scrollTo(0, 4400)")
    #print('scrolled paid field into view')
    sleep(3)
    #paymentfield=vsp.find_element(by=By.XPATH, value="//*[@id=\"services-patient-paid-amount-input\"]")
    paymentfield = automation.wait_for_element(By.XPATH, "//*[@id=\"services-patient-paid-amount-input\"]")
    paymentfield.click()
    paymentfield.clear()
    #print(member.copay)
    paymentfield.send_keys(member.copay)
    sleep(.5)
    


def set_gender(automation,member):
    automation.execute_script("window.scrollTo(0, 4725)")


    if member.gender == 'Male':
        automation.wait_for_element(By.XPATH, '//*[@id="patient-sex-male-toggle"]').click()
    else:
        automation.wait_for_element(By.XPATH, '//*[@id="patient-sex-female-toggle"]').click()


def fill_address(automation,member):
    automation.execute_script("window.scrollTo(0, 4725)")
    sleep(.5)
    address_field = automation.wait_for_element(By.XPATH, "//*[@id='patient-address1']")
    #check to see if there is any text already in the address field
    address_field_text = address_field.get_attribute('value')
    #print(f'the address field contains: {address_field_text}')
    if address_field_text == '':
        address_field.send_keys(member.address)
        automation.execute_script("window.scrollTo(0, 4725)")
        city_field = automation.wait_for_element(By.XPATH, "//*[@id='patient-city-input']")
        city_field.send_keys(member.city)
        automation.execute_script("window.scrollTo(0, 4725)")

        import us

        def get_state_abbreviation(state_name):
            state = us.states.lookup(state_name)
            return state.abbr if state else None

        abbreviated_state = get_state_abbreviation(member.state)
        #select the state from a listbox by the state abbreviation text inside the class 'ng-option-label ng-star-inserted'
        state_field = automation.wait_for_element(By.XPATH, "//*[@id='patient-state-input']")
        state_field.click()
        automation.send_keys(abbreviated_state)
        sleep(.5)
        automation.send_keys(Keys.ENTER)
    
        #state_field.send_keys(Keys.ENTER)
        automation.execute_script("window.scrollTo(0, 4725)")
        zip_field = automation.wait_for_element(By.XPATH, "//*[@id='patient-zip-code-input']")
        zip_field.send_keys(member.zip)







def click_submit_claim(automation,member):
    sleep(2)
   # print('submitting claim')
    automation.wait_for_element(By.XPATH, '//*[@id="claimTracker-submitClaim"]').click()
    automation.wait_for_element(By.XPATH, '//*[@id="submit-claim-modal-ok-button"]').click()
   # print('claim submitted')

    
def download_report(automation): # not working. i'm using generate report instead
    view_report_button = automation.wait_for_element(By.XPATH, "//*[@button id='successfully-submitted-claim-modal-yes-button']")
    view_report_button.click()

    #switch to the new popup window
    automation.switch_to_tab(2)

    
    frame = automation.wait_for_element(By.XPATH, "//*[@name='rptTop']")
    automation.switch_to_frame(frame_element=frame)
    
    packing_slip = automation.find_element(By.XPATH, "//*[@name='imgpkslp']")
    packing_slip.click()
    sleep(1)

    #take a screenshot of the packing slip
    automation.save_screenshot('packing_slip.png')
    sleep(1)

    


def generate_report(automation,member):
   # print('generating report')
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import os
    from datetime import datetime
    
    success = False
    #print('looking for popup to show success')
    sleep(2)
    
    try:
        view_report_button = automation.wait_for_element(By.XPATH, "//*[@id='successfully-submitted-claim-modal-no-button']")
        view_report_button.click()
        success = True
    except:
        try:
            alert_box = automation.wait_for_element(By.XPATH, "//*[@id='warning-message-container']")
            #get all of the inner text of the alert box
            alert_message = alert_box.text
            #print(alert_message)
            if 'Opposite signs' in alert_message:
                acknowledge = automation.wait_for_element(By.XPATH, "//*[@class='mat-focus-indicator acknowledge-button mat-stroked-button mat-button-base mat-primary']")
                acknowledge.click()
                submit_claim = automation.wait_for_element(By.XPATH, "//*[@id='claimTracker-submitClaim']")
                submit_claim.click()
                sleep(2)
                ok_button = automation.wait_for_element(By.XPATH, '//*[@id="submit-claim-modal-ok-button"]')
                ok_button.click()
                view_report_button = automation.wait_for_element(By.XPATH, "//*[@id='successfully-submitted-claim-modal-no-button']")
                view_report_button.click()
                success = True
                
        except:
        
            pass
        
    if success != True:
        #print('no report generated')
        return

    # Get today's date
    today_date = datetime.now()

    # Format the date as MM/DD/YYYY
    date_string = today_date.strftime("%m/%d/%Y")

    #print(date_string)


    file_path = "/home/jake/Documents/member_report.pdf"
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    # Starting Y position
    y_position = height - 50

    # Add content
    c.drawString(30, y_position, f"Name: {member.first_name} {member.last_name}")
    y_position -= 20
    c.drawString(30, y_position, f"Age: {member.date_of_birth}")
    y_position -= 20
    c.drawString(30, y_position, f"DOS: {member.dos}")
    y_position -= 20
    c.drawString(30, y_position, f"Authorization: {member.authorization}")
    y_position -= 20
    c.drawString(30, y_position, f"Filed: {date_string}")

    
    # Save the PDF
    c.save()
    #print("pdf saved")
    automation.switch_to_tab(0)
    automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerParentNavigateButtonaccounting']").click()
    sleep(1)
    automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerChildNavigateButtoninvoices']").click()
    sleep(1)
    automation.wait_for_element(By.XPATH, "//*[@data-test-id='invoiceDetailsDocsAndImagesTab']").click()
    sleep(1)
    automation.wait_for_element(By.XPATH, "//*[@data-test-id='patientDocumentsUploadButton']").click()
    sleep(1)


    documents = automation.wait_for_element(By.XPATH, '//*[@title="Documents"]')
    documents.click()
    documents.click()
    sleep(1)
    insurance_folder = automation.wait_for_element(By.XPATH, '//*[@title="Insurance"]')
    insurance_folder.click()
    sleep(1)

    input_element = automation.wait_for_element(By.XPATH, '//*[@type="file"]')
    
    input_element.send_keys(file_path)
    sleep(1)
    automation.wait_for_element(By.XPATH, "//*[@data-test-id='fileModalUploadButton']").click()

    member.success = True
    
    sleep(2)
    #print(f'successfully submited claim for {member.first_name} {member.last_name}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    #main_tab = automation.wait_for_clickable(By.XPATH, "//*[@tabindex='0']")
    #sleep(2)
    #main_tab.click()
    
    
def mark_as_success(automation,member):
    #if member.success == True:, add member name to success list and add a +1 to the total number of claims submitted
    #print('marking as success')
    if member.success != True:
        if not os.path.exists ('need_to_submit.txt'):
            with open('need_to_submit.txt', 'w') as f:
                f.write(f'{member.last_name}, {member.first_name} needs to be submitted\n')
        return
    
    #if a text file does not exist, create one
    if not os.path.exists('submitted_claims.txt'):
        with open('submitted_claims.txt', 'w') as f:
            #add member.last name, member.firstname to the success list
            f.write(f'{member.last_name}, {member.first_name}\n submitted successfully\n')


def send_add_and_seg_to_vsp(automation,member): # not finished. Need to test selector for mono vs dual pd
    #clear and submit add power for right and left eye
    automation.execute_script("window.scrollTo(0, 2800)")

    od_add_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionRightEyeAddInput']")
    od_add_field.clear()
    od_add_field.send_keys(member.od_add)
    
    os_add_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionLeftEyeAddInput']")
    os_add_field.clear()
    os_add_field.send_keys(member.os_add)   


    #clear and submit seg height for right and left eye
    os_segheight_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionLeftEyeSegmentHeightInput']")  
    os_segheight_field.clear()
    os_segheight_field.send_keys(member.seg_height)
    
    od_segheight_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionRightEyeSegmentHeightInput']")
    od_segheight_field.clear()
    od_segheight_field.send_keys(member.seg_height)
    
    
def sendrx(automation,member):
    if member.lens_type == None:
        return
    #print('sending rx')
    sleep(1)
    automation.execute_script("window.scrollTo(0, 3000)")
    sleep(1)
    
    #right eye
    od_sph_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionRightEyeSphereInput']")
    od_sph_field.clear()
    od_sph_field.send_keys(member.od_sph)
    
    od_cyl_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionRightEyeCylinderInput']")    
    od_cyl_field.clear()
    od_cyl_field.send_keys(member.od_cyl)
    
    od_axis_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionRightEyeAxisInput']")
    od_axis_field.clear()
    od_axis_field.send_keys(member.od_axis)
    automation.execute_script("window.scrollTo(0, 3000)")
    sleep(1)
    #left eye   
    os_sph_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionLeftEyeSphereInput']")
    os_sph_field.clear()
 
    os_sph_field.send_keys(member.os_sph)
    
    os_cyl_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionLeftEyeCylinderInput']")
    os_cyl_field.clear()
    os_cyl_field.send_keys(member.os_cyl)
    
    os_axis_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionLeftEyeAxisInput']")
    os_axis_field.clear()
    os_axis_field.send_keys(member.os_axis)


    if member.od_pd!= '':
        automation.execute_script("window.scrollTo(0, 3000)")
        sleep(.5)
        select_binoculer = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionBinocularMonocularSelect']")
        select_binoculer.click()
        sleep(.5)

        select_binoculer = automation.wait_for_element(By.XPATH, "/html/body/app-root/div/app-secure/div[2]/div/app-claim-form/div/div[3]/app-prescription/div/mat-card/mat-card-content/form/div[6]/div[2]/select/option[2]")
        select_binoculer.click()
        sleep(.5)

        od_pd_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionRightEyeDistanceInput']")
        od_pd_field.clear()
        od_pd_field.send_keys(member.od_pd)
        sleep(.5)

        os_pd_field = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionLeftEyeDistanceInput']")
        os_pd_field.clear()
        os_pd_field.send_keys(member.os_pd)
        sleep(.5)

    else:
        automation.execute_script("window.scrollTo(0, 3000)")
        sleep(.5)
        select_monoculer = automation.wait_for_element(By.XPATH, "//*[@id='prescriptionBinocularMonocularSelect']")
        select_monoculer.click()
        sleep(.5)

        select_monoculer = automation.wait_for_element(By.XPATH, "//option[@value='BINOCULAR']")
        select_monoculer.click()
        sleep(.5)

        dpd_field = automation.wait_for_element(By.XPATH, "//*[@id=\"prescriptionRightEyeDistanceInput\"]")
        dpd_field.clear()
        dpd_field.send_keys(member.dpd)


    if member.lens_type != 'Single Vision':
        send_add_and_seg_to_vsp(automation,member)
    

def submit_frame(automation,member): #should be working. added sleeps to every step.
    #print(f'about to submit frame. search for membe.lens_type and member.whoelsale now')
    #print(member.lens_type)
    #print(member.wholesale)
    sleep(1)
    if member.lens_type == None:
        #print('no lens found. skipping frame')
        return
    #automation.execute_script("window.scrollTo(0, 400)")
    #sleep(1)
    #automation.wait_for_element(By.XPATH, "/html/body/app-root/div/app-secure/div[2]/div/app-claim-form/div/div[3]/app-frame/div/mat-card/mat-card-content/form/div[2]/div[1]/select/option[2]").click()
    sleep(1)
    automation.execute_script("window.scrollTo(0, 2000)")
    frame_supplier = automation.wait_for_element(By.XPATH, "//*[@id=\"frames-frame-supplier-dropdown\"]")
    frame_supplier.click()
    sleep(1)
    
    #sets who supplied the frame
    if member.wholesale != None:
        #print('setting frame supplier to doctor')
        automation.wait_for_element(By.XPATH, "/html/body/app-root/div/app-secure/div[2]/div/app-claim-form/div/div[3]/app-frame/div/mat-card/mat-card-content/form/div[2]/div[1]/select/option[2]").click()
    else:
        #print('setting frame supplier to patient')
        automation.wait_for_element(By.XPATH, "/html/body/app-root/div/app-secure/div[2]/div/app-claim-form/div/div[3]/app-frame/div/mat-card/mat-card-content/form/div[2]/div[1]/select/option[3]").click()
    automation.execute_script("window.scrollTo(0, 2000)")
    sleep(1)  
    
    search_frame = automation.wait_for_element(By.XPATH,"//*[@id=\"frame-search-textbox\"]")
    search_frame.send_keys("1234")
    sleep(1)
    automation.execute_script("window.scrollTo(0, 2000)")
    sleep(1)
    search_button = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-search-button\"]")
    search_button.click()
    sleep(1)
    try:
        search_manual = automation.wait_for_element(By.XPATH, "//*[@id=\"search-manual-frames\"]")
        search_manual.click()
    except:
        pass
    sleep(2)
    
    #sets frame manafacturer
   
    manafacturer_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-manufacturer\"]")
    #print(f'found manafacturer field')

    #focus on the popup element containing manafacturer
    try:
        manafacturer_field.click()
        #print(f'attempting to send send {member.manafacturer} to the manafacturer field')
        manafacturer_field.send_keys(member.manafacturer)
        sleep(.5)
        #print('sent manafacturer successfully')
    except:
        automation.send_keys(Keys.SHIFT + Keys.TAB)
        sleep(1)
        manafacturer_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-manufacturer\"]")
        manafacturer_field.send_keys(member.manafacturer)
        #print('sent manafacturer successfully')
        
    #sets frame collection
    collection_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-collection\"]")
    collection_field.send_keys(member.collection)
    sleep(.5)
    
    #sets frame model
    try:
        model_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-model\"]")
        model_field.send_keys(member.model)
        sleep(.5)
    except:
        model_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-model\"]")
        model = "unknown"
        model_field.send_keys(model)
    
    #sets frame color
    color_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-color\"]")
    color_field.send_keys(member.color)
    sleep(.5)
    
    #sets frame temple
    temple_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-temple\"]")
    temple_field.send_keys(member.temple)
    sleep(.5)
    
    #sets frame material
    material_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-materialType\"]")
    material_field.send_keys(member.material)
    sleep(.5)
    
    #sets frame eyesize
    eyesize_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-eyesize\"]")
    eyesize_field.send_keys(member.eyesize)
    sleep(.5)
    
    #sets frame dbl
    dbl_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-dbl\"]")
    dbl_field.send_keys(member.dbl)
    sleep(.5)
    
    #sets frame wholesale cost
    if member.wholesale != None:
        if member.wholesale  == '0.00':
            member.wholesale = '64.95'
        wholesale_field = automation.wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-wholesale-cost\"]")
        wholesale_field.send_keys(member.wholesale)
        sleep(.5)
    
    #saves details
    save_details_button = automation.wait_for_element(By.XPATH, "//*[@title='Click to save your edits']")
    save_details_button.click()
    sleep(1)

    
        
   
def submit_lens(automation,member): #this will be the most complex. I will need to go into more detail when i'm fully caught up. For now i'm just looking for IOF
    
    if member.lens_type == None:
        return
    #print('submitting lens')
    sleep(1)
    automation.execute_script("window.scrollTo(0, 500)")
    sleep(1)
    actions = ActionChains(automation.driver)
    #print(member.lens_type)
    IOF = False
    if member.lens_type == 'Single Vision':
        IOF = True
    #print(f'IOF: {IOF}')

    #print(f'lens type: {member.lens_type}')
    #print(f'material: {member.lens_material}')
    #print(f'lens ar: {member.lens_ar}')
    #print(f'photochromatic: {member.photochromatic}')

    
    design_position =  None
    if member.lens_type == 'Single Vision':
        design_position = '2'
    elif member.lens_type == 'Flat Top 28':
        design_position = '2'
    elif member.lens_type == 'Progressive':
        design_position = '6'
    
    material_position = '3'
    if member.lens_material == 'Polycarbonate':
        material_position = '3'
    elif member.lens_material == '1.67':
        material_position = '5'
    elif member.lens_material == 'CR-39':
        material_position = '2'
    else:
        pass

    if member.lens_ar == "Zeiss DuraVsision Silver Premium AR (C)":
        member.lens_ar = "Lab Choice (AR Coating C) (AR Coating C)"
    
    
    if member.lens_ar == '' and member.lens_material == 'CR-39' and IOF == True:

        lens_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-dropdown\"]")
        lens_type_dropdown.click()
        sleep(1)

        lab_finishing_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-option-in-office-stock-lens\"]")
        lab_finishing_field.click()
        sleep(1)

        vision_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]")
        vision_type_dropdown.click()
        sleep(1)

        select_sv = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]/option[2]")
        select_sv.click()
        sleep(1)

        material_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]")
        material_dropdown.click()
        sleep(1)

        select_polycarbonate = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]/option[3]")
        select_polycarbonate.click()
        sleep(1)

        select_lens_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-lens-dropdown\"]")
        select_lens_dropdown.click()
        sleep(1)

        actions.send_keys("Stock Spherical - Clear")
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.TAB)
        actions.perform()
        sleep(1)

        automation.execute_script("window.scrollTo(0, 1900)")
        sleep(1)
        lab_id_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lab-lab-textbox\"]")
        lab_id_field.send_keys("0557")
        sleep(1)

    if member.lens_ar == '' and member.lens_material == 'Polycarbonate' and IOF == True and member.photochromatic != True:

        lens_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-dropdown\"]")
        lens_type_dropdown.click()
        sleep(1)

        lab_finishing_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-option-in-office-stock-lens\"]")
        lab_finishing_field.click()
        sleep(1)

        vision_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]")
        vision_type_dropdown.click()
        sleep(1)

        select_sv = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]/option[2]")
        select_sv.click()
        sleep(1)

        material_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]")
        material_dropdown.click()
        sleep(1)

        select_polycarbonate = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]/option[3]")
        select_polycarbonate.click()
        sleep(1)

        select_lens_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-lens-dropdown\"]")
        select_lens_dropdown.click()
        sleep(1)

        actions.send_keys("Stock Spherical - Clear")
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.TAB)
        actions.perform()
        sleep(1)

        automation.execute_script("window.scrollTo(0, 1900)")
        sleep(1)
        lab_id_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lab-lab-textbox\"]")
        lab_id_field.send_keys("0557")
        sleep(1)
    
    elif member.lens_ar == "Other (AR Coating A)" and member.lens_material == 'Polycarbonate' and IOF == True:   #this is has not been proven to work. I'm trying to include the lenses that are iof but not done with vsp estimator. 
        lens_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-dropdown\"]")
        lens_type_dropdown.click()
        sleep(1)
        
        lab_finishing_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-option-in-office-stock-lens\"]")  
        lab_finishing_field.click()
        sleep(1)
        
        vision_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]")
        vision_type_dropdown.click()
        sleep(1)
        
        select_sv = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]/option[2]")
        select_sv.click()
        sleep(1)
        
        

        material_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]")
        material_dropdown.click()
        sleep(1)

        select_polycarbonate = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]/option[3]")
        select_polycarbonate.click()
        sleep(1)

        select_lens_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-lens-dropdown\"]")
        select_lens_dropdown.click()
        sleep(1)

        actions.send_keys("Stock Aspheric w/ Standard AR (A) - Clear")
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.TAB)
        actions.perform()
        sleep(1)
        
        automation.execute_script("window.scrollTo(0, 1900)")
        sleep(1)
        lab_id_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lab-lab-textbox\"]")
        lab_id_field.send_keys("0557")
        sleep(1)
    
    elif member.lens_ar == "Lab Choice (AR Coating C) (AR Coating C)" and member.lens_material == 'Polycarbonate' and IOF == True and member.photochromatic == True:
        lens_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-dropdown\"]")
        lens_type_dropdown.click()
        sleep(1)
        
        lab_finishing_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-option-in-office-stock-lens\"]")  
        lab_finishing_field.click()
        sleep(1)
        
        vision_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]")
        vision_type_dropdown.click()
        sleep(1)
        
        select_sv = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]/option[2]")
        select_sv.click()
        sleep(1)
        
        

        material_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]")
        material_dropdown.click()
        sleep(1)

        select_polycarbonate = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]/option[3]")
        select_polycarbonate.click()
        sleep(1)

        select_lens_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-lens-dropdown\"]")
        select_lens_dropdown.click()
        sleep(1)

        actions.send_keys("Stock Aspheric w/ Premium AR (C) - Photochromic Other")
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.TAB)
        actions.perform()
        sleep(1)
        
        automation.execute_script("window.scrollTo(0, 1900)")
        sleep(1)
        lab_id_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lab-lab-textbox\"]")
        lab_id_field.send_keys("0557")
        sleep(1)

    elif member.lens_ar == "Lab Choice (AR Coating C) (AR Coating C)" and member.lens_material == 'Polycarbonate' and IOF == True and member.photochromatic != True:
        lens_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-dropdown\"]")
        lens_type_dropdown.click()
        sleep(1)
        
        lab_finishing_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-option-in-office-stock-lens\"]")  
        lab_finishing_field.click()
        sleep(1)
        
        vision_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]")
        vision_type_dropdown.click()
        sleep(1)
        
        select_sv = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]/option[2]")
        select_sv.click()
        sleep(1)
        
        

        material_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]")
        material_dropdown.click()
        sleep(1)

        select_polycarbonate = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]/option[3]")
        select_polycarbonate.click()
        sleep(1)

        select_lens_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-lens-dropdown\"]")
        select_lens_dropdown.click()
        sleep(1)

        actions.send_keys("Stock Spherical w/ Premium AR (C) - Clear")
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.TAB)
        actions.perform()
        sleep(1)
        
        automation.execute_script("window.scrollTo(0, 1900)")
        sleep(1)
        lab_id_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lab-lab-textbox\"]")
        lab_id_field.send_keys("0557")
        sleep(1)

    elif member.lens_ar == "" and IOF == True and member.lens_material == 'Polycarbonate' and member.photochromatic == True:
        lens_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-dropdown\"]")
        lens_type_dropdown.click()
        sleep(1)
        
        lab_finishing_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-finishing-option-in-office-stock-lens\"]")  
        lab_finishing_field.click()
        sleep(1)
        
        vision_type_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]")
        vision_type_dropdown.click()
        sleep(1)
        
        select_sv = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-vision-dropdown\"]/option[2]")
        select_sv.click()
        sleep(1)
        
        

        material_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]")
        material_dropdown.click()
        sleep(1)

        select_polycarbonate = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-material-dropdown\"]/option[3]")
        select_polycarbonate.click()
        sleep(1)

        select_lens_dropdown = automation.wait_for_element(By.XPATH, "//*[@id=\"lens-lens-dropdown\"]")
        select_lens_dropdown.click()
        sleep(1)

        actions.send_keys("Stock Spherical - Photochromic Other")
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        sleep(1)
        actions.send_keys(Keys.TAB)
        actions.perform()
        sleep(1)
        
        automation.execute_script("window.scrollTo(0, 1900)")
        sleep(1)
        lab_id_field = automation.wait_for_element(By.XPATH, "//*[@id=\"lab-lab-textbox\"]")
        lab_id_field.send_keys("0557")
        sleep(1)
        

# REVOLUTION EHR FUNCTIONS


def scrape_invoice(automation,member):
    automation.switch_to_tab(0)
    html_content = automation.get_page_source()

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')


    # Locate the table - in this case, we'll use the 'e-gridcontent' class as the identifier
    table = soup.find('div', class_='e-gridcontent').find('table')

    # Initialize a list to store each row's data
    data_rows = []

    # Iterate through the table rows
    for row in table.find_all('tr', class_='e-row'):
        # Extract data from each cell in the row
        cells = row.find_all('td')
        row_data = {
            'post_date': cells[1].get_text(strip=True),
            'code': cells[2].get_text(strip=True),
            'modifiers': cells[3].get_text(strip=True),
            'diagnoses': cells[4].get_text(strip=True),
            'description': cells[5].get_text(strip=True),
            'Qty': cells[6].get_text(strip=True),
            'Price':cells[10].get_text(strip=True),
            'copay':cells[11].get_text(strip=True),

            # ... continue for other cells
        }
        data_rows.append(row_data)
        
        
    

    

    from decimal import Decimal

    merged_data = {}

    for row in data_rows:
        code = row['code']

        if code in merged_data:
            # Update existing entry
            merged_data[code]['Qty'] = str(int(merged_data[code]['Qty']) + int(row['Qty']))
            merged_data[code]['Price'] = str(Decimal(merged_data[code]['Price'].strip('$')) + Decimal(row['Price'].strip('$')))
        else:
            # Add new entry
            merged_data[code] = row
            # Convert price to a format that can be summed
            merged_data[code]['Price'] = row['Price'].strip('$')

    # Convert back to list if necessary
    merged_data_rows = list(merged_data.values())


    member.diagnoses = merged_data_rows[0]['diagnoses']
    
    if not member.diagnoses:
    
        member.diagnoses = 'H52.223'
        diagnosis_button = automation.wait_for_element(By.XPATH, "//*[@data-test-id='invoiceHeaderDiagnosisButton']")
        diagnosis_button.click()
        diagnoses = automation.wait_for_elements(By.XPATH, "//*[@row-id]")
        for i, row in enumerate(diagnoses):
            #print(f"Row {i}:")
            
            # Find elements within the row - adjust the selector as per your HTML structure
            elements = row.find_elements(By.XPATH, "//*[@revtooltip]")

            # Iterate over each element and print the text
            for element in elements:
                if 'H52.' in element.text:
                    diagnosis_code_pattern = r'H\d{2}\.\d+'
                    match = re.search(diagnosis_code_pattern, element.text)
                    #print(element.text)
                    #print('found diag element')
                    # If a match is found, store it in member.diagnoses
                    if match:
                        member.diagnoses = match.group(0)
                        #print("Diagnosis code:", member.diagnoses)
                    else:

                        #print("No diagnosis code found in the text.")
                        pass
                    break  # Break the loop if 'H52.' is found
    
    

        close_diagnsoses = automation.wait_for_element(By.XPATH, "//*[@data-test-id='selectADiagnosisCancelButton']")
        close_diagnsoses.click()
    #print(f'diagnoses is {member.diagnoses}')
 
    member.dos = merged_data_rows[0]['post_date']


        # Assuming 'soup' is already created from your HTML content
    patient_name_element = soup.find(attrs={"data-test-id": "invoiceHeaderPatientNameLink"})

    # Check if the element was found
    if patient_name_element:
        patient_name = patient_name_element.get_text(strip=True)

        # Split the name at the comma
        name_parts = patient_name.split(',')

        # Extract last and first names
        member.last_name = name_parts[0].strip()
        member.first_name = name_parts[1].strip() if len(name_parts) > 1 else ''
        # strip nicknames by removing any content that would be in ""
        member.first_name = re.sub(r'\".*\"', '', member.first_name).strip()
        #strip any * from the first name if any are left
        member.first_name = member.first_name.replace('*', '')

        #print("Last Name:", member.last_name)
        #print("First Name:", member.first_name)

    else:
        #print("Element with data-test-id='invoiceHeaderPatientNameLink' not found")
        pass

            # Assuming 'soup' is already created from your HTML content
    doctor_icon = soup.find('i', class_='fa-user-md')

    # Check if the icon element was found
    if doctor_icon:
        doctor_li = doctor_icon.find_parent('li')
        if doctor_li:
            member.doctor = doctor_li.get_text(strip=True)
            #print(member.doctor)
        else:
            
            # print("Doctor list item not found")
            pass
    else:
        #print("Doctor icon not found")
        pass

    # find the element using selenium for the building in the class fa fa-building text-info margin-right-xs
    building_icon = automation.wait_for_element(By.XPATH, "//*[@class='fa fa-building']")

    # get the text value of the child element of the building icon
    building_name = building_icon.find_element(By.XPATH, "..").text
    member.location = building_name
    if member.location == "Borger":
        member.location = 2

    elif member.location == "Amarillo":
        member.location = 1

    #print(member.location)

    



    member.billed_items = merged_data_rows

    #print(f'billing for: {member.billed_items}')
    
    
def set_copay(automation, member):
    member.copay = 0.00  # Initialize member.copay as a float

    for item in member.billed_items:
        if item['code'].startswith('V21') or item['code'].startswith('V22'):
            #print('getting copay from optical invoices')
            return
    # Iterate through the items
    for item in member.billed_items:
        # only catch copays for exams and contacts
        if item['code'].startswith('9201') or item['code'].startswith('9200') or item['code'].startswith('V25'):

            # Remove the dollar sign and convert to float
            copay = float(item['copay'].replace('$', '').replace('-', ''))

            # Add to total copay
            member.copay += copay

    member.copay = str(member.copay)  # Convert back to string
    #print(member.copay)
  

def open_vsp_benefit(automation,member):
    automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceHeaderPatientNameLink"]').click()
    sleep(1)
    try:
        automation.quick_check(By.XPATH, "//*[@data-test-id='alertHistoryModalCloseButton']").click()
    except:
        pass
    member.date_of_birth = automation.wait_for_element(By.XPATH, "//*[@data-test-id='patientHeaderDateOfBirth']").text
    member.date_of_birth = member.date_of_birth.split(' ')[0]
    #print(f'dob is {member.date_of_birth}')
    member.gender = automation.wait_for_element(By.XPATH, "//li[@data-test-id='patientHeaderGender']").text
    sleep(.5)

    try:
        address_data = automation.wait_for_element(By.XPATH, "//*[@data-test-id='patientHeaderAddress']").text
        #print(f'address data is {address_data}')
        address_data = address_data.split(',')
    except:
        #print(f'unable to get address')
        sleep(.1)
    try:
        member.address = address_data[0]
    except:
        member.address = '1476 Biggs'
    try:

        member.city = address_data[1]
    except:
        member.city = 'Amarillo'

    try:

        member.state = address_data[2].split(' ')[1]
    except:
        member.state = 'TX'
    
    try:
        member.zip = address_data[2].split(' ')[2]
    except:
        member.zip = '79110'
    
    #try:
        #print(f'extracted address is {member.address}, {member.city}, {member.state}, {member.zip}')
    #except:
        #print('unable to print address')

    automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='insuranceSummaryPodexpand']").click()
    try:
        automation.wait_for_clickable(By.XPATH, "//span[contains(text(), 'Vision Service Plan (VSP)')]").click()
    except:
        #print('vsp not found or already open')
        pass


def get_vsp_auth_from_rev(automation,member):
    auth_field = automation.wait_for_element(By.XPATH, "//*[@formcontrolname='authorizationNumber']")
    member.authorization = auth_field.get_attribute('value')
    
    #if the member authorization doesn't contain numbers, set it to None
    if not any(char.isdigit() for char in member.authorization):
        member.authorization = None
        
    if member.authorization:
        #print(f'authorization is {member.authorization}')
        sleep(1)
        auth_field.clear()
        auth_field.send_keys(Keys.BACK_SPACE)
        sleep(1)
        
        #set the field to contain a zero
        auth_field.send_keys('0')
        if member.authorization == '0':
            member.authorization = None
        sleep(1)

    save_button = automation.wait_for_clickable(By.XPATH, '//*[@data-test-id="insuranceDetailsSaveButton"]')
    save_button.click()
    sleep(1)
    #print(f'moving back')
    back_button = automation.wait_for_element(By.XPATH, "//*[@data-test-id='allPatientInsurancesButton']")
    back_button.click()
    sleep(1)
    patient_summary = automation.wait_for_element(By.XPATH, "//*[@data-test-id='patientSummaryMenu']")
    patient_summary.click()


def get_member_information_to_search_VSP(automation,member):
    #if memer.authorization is not empty, end this function and move on with the program
    if member.authorization:
        return
    
    member.secondary_date_of_birth = ''
    member.secondary_first_name = ''
    member.secondary_last_name = ''

    
    sleep(1)
    automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='insuranceSummaryPodexpand']").click()
    #automation.wait_for_clickable(By.XPATH, "//span[contains(text(), 'Vision Service Plan (VSP)')]").click()
    try:
        automation.wait_for_clickable(By.XPATH, "//span[contains(text(), 'Vision Service Plan (VSP)')]").click()
    except:
        #print('vsp not found or already open')
        pass
    policy_field = automation.wait_for_element(By.XPATH, "//*[@formcontrolname='policyNumber']")
    member.memberid = policy_field.get_attribute('value')

    #if the member id is just 4 characters, make it a ''
    if len(member.memberid) == 4:
        member.memberid = ''
    

    #print a statement stating what is stored in member id
    #print(f'member id value is {member.memberid}')
    #if member id is structured like a date of birth, set secondary dob to the member id
    if member.memberid:
        if '/' in member.memberid:
            member.secondary_date_of_birth = member.memberid
            member.memberid = ''
            #print(f'secondary dob is {member.secondary_date_of_birth}')


    primary_dob = automation.wait_for_element(By.XPATH, "//*[@data-test-id='basicInformationPolicyDateOfBirthFormGroup']//*[@class='form-control-static']")
    member.primary_date_of_birth = primary_dob.text 
    primary_name = automation.wait_for_element(By.XPATH, "//*[@data-test-id='basicInformationPolicyHolderFormGroup']//*[@class='form-control-static margin-right-sm display-inline-block']")
    primary_name = primary_name.text

    #print a statement about what was found in primary name, 
    #print(f'primary name is {primary_name}')
    #print(f'primary dob is {member.primary_date_of_birth}')

    #get plan name field text
    plan_name = automation.wait_for_element(By.XPATH, "//*[@formcontrolname='planName']")
    plan_name = plan_name.get_attribute('value')
    #print a statement about what was found in plan name
    #print(f'plan name is {plan_name}')

    #if plan name is structured like a firstname lastname, set the secondaries first and last name to the first and last name of the plan name
    if plan_name:
        if ' ' in plan_name:
            try:
                member.secondary_first_name, member.secondary_last_name = plan_name.split(' ')
                #print(f'secondary name is {member.secondary_first_name} {member.secondary_last_name}')
            except:
                try:
                    member.secondary_first_name, member.secondary_last_name, member.dob = plan_name.split(' ')
                    #print(f'secondary name is {member.secondary_first_name} {member.secondary_last_name}')
                except:
                    pass

    #get group number field text
    group_number = automation.wait_for_element(By.XPATH, "//*[@formcontrolname='groupNumber']")
    group_number = group_number.get_attribute('value')
    #print(f'group number is {group_number}')
    
    #if group number is structured like a firstname lastname, set the secondaries first and last name to the first and last name of the group number
    if group_number:
        if ' ' in group_number:
            member.secondary_first_name, member.secondary_last_name = group_number.split(' ')
            
            #print(f'secondary name is {member.secondary_first_name} {member.secondary_last_name}')

    if primary_name:

        # Split the name at the comma
        name_parts = primary_name.split(',')

        # Extract last and first names
        member.primary_last_name = name_parts[0].strip()
        member.primary_first_name = name_parts[1].strip() if len(name_parts) > 1 else ''

        #print("Last Name:", member.primary_last_name)
        #print("First Name:", member.primary_first_name)

    else:
        #print("Element with data-test-id='invoiceHeaderPatientNameLink' not found")
        pass
    #strip out any commas frome either name
    member.secondary_first_name = member.secondary_first_name.replace(',', '')
    member.secondary_last_name = member.secondary_last_name.replace(',', '')
    #build a data set containing 3 values, primary first name, primary last name, and primary dob
    member.member_list = []
    #append member_list as a dictionary
    member.member_list.append({'first_name': member.primary_first_name, 'last_name': member.primary_last_name, 'dob': member.primary_date_of_birth})
    member.member_list.append({'first_name': member.secondary_first_name, 'last_name': member.secondary_last_name, 'dob': member.secondary_date_of_birth})
    member.member_list.append({'first_name': member.secondary_last_name, 'last_name': member.secondary_first_name, 'dob': member.secondary_date_of_birth})
    #print(f'member list is {member.member_list}')

    

    #Consdier making this a new function
    #print(f'moving back')
    sleep(1)
    back_button = automation.wait_for_element(By.XPATH, "//*[@data-test-id='allPatientInsurancesButton']")
    back_button.click()
    sleep(1)
    patient_summary = automation.wait_for_element(By.XPATH, "//*[@data-test-id='patientSummaryMenu']")
    patient_summary.click()

    sleep(3)
    listed_contacts = automation.wait_for_elements(By.XPATH, "//*[@col-id='formattedName']")
    #print(f'found {len(listed_contacts)} contacts')

    #use a counter to iterate through the contacts in order to avoid stale elements
    for i in range(len(listed_contacts)):
        #skip the first iteration
        if i > 0:

            listed_contacts = automation.wait_for_elements(By.XPATH, "//*[@col-id='formattedName']")
            contact = listed_contacts[i]
            contact.click()
            sleep(1)
            #check for the alert popup and close it
            try:
                automation.quick_check(By.XPATH, "//*[@data-test-id='alertHistoryModalCloseButton']").click()
            except:
                pass
            name_field = automation.wait_for_element(By.XPATH, "//*[@class='media-heading display-inline-block vertical-align-middle margin-top-0 margin-bottom-0 margin-right-lg']")
            #secondary last name is the first part of the text and first name is the second part of the text, seperated by , and a space
            name = name_field.text
            name_parts = name.split(',')
            last_name = name_parts[0]
            first_name = name_parts[1]
            #strip evertying from the hasthag on on in the first name. eg: Bobby #111510788 would strip to Bobby
            first_name = re.sub(r'#.*', '', first_name)
            
            dob = automation.wait_for_element(By.XPATH, "//*[@class='fa fa-birthday-cake text-primary margin-right-xs']")
            if dob:
                dob = dob.find_element(By.XPATH, "..").text
            
            else:
                dob = automation.wait_for_element(By.XPATH, "//*[@class='fa fa-birthday-cake text-info margin-right-xs']")
                dob = dob.find_element(By.XPATH, "..").text
            
            #strip the age in () from the text
            dob = re.sub(r'\([^)]*\)', '', dob)
            
            #print (f'adding {first_name} {last_name} {dob} to member list')
            #add value to the dictionary
            member.member_list.append({'first_name': first_name, 'last_name': last_name, 'dob': dob})
            #print(f'member list is {member.member_list}')

            #get the text inside the element with the class media-heading display-inline-block vertical-align-middle margin-top-0 margin-bottom-0 margin-right-lg
            closing_name_pattern = automation.wait_for_element(By.XPATH, "//*[@class='media-heading display-inline-block vertical-align-middle margin-top-0 margin-bottom-0 margin-right-lg']")
            #set closing name to the text but strip out everything after the first letter of the first name. The pattern is Lastname, Firstane, so it should save Lastname, F
            closing_name = closing_name_pattern.text
            #split the closing name at the comma, and only keep the first part and the first letter after the comma
            closing_name_parts = closing_name.split(',')
            closing_name = closing_name_parts[0] + ', ' + closing_name_parts[1][1]
            closing_name = closing_name.lower().replace(" ", "")
            close_icon = automation.wait_for_elements(By.XPATH, f"//span[@data-test-id='{closing_name}.navigationTab']/ancestor::div[contains(@class, 'e-text-wrap')]/span[contains(@class, 'e-close-icon')]")
            close_icon[-1].click()

            sleep(1)

    


    
    for contact in listed_contacts:

        
        try:

            contact.click()
            try:
                automation.quick_check(By.XPATH, "//*[@data-test-id='alertHistoryModalCloseButton']").click()
            except:
                pass
            name_field = automation.wait_for_element(By.XPATH, "//*[@class='media-heading display-inline-block vertical-align-middle margin-top-0 margin-bottom-0 margin-right-lg']")
            #secondary last name is the first part of the text and first name is the second part of the text, seperated by , and a space
            name = name_field.text
            name_parts = name.split(',')
            last_name = name_parts[0]
            first_name = name_parts[1]
            

                #locate the text in the element next to the icon  fa fa-birthday-cake text-info margin-right-xs
            secondary_dob = automation.wait_for_element(By.XPATH, "//*[@class='fa fa-birthday-cake text-info margin-right-xs']")
            secondary_dob = secondary_dob.find_element(By.XPATH, "..").text
            
            #strip the age in () from the text
            secondary_dob = re.sub(r'\([^)]*\)', '', member.secondary_date_of_birth)
            
            
            #add value to the dictionary
            member.member_list.append({'first_name': first_name, 'last_name': last_name, 'dob': secondary_dob})
            #print(f'member list is {member.member_list}')

            #THIS IS HOW TO CLOSE A PATIENT TAB

            #get the text inside the element with the class media-heading display-inline-block vertical-align-middle margin-top-0 margin-bottom-0 margin-right-lg
            closing_name_pattern = automation.wait_for_element(By.XPATH, "//*[@class='media-heading display-inline-block vertical-align-middle margin-top-0 margin-bottom-0 margin-right-lg']")
            #set closing name to the text but strip out everything after the first letter of the first name. The pattern is Lastname, Firstane, so it should save Lastname, F
            closing_name = closing_name_pattern.text
            
            #split the closing name at the comma, and only keep the first part and the first letter after the comma
            closing_name_parts = closing_name.split(',')
            closing_name = closing_name_parts[0] + ', ' + closing_name_parts[1][1]
            #print(f'this time the closeing name is set to {closing_name}')
            closing_name = closing_name.lower().replace(" ", "")
            #print(f'closing name is now {closing_name}')
            close_icon = automation.wait_for_element(By.XPATH, f"//span[@data-test-id='{closing_name}.navigationTab']/ancestor::div[contains(@class, 'e-text-wrap')]/span[contains(@class, 'e-close-icon')]")
            close_icon.click()
        except:
            #print('this element was not clickable')
            pass
    #print(f'member list is {member.member_list}')


def get_eyewear_order(automation, member):
    # Check for lens order in billed items
    for item in member.billed_items:
        if item['code'].startswith("V21") or item['code'].startswith("V22"):
            #print('Found lens order.')
            break
    else:
        #print('No lens order found.')
        return

    sleep(random.uniform(1, 2))  # Use random sleep

    # Expand orders section
    try:
        get_gl_order = automation.wait_for_element(By.XPATH, "//*[@data-test-id='ordersOpticalPodexpand']")
        get_gl_order.click()
        sleep(random.uniform(1, 2))
    except (NoSuchElementException, TimeoutException) as e:
        #print(f'Failed to expand orders section: {e}')
        return

    # Locate the table rows
    try:
        rows = automation.wait_for_elements(By.XPATH, "//table[@role='presentation']/tbody/tr")
    except (NoSuchElementException, TimeoutException) as e:
        #print(f'Failed to locate table rows: {e}')
        return

    # Text variables to check for
    text_options = [
        'VSP IOF PROGRAM - Sacramento, CA',
        'CARL ZEISS VISION KENTUCKY - Hebron, KY **CA-RNP** **ADVTG/NAT-RNP** **SELECT**',
        'VSP',
        'vsp'
    ]

    # Loop through the rows to find a matching date and text
    #print(f'Checking {len(rows)} rows for matching order...')
    for row in rows:
        try:
            #date_cell = row.find_element(By.XPATH, ".//td[@aria-label='Order Date']")
            #date cell alternative finds  row that contains 'Order Date' 
            date_cell = row.find_element(By.XPATH, ".//*[@data-colindex='1']")

            #print(date_cell.text)
            if date_cell.text == member.dos:
                for text_option in text_options:
                    try:
                        
                        text_cell = row.find_element(By.XPATH, f".//td[contains(text(), '{text_option}')]")
                        #print(text_cell.text)
                        text_cell.click()
          
                        #print(f'Order found and clicked for text: {text_option}')
                        return
                    except NoSuchElementException:
                        #print(f'No matching text found in row: {row}')
                        continue
        except NoSuchElementException:
            #print(f'No matching date found in row: {row}')
            continue

    #print('No matching orders found.')
    sleep(.1)


def get_wholesale(automation,member):
    
    #print(f'wholesale is {member.wholesale}')
    frame_exists = False
    #i want my code to find out if a billed item starts with v202 or V202. if it does, i want to run the rest of this function. if it does not i want to end the function
    for item in member.billed_items:
        # find out if there is a frame billed
        if item['code'].startswith('V202') or item['code'].startswith('v202'):
            #if that condition is met, make sure the first letter of the string is capitalized
            item['code'] = item['code'].capitalize()

            #print('found frame')
            frame_exists = True
            break
            
    if frame_exists == False:
        return
    

    #print('getting wholesale')
    automation.switch_to_tab(0)
    sleep(1)
    details_tab = automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='orderDetailsTab']")

    #use a true statement to try to click on details tab until sucessful. iterate 5 times with a one second wait. Sometimes it can be blocked by a spinner
    for i in range(5):
        try:
            details_tab.click()
            break
        except:
            sleep(1)
            continue


    wholesale = None

    if wholesale == None:
        try:
            wholesale = ''
            sleep(1)
            frame_tab = automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='frameInformationTab']")
            frame_tab.click()
            sleep(2)
            frame = automation.wait_for_element(By.XPATH, "//div[@data-test-id='frameProductSelectionStyleSection']//p[@class='form-control-static']")
            frame = frame.text 
            inventory_tab = automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='headerParentNavigateButtoninventory']")
            inventory_tab.click()
            products = automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='headerChildNavigateButtonproducts']")
            products.click()
            products_tab = automation.wait_for_element(By.XPATH, "/html/body/div[2]/div/div/div[8]/rev-inventory-dashboard/div/div/div/rev-inventory-products-dashboard/div/div[1]/ul/li[1]/a/uib-tab-heading")
            products_tab.click()
            sleep(2)
            clear_search = automation.wait_for_element(By.CSS_SELECTOR, 'form.mrgn-btm:nth-child(1) > div:nth-child(4) > button:nth-child(2)')
            clear_search.click()
            search_field = automation.wait_for_element(By.XPATH, "//*[@name='productSimpleSearch']")
            search_field.send_keys(frame)
            sleep(2)
            search_field.send_keys(Keys.ENTER)
            sleep(2)
            #search = automation.wait_for_element(By.XPATH, "//*[@rev-button='search']").click()
            #sleep(2)
            frame_link = automation.wait_for_element(By.XPATH, f"//*[@uib-popover='{frame}']")
            frame_link.click()
            
            wholesale_field = automation.wait_for_element(By.XPATH, '/html/body/div[2]/div/div/div[8]/rev-inventory-dashboard/div/div/div/rev-inventory-products-dashboard/div/div[2]/div[2]/rev-inventory-product-tab-container/div[2]/div/div[1]/rev-inventory-product-details/form/div[1]/div/div[2]/div/rev-currency[2]/rev-form-control/div/div/rev-currency-input/div/input')
            wholesale = wholesale_field.get_attribute('value')
        
        except:
            #print('no wholesale found')
            wholesale = '64.95'
            
        
        
        


    #print(f'wholesale is {wholesale}')
    

    member.wholesale = wholesale
    
    orders_tab = automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerParentNavigateButtonorders']")
    orders_tab.click()


def get_frame_data(automation, member):
    sleep(1)
    frame_tab = automation.wait_for_element(By.XPATH, "//*[@data-test-id='frameInformationTab']")
    #try to click on the frame tab until it's successful. I'ts sometimes blocked by a spinner. Loop 5 times with a one second wait
    for i in range(5):
        try:
            frame_tab.click()
            break
        except:
            sleep(1)
            continue
    sleep(1)

    try:
        frame = automation.wait_for_element(By.XPATH, "//div[@data-test-id='frameProductSelectionStyleSection']//p[@class='form-control-static']")
        member.model = frame.text
    except:
        member.model = 'unknown'
    if not member.model:
        member.model = 'unknown'
    #print(f'frame model is {member.model}')

    try:
        manafacturer = automation.wait_for_element(By.XPATH, "//div[@data-test-id='frameProductSelectionManufacturerSection']//p[@class='form-control-static']")
        member.manafacturer = manafacturer.text
    except:
        member.manafacturer = 'unknown'

    try:
        collection = automation.wait_for_element(By.XPATH, "//div[@data-test-id='frameProductSelectionCollectionSection']//p[@class='form-control-static']")
        member.collection = collection.text
    except:
        member.collection = member.manafacturer

    #print(f'frame data is {member.model}, {member.manafacturer}, {member.collection}')

    try:
        frame_color = automation.wait_for_element(By.XPATH, "//div[@data-test-id='frameColorSection']//p[@class='form-control-static']")
        member.color = frame_color.text
    except:
        member.color = 'unknown'

    try:
        temple = automation.wait_for_element(By.XPATH, "//label[text()='Temple']/following-sibling::div/p[@class='form-control-static']")
        temple = temple.text[:3] 
        member.temple = temple
        if member.temple == '':
            member.temple = '135'
    except:
        member.temple = '135'

    material = random.choice(['zyl', 'metal'])
    member.material = material
    
    try:
        eyesize = automation.wait_for_element(By.XPATH, "//label[text()='Eye']/following-sibling::div/p[@class='form-control-static']")
        member.eyesize = eyesize.text[:2]
    except:
        member.eyesize = '54'
    
    try:

        dbl = automation.wait_for_element(By.XPATH, "//label[text()='Bridge']/following-sibling::div/p[@class='form-control-static']")
        member.dbl = dbl.text[:2]
    except:
        member.dbl = '17'

    #print(f'frame data is {member.model}, {member.manafacturer}, {member.collection}, {member.color}, {member.temple}, {member.material}, {member.eyesize}, {member.dbl}')

def get_estimator_lens_data(automation,member):

    sleep(1)
    lens_tab = automation.wait_for_element(By.XPATH, "//*[@data-test-id='rxLensInformationTab']")
    lens_tab.click()
    sleep(1)
    sph = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(3)")
    sph_inner_html = sph.get_attribute("innerHTML")
    #print(sph_inner_html)

    parts = sph_inner_html.split("<br>")

    # Initialize variables
    right_eye = ""
    left_eye = ""

    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye = parts[0].strip()

    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye = parts[1].strip()

    #print("Right Eye:", right_eye, "Left Eye:", left_eye)
    
    cyl = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4)")
    cyl_inner_html = cyl.get_attribute("innerHTML")
    #print(cyl_inner_html)
    
    parts = cyl_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_cyl = ""
    left_eye_cyl = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_cyl = parts[0].strip()
        
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_cyl = parts[1].strip()
    
    #print("Right Eye Cyl:", right_eye_cyl, "Left Eye Cyl:", left_eye_cyl)
    
    axis = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(5)")
    axis_inner_html = axis.get_attribute("innerHTML")
    #print(axis_inner_html)
    
    parts = axis_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_axis = ""
    left_eye_axis = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_axis = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_axis = parts[1].strip()
    
    #print("Right Eye Axis:", right_eye_axis, "Left Eye Axis:", left_eye_axis)
    
    add = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(6)")
    add_inner_html = add.get_attribute("innerHTML")
    #print(add_inner_html)
    
    parts = add_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_add = ""
    left_eye_add = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_add = parts[0].strip()
        
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_add = parts[1].strip()
    
    #print("Right Eye Add:", right_eye_add, "Left Eye Add:", left_eye_add)
    
    h_prism = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(8)")
    h_prism_inner_html = h_prism.get_attribute("innerHTML")
    #print(h_prism_inner_html)
    
    parts = h_prism_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_h_prism = ""
    left_eye_h_prism = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_h_prism = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_h_prism = parts[1].strip()
        
    #print("Right Eye Prism:", right_eye_h_prism, "Left Eye Prism:", left_eye_h_prism)
    
    h_base = automation.wait_for_element(By.CSS_SELECTOR, "td.nostretch:nth-child(9)")
    h_base_inner_html = h_base.get_attribute("innerHTML")
    #print(h_base_inner_html)
    
    parts = h_base_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_h_base = ""
    left_eye_h_base = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_h_base = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_h_base = parts[1].strip()
    
    #print("Right Eye Base:", right_eye_h_base, "Left Eye Base:", left_eye_h_base)
    
    v_prism = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(10)")
    v_prism_inner_html = v_prism.get_attribute("innerHTML")
    #print(v_prism_inner_html)
    
    parts = v_prism_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_v_prism = ""
    left_eye_v_prism = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_v_prism = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_v_prism = parts[1].strip()
    
    #print("Right Eye Prism:", right_eye_v_prism, "Left Eye Prism:", left_eye_v_prism)
    
    v_base = automation.wait_for_element(By.CSS_SELECTOR, "td.nostretch:nth-child(11)")
    v_base_inner_html = v_base.get_attribute("innerHTML")
    #print(v_base_inner_html)
    
    parts = v_base_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_v_base = ""
    left_eye_v_base = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_v_base = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_v_base = parts[1].strip()
    
    #print("Right Eye Base:", right_eye_v_base, "Left Eye Base:", left_eye_v_base)
    
    
    od_pd_element =  automation.wait_for_element(By.XPATH, "//*[@data-test-id='eyeglassLensMeasurementsOdSection']//input[@type='text' and @placeholder='MPD-D']")
    od_pd = od_pd_element.get_attribute('value')
    #print(od_pd)
    
    os_pd_element =  automation.wait_for_element(By.XPATH, "//*[@data-test-id='eyeglassLensMeasurementsOsSection']//input[@type='text' and @placeholder='MPD-D']")
    os_pd = os_pd_element.get_attribute('value')
    #print(os_pd)
    
    dpd_element =  automation.wait_for_element(By.XPATH, "//*[@data-test-id='eyeglassLensMeasurementsBinocularSection']//input[@type='text' and @placeholder='']")
    dpd = dpd_element.get_attribute('value')
    #print(dpd)

    seg_height_element =  automation.wait_for_element(By.XPATH, "//*[@formcontrolname='segHeight']//input[@type='text' and @placeholder='']")
    seg_height = seg_height_element.get_attribute('value')
    #print(f'seg height is {seg_height}')
    
    
    lens_element = automation.quick_check(By.XPATH, '//*[@placeholder="Select Lens Style"]')
    lens_value = lens_element.get_attribute('innerHTML')
    #print(lens_value)
    # Regular expression to extract the value from the input element
    match = re.search(r'<option[^>]*>([^<]+)</option>', lens_value)

    # Extract and print the value
    if match:
        lens_description = match.group(1)
        #print("Lens Description:", lens_description)
    #else:
        #print("No lens description found in the HTML content.")
        
    
    material_element = automation.wait_for_element(By.XPATH, '//*[@placeholder="Select Material"]')
    material_value = material_element.get_attribute('value')
    #print(material_value)
    
    
    ar_element = automation.wait_for_element(By.XPATH, '//*[@placeholder="Select AR"]')
    ar_value = ar_element.get_attribute('value')
    #print(f'The AR value is :{ar_value}')
        
    lens_type = automation.wait_for_element(By.XPATH, '//*[@placeholder="Select Type"]')
    lens_value = lens_type.get_attribute('value')
    #print(lens_value)
    
    #if 'Photo' in lens_description:
        #member.photochromatic = True
        
    #print(f'photochromatic is {member.photochromatic}')
        
    member.lens_type = lens_value
    member.lens_ar = ar_value
    #member.lens_material = material_value
    member.lens = lens_description
    member.od_h_prism = right_eye_h_prism
    member.od_v_prism = right_eye_v_prism
    member.od_h_base = right_eye_h_base
    member.od_v_base = right_eye_v_base
    member.os_h_prism = left_eye_h_prism
    member.os_v_prism = left_eye_v_prism
    member.os_h_base = left_eye_h_base
    member.os_v_base = left_eye_v_base
    member.od_sph = right_eye
    member.od_cyl = right_eye_cyl
    member.od_axis = right_eye_axis
    member.od_add = right_eye_add
    member.od_pd = od_pd
    member.os_sph = left_eye
    member.os_cyl = left_eye_cyl
    member.os_axis = left_eye_axis
    member.os_add = left_eye_add
    member.os_pd = os_pd
    member.dpd = dpd
    member.seg_height = seg_height


def get_manual_lens_data(automation,member):
    #('getting manual lens data')
    sleep(1)
    lens_tab = automation.wait_for_element(By.XPATH, "//*[@data-test-id='rxLensInformationTab']")
    lens_tab.click()
    sleep(1)
    sph = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(3)")
    sph_inner_html = sph.get_attribute("innerHTML")
    #print(sph_inner_html)

    parts = sph_inner_html.split("<br>")

    # Initialize variables
    right_eye = ""
    left_eye = ""

    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye = parts[0].strip()

    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye = parts[1].strip()

    #print("Right Eye:", right_eye, "Left Eye:", left_eye)
    
    cyl = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(4)")
    cyl_inner_html = cyl.get_attribute("innerHTML")
    #print(cyl_inner_html)
    
    parts = cyl_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_cyl = ""
    left_eye_cyl = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_cyl = parts[0].strip()
        
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_cyl = parts[1].strip()
    
    #print("Right Eye Cyl:", right_eye_cyl, "Left Eye Cyl:", left_eye_cyl)
    
    axis = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(5)")
    axis_inner_html = axis.get_attribute("innerHTML")
    #print(axis_inner_html)
    
    parts = axis_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_axis = ""
    left_eye_axis = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_axis = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_axis = parts[1].strip()
    
    #print("Right Eye Axis:", right_eye_axis, "Left Eye Axis:", left_eye_axis)
    
    add = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(6)")
    add_inner_html = add.get_attribute("innerHTML")
    #print(add_inner_html)
    
    parts = add_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_add = ""
    left_eye_add = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_add = parts[0].strip()
        
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_add = parts[1].strip()
    
    #print("Right Eye Add:", right_eye_add, "Left Eye Add:", left_eye_add)
    
    h_prism = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(8)")
    h_prism_inner_html = h_prism.get_attribute("innerHTML")
    #print(h_prism_inner_html)
    
    parts = h_prism_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_h_prism = ""
    left_eye_h_prism = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_h_prism = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_h_prism = parts[1].strip()
        
    #print("Right Eye Prism:", right_eye_h_prism, "Left Eye Prism:", left_eye_h_prism)
    
    h_base = automation.wait_for_element(By.CSS_SELECTOR, "td.nostretch:nth-child(9)")
    h_base_inner_html = h_base.get_attribute("innerHTML")
    #print(h_base_inner_html)
    
    parts = h_base_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_h_base = ""
    left_eye_h_base = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_h_base = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_h_base = parts[1].strip()
    
    #print("Right Eye Base:", right_eye_h_base, "Left Eye Base:", left_eye_h_base)
    
    v_prism = automation.wait_for_element(By.CSS_SELECTOR, "table.text-right > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(10)")
    v_prism_inner_html = v_prism.get_attribute("innerHTML")
    #print(v_prism_inner_html)
    
    parts = v_prism_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_v_prism = ""
    left_eye_v_prism = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_v_prism = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_v_prism = parts[1].strip()
    
    #print("Right Eye Prism:", right_eye_v_prism, "Left Eye Prism:", left_eye_v_prism)
    
    v_base = automation.wait_for_element(By.CSS_SELECTOR, "td.nostretch:nth-child(11)")
    v_base_inner_html = v_base.get_attribute("innerHTML")
    #print(v_base_inner_html)
    
    parts = v_base_inner_html.split("<br>")
    
    # Initialize variables
    right_eye_v_base = ""
    left_eye_v_base = ""
    
    # Check and assign the right eye value
    if parts[0].strip():  # Checks if there is a value before <br>
        right_eye_v_base = parts[0].strip()
    
    # Check and assign the left eye value
    if len(parts) > 1 and parts[1].strip():  # Checks if there is a value after <br>
        left_eye_v_base = parts[1].strip()
    
    #print("Right Eye Base:", right_eye_v_base, "Left Eye Base:", left_eye_v_base)
    
    
    od_pd_element =  automation.wait_for_element(By.XPATH, "//*[@data-test-id='eyeglassLensMeasurementsOdSection']//input[@type='text' and @placeholder='MPD-D']")
    od_pd = od_pd_element.get_attribute('value')
    #print(od_pd)
    
    os_pd_element =  automation.wait_for_element(By.XPATH, "//*[@data-test-id='eyeglassLensMeasurementsOsSection']//input[@type='text' and @placeholder='MPD-D']")
    os_pd = os_pd_element.get_attribute('value')
    #print(os_pd)
    
    dpd_element =  automation.wait_for_element(By.XPATH, "//*[@data-test-id='eyeglassLensMeasurementsBinocularSection']//input[@type='text' and @placeholder='']")
    dpd = dpd_element.get_attribute('value')
    #print(dpd)

    seg_height_element =  automation.wait_for_element(By.XPATH, "//*[@formcontrolname='segHeight']//input[@type='text' and @placeholder='']")
    seg_height = seg_height_element.get_attribute('value')
    #print(f'seg height is {seg_height}')
    
    material_element = automation.wait_for_element(By.XPATH, '//*[@data-test-id="eyeglassLensOptionsMaterial"]')
    material = material_element.text
    #print(material)
    #if 'Polycarbonate' in material:
        #material_value = 'Polycarbonate'
    #print(f'material value is {material_value}')
    
    ar_element = automation.wait_for_element(By.XPATH, '//*[@data-test-id="eyeglassLensCoatingsArCoatingsSection"]')
    ar_value = ar_element.text
    #print(ar_value)
    if '(A)' in ar_value:
        ar_value = "Other (AR Coating A)"
    elif '(C)' in ar_value:
        ar_value = "Lab Choice (AR Coating C) (AR Coating C)"
    elif '(C, Teir 2)' in ar_value:
        ar_value = "Lab Choice (AR Coating C) (AR Coating C)"
    elif ar_value == 'AR Coating':
        ar_value = ''
    #print(f'ar value is {ar_value}')



    lens_type = "PAL"
    lens_type_element = automation.wait_for_element(By.XPATH, '//*[@data-test-id="lensDetailsManufacturerModelSection"]')
    lens_type_data= lens_type_element.text
   
    if 'sv' in lens_type_data.lower():
        lens_type = 'Single Vision'
    #print(lens_type)
   
    member.lens_type = lens_type
    member.lens_ar = ar_value
    #member.lens_material = material_value
    member.lens = "SV Poly W/ AR"
    member.od_h_prism = right_eye_h_prism
    member.od_v_prism = right_eye_v_prism
    member.od_h_base = right_eye_h_base
    member.od_v_base = right_eye_v_base
    member.os_h_prism = left_eye_h_prism
    member.os_v_prism = left_eye_v_prism
    member.os_h_base = left_eye_h_base
    member.os_v_base = left_eye_v_base
    member.od_sph = right_eye
    member.od_cyl = right_eye_cyl
    member.od_axis = right_eye_axis
    member.od_add = right_eye_add
    member.od_pd = od_pd
    member.os_sph = left_eye
    member.os_cyl = left_eye_cyl
    member.os_axis = left_eye_axis
    member.os_add = left_eye_add
    member.os_pd = os_pd
    member.dpd = dpd
    member.seg_height = seg_height


def get_lens_data(automation,member):

    #look through the billed items for the vcode V2744, and if it's found set photochromatic to true
    for item in member.billed_items:
        if item['code'].startswith('V2744') or item['code'].startswith('v2744'):
            member.photochromatic = True
            break
    #print(f'photochromatic is {member.photochromatic}')

    member.lens_material = 'CR-39'

    #look for polycarbonate code in billed items
    for item in member.billed_items:
        if item['code'].startswith('V2784') or item['code'].startswith('v2784'):
            member.lens_material = 'Polycarbonate'
            break
    
    #look for high index in billed items
    for item in member.billed_items:
        if item['code'].startswith('V2783') or item['code'].startswith('v2783'):
            member.lens_material = 'High Index'
            break


    try:
        get_estimator_lens_data(automation,member)
    except:
        get_manual_lens_data(automation,member)
    

def get_estimator_copay(automation,member):
    sleep(1)
   # print(f'member copay is {member.copay}')
    billing_tab = automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='billingTab']")
    billing_tab.click()
    sleep(1)
    
    copay_field = automation.quick_check(By.XPATH, "(//*[@col-id='patientTotal'])[last()]")
    copay_value = copay_field.get_attribute('innerHTML')
    #print(copay_value)
    copay_value = copay_value.replace("$", "")

    #print(copay_value) 

    member.copay = float(member.copay)
    member.copay += float(copay_value)
    member.copay = str(member.copay)
    #print(member.copay)


def get_manual_copay(automation,member):
    sleep(1)
   # print(f'member copay is {member.copay}')
    billing_tab = automation.wait_for_clickable(By.XPATH, "//*[@data-test-id='billingTab']")
    billing_tab.click()
    sleep(1)
    
    billable_items = automation.wait_for_element(By.XPATH, "//*[@data-test-id='assignedItemsTab']")
    billable_items.click()

    invoice_id = automation.wait_for_element(By.XPATH, "(//*[@col-id='invoiceId'])[2]")
    invoice_id = invoice_id.text
    #print(invoice_id)

    #get the elements inside the table with the data test id "pyersInvoicesTable"
    table = automation.wait_for_element(By.XPATH, "//*[@data-test-id='payersInvoicesTable']")
    #click on the element inside the table containing the text of the invoice id
    invoice_link = table.find_element(By.XPATH, f".//a[contains(text(), '{invoice_id}')]")
    invoice_link.click()

    sleep(2)
    
    copay_field = automation.wait_for_element(By.XPATH, "//*[@data-test-id='invoiceDetailAggregateTableAdjustableTotalAmount']")
    copay_value = copay_field.get_attribute('innerHTML')
    #(copay_value)
    copay_value = copay_value.replace("$", "")
    copay_value = copay_value.replace("-", "")
    #print(copay_value)

    close_invoice_button = automation.wait_for_element(By.XPATH, "//*[@data-test-id='invoiceDetailsModalCloseButton']")
    close_invoice_button.click()

    

    member.copay = float(member.copay)
    member.copay += float(copay_value)
    member.copay = str(member.copay)
    #print(member.copay)


def get_optical_copay(automation,member):
    try:
        get_estimator_copay(automation,member)
    except:
        get_manual_copay(automation,member)