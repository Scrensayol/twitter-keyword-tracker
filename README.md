# twitter keyword tracker

a simple python script that watches a twitter/x user for recent tweets containing a keyword and sends them to a discord webhook.

## features

* scans recent tweets from a user (within the last 12 hours)
* matches tweets containing a specific keyword
* sends matching tweets to a discord webhook
* uses browser cookies for login instead of api keys.

## requirements

* python 3.8+
* google chrome (or any kind of chromium fork) installed
* playwright

## setup

1. install dependencies:

```terminal
pip install -r requirements.txt
python -m playwright install
```

2. run the script and log into your x.com account (only needed once):

```terminal
python main.py
```

3. update the config in `main.py`:

* `TWITTER_USERNAME` = username to monitor
* `KEYWORD` = word to search for
* `DISCORD_WEBHOOK_URL` = your discord webhook url

## notes

* your login session is saved to the `user-data` folder.
* only public tweets can be scanned.
* run periodically using task scheduler or cron if needed.

## disclaimer

this project is for educational and informational purposes only.  
it is not intended to be used for stalking, harassment, or violating anyone's privacy.

by using this program, you agree that the author is not responsible for any misuse or damage resulting from its use.

## license

[mit](LICENSE)
