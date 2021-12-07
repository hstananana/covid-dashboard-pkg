# Introduction

This is a Covid-19 dashboard designed to give the user local and national Covid data, news articles, and allow the user to schedule when the data is updated. Whilst it has been designed with Covid news articles in mind, the config.json can be configured to request different keywords

# Installation

Install flask (see here: https://flask.palletsprojects.com/en/2.0.x/installation/). Download and extract the files from this repositry. Get a news api key by signing up for a free news api account here: https://newsapi.org/. Add that to the config.json.

# Usage

Run app.py. This launches an internal server at http://127.0.0.1:5000/. You can schedule updates for the covid data and for the news updates with the timer. Please use a unique name for each update.

# Licence

Licenced under MIT
