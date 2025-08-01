"""Batch claim submission for all Vision invoices.

This script searches for invoices with payor 'vision' and submits a
claim for each invoice that does not already have a document uploaded.
"""

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from time import sleep

from core.logger import Logger
from config.vsp_map.vsp_session import VspSession
from config.rev_map.rev_session import RevSession
from core.utils import get_claim_service_flags


def launch_browser():
    """Start Playwright and return browser sessions."""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    logger = Logger()
    rev = RevSession(context.new_page(), logger, context)
    vsp = VspSession(context.new_page(), logger)
    return p, browser, rev, vsp


def process_invoice(invoice_id: str, rev: RevSession, vsp: VspSession) -> None:
    """Handle a single invoice number."""
    # Search for specific invoice by ID
    rev.invoice_page.search_invoice(invoice_number=invoice_id)
    sleep(2)
    #open invoice
    rev.invoice_page.open_invoice(invoice_id)
    rev.invoice_page.click_docs_and_images_tab()
    # Check if invoice has document before opening
    if rev.invoice_page.check_for_document():
        print(f"Invoice {invoice_id} already has document, skipping")
        return
    


    # Create patient from invoice and scrape details
    #click back to details tab
    rev.invoice_page.click_invoice_details_tab()
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

    flags = get_claim_service_flags(patient)

    member_found = vsp.member_search_page.search_member(patient)
    if not member_found:
        print("Member not found, skipping authorization")
        rev.invoice_page.close_invoice_tabs(invoice_id)
        return
    sleep(2)

    vsp.authorization_page.select_patient(patient)
    sleep(1)
    auth_status = vsp.authorization_page.select_services_for_patient(patient)
    sleep(0.5)

    if auth_status in {"unavailable", "exam_authorized"}:
        vsp.authorization_page.get_plan_name(patient)
        sleep(0.5)
        if patient.insurance_data.get("plan_name") == "VSP Exam Plus Plan":
            patient.insurance_data["copay"] = "0.00"
            vsp.authorization_page.get_exam_service()
            if auth_status == "unavailable":
                vsp.authorization_page.issue_authorization(patient)
                vsp.authorization_page.get_confirmation_number()
                vsp.authorization_page.navigate_to_claim()
            else:
                vsp.authorization_page.navigate_to_authorizations()
                vsp.authorization_page.select_authorization(patient)
            flags["frame"] = False
            flags["lens"] = False
            flags["contacts"] = False
        else:
            print("Unknown plan name, skipping")
            rev.invoice_page.close_invoice_tabs(invoice_id)
            return
    elif auth_status == "use_existing":
        sleep(0.5)
        vsp.authorization_page.navigate_to_authorizations()
        sleep(0.5)
        vsp.authorization_page.select_authorization(patient)
    elif auth_status == "delete_existing":
        vsp.authorization_page.navigate_to_authorizations()
        sleep(0.5)
        vsp.authorization_page.delete_authorization(patient)
        sleep(0.5)
        vsp.authorization_page.select_patient(patient)
        sleep(0.5)
        vsp.authorization_page.select_services_for_patient(patient)
        sleep(0.5)
        vsp.authorization_page.issue_authorization(patient)
        sleep(0.5)
        vsp.authorization_page.get_confirmation_number()
        sleep(0.5)
        vsp.authorization_page.navigate_to_claim()
    elif auth_status == "issue":
        vsp.authorization_page.select_services_for_patient(patient)
        vsp.authorization_page.issue_authorization(patient)
        sleep(0.5)
        vsp.authorization_page.get_confirmation_number()
        sleep(0.5)
        vsp.authorization_page.navigate_to_claim()

    sleep(2)
    vsp.claim_page.set_dos(patient)
    vsp.claim_page.set_doctor(patient)

    if flags["exam"]:
        vsp.claim_page.submit_exam(patient)

    if flags["lens"]:
        vsp.claim_page.submit_frame(patient)
        vsp.claim_page.submit_lens(patient)
        vsp.claim_page.send_rx(patient)

    if flags["contacts"]:
        vsp.claim_page.submit_cl(patient)

    sleep(0.5)
    vsp.claim_page.disease_reporting(patient)
    sleep(0.5)
    vsp.claim_page.calculate(patient)
    sleep(0.5)
    vsp.claim_page.fill_pricing(patient)
    sleep(0.5)
    vsp.claim_page.set_gender(patient)
    sleep(0.5)
    vsp.claim_page.fill_address(patient)
    sleep(0.5)
    vsp.claim_page.click_submit_claim()
    rev.invoice_page.close_invoice_tabs(invoice_id)


def main():
    load_dotenv("/home/jake/Code/.env")
    p, browser, rev, vsp = launch_browser()

    rev.login()
    vsp.login("ama")

    rev.invoice_page.navigate_to_invoices_page()
    rev.invoice_page.search_invoice(payor="vision")
    sleep(2)

    results = rev.invoice_page.scrape_all_search_results()
    invoice_ids = [r["invoice_id"] for r in results]
    print(f'Found {len(invoice_ids)} invoices to process')

    for inv in invoice_ids:
        try:
            process_invoice(inv, rev, vsp)
            #close the invoice tab
            rev.invoice_page.close_invoice_tabs(inv)
        except Exception as e:
            print(f"Error processing {inv}: {e}")
            rev.invoice_page.close_invoice_tabs(inv)

    browser.close()
    p.stop()


if __name__ == "__main__":
    main()
