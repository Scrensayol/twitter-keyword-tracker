# twitter keyword tracker

a simple python script that watches a twitter/x user for recent tweets containing a keyword and sends them to a discord webhook.

## features

* scans recent tweets from a user (within the last 12 hours)  
* matches tweets containing a specific keyword  
* sends matching tweets to a discord webhook  
* uses browser cookies for login instead of api keys  
* remembers already sent tweets to prevent duplicate notifications  
* automatically cleans up old tracking data (1 day)  
* works with both tweet urls and content hashing for reliable detection  
* handles login sessions and cookies automatically  

## requirements

* python 3.8+  
* google chrome (or any chromium-based browser)  
* playwright  

## setup

1. install dependencies:

```bash
pip install -r requirements.txt
python -m playwright install
```

2. run the script and log into your x.com account (only needed once):

```bash
python main.py
```

3. update the config in `main.py`:

* `TWITTER_USERNAME` = username to monitor
* `KEYWORD` = word to search for
* `DISCORD_WEBHOOK_URL` = your discord webhook url

## how it works

- first run opens a browser for you to log in (saves cookies to `cookies.json`)  
- subsequent runs use the saved cookies for authentication  
- scans the user's tweets every 5 minutes (configurable)  
- tracks sent tweets in `sent_tweets.json` to prevent duplicates  
- automatically cleans up old entries after 1 day (by default).  

## notes

* your login session is saved to the `user-data` folder  
* sent tweet history is saved to `sent_tweets.json`  
* only public tweets can be scanned    

## troubleshooting

* to reset tracking, delete `sent_tweets.json`  
* to re-login, delete `cookies.json`  
* debug screenshots are saved when errors occur  
* increase the `--interval` value if you get rate limited  

## DISCLAIMER!!!!!

THIS PROJECT IS FOR EDUCATIONAL AND INFORMATIONAL PURPOSES ONLY.  
IT IS NOT INTENDED TO BE USED FOR STALKING, HARASSMENT, OR VIOLATING ANYONE'S PRIVACY.

BY USING THIS PROGRAM, YOU AGREE THAT THE AUTHOR IS NOT RESPONSIBLE FOR ANY MISUSE OR DAMAGE RESULTING FROM ITS USE.

## license

[mit](LICENSE)
