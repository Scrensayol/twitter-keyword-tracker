import json
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import requests
import re
import time
import argparse
import os
import hashlib

# Config
TWITTER_USERNAME = "insert username here"
KEYWORD = "insert keyword here"
DISCORD_WEBHOOK_URL = "insert webhook here"
SENT_TWEETS_FILE = "sent_tweets.json"  # file to store already sent tweet IDs
CLEANUP_DAYS = 1  # cleanup tweets older than this many days

# helper functions for tracking sent tweets
def load_sent_tweets():
# load uhhhh already existing set
    if os.path.exists(SENT_TWEETS_FILE):
        with open(SENT_TWEETS_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_sent_tweets(sent_tweets):
# save stuff
    with open(SENT_TWEETS_FILE, 'w') as f:
        json.dump(list(sent_tweets), f)

def get_tweet_id(url):
#extract the tweet id
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else None

def clean_old_tweets():
#i forgot what this does but whatever
    if os.path.exists(SENT_TWEETS_FILE):
        cutoff = datetime.now() - timedelta(days=CLEANUP_DAYS)
        try:
            with open(SENT_TWEETS_FILE, 'r') as f:
                data = json.load(f)
            
            # if we stored timestamps (optional enhancement)
            if isinstance(data, dict):
                cleaned = {k:v for k,v in data.items() 
                         if datetime.fromtimestamp(v) > cutoff}
                with open(SENT_TWEETS_FILE, 'w') as f:
                    json.dump(cleaned, f)
        except:
            pass

# discord webhook
def send_to_discord(tweet_text, tweet_url, tweet_time):
    data = {
        "content": f"**{TWITTER_USERNAME}** sent a tweet with the matching keywords: \"{tweet_text}\"\n{tweet_url}\nsent at: {tweet_time} UTC"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=data)

# the main thing aka tweet scraping
def get_recent_matching_tweets():
    matching_tweets = []
    sent_tweets = load_sent_tweets()
    user_data_dir = os.path.abspath("./user-data")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )

        page = browser.new_page()

        if os.path.exists("cookies.json"):
            with open("cookies.json", 'r') as f:
                cookies = json.load(f)
                page.context.add_cookies(cookies)

        page.goto(f"https://x.com/{TWITTER_USERNAME}", timeout=60000)
        
        if "login" in page.url:
            page.screenshot(path="debug_login_required.png")
            browser.close()
            raise Exception("login required. screenshot saved to debug_login_required.png")

        max_wait_time = 30
        waited = 0
        while "x.com/account/access" in page.url and waited < max_wait_time:
            print("wait for access page to clear")
            page.wait_for_timeout(1000)
            waited += 1

        if "x.com/account/access" in page.url:
            print("stuck, try to log in on another browser")
            browser.close()
            return []

        try:
            page.wait_for_selector("article, div[role='article']", timeout=20000)
        except:
            page.screenshot(path="debug_no_articles.png")
            browser.close()
            raise Exception("failed to find any articles on page")

        for _ in range(1):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

        articles = page.locator("article")
        count = articles.count()
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=12)

        for i in range(count):
            article = articles.nth(i)
            try:
                tweet_text = article.locator("div[lang]").inner_text()
                timestamp_element = article.locator("time")
                tweet_time_str = timestamp_element.get_attribute("datetime")
                tweet_time = datetime.fromisoformat(tweet_time_str.replace("Z", "+00:00"))

                if tweet_time < cutoff:
                    continue

                if re.search(rf'\b{re.escape(KEYWORD)}\b', tweet_text, re.IGNORECASE):
                    tweet_url = timestamp_element.locator("..").get_attribute("href")
                    full_url = f"https://vxtwitter.com{tweet_url}"
                    tweet_id = get_tweet_id(full_url)
                    
                    if tweet_id and tweet_id not in sent_tweets:
                        matching_tweets.append((tweet_text.strip(), full_url, tweet_time.strftime('%Y-%m-%d %H:%M:%S')))
                        sent_tweets.add(tweet_id)
            except:
                continue

        browser.close()
    
    # save the updated list of sent tweets
    save_sent_tweets(sent_tweets)
    return matching_tweets

# login handling
def needs_login():
    cookies_path = os.path.join("cookies.json")
    return not os.path.exists(cookies_path)

# WHATEVER THIS IS
if __name__ == "__main__":
    if needs_login():
        print("login required. opening browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir="./user-data",
                headless=False,
                viewport={"width": 1280, "height": 800}
            )
            page = browser.new_page()
            page.goto("https://x.com/login")
            print("please log in to x.com in the browser window.")
            print("close the browser window after you're fully logged in.")
            
            try:
                page.wait_for_url("https://x.com/home", timeout=120000)
            except:
                print("timed out waiting for login to complete")
            
            cookies = page.context.cookies()
            with open("cookies.json", 'w') as f:
                json.dump(cookies, f)
            
            browser.close()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=300, help="Interval between checks in seconds (default: 300)")
    args = parser.parse_args()

    # cleanup thing
    clean_old_tweets()

    while True:
        print(f"\nchecking tweets at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            tweets = get_recent_matching_tweets()
            if tweets:
                for text, url, time_sent in tweets:
                    send_to_discord(text, url, time_sent)
            else:
                print("no matching tweets found")
        except Exception as e:
            print(f"error: {e}")

        print(f"waiting {args.interval} seconds\n")
        time.sleep(args.interval)