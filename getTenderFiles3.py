from playwright.sync_api import sync_playwright
import re
import json
import requests
import os
from bs4 import BeautifulSoup
import time

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
        page.goto("C:\\Users\\Александр\\Documents\\GitHub\\tendergpt\\tmpCat.html")
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
            response = requests.get(current_data['documentationurl'])
            with open(new_file_path, "wb") as file:
                file.write(response.content)
            
            # Добавляем путь к скачанному файлу в данные о тендере
            current_data['documentationfilepath'] = new_file_path

            if tenderid and current_data:
                existing_tenders.append(current_data)
                new_tenders_count += 1
                save_tenders_to_file(existing_tenders)

        # Display the count of new tenders found
        print(f"Total new tenders found: {new_tenders_count}")

        browser.close()


if __name__ == "__main__":
    main()