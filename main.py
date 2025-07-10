import json
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import requests
import re

# CONFIG
TWITTER_USERNAME = "insert username here"
KEYWORD = "insert keyword here"
DISCORD_WEBHOOK_URL = "insert webhook here"

# THE ACTUAL SCRIPT
def send_to_discord(tweet_text, tweet_url, tweet_time):
    data = {
        "content": f"**{TWITTER_USERNAME}** sent a tweet with the matching keywords: \"{tweet_text}\"\n{tweet_url}\nsent at：{tweet_time} UTC"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def get_recent_matching_tweets():
    matching_tweets = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(user_data_dir="./user-data", headless=False, slow_mo=100,
                                                       user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")

        page = browser.new_page()

        # wait until the access page is gone (probably useless)
        page.goto(f"https://x.com/{TWITTER_USERNAME}", timeout=60000)
        max_wait_time = 30  # seconds
        waited = 0
        while "x.com/account/access" in page.url and waited < max_wait_time:
            print("wait for access page to clear")
            page.wait_for_timeout(1000)
            waited += 1

        if "x.com/account/access" in page.url:
            print("stuck, try to log in on an another browser, clear the issues and try again.")
            browser.close()
            return []

        if "login" in page.url:
            page.screenshot(path="debug_login_required.png")
            raise Exception("cookies are missing or session expired. screenshot saved to debug_login_required.png")

        # Wait longer and for multiple possible selectors
        try:
            page.wait_for_selector("article, div[role='article']", timeout=20000)
        except:
            page.screenshot(path="debug_no_articles.png")
            raise Exception("failed to find any articles on page. screenshot saved to debug_no_articles.png")

        # MODIFY THIS IF YOU WANT TO SCAN FOR MORE POSTS
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
                    continue  # older than 12 hours

                if re.search(rf'\b{re.escape(KEYWORD)}\b', tweet_text, re.IGNORECASE):
                    tweet_url = timestamp_element.locator("..").get_attribute("href")
                    full_url = f"https://x.com{tweet_url}"
                    matching_tweets.append((tweet_text.strip(), full_url, tweet_time.strftime('%Y-%m-%d %H:%M:%S')))
            except:
                continue

        browser.close()
    return matching_tweets

if __name__ == "__main__":
    tweets = get_recent_matching_tweets()
    if tweets:
        for text, url, time_sent in tweets:
            send_to_discord(text, url, time_sent)
    else:
        print("no matching tweets found")