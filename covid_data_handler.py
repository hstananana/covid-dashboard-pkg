'''
handle aspects of covid data
including as infection rates, death rates and hospital admissions
'''
import json
import csv
import time
import sched
import logging
from uk_covid19 import Cov19API

logging.basicConfig(filename='logfile.log', level=logging.DEBUG)

'''
open the config file and assign variables to its contents
'''
config_json = open('config.json', 'r').read()
config_json = open('config.json', 'r').read()
config = json.loads(config_json)
location = config['Location']
location_type = config['Location_type']
title = config['Title']

# define updates and repeated_updates as lists, and canceled as a dictionary

updates = []
cancelled = {}


def minutes_to_seconds(minutes: str) -> int:
    '''
    Convert minutes to seconds
    '''
    return int(minutes)*60


def hours_to_minutes(hours: str) -> int:
    '''
    Convert hours to minutes
    '''
    return int(hours)*60


def hhmm_to_seconds(hhmm: str) -> int:
    '''
    Use hours to minutes and minutes to seconds to convert HH:MM to seconds
    '''
    if len(hhmm.split(':')) != 2:
        print('Incorrect format. Argument must be formatted as HH:MM')
        return None
    return minutes_to_seconds(hours_to_minutes(hhmm.split(':')[0])) + \
        minutes_to_seconds(hhmm.split(':')[1])


s = sched.scheduler(time.time, time.sleep)


def parse_csv_data(csv_filename):
    '''
    Open a csv file and turn it into a list of lists
    '''
    csv_data = csv.reader(open(csv_filename, 'r'))
    csv_list = []
    for row in csv_data:
        row_list = []
        for value in row:
            row_list.append(value)
        csv_list.append(row_list)
    return csv_list


def process_covid_csv_data(covid_csv_data):
    '''
    Take the result pf parse_csv_data and fetch data from it
    '''
    last7days_cases = 0
    for number in range(3, 10):
        last7days_cases += int(covid_csv_data[number][6])
    current_hospital_cases = int(covid_csv_data[1][5])
    total_deaths = int(covid_csv_data[14][4])
    return last7days_cases, current_hospital_cases, total_deaths


def covid_API_request(location='Exeter', location_type='ltla'):
    '''
    Use the UK government's covid api to get covid data
    '''
    location_filter = [
        'areaType='+location_type,
        'areaName='+location
    ]
    data = {
        "date": "date",
        "areaName": "areaName",
        "areaCode": "areaCode",
        "newCasesByPublishDate": "newCasesByPublishDate",
        "hospitalCases": "hospitalCases",
        "cumDeaths28DaysByPublishDate": "cumDeaths28DaysByPublishDate"
    }
    try:
        api = Cov19API(filters=location_filter, structure=data)
        json_data = api.get_json(as_string=True)
        api_dict = json.loads(json_data)
    except:
        logging.error(
            'Failed to get covid data. Please check you are connected to the internet')
        raise ConnectionError
    return api_dict


def process_covid_API(covid_api_data):
    '''
    get useful values from the data
    '''
    json_file = covid_api_data['data']
    last7days_cases = 0
    for number in range(0, 6):
        data_for_date = json_file[number]
        last7days_cases += data_for_date['newCasesByPublishDate']
    if last7days_cases is None:
        last7days_cases = 0
    # There is a 5-day delay for hospital cases to be reported
    current_hospital_cases = json_file[5]['hospitalCases']
    if current_hospital_cases is None:
        current_hospital_cases = 0
    total_deaths = json_file[0]['cumDeaths28DaysByPublishDate']
    if total_deaths is None:
        total_deaths = 0
    return last7days_cases, current_hospital_cases, total_deaths


def repeat_if_applicable(update_name, repeat):
    '''
    if repeat is true, schedule the update for the same time the next day.
    if it is not, then remove the update from the list
    '''
    if repeat is True:
        schedule_covid_updates(86400, update_name, repeat)
    else:
        for update in updates:
            if update['title'] == update_name:
                updates.remove(update)


def update_covid():
    '''
    Update the covid data
    '''
    local_data = covid_API_request(location, location_type)
    local_7day_infections, local_hospital_cases, local_deaths_total = process_covid_API(
        local_data)
    national_data = covid_API_request('United Kingdom', 'overview')
    national_7day_infections, hospital_cases, deaths_total = process_covid_API(
        national_data)


def schedule_covid_updates(update_interval, update_name, repeat=False):
    '''
    Schedule an update to happen in update_interval seconds
    '''
    logging.info('Schedule successful for %s', update_name)
    event_1 = s.enter(update_interval, 1, update_covid)
    event_2 = s.enter(update_interval, 2, repeat_if_applicable,
                 argument=(update_name, repeat))

    if cancelled.get(update_name):  # don't run the update if its been cancelled
        logging.info('Cancelled %s', update_name)
        s.cancel(event_1)
        s.cancel(event_2)
    s.run(blocking=False)


for line in reversed(open("logfile.log").readlines()):
    '''
    Recover covid updates from the log file
    '''
    if line.find('INFO:root:RECOVERY_UPDATES:') != -1:
        info_from_line = line.replace('INFO:root:RECOVERY_UPDATES:', '')
        try:
            json_updates = json.loads(info_from_line)
            for line in json_updates:
                if line not in updates:
                    updates.append(line)
            logging.info('Successfully loaded covid updates from logfile')
            for update in updates:
                update_name = update['title']
                update_time = update['update_time']
                if update['repeat'] == 'True':
                    repeat = True
                else:
                    repeat = False
                logging.info('Update name is %s', update_name)
                current_time = hhmm_to_seconds(
                    time.strftime('%H:%M', time.localtime()))
                if hhmm_to_seconds(update_time) < current_time:
                    update_interval = (
                        86400+hhmm_to_seconds(update_time) - current_time)
                    logging.info('Will happen tomorrow at %s',
                                 str(update_time))
                else:
                    update_interval = (hhmm_to_seconds(
                        update_time) - current_time)
                    logging.info('Seconds before update: %s ',
                                 str(update_interval))
                if update['update_covid'] != 'None':
                    schedule_covid_updates(
                        update_interval, update_name, repeat)
        except:
            logging.info('Failed to load covid updates from logfile')
            break

# set some initial values for local_data, local_7day_infections, national_data etc

local_data = covid_API_request(
    location, location_type)
local_7day_infections, local_hospital_cases, local_deaths_total = process_covid_API(
    local_data)
national_data = covid_API_request('United Kingdom', 'overview')
national_7day_infections, hospital_cases, deaths_total = process_covid_API(
    national_data)
