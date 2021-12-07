'''
Module for news-related functions
'''

import json
import sched
import time
import logging
import flask
import requests
import covid_data_handler

logging.basicConfig(filename='logfile.log', level=logging.DEBUG)

# get key for newsapi and news article terms from config file
config_json = open('config.json', 'r').read()
config = json.loads(config_json)
api_key = config['API_KEY']
news_article_terms = config['News_article_terms']

s = sched.scheduler(time.time, time.sleep)

# request news articles from newsapi


def news_API_request(covid_terms='Covid COVID-19 coronavirus'):
    '''
    Get news articles from the news api
    '''
    list_terms = covid_terms.split(' ')
    url = ('https://newsapi.org/v2/everything?'
           'q='+" OR ".join(list_terms)+'&'
           'apiKey='+api_key)
    try:
        api = requests.get(url)
        json_file = api.json()
    except:
        logging.error(
            'Failed to get news articles. Please check you are connected to the internet and the API key is valid')
        raise ConnectionError
    articles = json_file['articles']
    for article in articles:
        article['content'] = flask.Markup(
            '<a href=' + article['url'] + '>' + article['content'] + '</a>')
    logging.info('News API request made')

    return articles


news_articles_total = []
news_articles_total = news_API_request(news_article_terms)


# load states from log file

for line in reversed(open("logfile.log").readlines()):
    if line.find('INFO:root:RECOVERY_REMOVED_ARTICLES') != -1:
        info_from_line = line.replace(
            'INFO:root:RECOVERY_REMOVED_ARTICLES:', '')
        try:
            removed_articles = json.loads(info_from_line)
            for removed in removed_articles:
                for possible_article in news_articles_total:
                    if possible_article['title'] == removed:
                        news_articles_total.remove(possible_article)
            break
        except:
            logging.info('Failed to get previously removed articles')
            break

# set initial articles

news_articles = []
for number in range(4):
    news_articles.append(news_articles_total[number])
removed_articles = []


def remove_seen_articles():
    '''
    prevent the user seeing the same articles after the update
    '''
    for article in news_articles:
        removed_articles.append(article['title'])
        logging.info('RECOVERY_REMOVED_ARTICLES: %s',
                     (str(removed_articles).replace("'", '"')))
    news_articles.clear()


def update_news(name='news_update'):
    '''
    update news articles
    '''
    logging.info('Running news update with name %s', name)
    news_articles_total = list(news_API_request(news_article_terms))
    for removed in removed_articles:
        for possible_article in news_articles_total:
            if possible_article['title'] == removed:
                news_articles_total.remove(possible_article)
    for number in range(4):
        news_articles.append(news_articles_total[number])


def repeat_if_applicable(name, update_repeat):
    '''
    if repeat is true, schedule the update again for the same time tomorrow.
    if not, remove it from the list
    '''
    if update_repeat == True:
        covid_data_handler.schedule_covid_updates(86400, name, update_repeat)
    else:
        for update in covid_data_handler.updates:
            if update['title'] == name:
                # remove the update from the list of updates
                covid_data_handler.updates.remove(update)



def schedule_news_updates(interval, name, update_repeat=False):
    '''
    Schedule news updates for a given interval
    '''
    logging.info('Schedule for '+name+' successful')
    e1 = s.enter(interval, 1, remove_seen_articles)
    e2 = s.enter(interval, 2, update_news, argument=name)
    e3 = s.enter(interval, 3, repeat_if_applicable,
                argument=(name, update_repeat))

    if covid_data_handler.cancelled.get(name) == True:
        s.cancel(e1)
        s.cancel(e2)
        s.cancel(e3)

    s.run(blocking=False)

# recover updates from the log file


for line in reversed(open("logfile.log").readlines()):
    if line.find('INFO:root:RECOVERY_UPDATES:') != -1:
        info_from_line = line.replace('INFO:root:RECOVERY_UPDATES:', '')
        try:
            json_updates = json.loads(info_from_line)
            for line in json_updates:
                if line not in covid_data_handler.updates:
                    covid_data_handler.updates.append(line)
            logging.info('Successfully loaded news updates from logfile')
            for update in covid_data_handler.updates:
                update_name = update['title']
                update_time = update['update_time']
                if update['repeat'] == 'True':
                    repeat = True
                else:
                    repeat = False
                logging.info('Update name is %s', update_name)
                current_time = covid_data_handler.hhmm_to_seconds(
                    time.strftime('%H:%M', time.localtime()))
                if covid_data_handler.hhmm_to_seconds(update_time) < current_time:
                    update_interval = (
                        86400+covid_data_handler.hhmm_to_seconds(update_time) - current_time)
                    logging.info('Will happen tomorrow at %s', str(update_time))
                else:
                    update_interval = (covid_data_handler.hhmm_to_seconds(
                        update_time) - current_time)
                    logging.info('Seconds before update: %s', update_interval)
                if update['update_news'] != 'None':
                    schedule_news_updates(update_interval, update_name, repeat)
        except:
            logging.info('Failed to load news updates from logfile')
            break
