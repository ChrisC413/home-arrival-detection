import sched
import os
import requests
import base64
import logging
import re
import yaml
from datetime import datetime, timedelta
import time
import pysmartthings
import aiohttp
import asyncio

schedule = sched.scheduler(time.time, time.sleep)


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

with open(r'detection.yml') as file:

    objects = yaml.load(file, Loader=yaml.FullLoader)
    people = []
    smart_things = []
    actions = []
    for yml_object in objects:
        if 'person' in yml_object:
            yml_object['person']['last_detected']= datetime.now()
            people.append(yml_object['person'])
        if 'SmartThings' in yml_object:
            smart_things = yml_object['SmartThings']
        if 'Action' in yml_object:
            actions = yml_object['Action'][0]


router = os.getenv('ROUTER_ADDRESS', '10.0.1.1')
user = os.getenv('ROUTER_USER', 'admin')
password = os.getenv('ROUTER_PASSWORD')
waiting_period_mins = 30


def detect_person():

    try:
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
            eligible_to_return = person['last_detected'] < (datetime.now() - timedelta(minutes=waiting_period_mins))
            if all_present and eligible_to_return:
                logging.info('arrival detected for ' + person['name'])
                person['last_detected'] = datetime.now()
                try_trigger_action()

            if present and not eligible_to_return:
                logging.debug("at least one device detected presence for " + person['name'] + " so uodating last detected time")
                person['last_detected'] = datetime.now()

        ## debugging
        try_trigger_action()
    finally:
        schedule.enter(30, 1, detect_person)

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


# Run action if in eligible timeframe
def try_trigger_action():
    actionable = False
    start = datetime.strptime(actions['Timeframe']['Start'], "%H:%M")
    now = datetime.strptime(str(datetime.now().hour)+ ':' + str(datetime.now().minute), "%H:%M" )
    stop = datetime.strptime(actions['Timeframe']['End'], "%H:%M")
    if stop < start:
        stop = stop + timedelta(days=1)
    if start < now:
        if now < stop:
            actionable = True
    if actionable:
        logging.info("trigger is actionable")
        loop.run_until_complete(trigger_action())
    else:
        logging.info("not actionable at this time")
        logging.debug(start)
        logging.debug(stop)
        logging.debug(now)


async def trigger_action():
    async with aiohttp.ClientSession() as session:
        api = pysmartthings.SmartThings(session, smart_things['access-token'])
        result = await api.scenes()
        assert result
        for scene in result:
            for requested_scene in actions['Action']['SmartThings']['PowerOn']:
                if scene.scene_id in  requested_scene['SceneID']:
                    result = await scene.execute()




if __name__ == "__main__":
    pass
print("main")
loop = asyncio.get_event_loop()
detect_person()
schedule.run()
loop.close()
logging.error("Broke out of scheduler, exiting")
