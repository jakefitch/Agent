










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
    if not member.authorization:
        error_msg = f'unable to obtain an authorization for {member.first_name} {member.last_name}'
        print(error_msg)
        raise Exception(error_msg)  # This will stop the entire claim submission process
        
    #try looking for a link that has an id 'cob-coverage-navigate-to-claim-link'
    try:
        cob_link = automation.short_wait_for_element(By.ID, "cob-coverage-navigate-to-claim-link")
        if cob_link:
            cob_link.click()
    except Exception as e:
        pass
    
    #wait for no overlay
    automation.wait_for_no_overlay()
    #print('overlay gone')
    try:
        dos_field = automation.wait_for_element(By.XPATH, "//*[@id='date-of-service']")
        if not dos_field:
            error_msg = f'DOS field not found for {member.first_name} {member.last_name} - authorization may not be valid'
            print(error_msg)
            raise Exception(error_msg)
            
        date_string = member.dos
        for char in date_string:
            dos_field.send_keys(char)
        #print(f'Successfully set DOS for {member.first_name} {member.last_name}')
    except Exception as e:
        error_msg = f'error finding dos field: {e}. Authorization may not have been issued'
        print(error_msg)
        raise Exception(error_msg)


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
    automation.wait_for_no_overlay()
    #print('overlay gone')

    try:
        alert_box = automation.short_wait_for_element(By.XPATH, "//*[@id='warning-message-container']")
            #get all of the inner text of the alert box
        alert_message = alert_box.text
        #print(alert_message)
        if 'UPC and SKU' in alert_message:
            acknowledge = automation.wait_for_element(By.XPATH, "//*[@class='mat-focus-indicator acknowledge-button mat-stroked-button mat-button-base mat-primary']")
            acknowledge.click()
            automation.wait_for_element(By.XPATH, "//*[@id='claim-tracker-calculate']").click()
            automation.wait_for_no_overlay()
            #print('overlay gone')
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
    for i in range(10):
        try:
            automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerParentNavigateButtonaccounting']").click()
            sleep(1)
            automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerChildNavigateButtoninvoices']").click()
            sleep(1)
            break
        except:
            pass
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
    print(f'successfully submited claim for {member.first_name} {member.last_name}')
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
   
    manafacturer_field = automation.short_wait_for_element(By.XPATH, "//*[@id=\"frame-display-form-manufacturer\"]")
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
        

