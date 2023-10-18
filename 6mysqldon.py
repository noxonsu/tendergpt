import os
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "https://apitorgi.myseldon.com"
LOGIN_ENDPOINT = "/User/Login"
CREATE_TENDER_REQUEST_ENDPOINT = "/Purchases/New"  
FETCH_TENDERS_RESULTS_ENDPOINT = "/Purchases/Result"

def login_to_service():
    login_url = f"{BASE_URL}{LOGIN_ENDPOINT}"
    
    payload = {
        "name": os.getenv("MYSELDON_LOGIN"),
        "password": os.getenv("MYSELDON_PASS")
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.post(login_url, json=payload, headers=headers)
    if response.status_code == 200 and 'result' in response.json() and 'token' in response.json()['result']:
        return response.json()['result']['token']
    else:
        raise ValueError("Failed to login!")

def request_tender_data(token):
    tender_request_url = f"{BASE_URL}{CREATE_TENDER_REQUEST_ENDPOINT}?token={token}"
    
    date_one_day_ago = (datetime.now() - timedelta(days=1)).isoformat() + "Z"
    payload = {
        "filterId": 4348347,
        "dateFrom": date_one_day_ago,
        "dateTo": datetime.now().isoformat() + "Z",
        "subtype": 0
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.post(tender_request_url, json=payload, headers=headers)
    response_data = response.json()
    if response.status_code == 200 and 'result' in response_data and 'taskId' in response_data['result']:
        return response_data['result']['taskId']
    else:
        raise ValueError("Failed to request tender data!")

def fetch_tenders_results(token, task_id):
    time.sleep(5)  # wait for 10 seconds
    result_url = f"{BASE_URL}{FETCH_TENDERS_RESULTS_ENDPOINT}?token={token}"
    payload = {
        "taskId": task_id,
        "pageIndex": 0
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.post(result_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(response.json())
        with open('seldon.json', 'w') as outfile:
            json.dump(response.json(), outfile)
    else:
        raise ValueError("Failed to fetch tenders results!")

if __name__ == "__main__":
    token = login_to_service()
    print(f"Token: {token}")
    task_id = request_tender_data(token)
    print(f"Task ID: {task_id}")

    fetch_tenders_results(token, task_id)
