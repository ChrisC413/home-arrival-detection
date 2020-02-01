
import os
import requests
import base64
import logging
import re
import yaml
from datetime import datetime, timedelta
import time

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

with open(r'detection.yml') as file:

    objects = yaml.load(file, Loader=yaml.FullLoader)
    people = []
    smart_things = []
    for yml_object in objects:
        if 'person' in yml_object:
            yml_object['person']['last_detected']= datetime.now()
            people.append(yml_object['person'])
        if 'SmartThings' in yml_object:
            smart_things = yml_object['SmartThings']


router = os.getenv('ROUTER_ADDRESS', '10.0.1.1')
user = os.getenv('ROUTER_USER', 'admin')
password = os.getenv('ROUTER_PASSWORD')
waiting_period_mins = 30


def detect_person():
    time.sleep(1)
    online_macs = get_router_macs()
    for person in people:
        logging.info("checking presence for " + person['name'])
        present = False
        all_present = True
        for mac in person['macs']:
            present = (mac['mac'] in online_macs) or present
            all_present = all_present & present
        logging.info('presence determined to be ' + str(all_present) + ", partial presence " + str(present))
        if all_present and (person['last_detected'] < (datetime.now() - timedelta(minutes=waiting_period_mins))):
            logging.info('arrival detected for ' + person['name'])
            trigger_action()

        if present:
            person['last_detected'] = datetime.now()


def get_router_macs():
    if not password:
        logging.error('password must be set in environment variables')
    url = 'https://' + router + '/Status_Wireless.live.asp'
    creds = base64.b64encode((user + ':' + password).encode())
    payload = {}
    headers = {
        'Authorization': 'Basic ' + creds.decode("utf-8")
    }
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)

    print(response.text[0])
    pattern = "(?:')([a-fA-F0-9:]{17}|[a-fA-F0-9]{12}$)"
    macs = re.findall(pattern, response.text)
    logging.debug(macs)
    return macs

def trigger_action():
    pass


if __name__ == "__main__":
    detect_person()
