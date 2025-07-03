from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup
from my_classes import Member







def scrape_patients(advance_days, automation,insurance_func):

    start_index = 0  # Initialize the start_index
    while True:  # Main loop to handle StaleElement exceptions
        automation.switch_to_tab(0)
        automation.wait_for_element(By.XPATH, f'//*[@class="fa fa-calendar"]').click()
        
        next_day_element = automation.wait_for_element(By.XPATH, f'//*[@class="e-btn-icon fa fa-arrow-right"]')
        previous_day_element = automation.wait_for_element(By.XPATH, f'//*[@class="e-btn-icon fa fa-arrow-left"]')

        # Navigate days
        for i in range(1): #-----------------------------------------------------------------------adjusts the date
            sleep(3)
            next_day_element.click()
            sleep(3)
            automation.wait_for_element(By.CSS_SELECTOR, '[data-test-id="agendaButton"]').click()
            sleep(1)
            automation.wait_for_element(By.CSS_SELECTOR, '[data-test-id="agendaButton"]').click()
            sleep(1)

        # Get the list of appointment elements
        appointment_elements = automation.wait_for_elements(By.XPATH, f'//*[@class="appointment-name"]/strong[1]')

        for i in range(start_index, len(appointment_elements)):  # Loop through appointments
            try:
                member = Member()
                member.reset()
                automation.switch_to_tab(0)
                appointment = appointment_elements[i]
                patient = appointment.get_attribute('innerHTML')

                if patient in ['Schaeffer, Sterling', 'Fitch, James', 'Hollingsworth, Ryan']:
                    continue
                
                split_name = patient.split(", ")
                last_name = split_name[0].split("-")[0]
                first_name = split_name[1]
                member.last_name = last_name
                member.first_name = first_name
                

                appointment.click()
                sleep(.5)
                #print(f'Patient: {last_name}, {first_name}')
          
                date_of_birth = automation.wait_for_element(By.XPATH, f'//*[@data-test-id="appointmentDetailsPatientAgeSection"]').get_attribute('innerHTML').split(" ")[0]
                member.date_of_birth = date_of_birth
                def calculate_age(date_of_birth):
                    today = datetime.today()
                    birthdate = datetime.strptime(date_of_birth, "%m/%d/%Y")
                    age = today.year - birthdate.year

                    # Adjust age if birthday hasn't occurred yet this year
                    if today.month < birthdate.month or (today.month == birthdate.month and today.day < birthdate.day):
                        age -= 1

                    return age
                member.age=calculate_age(date_of_birth)

                encounter = automation.wait_for_element(By.XPATH, f'//*[@data-test-id="appointmentDetailTabEncounterSection"]').get_attribute('innerHTML')
                soup = BeautifulSoup(encounter, 'html.parser')
                encounter = soup.find('a').text
                member.encounter = encounter
                #print(f'encounter: {member.encounter}')
            

                selected_insurance_button_label = None 
                automation.wait_for_element(By.XPATH, f'//*[@data-test-id="appointmentInsuranceTab"]').click()
                insurance_verification_element = automation.wait_for_element(By.CSS_SELECTOR, "pms-enum-select-button[formcontrolname='status']")
                insurance_verification_buttons = insurance_verification_element.find_elements(By.XPATH, ".//button[contains(@class, 'e-btn')]")
                selected_insurance_button_label = "Not Verified"
                for button in insurance_verification_buttons:
                    if "e-active" in button.get_attribute("class"):
                        selected_insurance_button_label = button.get_attribute("aria-label")
                        break
                if selected_insurance_button_label == "Valid" or selected_insurance_button_label == "Invalid":
                    sleep(.1)
                    continue
                else:
                    sleep(.1)
                insurance_func(member, advance_days, automation)
       

                
            except StaleElementReferenceException:  # Catch the stale element exception
                #print(f"Stale element detected at index {i}. Refreshing list and retrying...")
                start_index = i  # Update the start index
                break  # Break the for-loop, return to the start of the while-loop

        else:  # If the loop finishes without a break (i.e., no exception)
            #print("All appointments processed successfully.")
            break  # Exit the while loop















def update_insurance(automation,insurance_func):
    advance_days = 1
    for i in range(7):
        scrape_patients(advance_days, automation,insurance_func)
        advance_days += 1
