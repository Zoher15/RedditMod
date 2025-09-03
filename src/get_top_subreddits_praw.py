#!/usr/bin/env python3
"""
Get top subreddits using Reddit API (PRAW) with fallback to web scraping.
More reliable than pure web scraping but may not get exact subscriber rankings.
"""

import os
import sys
import json
import time
import praw
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from config import PRAW_CLIENT_ID, PRAW_CLIENT_SECRET, PRAW_USERNAME, PRAW_PW

def get_subreddits_via_praw(reddit, limit=500):
    """Get popular subreddits via Reddit API"""
    subreddits = []
    
    try:
        print("Fetching popular subreddits via Reddit API...")
        popular = list(reddit.subreddits.popular(limit=limit))
        
        for subreddit in tqdm(popular, desc="Getting subscriber counts"):
            try:
                subreddits.append({
                    'name': subreddit.display_name,
                    'subscribers': subreddit.subscribers,
                    'created_utc': subreddit.created_utc,
                    'public_description': subreddit.public_description[:200] if subreddit.public_description else "",
                    'over18': subreddit.over18
                })
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Error getting data for r/{subreddit.display_name}: {e}")
                continue
                
    except Exception as e:
        print(f"Error fetching popular subreddits: {e}")
        return []
    
    # Sort by subscriber count
    subreddits.sort(key=lambda x: x['subscribers'], reverse=True)
    return subreddits

def get_subreddits_via_scraping(max_rank=500):
    """Fallback: Get subreddits via web scraping (original method)"""
    print("Fetching subreddits via web scraping (fallback)...")
    
    base_url = "https://frontpagemetrics.com/top/offset/"
    data = {}
    
    try:
        for page_rank in tqdm(range(0, max_rank, 100), desc="Scraping pages"):
            url = base_url + str(page_rank)
            html_content = requests.get(url, headers={'User-Agent': 'Reddit Research Tool'}).text
            soup = BeautifulSoup(html_content, features="html.parser")

            table = soup.find("table", attrs={"class": "table-bordered"})
            if not table:
                print(f"No table found on page {page_rank}")
                continue
                
            rows = table.find_all("tr")[1:]  # exclude the heading
            
            if len(rows) != 100 and page_rank + 100 < max_rank:
                print(f"Warning: Only {len(rows)} rows found on page {page_rank}")

            if max_rank < 100:
                rows = rows[:max_rank]

            for row in rows:
                try:
                    row_data = row.find_all("td")
                    if len(row_data) < 3:
                        continue
                        
                    rank, name, subscribers = row_data[:3]
                    rank = int(rank.text.strip().replace(",", ""))
                    name = name.text.strip().replace("/r/", "")
                    subscribers = int(subscribers.text.strip().replace(",", ""))
                    
                    data[name] = {'rank': rank, 'subscribers': subscribers}
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
            
            time.sleep(0.5)  # Be nice to the server
            
    except Exception as e:
        print(f"Error in web scraping: {e}")
    
    return data

def combine_data_sources(praw_data, scraping_data):
    """Combine PRAW and scraping data for best results"""
    combined = {}
    
    # Start with PRAW data (more reliable)
    for i, subreddit in enumerate(praw_data):
        combined[subreddit['name']] = {
            'rank': i + 1,  # Assign rank based on subscriber sort
            'subscribers': subreddit['subscribers'],
            'source': 'praw',
            'extra_info': {
                'created_utc': subreddit['created_utc'],
                'description': subreddit['public_description'],
                'over18': subreddit['over18']
            }
        }
    
    # Fill gaps with scraping data
    for name, data in scraping_data.items():
        if name not in combined:
            combined[name] = {
                'rank': data['rank'],
                'subscribers': data['subscribers'], 
                'source': 'scraping'
            }
    
    return combined

def main():
    if len(sys.argv) < 2:
        print("Usage: python get_top_subreddits_praw.py {max_rank} [--praw-only|--scraping-only]")
        return 1
    
    max_rank = int(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else 'hybrid'
    
    path_save = "data/subreddits/"
    if not os.path.isdir(path_save):
        os.makedirs(path_save)
    
    praw_data = []
    scraping_data = {}
    
    # Try PRAW first (unless scraping-only mode)
    if mode != '--scraping-only':
        if PRAW_CLIENT_ID and PRAW_CLIENT_SECRET:
            try:
                reddit = praw.Reddit(
                    client_id=PRAW_CLIENT_ID,
                    client_secret=PRAW_CLIENT_SECRET,
                    user_agent='Subreddit Research Tool',
                    username=PRAW_USERNAME,
                    password=PRAW_PW
                )
                praw_data = get_subreddits_via_praw(reddit, max_rank)
            except Exception as e:
                print(f"PRAW failed: {e}")
        else:
            print("Reddit API credentials not found in config.py")
    
    # Try web scraping (unless praw-only mode)
    if mode != '--praw-only' and (not praw_data or len(praw_data) < max_rank // 2):
        print("Using web scraping to supplement/replace PRAW data...")
        scraping_data = get_subreddits_via_scraping(max_rank)
    
    # Combine the data
    if praw_data and scraping_data:
        print("Combining PRAW and scraping data...")
        final_data = combine_data_sources(praw_data, scraping_data)
    elif praw_data:
        print("Using PRAW data only...")
        final_data = {sub['name']: {'rank': i+1, 'subscribers': sub['subscribers'], 'source': 'praw'} 
                     for i, sub in enumerate(praw_data)}
    elif scraping_data:
        print("Using scraping data only...")
        final_data = scraping_data
    else:
        print("No data collected!")
        return 1
    
    # Save results
    path_out = os.path.join(path_save, f"top{max_rank}_enhanced.json")
    with open(path_out, "w") as file:
        json.dump(final_data, file, indent=2)
    
    print(f"\n✅ Collected {len(final_data)} subreddits")
    print(f"📁 Saved to: {path_out}")
    
    # Show top 10
    sorted_subs = sorted(final_data.items(), key=lambda x: x[1].get('rank', float('inf')))
    print(f"\n🏆 Top 10 subreddits:")
    for i, (name, data) in enumerate(sorted_subs[:10]):
        source = data.get('source', 'unknown')
        subscribers = data.get('subscribers', 'N/A')
        print(f"  {i+1:2d}. r/{name} - {subscribers:,} subscribers ({source})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())