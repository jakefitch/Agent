#!/usr/bin/env python3

import os
from time import sleep
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from my_classes import MyAutomation
from vsp import submit_claim
from dotenv import load_dotenv

#set the .env path
env_path = '/home/jake/Code/.env'
load_dotenv(env_path, override=True)

#############################################   START THE SETUP OF MESSAGING   ######################################
import asyncio
from telegram import Bot
from openai import OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
PROJECT_ID = os.getenv("PROJECT_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID,
    project=PROJECT_ID
)
print(f"Telegram token: {TELEGRAM_TOKEN}")
print(f"Chat ID: {CHAT_ID}")
async def send_ai_message(token, chat_id, message=None):
    bot = Bot(token=token)
    if message:
        await bot.send_message(chat_id=chat_id, text=message)
def ai_message(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return "Error generating message."
async def send_message(prompt):
    # Example prompt for generating a message
    generated_message = ai_message(prompt)
    # Send the generated message via Telegram
    await send_ai_message(TELEGRAM_TOKEN, CHAT_ID, generated_message)

''' #EXAMPLE OF HOW TO USE THE MESSAGING
prompt = "Generate a grumpy message letting me know you're done running an attendance report."
asyncio.run(send_message(prompt))'''

#############################################   END THE SETUP OF MESSAGING   ######################################


# Initialize automation
place = "Amarillo"
automation = MyAutomation(location=place,headless=False)
automation.load_pages_vsp()

automation.switch_to_tab(0)

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID,
    project=PROJECT_ID
)

# Function to send a Telegram message
async def send_telegram_message(token, chat_id, message=None):
    bot = Bot(token=token)
    if message:
        await bot.send_message(chat_id=chat_id, text=message)

# Function to generate human-like response using OpenAI
def get_human_like_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Replace with your desired model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Function to send a summary message after claims submission
def send_summary_message(success_count, failed_claims):
    # Create the prompt based on the success_count and failed_claims
    if failed_claims:
        failed_claims_details = "\n".join([f"- {name} (DOS: {dos})" for name, dos in failed_claims])
        prompt = (
            f"You are a bad ass buddy. Cool! You have just completed subitting some claims for your friend Jake. "
            f"You successfully submitted {success_count} claims. However, there were some claims that failed: \n"
            f"{failed_claims_details}. In a fun and funny and irreverent way, let Jake know how many claims you successfully submitted, and then tell him the details of the failed claims."
        )
    else:
        prompt = (
            f"You are a bad ass buddy. Cool! You have just completed subitting some claims for your friend Jake."
            f"You successfully submitted all {success_count} claims. Let Jake know that there are no further issues to address in a way that's going to put a smile on his face."
        )
    
    # Generate the human-like message using the prompt
    human_like_message = get_human_like_response(prompt)
    
    # Send the message via Telegram
    asyncio.run(send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message=human_like_message))

    print(f"Message sent: {human_like_message}")

class ClaimTracker:
    def __init__(self):
        self.success_count = 0
        self.failed_claims = []  # List of tuples (name, dos)
        
    def add_success(self):
        self.success_count += 1
        
    def add_failure(self, name, dos):
        self.failed_claims.append((name, dos))
        
    def get_summary(self):
        return self.success_count, self.failed_claims

def submit_multiple_claims(automation):
    tracker = ClaimTracker()
    automation.switch_to_tab(0)
    while True:  
        # Wait for and find the "Go to next page" element
        next_page = automation.wait_for_element(By.XPATH, '//*[@title="Go to next page"]')
        next_page_class = next_page.get_attribute("class")
        
        # Check if the "next page" button is disabled
        if "e-disable" in next_page_class or "e-prevpagedisabled" in next_page_class:
            process_page(automation, tracker)
            print("No more pages")
            break  # Exit the loop if the next page button is disabled
        else:
            process_page(automation, tracker)
            sleep(2)
            next_page = automation.wait_for_element(By.XPATH, '//*[@title="Go to next page"]')  
            next_page.click()
            sleep(2)  # Click the next page button if not disabled

    # Send summary message after all claims are processed
    success_count, failed_claims = tracker.get_summary()
    send_summary_message(success_count, failed_claims)

def process_page(automation, tracker):
    # Initial fetching of elements
    claims = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
    # Count the number of claims found
    count = len(claims)

    # Use a while loop instead of for loop to avoid stale elements
    index = 0
   
    while index < count:
        # Fetch elements fresh each time to avoid stale references
        sleep(1)
        elements = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
        sleep(1)

        try:
            elements[index].click()
        except Exception as e:
            automation.take_screenshot()
            raise e

        element = automation.wait_for_element(By.CSS_SELECTOR, 'span[data-test-id="invoiceDetailsDocsAndImagesTab"]')
        badge_span = element.find_element(By.CSS_SELECTOR, 'span.badge.margin-left-xs')
        needs_to_be_submitted = False
        if badge_span.text.strip():  # Check if it has content (remove leading/trailing spaces)
            decision = "Already Submitted"
            sleep(1)
        else:
            decision = "Needs to be Submitted"
            needs_to_be_submitted = True
        sleep(1)
        
        if needs_to_be_submitted:
            try:
                name = automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceHeaderPatientNameLink"]').text
                dos = automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceHeaderDateOfService"]').text
            except: 
                name = "Unknown Patient"
                dos = "Unknown DOS"
            
            print(f'submitting claim for {name}')

            try:
                submit_claim(automation)
                tracker.add_success()
                print(f'Successfully submitted claim for {name}')
            except Exception as e:
                print(f'Failed to submit claim for {name}: {str(e)}')
                tracker.add_failure(name, dos)
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

# Additional setup for initial automation steps
automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerParentNavigateButtonaccounting']").click()
sleep(1)
print("clicked on accounting")
automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerChildNavigateButtoninvoices']").click()
sleep(1)
print("clicked on invoices")
payor = automation.wait_for_element(By.XPATH, "//*[@formcontrolname='payerName']")
payor.clear()
sleep(1)
payor.send_keys("vision")
sleep(1)

search_button = automation.wait_for_element(By.XPATH, "//*[@data-test-id='invoiceDashboardSearchButton']").click()
sleep(1)

try:
    submit_multiple_claims(automation)
except Exception as e:
    print(f"Error submitting multiple claims: {e}")

#send a message to the user including the number of successes


automation.close_browser()

