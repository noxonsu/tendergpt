#bash: rostenderPASSWORD=i449 xvfb-run python getTenderFiles2.py 

from playwright.sync_api import sync_playwright
import re
import json
import requests
import os
import time  # Import the time module

def load_tenders_without_docs():
    with open("tenders.json", "r", encoding="utf-8") as file:
        tenders = json.load(file)
    return [tender for tender in tenders if not tender.get("documentation")]

def get_file_links(html_content):
    matches = re.findall(r'"title":"(.*?)","fsid":"(.*?)","link":"(.*?)"', html_content)
    target_titles = ["Извещение", "Кп", "ткп"]
    target_links = [(fsid, link) for title, fsid, link in matches if title in target_titles]
    return target_links if target_links else [title for title, _, _ in matches]

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

        password = os.environ.get("rostenderPASSWORD")
        if not password:
            raise ValueError("Environment variable 'rostenderPASSWORD' is not set!")

        page = browser.new_page()
        
        # Navigate to the login page and log in once
        page.goto("https://rostender.info/login")
        page.fill("#username", "i448539")
        page.fill("#password", os.environ.get("rostenderPASSWORD"))
        
        
        page.click("[name='login-button']")
        
        time.sleep(2)  # Sleep/wait for 10 seconds after login click
        html_content = page.content()
        page.screenshot(path='screenshotAfterLogin.png')
        with open("after_login.html", "w", encoding="utf-8") as f:
            f.write(html_content) 
        

        tenders_to_process = load_tenders_without_docs()

        for tender in tenders_to_process:
            tenderid = tender["tenderId"]
            page.goto("https://rostender.info/tender/"+ tenderid)
            html_content = page.content()
            with open("tenders/"+ str(tenderid)+".html", "w", encoding="utf-8") as f:
                f.write(html_content) 
           
            file_links_or_titles = get_file_links(html_content)

            if file_links_or_titles and isinstance(file_links_or_titles[0], tuple):  
                documentation_links = []
                for fsid, link in file_links_or_titles:
                    response = requests.get(link)
                    file_extension = os.path.splitext(fsid)[-1]
                    new_file_name = f"tenders/{tenderid}{file_extension}"
                    documentation_links.append(new_file_name)
                    with open(new_file_name, "wb") as file:
                        file.write(response.content)
                update_tender_json(tenderid, documentation_links)
            else:
                print(f"Files not found. Available files: {', '.join(file_links_or_titles)}")
                update_tender_json(tenderid, "not_found")
        
        browser.close()

if __name__ == "__main__":
    main()
