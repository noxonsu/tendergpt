from playwright.sync_api import sync_playwright
import re
import json
import requests
import os
from bs4 import BeautifulSoup

from langchain.document_transformers import BeautifulSoupTransformer
import time  # Import the time module
def update_tender_json(tenderid, documentation):
    with open("tenders.json", "r", encoding="utf-8") as file:
        tenders = json.load(file)
    for tender in tenders:
        if tender["tenderId"] == str(tenderid):
            tender["documentation"] = documentation
            break
    with open("tenders.json", "w", encoding="utf-8") as file:
        json.dump(tenders, file, ensure_ascii=False, indent=4)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Change to True if you don't want to see the browser

        password = os.environ.get("ROSTENDERPASSWORD")
        if not password:
            raise ValueError("Environment variable 'ROSTENDERPASSWORD' is not set!")

        page = browser.new_page()

        # Navigate to the login page and log in once
        page.goto("https://rostender.info/login")
        page.fill("#username", "i448539")
        page.fill("#password", password)
        page.click("[name='login-button']")

        time.sleep(2)  # Sleep/wait for 2 seconds after login click
        page.screenshot(path='screenshotAfterLogin.png')

        # find new tenders
        page.goto("https://rostender.info/extsearch/advanced?query=e9ac7cfa7191307db492aaf70b1b5cf6")
        page.screenshot(path='screenshotTenders.png')
        result = page.content()

        soup = BeautifulSoup(result, 'html.parser')

        # Find all <a> and <span> tags
        tags = soup.find_all(['a', 'span'])

        # Extract href and class attributes
        extracted_data = []
        for tag in tags:
            data = {
                "tag": tag.name,
                "href": tag.get('href'),
                "class": " ".join(tag.get('class', []))
            }
            extracted_data.append(data)

        # Print the results
        for data in extracted_data:
            print(data)

        pattern = re.compile(r'href="/tender/(\d+)"'  # Capture the tender ID
                             r'.+?class="box-opisTender__file-name">([^<]+)</span>'  # Capture the file name
                             r'.+?href="(https://files\.rostender\.info/\?t=[^"]+)"',  # Capture the file link
                             re.DOTALL)  # To make . match newline characters as well

        seen_tender_ids = set()
        tenders = []
        existing_tenders = []

        if os.path.exists("tenders.json"):
            with open("tenders.json", "r", encoding='utf-8') as f:
                existing_tenders = json.load(f)
                for tender in existing_tenders:
                    seen_tender_ids.add(tender["tenderId"])

        matches = pattern.findall(result)

        processed_tenders_count = 0  # Counter to keep track of processed tenders
        for match in matches:
            tender_id = match[0]
            file_name = match[1]
            link = match[2]

            if tender_id not in seen_tender_ids:
                seen_tender_ids.add(tender_id)
                tender_data = {
                    "tenderId": tender_id,
                    "region": match[1].strip(),
                    "link": "https://rostender.info/tender/" + tender_id
                }
                tenders.append(tender_data)

                # Send data to webhook
                webhook_url = f"https://noxon.wpmix.net/counter.php?totenders=1&msg={json.dumps(tender_data, ensure_ascii=False)}"
                requests.get(webhook_url)

                # Directly download the documentation here
                file_extension = os.path.splitext(file_name)[-1]
                new_file_name = f"tenders/{tender_id}{file_extension}"

                response = requests.get(link)
                with open(new_file_name, "wb") as file:
                    file.write(response.content)

                update_tender_json(tender_id, new_file_name)

                processed_tenders_count += 1  # Increment the counter after processing each tender

        # Append new tenders to the list of existing tenders
        existing_tenders.extend(tenders)
        time.sleep(10)

        # Save to JSON
        with open("tenders.json", "w", encoding='utf-8') as f:
            json.dump(existing_tenders, f, ensure_ascii=False, indent=4)

        # Display the count of new tenders found
        print(f"Total new tenders found: {len(tenders)}")
        for tender in tenders:
            print(f"Tender ID: {tender['tenderId']}, Region: {tender['region']}, Link: {tender['link']}")

        print(f"Total tenders processed: {processed_tenders_count}")
        browser.close()

if __name__ == "__main__":
    main()
