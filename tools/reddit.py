from langchain.tools import tool
import requests
import feedparser
import os

@tool
def search_reddit_country(country: str) -> str:
    """
    Search Reddit for discussions about a country.
    Use this to find what people are actually talking about,
    social sentiment, and grassroots opinions.
    Input should be a country name like 'Japan' or 'Brazil'
    """
    try:
        # List of subreddits to check for the country
        subreddits = [
            country.lower().replace(" ", ""),
            f"{country.lower()}news",
            "worldnews",
            "geopolitics",
            "internationalnews"
        ]
        
        all_posts = []
        
        for subreddit in subreddits[:3]:  # Check first 3 subreddits
            try:
                # Use Reddit RSS feed — no API key needed
                url = f"https://www.reddit.com/r/{subreddit}/hot.rss?limit=5"
                headers = {
                    "User-Agent": "WavAgent/1.0 (Country Intelligence Agent)"
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries[:5]:
                        title = entry.get('title', 'No title')
                        summary = entry.get('summary', '')[:300]
                        link = entry.get('link', '')
                        
                        # Filter for country relevance
                        if country.lower() in title.lower() or \
                           country.lower() in summary.lower() or \
                           subreddit == country.lower().replace(" ", ""):
                            all_posts.append(f"""
Post: {title}
Summary: {summary}
Source: r/{subreddit}
URL: {link}
""")
                            
            except Exception as e:
                continue  # Try next subreddit if this one fails
        
        if not all_posts:
            # Fallback to worldnews search
            try:
                url = f"https://www.reddit.com/r/worldnews/search.rss?q={country}&sort=hot&limit=5"
                headers = {"User-Agent": "WavAgent/1.0"}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    for entry in feed.entries[:5]:
                        title = entry.get('title', '')
                        summary = entry.get('summary', '')[:300]
                        link = entry.get('link', '')
                        all_posts.append(f"""
Post: {title}
Summary: {summary}
Source: r/worldnews
URL: {link}
""")
            except:
                return f"Could not fetch Reddit data for {country}. Moving to other sources."
        
        if not all_posts:
            return f"No Reddit discussions found for {country}. Try other sources."
            
        return f"Reddit discussions about {country}:\n\n" + "\n---\n".join(all_posts[:8])
        
    except Exception as e:
        return f"Reddit search failed: {str(e)}. Continuing with other sources."


@tool
def get_reddit_sentiment(country: str) -> str:
    """
    Get overall sentiment from Reddit discussions about a country.
    Use this to understand public opinion and mood.
    Input should be a country name.
    """
    try:
        url = f"https://www.reddit.com/r/worldnews/search.rss?q={country}&sort=new&limit=10"
        headers = {"User-Agent": "WavAgent/1.0"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"Could not fetch sentiment data for {country}"
        
        feed = feedparser.parse(response.content)
        
        titles = []
        for entry in feed.entries[:10]:
            title = entry.get('title', '')
            if title:
                titles.append(title)
        
        if not titles:
            return f"No sentiment data available for {country}"
        
        titles_text = "\n".join(titles)
        
        return f"""
Recent Reddit headlines about {country}:
{titles_text}

Use these headlines to gauge public sentiment and trending topics.
"""
        
    except Exception as e:
        return f"Sentiment fetch failed: {str(e)}"