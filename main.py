from core.base import PatientManager
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from core.logger import Logger
from time import sleep
from config.vsp_map.vsp_session import VspSession
from config.rev_map.rev_session import RevSession
from core.utils import get_claim_service_flags



def launch_browser():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    logger = Logger()
    rev = RevSession(context.new_page(), logger, context)
    vsp = VspSession(context.new_page(), logger)
    #return p, browser, rev
    return p, browser, rev, vsp




if __name__ == "__main__":
    load_dotenv("/home/jake/Code/.env")

    p, browser, rev, vsp = launch_browser()
    #p, browser, rev = launch_browser()
    
    rev.login()

    vsp.login("ama")
   

    #navigate to patient page
    rev.invoice_page.navigate_to_invoices_page()
    rev.invoice_page.search_invoice(payor="vision")
    sleep(2)
    rev.invoice_page.open_invoice("287147650")
    patient = rev.invoice_page.create_patient_from_invoice()
    rev.invoice_page.scrape_invoice_details(patient)
    rev.invoice_page.click_patient_name_link()
    rev.patient_page.scrape_demographics(patient)
    rev.patient_page.scrape_family_demographics(patient)
    rev.patient_page.expand_insurance()
    rev.insurance_tab.select_insurance("VSP")
    rev.insurance_tab.scrape_insurance(patient)
    rev.patient_page.click_patient_summary_menu()
    if patient.has_optical_order:
        rev.patient_page.expand_optical_orders()
        sleep(2)
        rev.patient_page.open_optical_order(patient)
        rev.optical_order.scrape_frame_data(patient)
        rev.optical_order.scrape_lens_data(patient)
        rev.optical_order.scrape_optical_copay(patient)
        rev.products.navigate_to_products()
        rev.products.get_wholesale_price(patient)
    patient.print_data()

    # Determine claim flags based on invoice items
    flags = get_claim_service_flags(patient)

    member_found = vsp.member_search_page.search_member(patient)
    if not member_found:
        print("Member not found, skipping authorization")
        raise Exception("Member not found, skipping authorization")
    sleep(2)
    write_off_materials = False

    vsp.authorization_page.select_patient(patient)
    sleep(1)
    
    auth_status = vsp.authorization_page.select_services_for_patient(patient)
    sleep(.5)
    print(f'auth_status: {auth_status}')
    if auth_status == "unavailable" or auth_status == "exam_authorized":
    
        vsp.authorization_page.get_plan_name(patient)
        #check the plan name from the insurance data
        sleep(.5)
        if patient.insurance_data['plan_name'] == "VSP Exam Plus Plan":
            #set the patient copay to 0
            patient.insurance_data['copay'] = "0.00"
            patient.print_data()
            print("Plan is VSP Exam Plus Plan, submitting just exam")
            vsp.authorization_page.get_exam_service() #THIS STILL NEEDS TO CHECK IF THE EXAM IS AVAILABLE FOR AUTHORIZATION
            if auth_status == "unavailable":               
                vsp.authorization_page.issue_authorization(patient)
                vsp.authorization_page.get_confirmation_number()
                vsp.authorization_page.navigate_to_claim()
            else:
                print("Exam is authorized, skipping authorization")
                vsp.authorization_page.navigate_to_authorizations()
                vsp.authorization_page.select_authorization(patient)
                
                
            #unflag frame lens and contacts
            flags["frame"] = False
            flags["lens"] = False
            flags["contacts"] = False
            write_off_materials = True
            
            
        else:
            print("Plan name is not familiar, skipping authorization")
            raise Exception("Plan name is not familiar, skipping authorization")
        
  


    elif auth_status == "use_existing":
        sleep(.5)
        print("Services already authorized for patient")
        vsp.authorization_page.navigate_to_authorizations()
        sleep(.5)
        vsp.authorization_page.select_authorization(patient)
    elif auth_status == "delete_existing":
        print("Services already authorized for patient")
        vsp.authorization_page.navigate_to_authorizations()
        sleep(.5)
        vsp.authorization_page.delete_authorization(patient)
        sleep(.5)
        vsp.authorization_page.select_patient(patient)
        sleep(.5)
        vsp.authorization_page.select_services_for_patient(patient)
        sleep(.5)
        vsp.authorization_page.issue_authorization(patient)
        sleep(.5)
        vsp.authorization_page.get_confirmation_number()
        sleep(.5)
        vsp.authorization_page.navigate_to_claim()
    elif auth_status == "issue":
        print("Services not yet authorized for patient")
        vsp.authorization_page.select_services_for_patient(patient)
        vsp.authorization_page.issue_authorization(patient)
        sleep(.5)
        vsp.authorization_page.get_confirmation_number()
        sleep(.5)
        vsp.authorization_page.navigate_to_claim()


    sleep(2)
    vsp.claim_page.set_dos(patient)
    vsp.claim_page.set_doctor(patient)

    # Exam submission
    if flags["exam"]:
        vsp.claim_page.submit_exam(patient)

    # Glasses related processing

       
    if flags["lens"]:
        vsp.claim_page.submit_frame(patient)
        vsp.claim_page.submit_lens(patient)
        vsp.claim_page.send_rx(patient)


    # Contact lens materials or services
    if flags["contacts"]:
        vsp.claim_page.submit_cl(patient)
    sleep(.5)
    vsp.claim_page.disease_reporting(patient) 
    sleep(.5)
    vsp.claim_page.calculate(patient)
    sleep(.5)
    vsp.claim_page.fill_pricing(patient)
    sleep(.5)
    vsp.claim_page.set_gender(patient)
    sleep(.5)
    vsp.claim_page.fill_address(patient)
    sleep(.5)
    success = vsp.claim_page.click_submit_claim()
    if not success:
        pass
    print("returning  to  patient  page")
    print('done')

    


    



    
    
    
