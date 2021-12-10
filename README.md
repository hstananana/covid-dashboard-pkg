# Introduction

This is a Covid-19 dashboard designed to give the user local and national Covid data, news articles, and allow the user to schedule when the data is updated. Whilst it has been designed with Covid news articles in mind, the config.json can be configured to request different keywords

# Installation

Install flask (see here: https://flask.palletsprojects.com/en/2.0.x/installation/). Download and extract the files from the GitHub repository (https://github.com/hstananana/covid-dashboard-pkg). Get a news api key by signing up for a free news api account here: https://newsapi.org/. Add that to the config.json using double quote marks (").

# Getting Started

Run app.py. This launches an internal server at http://127.0.0.1:5000/. You can schedule updates for the covid data and for the news updates with the timer. Please use a unique name for each update.

# Testing

This project has testing modules that can be run with pytest. The installation instructions can be found here: https://docs.pytest.org/en/6.2.x/getting-started.html. To test the code, run pytest in the program's directory

# Licence

Licenced under MIT