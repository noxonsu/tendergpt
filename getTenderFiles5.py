from playwright.sync_api import sync_playwright
import re
import json
import requests
import os
from bs4 import BeautifulSoup
import time
from pyunpack import Archive



from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage

def load_tenders_from_file(file_name="tenders.json"):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_tenders_to_file(tenders, file_name="tenders.json"):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(tenders, f, ensure_ascii=False, indent=4)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

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

        page.goto("https://rostender.info/extsearch/advanced?query=e9ac7cfa7191307db492aaf70b1b5cf6")
        page.screenshot(path='screenshotTenders.png')
        result = page.content()

        soup = BeautifulSoup(result, 'html.parser')
        tenders = soup.find_all('div', class_='tender__info')
        
        existing_tenders = load_tenders_from_file()
        new_tenders_count = 0
        for tender in tenders:
            current_data = {}
            save_current_tender = False
            

            # Extract tender ID
            tender_number_tag = tender.find(class_='tender__number')
            if tender_number_tag:
                tender_id_text = tender_number_tag.get_text(strip=True)
                tenderid_match = re.search(r'Тендер\s*№(\d+)', tender_id_text)
                if tenderid_match:
                    tenderid = tenderid_match.group(1)
                    current_data["tenderId"] = tenderid
                else:
                    continue  # If tender ID is not found, skip the current iteration


            # Extract tender name
            tender_name_tag = tender.find(class_='description tender-info__description tender-info__link')
            if tender_name_tag:
                current_data["tendername"] = tender_name_tag.get_text(strip=True)

            # Extract documentation filename
            doc_name_tag = tender.find(class_='box-opisTender__file-name')
            if doc_name_tag:
                current_data["documentationfilename"] = doc_name_tag.get_text(strip=True)

            # Extract documentation URL
            doc_url_tag = tender.find(class_='box-opisTender__file-icon sprite-pseudo')
            if doc_url_tag:
                current_data["documentationurl"] = doc_url_tag.get('href')
            
            #  extract <i class=\"shl\"></i>
            keyword_tag = tender.find(class_='shl')
            if keyword_tag:
                current_data["keyword"] = keyword_tag.get_text(strip=True)

            # Extract file-snippet
            snippet_tag = tender.find('span', id=re.compile(r'^file-snippet-\d+$'))
            if snippet_tag:
                current_data["file-snippet"] = snippet_tag.get_text(strip=True)

            if 'documentationfilename' not in current_data:
                continue

            file_extension = os.path.splitext(current_data['documentationfilename'])[-1]
            new_file_path = f"tenders/{tenderid}{file_extension}"

            # Проверка наличия URL для скачивания файла
            if 'documentationurl' not in current_data or not current_data['documentationurl']:
                continue

            # Если файл уже существует, не скачиваем его снова
            if os.path.exists(new_file_path):
                continue

            # Скачивание файла
            #response = requests.get(current_data['documentationurl'])
            #with open(new_file_path, "wb") as file:
            #    file.write(response.content)

            #write documentationurl to tenderid.md
            #TypeError: a bytes-like object is required, not 'str'
            with open('tenders/'+tenderid+'.md', "wb") as file:
                file.write(current_data['documentationurl'].encode('utf-8'))


            # Check if the file is an archive
            #if file_extension.lower() in ['.7z', '.rar', '.zip']:
                # Define a directory named "extracted_<tenderid>" to extract to
            #    extract_to = f"tenders/extracted_{tenderid}/"
                
                # Check if directory exists, if not, create it
            #    if not os.path.exists(extract_to):
            #        os.makedirs(extract_to)
                
                # Unpack the archive to the created directory
            #    Archive(new_file_path).extractall(extract_to)
            #    print(f"Extracted {new_file_path} to {extract_to}")
            
            # Добавляем путь к скачанному файлу в данные о тендере
            current_data['documentationfilepath'] = new_file_path

            tendername = current_data['tendername']
            keyword=current_data['keyword']
            chat = ChatOpenAI(temperature=0)
            messages = [
                SystemMessage(
                content="Ты помошник по тендерам. Я буду искать тендеры по ключевым словам и присылать тебе. Твоя задача определить подходит ли тендер тебе или нет. Если не подходит пиши 'Не подходит'. Если подходит напиши почему ты так думаешь. Мы поставляем сырье (не производные, не готовые продукты), проанализируй заголовок тендера и реши может ли это быть потенциально наш клиент"
                ),
                HumanMessage(
                content="Заголовок тендера: " + tendername+ ". Ключевое слово: " + keyword+". "
                )
            ]
            gpttitle = chat(messages)
            if "Не подходит" not in gpttitle.content:
                        # Construct the webhook URL with the tender data
                        tender_data_json = json.dumps(tender, ensure_ascii=False)
                        webhook_url = f"https://noxon.wpmix.net/counter.php?totenders=1&msg={tender_data_json}"
                        
                        # Send a POST request to the webhook URL
                        response = requests.post(webhook_url)
                        if response.status_code != 200:
                            print(f"Failed to send webhook for tender at index {idx}. Status code: {response.status_code}")

            current_data['gpttitle'] = gpttitle.content
            current_data["tenderId"] = tenderid
            current_data['url'] = 'https://rostender.info/tender/' + current_data['tenderId']
            current_data['documentationurl'] = 'https://github.com/noxonsu/tendergpt/raw/main/'+tender['tenderId']+'.md'
        
            if tenderid and current_data:
                existing_tenders.append(current_data)
                new_tenders_count += 1
                save_tenders_to_file(existing_tenders)

        # Display the count of new tenders found
        print(f"Total new tenders found: {new_tenders_count}")

        browser.close()


if __name__ == "__main__":
    main()