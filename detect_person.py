
import os
import requests
import base64
import logging

router = os.getenv('ROUTER_ADDRESS', '10.0.1.1')
user = os.getenv('ROUTER_USER', 'admin')
password = os.getenv('ROUTER_PASSWORD')


def detect_person():
    response = get_user_macs()


def get_user_macs():
    if not password:
        logging.error('password must be set in environment variables')
    url = 'https://' + router + '/Status_Wireless.live.asp'
    creds = base64.b64encode((user + ':' + password).encode())
    payload = {}
    headers = {
        'Authorization': 'Basic ' + creds.decode("utf-8")
    }
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)

    print(response.text.encode('utf8'))


if __name__ == "__main__":
    detect_person()
