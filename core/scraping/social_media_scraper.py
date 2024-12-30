import json
import snscrape.modules.twitter as sntwitter
import snscrape.modules.reddit as snreddit
import yaml
import os
import logging
import requests
import urllib3
from datetime import datetime
from typing import List, Dict, Any
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
try:
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='logs/scraping.log'
    )
    logger = logging.getLogger(__name__)
    logger.info("Social media scraper initialized")
except Exception as e:
    print(f"Failed to initialize logger: {str(e)}")
    raise

class SocialMediaScraper:
    def __init__(self, config_path: str = 'core/scraping/config.yaml'):
        """Initialize scraper with configuration"""
        self.config = self._load_config(config_path)
        self.output_dir = 'core/data/raw/social_media'
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load scraping configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _create_scraper_session(self):
        """Create a session with retry logic and SSL verification handling"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Configure SSL verification based on config
        verify_ssl = self.config.get('settings', {}).get('verify_ssl', True)
        session.verify = verify_ssl
        
        # Add proxies if configured
        if 'proxies' in self.config.get('settings', {}):
            session.proxies = self.config['settings']['proxies']
            
        return session

    def scrape_twitter(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape tweets based on search query"""
        try:
            # Create custom session
            session = self._create_scraper_session()
            
            # Configure Twitter scraper
            scraper = sntwitter.TwitterSearchScraper(query)
            scraper._session = session
            
            tweets = []
            for i, tweet in enumerate(scraper.get_items()):
                if i >= limit:
                    break
                tweets.append({
                    'date': tweet.date.isoformat(),
                    'content': tweet.content,
                    'username': tweet.user.username,
                    'retweets': tweet.retweetCount,
                    'likes': tweet.likeCount,
                    'url': tweet.url
                })
            return tweets
        except Exception as e:
            logger.error(f"Twitter scraping failed: {e}")
            return []

    def scrape_reddit(self, subreddit: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape posts from a subreddit"""
        try:
            posts = []
            for i, post in enumerate(snreddit.RedditSubredditScraper(subreddit).get_items()):
                if i >= limit:
                    break
                posts.append({
                    'date': post.date.isoformat(),
                    'title': post.title,
                    'content': post.selftext,
                    'author': post.author,
                    'upvotes': post.score,
                    'url': post.url
                })
            return posts
        except Exception as e:
            logger.error(f"Reddit scraping failed: {e}")
            return []

    def save_results(self, data: List[Dict[str, Any]], platform: str) -> str:
        """Save scraped data to JSON file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{platform}_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(data)} items to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise

    def run(self):
        """Main execution method"""
        try:
            logger.info("Starting social media scraping")
            
            # Twitter scraping
            if 'social_media' in self.config and 'twitter' in self.config['social_media']:
                twitter_config = self.config['social_media']['twitter']
                for query in twitter_config.get('search_terms', []):
                    logger.info(f"Scraping Twitter for query: {query}")
                    tweets = self.scrape_twitter(
                        query, 
                        twitter_config.get('max_tweets_per_term', 100)
                    )
                    if tweets:
                        self.save_results(tweets, 'twitter')
                        logger.info(f"Saved {len(tweets)} tweets for query: {query}")

            # Reddit scraping
            if 'social_media' in self.config and 'reddit' in self.config['social_media']:
                reddit_config = self.config['social_media']['reddit']
                for subreddit in reddit_config.get('subreddits', []):
                    logger.info(f"Scraping Reddit subreddit: {subreddit}")
                    posts = self.scrape_reddit(
                        subreddit,
                        reddit_config.get('post_limit', 100)
                    )
                    if posts:
                        self.save_results(posts, 'reddit')
                        logger.info(f"Saved {len(posts)} posts from subreddit: {subreddit}")

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise

if __name__ == "__main__":
    scraper = SocialMediaScraper()
    scraper.run()
