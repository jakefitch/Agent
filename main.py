from core.base import PatientManager
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from core.logger import Logger
from time import sleep
from config.vsp_map.vsp_session import VspSession
from config.rev_map.rev_session import RevSession



def launch_browser():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    logger = Logger()
    rev = RevSession(context.new_page(), logger, context)
    vsp = VspSession(context.new_page(), logger)
    #return p, browser, rev
    return p, browser, rev, vsp


def create_test_patient():
    patient_manager = PatientManager()
    return patient_manager.create_patient(
        first_name="Jacob",
        last_name="Fitch",
        dob="11/24/1982"
    )


if __name__ == "__main__":
    load_dotenv("/home/jake/Code/.env")

    p, browser, rev, vsp = launch_browser()
    #p, browser, rev = launch_browser()
    patient = create_test_patient()
    rev.login()

    #vsp.login("ama")
    #vsp.claim_page.submit_claim(patient)

    #navigate to patient page
    rev.invoice_page.navigate_to_invoices_page()
    rev.invoice_page.search_invoice(payor="vision")
    sleep(2)
    rev.invoice_page.open_invoice("277404029")
    rev.invoice_page.create_patient_from_invoice()
    rev.invoice_page.scrape_invoice_details(patient)
    rev.invoice_page.click_patient_name_link()
    rev.patient_page.scrape_demographics(patient)
    rev.patient_page.scrape_family_demographics(patient)
    rev.patient_page.expand_insurance()
    rev.insurance_tab.select_insurance("VSP")
    rev.insurance_tab.scrape_insurance(patient)
    rev.patient_page.click_patient_summary_menu()
    rev.patient_page.expand_optical_orders()
    rev.patient_page.open_optical_order(patient)
    rev.optical_order.scrape_frame_data(patient)
    rev.optical_order.scrape_lens_data(patient)
    rev.optical_order.scrape_medical_data(patient)
    patient.print_data()
    print('returning  to  patient  page')
    


    



    
    
    
