











    






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
        

