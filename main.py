import json
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import requests
import re
import time
import argparse
import os

# config
TWITTER_USERNAME = "insert username here"
KEYWORD = "insert keyword here"
DISCORD_WEBHOOK_URL = "insert webhook here"

def send_to_discord(tweet_text, tweet_url, tweet_time):
    data = {
        "content": f"**{TWITTER_USERNAME}** sent a tweet with the matching keywords: \"{tweet_text}\"\n{tweet_url}\nsent at: {tweet_time} UTC"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def get_recent_matching_tweets():
    matching_tweets = []
    user_data_dir = os.path.abspath("./user-data")

    with sync_playwright() as p:
        # try with existing content
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )

        page = browser.new_page()

        # attempt to load cookies if they exist
        if os.path.exists("cookies.json"):
            with open("cookies.json", "r") as f:
                cookies = json.load(f)
                page.context.add_cookies(cookies)

        page.goto(f"https://x.com/{TWITTER_USERNAME}", timeout=60000)
        
        # check if logged in.
        if "login" in page.url:
            page.screenshot(path="debug_login_required.png")
            browser.close()
            raise Exception("Login required. Screenshot saved to debug_login_required.png")

        max_wait_time = 30
        waited = 0
        while "x.com/account/access" in page.url and waited < max_wait_time:
            print("wait for access page to clear")
            page.wait_for_timeout(1000)
            waited += 1

        if "x.com/account/access" in page.url:
            print("stuck, try to log in on an another browser, clear the issues and try again.")
            browser.close()
            return []

        try:
            page.wait_for_selector("article, div[role='article']", timeout=20000)
        except:
            page.screenshot(path="debug_no_articles.png")
            browser.close()
            raise Exception("failed to find any articles on page. screenshot saved to debug_no_articles.png")

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
                    full_url = f"https://x.com{tweet_url}"
                    matching_tweets.append((tweet_text.strip(), full_url, tweet_time.strftime('%Y-%m-%d %H:%M:%S')))
            except:
                continue

        browser.close()
    return matching_tweets

def needs_login():
    cookies_path = os.path.join("cookies.json")
    return not os.path.exists(cookies_path)

if __name__ == "__main__":
    if needs_login():
        print("login required. opening browser...")
        print("log in to x.com in the opened browser. close the browser window when done.")
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir="./user-data",
                headless=False,
                viewport={"width": 1280, "height": 800}
            )
            page = browser.new_page()
            page.goto("https://x.com/login")
            print("please log in to x.com in the browser window.")
            print("do not close this terminal. close the browser window after you're fully logged in.")
            
            # wait for successful login (check for home page)
            try:
                page.wait_for_url("https://x.com/home", timeout=120000)
            except:
                print("timed out waiting for login to complete")
            
            # Save cookies after successful login
            cookies = page.context.cookies()
            with open("cookies.json", "w") as f:
                json.dump(cookies, f)
            
            browser.close()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=300, help="interval between checks in seconds (default: 300)")
    args = parser.parse_args()

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