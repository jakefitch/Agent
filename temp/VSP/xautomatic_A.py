#!/usr/bin/env python3

import os
from time import sleep
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from my_classes import MyAutomation
from vsp import submit_claim
import os
from time import sleep
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
        #print(f"OpenAI API call failed: {e}")
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


prompt = "I'm Jake and you are Sam. Generate a grumpy message letting me know you're going to submit my VSP claims AGAIN ."
asyncio.run(send_message(prompt))

# Initialize automation
place = "Amarillo"
automation = MyAutomation(location=place,headless=False)
automation.load_pages_vsp()
automation.switch_to_tab(0)




def submit_multiple_claims(automation):
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
            #print("No more pages")
            break  # Exit the loop if the next page button is disabled
        else:
            loop(success_count, failed_claims)
            sleep(2)
            next_page = automation.wait_for_element(By.XPATH, '//*[@title="Go to next page"]')  
            next_page.click()
            sleep(2)  # Click the next page button if not disabled


def loop(success_count, failed_claims):
    # Initial fetching of elements
    claims = automation.wait_for_elements(By.XPATH, '//span[text()="Authorized"]')
    # Count the number of claims found
    count = len(claims)
    #print(f'Found {count} claims')

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
        #print(decision)
        sleep(1)
        if needs_to_be_submitted:

            try:
                name = automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceHeaderPatientNameLink"]').text
            except: 
                name = "John Doe"
            
            try:
                dos = automation.wait_for_element(By.XPATH, '//*[@data-test-id="invoiceNavigateServiceDateButton"]').text
            

            except: 
                dos = "01/01/2024"

            print(f'submitting cliam for {name} on {dos}')


            try:
                submit_claim(automation)
                success_count += 1
            except Exception as e:
                print(f"Error submitting claim: {e}")
                automation.switch_to_tab(0)
                #if the date of service is more than 3 days ago, then we need to append failed claims
                if dos < (datetime.now() - timedelta(3)).strftime("%m/%d/%Y"):
                    failed_claims.append((name, dos))

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
#print("clicked on accounting")
automation.wait_for_element(By.XPATH, "//*[@data-test-id='headerChildNavigateButtoninvoices']").click()
sleep(1)
#print("clicked on invoices")
payor = automation.wait_for_element(By.XPATH, "//*[@formcontrolname='payerName']")
payor.clear()
sleep(1)
payor.send_keys("vision")
sleep(1)
# Find the element inside form controlname invoiceStartDate and inputmode is numeric

date1 = automation.wait_for_element(By.XPATH, "//ejs-datepicker[@formcontrolname='invoiceDateStart']//input[@inputmode='numeric']")
#yesterday = datetime.now() - timedelta(1)
yesterday = datetime.now()
five_days_ago = datetime.now() - timedelta(5) ##set how many days ago you want to search
date1.clear()
date1.send_keys(five_days_ago.strftime("%m/%d/%Y"))
sleep(1)
automation.send_keys(Keys.TAB)
date2 = automation.wait_for_element(By.XPATH, "//ejs-datepicker[@formcontrolname='invoiceDateEnd']//input[@inputmode='numeric']")
date2.clear()
date2.send_keys(yesterday.strftime("%m/%d/%Y"))
sleep(1)
automation.send_keys(Keys.TAB)
sleep(1)
search_button = automation.wait_for_element(By.XPATH, "//*[@data-test-id='invoiceDashboardSearchButton']").click()
sleep(1)

try:
    submit_multiple_claims(automation)
    prompt = "I'm Jake and you are Sam. Generate a grumpy message letting me know you're finnished submitting my VSP claims (call me a bastard at least!)."
    asyncio.run(send_message(prompt))
except Exception as e:
    print(f"Error submitting multiple claims: {e}")
    prompt = "I'm Jake and you are Sam. Generate a grumpy message letting me know you tried to submit my VSP claims but something went wrong and it's probably my fault."
    asyncio.run(send_message(prompt))
automation.close_browser()

