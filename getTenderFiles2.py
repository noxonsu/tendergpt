from playwright.sync_api import sync_playwright

from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_transformers import BeautifulSoupTransformer
import re
import json
import requests
import os

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Change 'headless' to True if you don't want to see the browser
        page = browser.new_page()

        # Navigate to the login page
        page.goto("https://rostender.info/login")

        # Fill in login details and submit
        page.fill("#username", "i448539")
        page.fill("#password", os.environ.get("rostenderPASSWORD"))
        page.click("[name='login-button']")

        # Wait for successful login (e.g., by checking if a specific element exists after login)
        page.wait_for_selector(".header-login__name")
        
        print(page.content())

        page.goto("https://rostender.info/tender/70940564")
        html = page.content()

        # Transform
        bs_transformer = BeautifulSoupTransformer()
        docs_transformed = bs_transformer.transform_documents(html,tags_to_extract=["a","span"])


        result = docs_transformed[0].page_content[0:2000000]

        print(result)

        # Close the browser
        browser.close()

if __name__ == "__main__":
    main()
