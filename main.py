import feedparser
import requests
import re
import time
import os
from datetime import datetime, timedelta

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

FEEDS = [
    {"name": "Crypto is Macro Now", "url": "https://www.cryptoismacro.com/feed", "category": "Macro"},
    {"name": "Lyn Alden", "url": "https://www.lynalden.com/feed/", "category": "Macro"},
    {"name": "Bitwise CIO Memo", "url": "https://bitwiseinvestments.substack.com/feed", "category": "Macro"},
    {"name": "Benjamin Cowen", "url": "https://intothecryptoverse.substack.com/feed", "category": "Macro"},
    {"name": "Onramp Bitcoin", "url": "https://onrampbitcoin.com/feed", "category": "Macro"},
    {"name": "TheMinerMag", "url": "https://theminermag.com/feed/", "category": "Mining"},
    {"name": "Hashrate Index", "url": "https://hashrateindex.com/blog/feed/", "category": "Mining"},
    {"name": "CoinShares Blog", "url": "https://blog.coinshares.com/feed", "category": "Flow"},
    {"name": "21Shares Research", "url": "https://www.21shares.com/feed", "category": "Macro"},
    {"name": "Galaxy Research", "url": "https://www.galaxy.com/research/feed/", "category": "Research"},
]

BTC_KEYWORDS = [
    "bitcoin", "btc", "hashrate", "hashprice", "mining", "miner",
    "halving", "macro", "liquidity", "m2", "fed", "interest rate",
    "treasury", "dollar", "dxy", "etf", "fund flow", "inflow",
    "outflow", "cycle", "bull", "bear", "on-chain", "difficulty",
    "block reward", "hash ribbon", "capitulation", "institutional",
    "reserve", "supply", "demand", "correlation", "risk",
    "crypto", "digital asset", "blockchain", "defi", "stablecoin",
]

CHART_SOURCES = {"TheMinerMag", "Hashrate Index", "CoinShares Blog",
                 "21Shares Research", "Galaxy Research"}

def matches_keywords(title, summary):
    text = (title + " " + summary).lower()
    return any(kw in text for kw in BTC_KEYWORDS)

def clean_html(raw_html):
    return re.sub('<[^<]+?>', '', raw_html or '').strip()[:500]

def parse_date(entry):
    for field in ["published_parsed", "updated_parsed"]:
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6]).strftime("%Y-%m-%d")
            except:
                pass
    return datetime.now().strftime("%Y-%m-%d")

def create_notion_page(entry_data):
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": entry_data["title"][:2000]}}]},
            "Source": {"select": {"name": entry_data["source"]}},
            "Category": {"select": {"name": entry_data["category"]}},
            "Date": {"date": {"start": entry_data["date"]}},
            "URL": {"url": entry_data["url"]},
            "Summary": {"rich_text": [{"text": {"content": entry_data["summary"][:2000]}}]},
            "Can Use Charts": {"checkbox": entry_data["can_use_charts"]},
            "Video Idea": {"rich_text": [{"text": {"content": ""}}]},
            "Status": {"select": {"name": "Unread"}},
        }
    }
    resp = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
    return resp.status_code == 200

def check_duplicate(title):
    payload = {"filter": {"property": "Title", "title": {"equals": title[:2000]}}}
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query",
        headers=NOTION_HEADERS, json=payload
    )
    if resp.status_code == 200:
        return len(resp.json().get("results", [])) > 0
    return False

def run():
    cutoff = datetime.now() - timedelta(days=3)
    new_count = 0
    skip_count = 0

    for feed_info in FEEDS:
        print(f"\n📡 {feed_info['name']}...")
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:10]:
                title = entry.get("title", "No Title")
                summary = clean_html(entry.get("summary", ""))
                link = entry.get("link", "")
                pub_date = parse_date(entry)

                try:
                    if datetime.strptime(pub_date, "%Y-%m-%d") < cutoff:
                        continue
                except:
                    pass

                if not matches_keywords(title, summary):
                    skip_count += 1
                    continue

                if check_duplicate(title):
                    skip_count += 1
                    continue

                entry_data = {
                    "title": title,
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                    "date": pub_date,
                    "url": link,
                    "summary": summary,
                    "can_use_charts": feed_info["name"] in CHART_SOURCES,
                }

                if create_notion_page(entry_data):
                    new_count += 1
                    print(f"   ✅ {title[:65]}")
                else:
                    print(f"   ❌ {title[:65]}")
                time.sleep(0.35)
        except Exception as e:
            print(f"   ⚠️ Error: {e}")

    print(f"\n{'='*50}")
    print(f"✅ New articles: {new_count} | ⏭️ Skipped: {skip_count}")
    print(f"{'='*50}")

if __name__ == "__main__":
    run()
