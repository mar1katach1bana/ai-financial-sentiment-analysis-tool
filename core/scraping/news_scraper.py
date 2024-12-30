import os
import json
import random
import time
from datetime import datetime
from pygooglenews import GoogleNews
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
try:
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='logs/scraping.log'
    )
    logger = logging.getLogger(__name__)
    logger.info("Logger initialized successfully")
except Exception as e:
    print(f"Failed to initialize logger: {str(e)}")
    raise

def load_proxies(proxy_file='config/proxies.txt'):
    """Load proxies from file"""
    try:
        with open(proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        logger.debug(f"Loaded {len(proxies)} proxies")
        return proxies
    except Exception as e:
        logger.error(f"Error loading proxies: {str(e)}")
        return []

def get_random_proxy(proxies):
    """Get a random proxy from the list"""
    if proxies:
        proxy = random.choice(proxies)
        logger.debug(f"Using proxy: {proxy}")
        return {'https': f'http://{proxy}'}
    logger.warning("No proxies available")
    return None

def create_session_with_retries():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session

def connect_to_mongodb(uri='mongodb://localhost:27017/', db_name='financial_news'):
    """Connect to MongoDB"""
    try:
        client = MongoClient(uri)
        client.admin.command('ping')  # Test connection
        db = client[db_name]
        logger.info("Successfully connected to MongoDB")
        return db
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return None

def save_to_mongodb(data, collection_name='news_articles'):
    """Save data to MongoDB"""
    db = connect_to_mongodb()
    if db is not None:
        try:
            collection = db[collection_name]
            result = collection.insert_one(data)
            logger.info(f"Inserted document with id: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {str(e)}")
    return False

def save_to_file(data, base_dir='data/raw/news'):
    """Save data to file as fallback"""
    try:
        ensure_directory_exists(base_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{base_dir}/news_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Successfully saved news data to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving to file: {str(e)}")
        return None

def ensure_directory_exists(directory):
    """Ensure the specified directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def extract_focused_news(proxies=None, max_retries=3, use_proxies=True):
    """Extract focused news articles from Google News with retry logic"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.info(f"Starting news extraction (attempt {retry_count + 1})")
            gn = GoogleNews()
            logger.debug("GoogleNews instance created")
            
            # Create session
            session = create_session_with_retries()
            if use_proxies and proxies:
                session.proxies = proxies
                
            # Set session for GoogleNews
            gn.session = session
            
            top = gn.topic_headlines('business')
            logger.debug(f"Retrieved {len(top['entries'])} news entries")
            
            focused_data = {
                "scraped_at": datetime.now().isoformat(),
                "updated": top["feed"].get("updated", ""),
                "entries": []
            }
            
            for entry in top["entries"]:
                article = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": {
                        "title": entry.get("source", {}).get("title", ""),
                        "href": entry.get("source", {}).get("href", "")
                    },
                    "sub_articles": []
                }
                
                if "sub_articles" in entry:
                    for sub in entry["sub_articles"]:
                        sub_article = {
                            "title": sub.get("title", ""),
                            "url": sub.get("url", ""),
                            "publisher": sub.get("publisher", "")
                        }
                        article["sub_articles"].append(sub_article)
                
                focused_data["entries"].append(article)
            
            logger.info("News extraction completed successfully")
            return focused_data
            
        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out (attempt {retry_count + 1})")
            retry_count += 1
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            logger.error(f"Error extracting news: {str(e)}")
            retry_count += 1
            time.sleep(5)  # Wait before retrying
    
    raise Exception(f"Failed to extract news after {max_retries} attempts")

if __name__ == "__main__":
    try:
        logger.info("Starting news scraper")
        
        # Load proxies
        proxies = load_proxies()
        current_proxy = get_random_proxy(proxies)
        
        # Extract news data - set use_proxies=False to test without proxies
        news_data = extract_focused_news(proxies=current_proxy, use_proxies=False)
        
        # Try saving to MongoDB first
        if not save_to_mongodb(news_data):
            # Fallback to file storage
            saved_file = save_to_file(news_data)
            logger.info(f"News data saved to file: {saved_file}")
            print(f"News data saved to file: {saved_file}")
        else:
            logger.info("News data successfully saved to MongoDB")
            print("News data successfully saved to MongoDB")
            
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        print(f"Error: {str(e)}")
