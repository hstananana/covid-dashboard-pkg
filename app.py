'''
backend for the covid dashboard
'''

import time
import json
import logging
from flask import Flask, request
from flask.templating import render_template
from werkzeug.utils import redirect
from covid_data_handler import schedule_covid_updates
import covid_data_handler
from covid_news_handling import schedule_news_updates
import covid_news_handling
import test_covid_data_handler
import test_news_data_handling

# set up a log file

app = Flask(__name__)

# set up the logger

logging.basicConfig(filename='logfile.log',
                    encoding='utf-8', level=logging.DEBUG)

# run basic tests

logging.info(str(test_covid_data_handler.test_covid_API_request()))
logging.info(str(test_covid_data_handler.test_process_covid_csv_data()))
logging.info(str(test_covid_data_handler.test_covid_API_request()))
logging.info(str(test_covid_data_handler.test_schedule_covid_updates()))
logging.info(str(test_news_data_handling.test_news_API_request()))
logging.info(str(test_news_data_handling.test_update_news))

def cancel_update_request():
    '''
    remove a cancelled update from the list and prevent it from running
    '''
    cancel_update = request.args.get('update_item')
    if cancel_update is not None:
        covid_data_handler.cancelled[cancel_update] = True
        for update in covid_data_handler.updates:
            if update['title'] == cancel_update:
                covid_data_handler.updates.remove(update)
        logging.info('RECOVERY_UPDATES: %s',
                     (str(covid_data_handler.updates).replace("'", '"')))


def remove_article_request():
    '''
    remove articles if the 'x' has been clicked
    '''
    request_remove_articles = request.args.get('notif')
    if request_remove_articles is not None:
        print(request.args.get('notif'))
        for article in covid_news_handling.news_articles:
            if article['title'] == request.args['notif'].replace('+', ' '):
                covid_news_handling.removed_articles.append(article['title'])
        logging.info('Removing article: %s', request.args.get('notif'))
        for article in covid_news_handling.news_articles:
            if article['title'] in covid_news_handling.removed_articles:
                covid_news_handling.news_articles.remove(article)
                covid_news_handling.news_articles_total.remove(article)
        if len(covid_news_handling.news_articles) < 4:
            for article in covid_news_handling.news_articles_total:
                if (article not in covid_news_handling.news_articles) and (article['title'] not in covid_news_handling.removed_articles) and (len(covid_news_handling.news_articles) < 4):
                    covid_news_handling.news_articles.append(article)
            logging.info('RECOVERY_REMOVED_ARTICLES: %s',
                         (str(covid_news_handling.removed_articles).replace("'", '"')))


def update_request():
    '''
take a requested update's name, time and variables
'''
    update_name = request.args.get('two')
    repeat = request.args.get('repeat')
    if repeat is None:
        repeat = False
    else:
        repeat = True
    if update_name is not None:
        update_time = request.args['update']
        logging.info('Update name is %s', update_name)
        current_time = covid_data_handler.hhmm_to_seconds(
            time.strftime('%H:%M', time.localtime()))
        logging.info(
            'Current time in seconds from midnight is: %s ', str(current_time))
        logging.info('Update requested for %s', request.args['update'])
        if covid_data_handler.hhmm_to_seconds(update_time) < current_time:
            update_interval = 86400 + \
                covid_data_handler.hhmm_to_seconds(update_time) - current_time
            logging.info('Will happen tomorrow at, %s' , str(update_time))
        else:
            update_interval = (covid_data_handler.hhmm_to_seconds(
                update_time) - current_time)
            logging.info('Will occur in %s' , str(update_interval))
    update_covid = request.args.get('covid-data')
    if update_covid is not None:
        schedule_covid_updates(update_interval, update_name, repeat)
    else:
        update_covid = 'None'
    update_news = request.args.get('news')
    if update_news is not None:
        schedule_news_updates(update_interval, update_name, repeat)
    else:
        update_news = 'None'
    if update_name is not None:
        covid_data_handler.updates.append({'title': update_name, 'content': str(
            update_time)+'\n Updating the following:   ' + str(update_covid)
            + ' ' + str(update_news) + '\nRepeating:    ' + str(repeat),
            'update_time': update_time, 'update_covid': update_covid,
            'update_news': update_news, 'repeat': str(repeat)})
        logging.info('RECOVERY_UPDATES: %s',
                     (json.dumps(covid_data_handler.updates).replace("'", '"')))


@app.route('/')
def get_index():
    '''
    redirect to index url
    '''
    return redirect('/index')


@app.route('/index')
def index():
    '''
    script that runs every time the page is loaded (at least once per minute)
    '''
    covid_data_handler.s.run(blocking=False)
    covid_news_handling.s.run(blocking=False)
    update_request()
    # ensure the number of articles displayed never goes below 4
    while len(covid_news_handling.news_articles) < 4:
        for article in covid_news_handling.news_articles_total:
            if article['title'] not in covid_news_handling.news_articles:
                if article not in covid_news_handling.removed_articles:
                    covid_news_handling.news_articles.append(article)

    # remove updates if the 'x' has been clicked on them

    cancel_update_request()
    remove_article_request()
    return render_template("index.html", image='covid_logo.jpg',
                           favicon='/static/favicon.ico', title=covid_data_handler.title,
                           news_articles=covid_news_handling.news_articles,
                           updates=covid_data_handler.updates,
                           local_7day_infections=covid_data_handler.local_7day_infections,
                           national_7day_infections=covid_data_handler.national_7day_infections,
                           hospital_cases=(
                               'Current hospital cases:  '+str(covid_data_handler.hospital_cases)),
                           deaths_total=('Total deaths: '+
                                        str(covid_data_handler.deaths_total)),
                           location=covid_data_handler.location, nation_location='United Kingdom')


if __name__ == '__main__':
    app.run()
