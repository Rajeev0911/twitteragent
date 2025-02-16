# import os
# import tweepy
# import requests
# from datetime import datetime, timedelta, timezone
# import schedule
# import time
# import logging
# import random
# from dotenv import load_dotenv
# from ratelimit import limits, sleep_and_retry

# def setup_logging():
#     """Configure logging with both file and console handlers"""
#     logging.basicConfig(
#         filename='bot.log',
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s'
#     )
#     console = logging.StreamHandler()
#     console.setLevel(logging.INFO)
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     console.setFormatter(formatter)
#     logging.getLogger('').addHandler(console)

# class Config:
#     """Configuration class to manage all settings"""
#     def __init__(self):
#         load_dotenv()
        
#         # API Keys
#         self.TWITTER_API_KEY = os.getenv("TW_API_KEY")
#         self.TWITTER_API_SECRET = os.getenv("TW_API_KEY_SECRET")
#         self.TWITTER_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
#         self.TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TW_ACCESS_TOKEN_SECRET")
#         self.TWITTER_BEARER_TOKEN = os.getenv("TW_BEARER_TOKEN")
#         self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")
#         self.HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
        
#         # API Rate Limits
#         self.HUGGINGFACE_CALLS_PER_DAY = int(os.getenv("HUGGINGFACE_CALLS_PER_DAY", "24"))
#         self.TWITTER_POSTS_PER_DAY = int(os.getenv("TWITTER_POSTS_PER_DAY", "2"))
#         self.TWITTER_READS_PER_DAY = int(os.getenv("TWITTER_READS_PER_DAY", "2"))
#         self.MAX_MENTIONS_PER_CHECK = 5  # Minimum value allowed by Twitter API

#         # API Endpoints
#         self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
#         self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# class ContentGenerator:
#     """Class to handle content generation and validation"""
#     TWEET_PROMPTS = [
#         "Write a tech news tweet about: {news}. Include key facts only.",
#         "Summarize this tech news in one tweet: {news}. Be clear and factual.",
#         "Share this tech update concisely: {news}. Focus on the main point."
#     ]

#     REPLY_PROMPTS = [
#         "Write a helpful reply to: {tweet}. Be brief and relevant.",
#         "Respond professionally to: {tweet}. Keep it short and helpful.",
#         "Answer this query: {tweet}. Be concise and informative."
#     ]

#     @staticmethod
#     def get_random_prompt(prompt_list):
#         return random.choice(prompt_list)

#     @staticmethod
#     def validate_content(text):
#         """Validate generated content"""
#         if not text or len(text.strip()) < 10:
#             return False
#         if text.count('@') > 2:  # Avoid spam-like content
#             return False
#         if len(text.split()) < 3:  # Ensure minimum meaningful content
#             return False
#         return True

#     @staticmethod
#     def clean_content(text):
#         """Clean and format content"""
#         # Remove excessive whitespace
#         text = ' '.join(text.split())
#         # Remove quotes that might come from the model
#         text = text.strip('""\'\'')
#         # Remove repetitive characters
#         text = ''.join(char for i, char in enumerate(text) 
#                       if i == 0 or char != text[i-1] or not char.isspace())
#         return text

# class APIHandler:
#     """Class to handle all API calls"""
#     def __init__(self, config):
#         self.config = config

#     @sleep_and_retry
#     @limits(calls=1, period=3600)
#     def huggingface_call(self, prompt, max_length=50):
#         headers = {"Authorization": f"Bearer {self.config.HUGGINGFACE_API_KEY}"}
#         payload = {
#             "inputs": prompt,
#             "parameters": {
#                 "max_length": max_length,
#                 "temperature": 0.7,
#                 "top_p": 0.95,
#                 "do_sample": True
#             }
#         }
        
#         try:
#             response = requests.post(
#                 self.config.HUGGINGFACE_API_URL,
#                 headers=headers,
#                 json=payload,
#                 timeout=10
#             )
#             response.raise_for_status()
#             time.sleep(1)
#             return response.json()[0].get("generated_text", "")
#         except Exception as e:
#             logging.error(f"Hugging Face API error: {str(e)}")
#             return ""

#     @sleep_and_retry
#     @limits(calls=1, period=3600)
#     def news_api_call(self):
#         params = {
#             "category": "technology",
#             "language": "en",
#             "apiKey": self.config.NEWS_API_KEY,
#             "pageSize": 5  # Get multiple articles to choose from
#         }
        
#         try:
#             response = requests.get(
#                 self.config.NEWS_API_URL, 
#                 params=params,
#                 timeout=10
#             )
#             response.raise_for_status()
#             data = response.json()
#             if data.get("articles"):
#                 # Choose a random article from the results
#                 article = random.choice(data["articles"][:5])
#                 title = article.get('title', '')
#                 # Clean the title by removing source names often added at the end
#                 title = title.split(' - ')[0].split(' | ')[0].strip()
#                 return title
#             return ""
#         except Exception as e:
#             logging.error(f"News API error: {str(e)}")
#             return ""

# class TwitterBot:
#     def __init__(self, config):
#         self.config = config
#         self.api_handler = APIHandler(config)
#         self.content_generator = ContentGenerator()
#         self.setup_twitter_clients()
        
#         self.daily_tweet_count = 0
#         self.daily_mention_check_count = 0
#         self.daily_huggingface_calls = 0
#         self.last_reset = datetime.now(timezone.utc)

#     def setup_twitter_clients(self):
#         """Initialize Twitter API clients"""
#         try:
#             self.client = tweepy.Client(
#                 bearer_token=self.config.TWITTER_BEARER_TOKEN,
#                 consumer_key=self.config.TWITTER_API_KEY,
#                 consumer_secret=self.config.TWITTER_API_SECRET,
#                 access_token=self.config.TWITTER_ACCESS_TOKEN,
#                 access_token_secret=self.config.TWITTER_ACCESS_TOKEN_SECRET,
#                 wait_on_rate_limit=True
#             )
#             self.twitter_me_id = self.client.get_me()[0].id
#             logging.info("Twitter API clients initialized successfully")
#         except Exception as e:
#             logging.error(f"Failed to initialize Twitter API: {str(e)}")
#             raise

#     def reset_counters(self):
#         """Reset daily counters if it's a new day"""
#         current_time = datetime.now(timezone.utc)
#         if (current_time - self.last_reset).days >= 1:
#             self.daily_tweet_count = 0
#             self.daily_mention_check_count = 0
#             self.daily_huggingface_calls = 0
#             self.last_reset = current_time
#             logging.info("Daily counters reset")

#     def can_make_huggingface_call(self):
#         """Check if we can make another Hugging Face API call"""
#         return self.daily_huggingface_calls < self.config.HUGGINGFACE_CALLS_PER_DAY

#     def post_tweet(self):
#         """Post a tweet with content validation"""
#         self.reset_counters()
        
#         if self.daily_tweet_count >= self.config.TWITTER_POSTS_PER_DAY:
#             logging.info("Daily tweet limit reached")
#             return

#         if not self.can_make_huggingface_call():
#             logging.info("Daily Hugging Face API limit reached")
#             return

#         try:
#             news = self.api_handler.news_api_call()
#             if news:
#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.TWEET_PROMPTS
#                 ).format(news=news)
#                 tweet_text = self.api_handler.huggingface_call(prompt, max_length=100)
                
#                 tweet_text = self.content_generator.clean_content(tweet_text)
                
#                 if self.content_generator.validate_content(tweet_text):
#                     tweet_text = tweet_text[:280]
#                     self.client.create_tweet(text=tweet_text)
#                     self.daily_tweet_count += 1
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Posted tweet: {tweet_text}")
#                 else:
#                     logging.warning("Generated tweet failed validation")
#         except Exception as e:
#             logging.error(f"Error posting tweet: {str(e)}")

#     def check_mentions(self):
#         """Check and respond to mentions"""
#         self.reset_counters()
        
#         if self.daily_mention_check_count >= self.config.TWITTER_READS_PER_DAY:
#             logging.info("Daily mention check limit reached")
#             return

#         try:
#             start_time = datetime.now(timezone.utc) - timedelta(hours=6)
#             mentions = self.client.get_users_mentions(
#                 id=self.twitter_me_id,
#                 start_time=start_time,
#                 max_results=5  # Twitter API minimum
#             )[0] or []

#             for mention in mentions[:self.config.MAX_MENTIONS_PER_CHECK]:
#                 if not self.can_make_huggingface_call():
#                     logging.info("Daily Hugging Face API limit reached during mentions check")
#                     return

#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.REPLY_PROMPTS
#                 ).format(tweet=mention.text)
#                 response = self.api_handler.huggingface_call(prompt, max_length=80)
                
#                 response = self.content_generator.clean_content(response)
                
#                 if self.content_generator.validate_content(response):
#                     response = f"@{mention.author_id} {response}"[:280]
#                     self.client.create_tweet(
#                         text=response,
#                         in_reply_to_tweet_id=mention.id
#                     )
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Replied to mention {mention.id}: {response}")

#             self.daily_mention_check_count += 1
#         except Exception as e:
#             logging.error(f"Error checking mentions: {str(e)}")

# def job(bot):
#     """Execute the main bot tasks"""
#     try:
#         bot.post_tweet()
#         time.sleep(5)
#         bot.check_mentions()
#     except Exception as e:
#         logging.error(f"Job execution failed: {str(e)}")

# def main():
#     """Main entry point of the application"""
#     setup_logging()
#     logging.info("Starting Twitter Bot")
    
#     try:
#         config = Config()
#         bot = TwitterBot(config)
        
#         # Schedule jobs every 12 hours
#         schedule.every(12).hours.do(job, bot)
        
#         # Run job immediately on startup
#         job(bot)
        
#         while True:
#             try:
#                 schedule.run_pending()
#                 time.sleep(60)
#             except Exception as e:
#                 logging.error(f"Main loop error: {str(e)}")
#                 time.sleep(300)
                
#     except Exception as e:
#         logging.error(f"Fatal error: {str(e)}")
#         raise

# if __name__ == "__main__":
#     main()








# import os
# import tweepy
# import requests
# from datetime import datetime, timedelta, timezone
# import schedule
# import time
# import logging
# import random
# from dotenv import load_dotenv

# def setup_logging():
#     """Configure logging with both file and console handlers"""
#     logging.basicConfig(
#         filename='bot.log',
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s'
#     )
#     console = logging.StreamHandler()
#     console.setLevel(logging.INFO)
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     console.setFormatter(formatter)
#     logging.getLogger('').addHandler(console)

# class Config:
#     """Configuration class to manage all settings"""
#     def __init__(self):
#         load_dotenv()
        
#         # API Keys
#         self.TWITTER_API_KEY = os.getenv("TW_API_KEY")
#         self.TWITTER_API_SECRET = os.getenv("TW_API_KEY_SECRET")
#         self.TWITTER_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
#         self.TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TW_ACCESS_TOKEN_SECRET")
#         self.TWITTER_BEARER_TOKEN = os.getenv("TW_BEARER_TOKEN")
#         self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")
#         self.HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
        
#         # API Rate Limits
#         self.HUGGINGFACE_CALLS_PER_DAY = int(os.getenv("HUGGINGFACE_CALLS_PER_DAY", "24"))
#         self.TWITTER_POSTS_PER_DAY = int(os.getenv("TWITTER_POSTS_PER_DAY", "2"))
#         self.TWITTER_READS_PER_DAY = int(os.getenv("TWITTER_READS_PER_DAY", "2"))
#         self.MAX_MENTIONS_PER_CHECK = 5
        
#         # Memory File for Tweet Storage
#         self.MEMORY_FILE = "posted_tweets.txt"

#         # API Endpoints
#         self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
#         self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# class ContentGenerator:
#     """Class to handle content generation and validation"""
#     TWEET_PROMPTS = [
#         "Write a tech news tweet about: {news}. Include key facts only.",
#         "Summarize this tech news in one tweet: {news}. Be clear and factual.",
#         "Share this tech update concisely: {news}. Focus on the main point."
#     ]

#     REPLY_PROMPTS = [
#         "Write a helpful reply to: {tweet}. Be brief and relevant.",
#         "Respond professionally to: {tweet}. Keep it short and helpful.",
#         "Answer this query: {tweet}. Be concise and informative."
#     ]

#     @staticmethod
#     def get_random_prompt(prompt_list):
#         return random.choice(prompt_list)

#     @staticmethod
#     def validate_content(text):
#         """Validate generated content"""
#         if not text or len(text.strip()) < 10:
#             return False
#         if text.count('@') > 2:
#             return False
#         if len(text.split()) < 3:
#             return False
#         return True

#     @staticmethod
#     def clean_content(text):
#         """Clean and format content"""
#         text = ' '.join(text.split())
#         text = text.strip('""\'\'')
#         text = ''.join(char for i, char in enumerate(text) 
#                       if i == 0 or char != text[i-1] or not char.isspace())
#         return text

# class APIHandler:
#     """Class to handle all API calls"""
#     def __init__(self, config):
#         self.config = config
#         self.posted_tweets = self.load_posted_tweets()

#     def load_posted_tweets(self):
#         """Load previously posted tweets from file"""
#         try:
#             with open(self.config.MEMORY_FILE, "r") as f:
#                 return set(line.strip() for line in f)
#         except FileNotFoundError:
#             return set()

#     def save_tweet(self, tweet_content):
#         """Save tweet to memory file"""
#         try:
#             with open(self.config.MEMORY_FILE, "a") as f:
#                 f.write(f"{tweet_content}\n")
#             self.posted_tweets.add(tweet_content)
#             logging.info("Tweet saved to memory file")
#         except Exception as e:
#             logging.error(f"Error saving tweet: {e}")

#     def huggingface_call(self, prompt, max_length=50):
#         """Make API call to Hugging Face"""
#         headers = {"Authorization": f"Bearer {self.config.HUGGINGFACE_API_KEY}"}
#         payload = {
#             "inputs": prompt,
#             "parameters": {
#                 "max_length": max_length,
#                 "temperature": 0.7,
#                 "top_p": 0.95,
#                 "do_sample": True
#             }
#         }
        
#         try:
#             response = requests.post(
#                 self.config.HUGGINGFACE_API_URL,
#                 headers=headers,
#                 json=payload,
#                 timeout=10
#             )
#             response.raise_for_status()
#             return response.json()[0].get("generated_text", "")
#         except Exception as e:
#             logging.error(f"Hugging Face API error: {str(e)}")
#             return ""

#     def news_api_call(self):
#         """Make API call to News API"""
#         params = {
#             "category": "technology",
#             "language": "en",
#             "apiKey": self.config.NEWS_API_KEY,
#             "pageSize": 5
#         }
        
#         try:
#             response = requests.get(
#                 self.config.NEWS_API_URL, 
#                 params=params,
#                 timeout=10
#             )
#             response.raise_for_status()
#             data = response.json()
            
#             if data.get("articles"):
#                 for article in data["articles"]:
#                     title = article.get('title', '')
#                     title = title.split(' - ')[0].split(' | ')[0].strip()
#                     if title and title not in self.posted_tweets:
#                         return title
#             return ""
#         except Exception as e:
#             logging.error(f"News API error: {str(e)}")
#             return ""

# class TwitterBot:
#     def __init__(self, config):
#         self.config = config
#         self.api_handler = APIHandler(config)
#         self.content_generator = ContentGenerator()
#         self.setup_twitter_clients()
        
#         self.daily_tweet_count = 0
#         self.daily_mention_check_count = 0
#         self.daily_huggingface_calls = 0
#         self.last_reset = datetime.now(timezone.utc)

#     def setup_twitter_clients(self):
#         """Initialize Twitter API clients"""
#         try:
#             self.client = tweepy.Client(
#                 bearer_token=self.config.TWITTER_BEARER_TOKEN,
#                 consumer_key=self.config.TWITTER_API_KEY,
#                 consumer_secret=self.config.TWITTER_API_SECRET,
#                 access_token=self.config.TWITTER_ACCESS_TOKEN,
#                 access_token_secret=self.config.TWITTER_ACCESS_TOKEN_SECRET,
#                 wait_on_rate_limit=True
#             )
#             self.twitter_me_id = self.client.get_me()[0].id
#             logging.info("Twitter API clients initialized successfully")
#         except Exception as e:
#             logging.error(f"Failed to initialize Twitter API: {str(e)}")
#             raise

#     def reset_counters(self):
#         """Reset daily counters if it's a new day"""
#         current_time = datetime.now(timezone.utc)
#         if (current_time - self.last_reset).days >= 1:
#             self.daily_tweet_count = 0
#             self.daily_mention_check_count = 0
#             self.daily_huggingface_calls = 0
#             self.last_reset = current_time
#             logging.info("Daily counters reset")

#     def can_make_huggingface_call(self):
#         """Check if we can make another Hugging Face API call"""
#         return self.daily_huggingface_calls < self.config.HUGGINGFACE_CALLS_PER_DAY

#     def post_tweet(self):
#         """Post a tweet with content validation"""
#         self.reset_counters()
        
#         if self.daily_tweet_count >= self.config.TWITTER_POSTS_PER_DAY:
#             logging.info("Daily tweet limit reached")
#             return

#         if not self.can_make_huggingface_call():
#             logging.info("Daily Hugging Face API limit reached")
#             return

#         try:
#             news = self.api_handler.news_api_call()
#             if news:
#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.TWEET_PROMPTS
#                 ).format(news=news)
#                 tweet_text = self.api_handler.huggingface_call(prompt, max_length=100)
                
#                 tweet_text = self.content_generator.clean_content(tweet_text)
                
#                 if self.content_generator.validate_content(tweet_text):
#                     tweet_text = tweet_text[:280]
#                     self.client.create_tweet(text=tweet_text)
#                     self.api_handler.save_tweet(tweet_text)
#                     self.daily_tweet_count += 1
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Posted tweet: {tweet_text}")
#                 else:
#                     logging.warning("Generated tweet failed validation")
#         except Exception as e:
#             logging.error(f"Error posting tweet: {str(e)}")

#     def check_mentions(self):
#         """Check and respond to mentions"""
#         self.reset_counters()
        
#         if self.daily_mention_check_count >= self.config.TWITTER_READS_PER_DAY:
#             logging.info("Daily mention check limit reached")
#             return

#         try:
#             start_time = datetime.now(timezone.utc) - timedelta(hours=6)
#             mentions = self.client.get_users_mentions(
#                 id=self.twitter_me_id,
#                 start_time=start_time,
#                 max_results=5
#             )[0] or []

#             for mention in mentions[:self.config.MAX_MENTIONS_PER_CHECK]:
#                 if not self.can_make_huggingface_call():
#                     logging.info("Daily Hugging Face API limit reached during mentions check")
#                     return

#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.REPLY_PROMPTS
#                 ).format(tweet=mention.text)
#                 response = self.api_handler.huggingface_call(prompt, max_length=80)
                
#                 response = self.content_generator.clean_content(response)
                
#                 if self.content_generator.validate_content(response):
#                     response = f"@{mention.author_id} {response}"[:280]
#                     self.client.create_tweet(
#                         text=response,
#                         in_reply_to_tweet_id=mention.id
#                     )
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Replied to mention {mention.id}: {response}")

#             self.daily_mention_check_count += 1
#         except Exception as e:
#             logging.error(f"Error checking mentions: {str(e)}")

# def job(bot):
#     """Execute the main bot tasks"""
#     try:
#         bot.post_tweet()
#         time.sleep(5)  # Small delay between operations
#         bot.check_mentions()
#     except Exception as e:
#         logging.error(f"Job execution failed: {str(e)}")

# def main():
#     """Main entry point of the application"""
#     setup_logging()
#     logging.info("Starting Twitter Bot")
    
#     try:
#         config = Config()
#         bot = TwitterBot(config)
        
#         # Schedule jobs every 12 hours
#         schedule.every(12).hours.do(job, bot)
        
#         # Run job immediately on startup
#         job(bot)
        
#         while True:
#             try:
#                 schedule.run_pending()
#                 time.sleep(60)
#             except Exception as e:
#                 logging.error(f"Main loop error: {str(e)}")
#                 time.sleep(300)  # Wait 5 minutes before retrying after an error
                
#     except Exception as e:
#         logging.error(f"Fatal error: {str(e)}")
#         raise

# if __name__ == "__main__":
#     main()












































# import os
# import tweepy
# import requests
# from datetime import datetime, timedelta, timezone
# import schedule
# import time
# import logging
# import random
# from dotenv import load_dotenv

# def setup_logging():
#     """Configure logging with both file and console handlers"""
#     logging.basicConfig(
#         filename='bot.log',
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s'
#     )
#     console = logging.StreamHandler()
#     console.setLevel(logging.INFO)
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     console.setFormatter(formatter)
#     logging.getLogger('').addHandler(console)

# class Config:
#     """Configuration class to manage all settings"""
#     def __init__(self):
#         load_dotenv()
        
#         # API Keys
#         self.TWITTER_API_KEY = os.getenv("TW_API_KEY")
#         self.TWITTER_API_SECRET = os.getenv("TW_API_KEY_SECRET")
#         self.TWITTER_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
#         self.TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TW_ACCESS_TOKEN_SECRET")
#         self.TWITTER_BEARER_TOKEN = os.getenv("TW_BEARER_TOKEN")
#         self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")
#         self.HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
        
#         # API Rate Limits
#         self.HUGGINGFACE_CALLS_PER_DAY = int(os.getenv("HUGGINGFACE_CALLS_PER_DAY", "24"))
#         self.TWITTER_POSTS_PER_DAY = int(os.getenv("TWITTER_POSTS_PER_DAY", "2"))
#         self.TWITTER_READS_PER_DAY = int(os.getenv("TWITTER_READS_PER_DAY", "2"))
#         self.MAX_MENTIONS_PER_CHECK = 5
        
#         # Memory File for Tweet Storage
#         self.MEMORY_FILE = "posted_tweets.txt"

#         # API Endpoints
#         self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
#         self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# class ContentGenerator:
#     """Class to handle content generation and validation"""
#     TWEET_PROMPTS = [
#         "Write an informative tech news update about {news}. Include key technical details and implications for the industry.",
#         "Create a detailed summary of this {topic} news: {news}. Explain why it matters.",
#         "Generate an insightful {topic} update about: {news}. Include context and significance."
#     ]

#     REPLY_PROMPTS = [
#         "Write a comprehensive technical reply to: {tweet}",
#         "Provide a detailed response about {topic} to: {tweet}",
#         "Give an informative answer about {topic} to: {tweet}"
#     ]

#     FALLBACK_PROMPTS = [
#         "Explain a significant development in {topic} and its impact on the industry.",
#         "Discuss an important trend in {topic} and why it matters for the future.",
#         "Share insights about recent advances in {topic} and their implications.",
#         "Analyze the current state of {topic} and its potential future developments.",
#         "Describe how {topic} is transforming the technology landscape and why it's significant."
#     ]

#     TOPIC_INSIGHTS = {
#         'blockchain': [
#             "Blockchain technology revolutionizes data security and transparency through decentralized ledgers, enabling trustless transactions and smart contract automation.",
#             "The evolution of blockchain networks introduces new consensus mechanisms and scaling solutions, improving efficiency and adoption.",
#             "Enterprise blockchain solutions transform supply chain management and cross-border transactions, reducing costs and increasing transparency."
#         ],
#         'cryptocurrency': [
#             "Cryptocurrency adoption drives financial innovation through decentralized finance protocols and digital asset management platforms.",
#             "Digital currencies reshape traditional banking through instant, borderless transactions and programmable money features.",
#             "The cryptocurrency ecosystem expands with layer-2 scaling solutions and interoperability protocols, enabling new use cases."
#         ],
#         'bitcoin': [
#             "Bitcoin's Lightning Network enables instant micropayments and scales transaction capabilities while maintaining decentralization.",
#             "Institutional Bitcoin adoption increases as corporations and investment firms recognize its potential as a digital store of value.",
#             "Bitcoin mining evolution focuses on renewable energy sources and efficiency improvements, addressing environmental concerns."
#         ],
#         'ai': [
#             "Advanced AI models demonstrate unprecedented natural language understanding and generation capabilities, transforming human-computer interaction.",
#             "Machine learning systems revolutionize healthcare through improved diagnosis and treatment recommendations based on vast medical datasets.",
#             "AI development in autonomous systems and robotics creates new possibilities for automation and human augmentation."
#         ],
#         'tech': [
#             "Quantum computing advances promise to revolutionize cryptography and complex problem-solving across industries.",
#             "Edge computing and 5G networks enable new real-time applications and improved IoT device performance.",
#             "Open-source technology development accelerates innovation and collaboration in software and hardware."
#         ]
#     }

#     # Primary topics to focus on
#     PRIORITY_TOPICS = {
#         'blockchain': ['blockchain', 'distributed ledger', 'web3', 'defi'],
#         'cryptocurrency': ['cryptocurrency', 'crypto', 'defi', 'digital currency', 'web3'],
#         'bitcoin': ['bitcoin', 'btc', 'satoshi', 'lightning network'],
#         'ai': ['artificial intelligence', 'ai', 'machine learning', 'deep learning', 'neural network', 'llm'],
#         'tech': ['technology', 'tech', 'innovation']
#     }

#     # Keywords to explicitly exclude
#     EXCLUSION_KEYWORDS = {
#         'deal', 'sale', 'discount', 'price', 'affordable', 'cheap', 'offer',
#         'black friday', 'cyber monday', 'presidents day', 'holiday'
#     }

#     @staticmethod
#     def identify_primary_topic(text):
#         """
#         Identify which primary topic the content belongs to.
#         Returns tuple of (topic_found, topic_name) or (False, None) if no match
#         """
#         text_lower = text.lower()
        
#         # First check for exclusion keywords
#         if any(keyword in text_lower for keyword in ContentGenerator.EXCLUSION_KEYWORDS):
#             return False, None
        
#         # Check each primary topic
#         for topic, keywords in ContentGenerator.PRIORITY_TOPICS.items():
#             if any(keyword in text_lower for keyword in keywords):
#                 return True, topic
        
#         return False, None

#     @staticmethod
#     def get_random_prompt(prompt_list, topic="tech"):
#         """Get a random prompt with the topic inserted"""
#         prompt = random.choice(prompt_list)
#         return prompt.format(topic=topic, news="{news}")

#     @staticmethod
#     def get_fallback_prompt(topic):
#         """Get a random fallback prompt for a specific topic"""
#         base_prompt = random.choice(ContentGenerator.FALLBACK_PROMPTS)
#         insight = random.choice(ContentGenerator.TOPIC_INSIGHTS.get(topic, ContentGenerator.TOPIC_INSIGHTS['tech']))
#         return base_prompt.format(topic=topic), insight

#     @staticmethod
#     def validate_content(text, min_words=10, max_words=60):
#         """Validate generated content with minimum length requirement"""
#         if not text or len(text.strip()) < 20:  # Minimum 20 characters
#             return False
        
#         # Check word count
#         word_count = len(text.split())
#         if word_count < min_words or word_count > max_words:
#             return False
            
#         # Ensure no promotional content
#         text_lower = text.lower()
#         if any(keyword in text_lower for keyword in ContentGenerator.EXCLUSION_KEYWORDS):
#             return False
            
#         return True

#     @staticmethod
#     def clean_content(text):
#         """Clean and format content"""
#         text = ' '.join(text.split())
#         text = text.strip('""\'\'')
#         # Remove excessive hashtags but keep relevant ones
#         words = text.split()
#         hashtags = [w for w in words if w.startswith('#')]
#         non_hashtags = [w for w in words if not w.startswith('#')]
        
#         # Keep only up to 2 most relevant hashtags
#         if len(hashtags) > 2:
#             hashtags = hashtags[:2]
            
#         return ' '.join(non_hashtags + hashtags).strip()

# class APIHandler:
#     """Class to handle all API calls"""
#     def __init__(self, config):
#         self.config = config
#         self.posted_tweets = self.load_posted_tweets()
#         self.content_generator = ContentGenerator()

#     def load_posted_tweets(self):
#         """Load previously posted tweets from file"""
#         try:
#             with open(self.config.MEMORY_FILE, "r") as f:
#                 return set(line.strip() for line in f)
#         except FileNotFoundError:
#             # If file doesn't exist, create it
#             open(self.config.MEMORY_FILE, "a").close()
#             return set()

#     def save_tweet(self, tweet_content):
#         """Save tweet to memory file"""
#         try:
#             with open(self.config.MEMORY_FILE, "a") as f:
#                 f.write(f"{tweet_content}\n")
#             self.posted_tweets.add(tweet_content)
#             logging.info("Tweet saved to memory file")
#         except Exception as e:
#             logging.error(f"Error saving tweet: {e}")

#     def news_api_call(self):
#         """Make API call to News API with strict filtering"""
#         params = {
#             "category": "technology",
#             "language": "en",
#             "apiKey": self.config.NEWS_API_KEY,
#             "pageSize": 20,
#             "q": "blockchain OR cryptocurrency OR bitcoin OR AI OR artificial intelligence"
#         }
        
#         try:
#             response = requests.get(
#                 self.config.NEWS_API_URL, 
#                 params=params,
#                 timeout=10
#             )
#             response.raise_for_status()
#             data = response.json()
            
#             if data.get("articles"):
#                 for article in data["articles"]:
#                     title = article.get('title', '')
#                     description = article.get('description', '')
#                     content = article.get('content', '')
                    
#                     # Clean title
#                     title = title.split(' - ')[0].split(' | ')[0].strip()
                    
#                     # Skip if already posted
#                     if title in self.posted_tweets:
#                         continue
                        
#                     # Check for primary topic match
#                     is_valid_topic, topic = self.content_generator.identify_primary_topic(
#                         f"{title} {description} {content}"
#                     )
                    
#                     if is_valid_topic:
#                         return title, topic, description
                        
#             return "", None, ""
            
#         except Exception as e:
#             logging.error(f"News API error: {str(e)}")
#             return "", None, ""

#     def huggingface_call(self, prompt, topic, max_length=120):
#         """Make API call to Hugging Face with topic context"""
#         headers = {"Authorization": f"Bearer {self.config.HUGGINGFACE_API_KEY}"}
        
#         # Add topic context to prompt
#         enhanced_prompt = f"Create an informative {topic} update about: {prompt}. Include technical details and significance."
        
#         payload = {
#             "inputs": enhanced_prompt,
#             "parameters": {
#                 "max_length": max_length,
#                 "temperature": 0.8,
#                 "top_p": 0.95,
#                 "do_sample": True
#             }
#         }
        
#         try:
#             response = requests.post(
#                 self.config.HUGGINGFACE_API_URL,
#                 headers=headers,
#                 json=payload,
#                 timeout=10
#             )
#             response.raise_for_status()
#             return response.json()[0].get("generated_text", "")
#         except Exception as e:
#             logging.error(f"Hugging Face API error: {str(e)}")
#             return ""

# class TwitterBot:
#     def __init__(self, config):
#         self.config = config
#         self.api_handler = APIHandler(config)
#         self.content_generator = ContentGenerator()
#         self.setup_twitter_clients()
        
#         self.daily_tweet_count = 0
#         self.daily_mention_check_count = 0
#         self.daily_huggingface_calls = 0
#         self.last_reset = datetime.now(timezone.utc)

#     def setup_twitter_clients(self):
#         """Initialize Twitter API clients"""
#         try:
#             self.client = tweepy.Client(
#                 bearer_token=self.config.TWITTER_BEARER_TOKEN,
#                 consumer_key=self.config.TWITTER_API_KEY,
#                 consumer_secret=self.config.TWITTER_API_SECRET,
#                 access_token=self.config.TWITTER_ACCESS_TOKEN,
#                 access_token_secret=self.config.TWITTER_ACCESS_TOKEN_SECRET,
#                 wait_on_rate_limit=True
#             )
#             self.twitter_me_id = self.client.get_me()[0].id
#             logging.info("Twitter API clients initialized successfully")
#         except Exception as e:
#             logging.error(f"Failed to initialize Twitter API: {str(e)}")
#             raise

#     def reset_counters(self):
#         """Reset daily counters if it's a new day"""
#         current_time = datetime.now(timezone.utc)
#         if (current_time - self.last_reset).days >= 1:
#             self.daily_tweet_count = 0
#             self.daily_mention_check_count = 0
#             self.daily_huggingface_calls = 0
#             self.last_reset = current_time
#             logging.info("Daily counters reset")

#     def can_make_huggingface_call(self):
#         """Check if we can make another Hugging Face API call"""
#         return self.daily_huggingface_calls < self.config.HUGGINGFACE_CALLS_PER_DAY

#     def generate_fallback_content(self):
#         """Generate thought-provoking content when no news is available"""
#         topic = random.choice(list(self.content_generator.PRIORITY_TOPICS.keys()))
#         prompt, insight = self.content_generator.get_fallback_prompt(topic)
#         tweet_text = self.api_handler.huggingface_call(insight, topic)
#         tweet_text = self.content_generator.clean_content(tweet_text)
#         return tweet_text, topic

#     def post_tweet(self):
#         """Post a tweet with fallback to generated content"""
#         self.reset_counters()
        
#         if self.daily_tweet_count >= self.config.TWITTER_POSTS_PER_DAY:
#             logging.info("Daily tweet limit reached")
#             return

#         if not self.can_make_huggingface_call():
#             logging.info("Daily Hugging Face API limit reached")
#             return

#         try:
#             news, topic, description = self.api_handler.news_api_call()
            
#             if news and topic:
#                 # Process news content with description for context
#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.TWEET_PROMPTS,
#                     topic=topic
#                 ).format(news=f"{news}. {description}")
                
#                 tweet_text = self.api_handler.huggingface_call(prompt, topic)
                
#             else:
#                 # Generate fallback content
#                 logging.info("No relevant tech news found, generating thought-provoking content")
#                 tweet_text, topic = self.generate_fallback_content()
            
#             tweet_text = self.content_generator.clean_content(tweet_text)
            
#             # Validate tweet content
#             if not self.content_generator.validate_content(tweet_text):
#                 logging.warning("Generated content failed validation, trying fallback")
#                 tweet_text, topic = self.generate_fallback_content()
#                 tweet_text = self.content_generator.clean_content(tweet_text)
                
#                 # If fallback also fails validation, abort
#                 if not self.content_generator.validate_content(tweet_text):
#                     logging.error("Failed to generate valid content")
#                     return

#             # Add relevant hashtags based on topic
#             hashtags = f" #{topic}" if topic else ""
#             final_tweet = f"{tweet_text}{hashtags}"

#             # Check if tweet is unique
#             if final_tweet in self.api_handler.posted_tweets:
#                 logging.info("Tweet content already posted, skipping")
#                 return

#             try:
#                 # Post tweet
#                 response = self.client.create_tweet(text=final_tweet)
#                 if response.data:
#                     self.api_handler.save_tweet(final_tweet)
#                     self.daily_tweet_count += 1
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Tweet posted successfully: {final_tweet}")
#                 else:
#                     logging.error("Failed to post tweet: No response data")
#             except Exception as e:
#                 logging.error(f"Error posting tweet: {str(e)}")
#         except Exception as e:
#             logging.error(f"Error in post_tweet: {str(e)}")

#     def check_mentions(self):
#         """Check and respond to mentions"""
#         self.reset_counters()
        
#         if self.daily_mention_check_count >= self.config.TWITTER_READS_PER_DAY:
#             logging.info("Daily mention check limit reached")
#             return

#         if not self.can_make_huggingface_call():
#             logging.info("Daily Hugging Face API limit reached")
#             return

#         try:
#             # Get mentions timeline
#             mentions = self.client.get_users_mentions(
#                 self.twitter_me_id,
#                 max_results=self.config.MAX_MENTIONS_PER_CHECK
#             )

#             if not mentions.data:
#                 logging.info("No new mentions found")
#                 return

#             for mention in mentions.data:
#                 # Skip if already processed
#                 if mention.text in self.api_handler.posted_tweets:
#                     continue

#                 # Identify topic from mention
#                 is_valid_topic, topic = self.content_generator.identify_primary_topic(mention.text)
                
#                 if not is_valid_topic:
#                     topic = "tech"  # Default to general tech if no specific topic identified

#                 # Generate response
#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.REPLY_PROMPTS,
#                     topic=topic
#                 ).format(tweet=mention.text)

#                 response_text = self.api_handler.huggingface_call(prompt, topic)
#                 response_text = self.content_generator.clean_content(response_text)

#                 if not self.content_generator.validate_content(response_text):
#                     logging.warning(f"Generated response failed validation for mention {mention.id}")
#                     continue

#                 try:
#                     # Reply to mention
#                     self.client.create_tweet(
#                         text=response_text,
#                         in_reply_to_tweet_id=mention.id
#                     )
#                     self.api_handler.save_tweet(response_text)
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Replied to mention {mention.id}: {response_text}")
#                 except Exception as e:
#                     logging.error(f"Error replying to mention {mention.id}: {str(e)}")

#             self.daily_mention_check_count += 1

#         except Exception as e:
#             logging.error(f"Error checking mentions: {str(e)}")

# def main():
#     """Main function to run the Twitter bot"""
#     # Initialize config and bot
#     config = Config()
#     setup_logging()
    
#     try:
#         bot = TwitterBot(config)
#         logging.info("Twitter bot initialized successfully")

#         # Schedule tasks
#         schedule.every(6).hours.do(bot.post_tweet)
#         schedule.every(6).hours.do(bot.check_mentions)

#         # Run continuously
#         while True:
#             schedule.run_pending()
#             time.sleep(60)

#     except Exception as e:
#         logging.error(f"Fatal error: {str(e)}")
#         raise

# if __name__ == "__main__":
#     main()




























# import os
# import threading
# import tweepy
# import requests
# from datetime import datetime, timedelta, timezone
# import schedule
# import time
# import logging
# import random
# from dotenv import load_dotenv
# from flask import Flask, jsonify

# def setup_logging():
#     """Configure logging with both file and console handlers"""
#     logging.basicConfig(
#         filename='bot.log',
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s'
#     )
#     console = logging.StreamHandler()
#     console.setLevel(logging.INFO)
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     console.setFormatter(formatter)
#     logging.getLogger('').addHandler(console)

# class Config:
#     """Configuration class to manage all settings"""
#     def __init__(self):
#         load_dotenv()
        
#         # API Keys
#         self.TWITTER_API_KEY = os.getenv("TW_API_KEY")
#         self.TWITTER_API_SECRET = os.getenv("TW_API_KEY_SECRET")
#         self.TWITTER_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
#         self.TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TW_ACCESS_TOKEN_SECRET")
#         self.TWITTER_BEARER_TOKEN = os.getenv("TW_BEARER_TOKEN")
#         self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")
#         self.HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
        
#         # API Rate Limits
#         self.HUGGINGFACE_CALLS_PER_DAY = int(os.getenv("HUGGINGFACE_CALLS_PER_DAY", "24"))
#         self.TWITTER_POSTS_PER_DAY = int(os.getenv("TWITTER_POSTS_PER_DAY", "2"))
#         self.TWITTER_READS_PER_DAY = int(os.getenv("TWITTER_READS_PER_DAY", "2"))
#         self.MAX_MENTIONS_PER_CHECK = 5
        
#         # Memory File for Tweet Storage
#         self.MEMORY_FILE = "posted_tweets.txt"

#         # API Endpoints
#         self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
#         self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# class ContentGenerator:
#     """Class to handle content generation and validation"""
#     TWEET_PROMPTS = [
#         "Write an informative tech news update about {news}. Include key technical details and implications for the industry.",
#         "Create a detailed summary of this {topic} news: {news}. Explain why it matters.",
#         "Generate an insightful {topic} update about: {news}. Include context and significance."
#     ]

#     REPLY_PROMPTS = [
#         "Write a comprehensive technical reply to: {tweet}",
#         "Provide a detailed response about {topic} to: {tweet}",
#         "Give an informative answer about {topic} to: {tweet}"
#     ]

#     FALLBACK_PROMPTS = [
#         "Explain a significant development in {topic} and its impact on the industry.",
#         "Discuss an important trend in {topic} and why it matters for the future.",
#         "Share insights about recent advances in {topic} and their implications.",
#         "Analyze the current state of {topic} and its potential future developments.",
#         "Describe how {topic} is transforming the technology landscape and why it's significant."
#     ]

#     TOPIC_INSIGHTS = {
#         'blockchain': [
#             "Blockchain technology revolutionizes data security and transparency through decentralized ledgers, enabling trustless transactions and smart contract automation.",
#             "The evolution of blockchain networks introduces new consensus mechanisms and scaling solutions, improving efficiency and adoption.",
#             "Enterprise blockchain solutions transform supply chain management and cross-border transactions, reducing costs and increasing transparency."
#         ],
#         'cryptocurrency': [
#             "Cryptocurrency adoption drives financial innovation through decentralized finance protocols and digital asset management platforms.",
#             "Digital currencies reshape traditional banking through instant, borderless transactions and programmable money features.",
#             "The cryptocurrency ecosystem expands with layer-2 scaling solutions and interoperability protocols, enabling new use cases."
#         ],
#         'bitcoin': [
#             "Bitcoin's Lightning Network enables instant micropayments and scales transaction capabilities while maintaining decentralization.",
#             "Institutional Bitcoin adoption increases as corporations and investment firms recognize its potential as a digital store of value.",
#             "Bitcoin mining evolution focuses on renewable energy sources and efficiency improvements, addressing environmental concerns."
#         ],
#         'ai': [
#             "Advanced AI models demonstrate unprecedented natural language understanding and generation capabilities, transforming human-computer interaction.",
#             "Machine learning systems revolutionize healthcare through improved diagnosis and treatment recommendations based on vast medical datasets.",
#             "AI development in autonomous systems and robotics creates new possibilities for automation and human augmentation."
#         ],
#         'tech': [
#             "Quantum computing advances promise to revolutionize cryptography and complex problem-solving across industries.",
#             "Edge computing and 5G networks enable new real-time applications and improved IoT device performance.",
#             "Open-source technology development accelerates innovation and collaboration in software and hardware."
#         ]
#     }

#     # Primary topics to focus on
#     PRIORITY_TOPICS = {
#         'blockchain': ['blockchain', 'distributed ledger', 'web3', 'defi'],
#         'cryptocurrency': ['cryptocurrency', 'crypto', 'defi', 'digital currency', 'web3'],
#         'bitcoin': ['bitcoin', 'btc', 'satoshi', 'lightning network'],
#         'ai': ['artificial intelligence', 'ai', 'machine learning', 'deep learning', 'neural network', 'llm'],
#         'tech': ['technology', 'tech', 'innovation']
#     }

#     # Keywords to explicitly exclude
#     EXCLUSION_KEYWORDS = {
#         'deal', 'sale', 'discount', 'price', 'affordable', 'cheap', 'offer',
#         'black friday', 'cyber monday', 'presidents day', 'holiday'
#     }

#     @staticmethod
#     def identify_primary_topic(text):
#         """
#         Identify which primary topic the content belongs to.
#         Returns tuple of (topic_found, topic_name) or (False, None) if no match
#         """
#         text_lower = text.lower()
        
#         # First check for exclusion keywords
#         if any(keyword in text_lower for keyword in ContentGenerator.EXCLUSION_KEYWORDS):
#             return False, None
        
#         # Check each primary topic
#         for topic, keywords in ContentGenerator.PRIORITY_TOPICS.items():
#             if any(keyword in text_lower for keyword in keywords):
#                 return True, topic
        
#         return False, None

#     @staticmethod
#     def get_random_prompt(prompt_list, topic="tech"):
#         """Get a random prompt with the topic inserted"""
#         prompt = random.choice(prompt_list)
#         return prompt.format(topic=topic, news="{news}")

#     @staticmethod
#     def get_fallback_prompt(topic):
#         """Get a random fallback prompt for a specific topic"""
#         base_prompt = random.choice(ContentGenerator.FALLBACK_PROMPTS)
#         insight = random.choice(ContentGenerator.TOPIC_INSIGHTS.get(topic, ContentGenerator.TOPIC_INSIGHTS['tech']))
#         return base_prompt.format(topic=topic), insight

#     @staticmethod
#     def validate_content(text, min_words=10, max_words=60):
#         """Validate generated content with minimum length requirement"""
#         if not text or len(text.strip()) < 20:  # Minimum 20 characters
#             return False
        
#         # Check word count
#         word_count = len(text.split())
#         if word_count < min_words or word_count > max_words:
#             return False
            
#         # Ensure no promotional content
#         text_lower = text.lower()
#         if any(keyword in text_lower for keyword in ContentGenerator.EXCLUSION_KEYWORDS):
#             return False
            
#         return True

#     @staticmethod
#     def clean_content(text):
#         """Clean and format content"""
#         text = ' '.join(text.split())
#         text = text.strip('""\'\'')
#         # Remove excessive hashtags but keep relevant ones
#         words = text.split()
#         hashtags = [w for w in words if w.startswith('#')]
#         non_hashtags = [w for w in words if not w.startswith('#')]
        
#         # Keep only up to 2 most relevant hashtags
#         if len(hashtags) > 2:
#             hashtags = hashtags[:2]
            
#         return ' '.join(non_hashtags + hashtags).strip()

# class APIHandler:
#     """Class to handle all API calls"""
#     def __init__(self, config):
#         self.config = config
#         self.posted_tweets = self.load_posted_tweets()
#         self.content_generator = ContentGenerator()

#     def load_posted_tweets(self):
#         """Load previously posted tweets from file"""
#         try:
#             with open(self.config.MEMORY_FILE, "r") as f:
#                 return set(line.strip() for line in f)
#         except FileNotFoundError:
#             # If file doesn't exist, create it
#             open(self.config.MEMORY_FILE, "a").close()
#             return set()

#     def save_tweet(self, tweet_content):
#         """Save tweet to memory file"""
#         try:
#             with open(self.config.MEMORY_FILE, "a") as f:
#                 f.write(f"{tweet_content}\n")
#             self.posted_tweets.add(tweet_content)
#             logging.info("Tweet saved to memory file")
#         except Exception as e:
#             logging.error(f"Error saving tweet: {e}")

#     def news_api_call(self):
#         """Make API call to News API with strict filtering"""
#         params = {
#             "category": "technology",
#             "language": "en",
#             "apiKey": self.config.NEWS_API_KEY,
#             "pageSize": 20,
#             "q": "blockchain OR cryptocurrency OR bitcoin OR AI OR artificial intelligence"
#         }
        
#         try:
#             response = requests.get(
#                 self.config.NEWS_API_URL, 
#                 params=params,
#                 timeout=10
#             )
#             response.raise_for_status()
#             data = response.json()
            
#             if data.get("articles"):
#                 for article in data["articles"]:
#                     title = article.get('title', '')
#                     description = article.get('description', '')
#                     content = article.get('content', '')
                    
#                     # Clean title
#                     title = title.split(' - ')[0].split(' | ')[0].strip()
                    
#                     # Skip if already posted
#                     if title in self.posted_tweets:
#                         continue
                        
#                     # Check for primary topic match
#                     is_valid_topic, topic = self.content_generator.identify_primary_topic(
#                         f"{title} {description} {content}"
#                     )
                    
#                     if is_valid_topic:
#                         return title, topic, description
                        
#             return "", None, ""
            
#         except Exception as e:
#             logging.error(f"News API error: {str(e)}")
#             return "", None, ""

#     def huggingface_call(self, prompt, topic, max_length=120):
#         """Make API call to Hugging Face with topic context"""
#         headers = {"Authorization": f"Bearer {self.config.HUGGINGFACE_API_KEY}"}
        
#         # Add topic context to prompt
#         enhanced_prompt = f"Create an informative {topic} update about: {prompt}. Include technical details and significance."
        
#         payload = {
#             "inputs": enhanced_prompt,
#             "parameters": {
#                 "max_length": max_length,
#                 "temperature": 0.8,
#                 "top_p": 0.95,
#                 "do_sample": True
#             }
#         }
        
#         try:
#             response = requests.post(
#                 self.config.HUGGINGFACE_API_URL,
#                 headers=headers,
#                 json=payload,
#                 timeout=10
#             )
#             response.raise_for_status()
#             return response.json()[0].get("generated_text", "")
#         except Exception as e:
#             logging.error(f"Hugging Face API error: {str(e)}")
#             return ""

# class TwitterBot:
#     def __init__(self, config):
#         self.config = config
#         self.api_handler = APIHandler(config)
#         self.content_generator = ContentGenerator()
#         self.setup_twitter_clients()
        
#         self.daily_tweet_count = 0
#         self.daily_mention_check_count = 0
#         self.daily_huggingface_calls = 0
#         self.last_reset = datetime.now(timezone.utc)

#     def setup_twitter_clients(self):
#         """Initialize Twitter API clients"""
#         try:
#             self.client = tweepy.Client(
#                 bearer_token=self.config.TWITTER_BEARER_TOKEN,
#                 consumer_key=self.config.TWITTER_API_KEY,
#                 consumer_secret=self.config.TWITTER_API_SECRET,
#                 access_token=self.config.TWITTER_ACCESS_TOKEN,
#                 access_token_secret=self.config.TWITTER_ACCESS_TOKEN_SECRET,
#                 wait_on_rate_limit=True
#             )
#             self.twitter_me_id = self.client.get_me()[0].id
#             logging.info("Twitter API clients initialized successfully")
#         except Exception as e:
#             logging.error(f"Failed to initialize Twitter API: {str(e)}")
#             raise

#     def reset_counters(self):
#         """Reset daily counters if it's a new day"""
#         current_time = datetime.now(timezone.utc)
#         if (current_time - self.last_reset).days >= 1:
#             self.daily_tweet_count = 0
#             self.daily_mention_check_count = 0
#             self.daily_huggingface_calls = 0
#             self.last_reset = current_time
#             logging.info("Daily counters reset")

#     def can_make_huggingface_call(self):
#         """Check if we can make another Hugging Face API call"""
#         return self.daily_huggingface_calls < self.config.HUGGINGFACE_CALLS_PER_DAY

#     def generate_fallback_content(self):
#         """Generate thought-provoking content when no news is available"""
#         topic = random.choice(list(self.content_generator.PRIORITY_TOPICS.keys()))
#         prompt, insight = self.content_generator.get_fallback_prompt(topic)
#         tweet_text = self.api_handler.huggingface_call(insight, topic)
#         tweet_text = self.content_generator.clean_content(tweet_text)
#         return tweet_text, topic

#     def post_tweet(self):
#         """Post a tweet with fallback to generated content"""
#         self.reset_counters()
        
#         if self.daily_tweet_count >= self.config.TWITTER_POSTS_PER_DAY:
#             logging.info("Daily tweet limit reached")
#             return

#         if not self.can_make_huggingface_call():
#             logging.info("Daily Hugging Face API limit reached")
#             return

#         try:
#             news, topic, description = self.api_handler.news_api_call()
            
#             if news and topic:
#                 # Process news content with description for context
#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.TWEET_PROMPTS,
#                     topic=topic
#                 ).format(news=f"{news}. {description}")
                
#                 tweet_text = self.api_handler.huggingface_call(prompt, topic)
                
#             else:
#                 # Generate fallback content
#                 logging.info("No relevant tech news found, generating thought-provoking content")
#                 tweet_text, topic = self.generate_fallback_content()
            
#             tweet_text = self.content_generator.clean_content(tweet_text)
            
#             # Validate tweet content
#             if not self.content_generator.validate_content(tweet_text):
#                 logging.warning("Generated content failed validation, trying fallback")
#                 tweet_text, topic = self.generate_fallback_content()
#                 tweet_text = self.content_generator.clean_content(tweet_text)
                
#                 # If fallback also fails validation, abort
#                 if not self.content_generator.validate_content(tweet_text):
#                     logging.error("Failed to generate valid content")
#                     return

#             # Add relevant hashtags based on topic
#             hashtags = f" #{topic}" if topic else ""
#             final_tweet = f"{tweet_text}{hashtags}"

#             # Check if tweet is unique
#             if final_tweet in self.api_handler.posted_tweets:
#                 logging.info("Tweet content already posted, skipping")
#                 return

#             try:
#                 # Post tweet
#                 response = self.client.create_tweet(text=final_tweet)
#                 if response.data:
#                     self.api_handler.save_tweet(final_tweet)
#                     self.daily_tweet_count += 1
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Tweet posted successfully: {final_tweet}")
#                 else:
#                     logging.error("Failed to post tweet: No response data")
#             except Exception as e:
#                 logging.error(f"Error posting tweet: {str(e)}")
#         except Exception as e:
#             logging.error(f"Error in post_tweet: {str(e)}")

#     def check_mentions(self):
#         """Check and respond to mentions"""
#         self.reset_counters()
        
#         if self.daily_mention_check_count >= self.config.TWITTER_READS_PER_DAY:
#             logging.info("Daily mention check limit reached")
#             return

#         if not self.can_make_huggingface_call():
#             logging.info("Daily Hugging Face API limit reached")
#             return

#         try:
#             # Get mentions timeline
#             mentions = self.client.get_users_mentions(
#                 self.twitter_me_id,
#                 max_results=self.config.MAX_MENTIONS_PER_CHECK
#             )

#             if not mentions.data:
#                 logging.info("No new mentions found")
#                 return

#             for mention in mentions.data:
#                 # Skip if already processed
#                 if mention.text in self.api_handler.posted_tweets:
#                     continue

#                 # Identify topic from mention
#                 is_valid_topic, topic = self.content_generator.identify_primary_topic(mention.text)
                
#                 if not is_valid_topic:
#                     topic = "tech"  # Default to general tech if no specific topic identified

#                 # Generate response
#                 prompt = self.content_generator.get_random_prompt(
#                     self.content_generator.REPLY_PROMPTS,
#                     topic=topic
#                 ).format(tweet=mention.text)

#                 response_text = self.api_handler.huggingface_call(prompt, topic)
#                 response_text = self.content_generator.clean_content(response_text)

#                 if not self.content_generator.validate_content(response_text):
#                     logging.warning(f"Generated response failed validation for mention {mention.id}")
#                     continue

#                 try:
#                     # Reply to mention
#                     self.client.create_tweet(
#                         text=response_text,
#                         in_reply_to_tweet_id=mention.id
#                     )
#                     self.api_handler.save_tweet(response_text)
#                     self.daily_huggingface_calls += 1
#                     logging.info(f"Replied to mention {mention.id}: {response_text}")
#                 except Exception as e:
#                     logging.error(f"Error replying to mention {mention.id}: {str(e)}")

#             self.daily_mention_check_count += 1

#         except Exception as e:
#             logging.error(f"Error checking mentions: {str(e)}")


# #####################
# # Flask Web Server for Self-Ping
# #####################
# app = Flask(__name__)

# @app.route("/ping", methods=["GET"])
# def ping():
#     return jsonify({"status": "alive"}), 200

# def start_flask():
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)

# def self_ping():
#     """Continuously ping the /ping endpoint every 2 minutes."""
#     port = os.environ.get("PORT", "5000")
#     # Use environment variable SELF_PING_URL if set; otherwise default to localhost
#     url = os.environ.get("SELF_PING_URL", f"http://localhost:{port}/ping")
#     while True:
#         try:
#             response = requests.get(url, timeout=10)
#             if response.status_code == 200:
#                 logging.info("Self-ping successful.")
#             else:
#                 logging.info(f"Self-ping returned status {response.status_code}.")
#         except Exception as e:
#             logging.error(f"Self-ping error: {str(e)}")
#         time.sleep(120)  # wait 2 minutes

# def main():
#     """Main function to run the Twitter bot"""
#     # Initialize config and bot
#     config = Config()
#     setup_logging()
    
#     try:
#         bot = TwitterBot(config)
#         logging.info("Twitter bot initialized successfully")

#         # Schedule tasks
#         schedule.every(6).hours.do(bot.post_tweet)
#         schedule.every(6).hours.do(bot.check_mentions)

#         # Run continuously
#         while True:
#             schedule.run_pending()
#             time.sleep(60)

#     except Exception as e:
#         logging.error(f"Fatal error: {str(e)}")
#         raise

# if __name__ == "__main__":
#     # Start Flask server in a background thread to expose /ping endpoint.
#     flask_thread = threading.Thread(target=start_flask, daemon=True)
#     flask_thread.start()
#     # Start self-ping thread to keep the app awake.
#     ping_thread = threading.Thread(target=self_ping, daemon=True)
#     ping_thread.start()
#     # Run the main Twitter bot loop.
#     main()













import os
import tweepy
import requests
import pytz
from datetime import datetime, timezone, timedelta
import schedule
import time
import logging
import random
from dotenv import load_dotenv

def setup_logging():
    """Configure logging with both file and console handlers"""
    logging.basicConfig(
        filename='bot.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

class Config:
    """Configuration class to manage settings"""
    def __init__(self):
        load_dotenv()
        
        # API Keys
        self.TWITTER_API_KEY = os.getenv("TW_API_KEY")
        self.TWITTER_API_SECRET = os.getenv("TW_API_KEY_SECRET")
        self.TWITTER_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
        self.TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TW_ACCESS_TOKEN_SECRET")
        self.TWITTER_BEARER_TOKEN = os.getenv("TW_BEARER_TOKEN")
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")
        self.HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
        
        # Settings
        self.POSTS_PER_DAY = 4
        self.MEMORY_FILE = "posted_tweets.txt"
        self.LAST_POST_FILE = "last_post.txt"
        self.TIMEZONE = pytz.timezone('Asia/Kolkata')
        self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
        self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

class TweetGenerator:
    """Class to handle tweet generation"""
    
    # Define topics and their related keywords
    TOPICS = {
        'blockchain': ['blockchain', 'web3', 'defi', 'smart contract', 'distributed ledger'],
        'cryptocurrency': ['cryptocurrency', 'crypto', 'digital currency', 'token', 'coin'],
        'bitcoin': ['bitcoin', 'btc', 'lightning network', 'satoshi'],
        'ai': ['artificial intelligence', 'ai', 'machine learning', 'deep learning', 'neural network', 'llm'],
        'tech': ['technology', 'tech', 'innovation', 'digital transformation']
    }

    # Prompts for generating tweets from news
    NEWS_PROMPTS = [
        "Write a technical analysis of this {topic} development: {news}",
        "Explain the significance of this {topic} news: {news}",
        "Break down this important {topic} update: {news}",
        "Analyze the implications of this {topic} news: {news}",
        "What does this {topic} development mean for the industry: {news}"
    ]

    # Prompts for generating tweets from trends
    TREND_PROMPTS = [
        "Share insights about the latest developments in {topic}",
        "Analyze current trends in {topic} technology",
        "Explain how {topic} is transforming the industry",
        "Discuss the future implications of {topic} advancement",
        "Highlight key innovations in {topic} development"
    ]

    # Topic-specific insights for fallback content
    FALLBACK_INSIGHTS = {
        'blockchain': [
            "Blockchain technology revolutionizes data security through decentralized ledgers, enabling trustless transactions and smart contract automation.",
            "The evolution of blockchain networks introduces new consensus mechanisms and scaling solutions, improving efficiency and adoption.",
            "Enterprise blockchain solutions transform supply chain management and cross-border transactions, reducing costs and increasing transparency.",
            "Smart contracts on blockchain networks automate complex processes, reducing intermediaries and increasing efficiency.",
            "Blockchain interoperability protocols enable seamless communication between different networks, expanding use cases."
        ],
        'cryptocurrency': [
            "Cryptocurrency adoption drives financial innovation through decentralized finance protocols and digital asset management.",
            "Digital currencies reshape traditional banking through instant, borderless transactions and programmable money features.",
            "The cryptocurrency ecosystem expands with layer-2 scaling solutions and interoperability protocols.",
            "Decentralized finance protocols create new possibilities for lending, borrowing, and trading digital assets.",
            "Stablecoins bridge traditional finance with crypto markets, enabling efficient cross-border transactions."
        ],
        'bitcoin': [
            "Bitcoin's Lightning Network enables instant micropayments and scales transaction capabilities while maintaining decentralization.",
            "Institutional Bitcoin adoption increases as corporations recognize its potential as a digital store of value.",
            "Bitcoin mining evolution focuses on renewable energy sources and efficiency improvements.",
            "Layer-2 scaling solutions enhance Bitcoin's transaction capacity while preserving security.",
            "Bitcoin's role as digital gold grows with increasing institutional investment and adoption."
        ],
        'ai': [
            "Advanced AI models demonstrate unprecedented natural language understanding and generation capabilities.",
            "Machine learning systems revolutionize healthcare through improved diagnosis and treatment recommendations.",
            "AI development in autonomous systems creates new possibilities for automation and human augmentation.",
            "Transformer models push the boundaries of language understanding and generation in AI applications.",
            "AI-powered tools enhance productivity across industries through automation and intelligent assistance."
        ],
        'tech': [
            "Quantum computing advances promise to revolutionize cryptography and complex problem-solving.",
            "Edge computing and 5G networks enable new real-time applications and improved IoT device performance.",
            "Open-source technology development accelerates innovation and collaboration in software.",
            "Cloud computing evolution enables more efficient and scalable business operations.",
            "Digital transformation accelerates with adoption of AI, blockchain, and IoT technologies."
        ]
    }

class TwitterBot:
    def __init__(self):
        self.config = Config()
        self.timezone = self.config.TIMEZONE
        self.generator = TweetGenerator()
        self.posted_tweets = self.load_posted_tweets()
        self.daily_post_count = 0
        self.last_reset = datetime.now(timezone.utc)
        self.last_post_time = self.load_last_post_time()
        self.next_post_time = None
        self.setup_twitter_client()
        self.log_post_status()

    def load_posted_tweets(self):
        """Load previously posted tweets from file"""
        try:
            with open(self.config.MEMORY_FILE, "r") as f:
                return set(line.strip() for line in f)
        except FileNotFoundError:
            open(self.config.MEMORY_FILE, "a").close()
            return set()

    def save_tweet(self, tweet_content):
        """Save tweet to memory file"""
        try:
            with open(self.config.MEMORY_FILE, "a") as f:
                f.write(f"{tweet_content}\n")
            self.posted_tweets.add(tweet_content)
            logging.info(f"Tweet saved to memory: {tweet_content[:50]}...")
        except Exception as e:
            logging.error(f"Error saving tweet: {e}")

    def load_last_post_time(self):
        """Load the last post time from file"""
        try:
            with open(self.config.LAST_POST_FILE, "r") as f:
                timestamp = f.read().strip()
                utc_time = datetime.fromtimestamp(float(timestamp), timezone.utc)
                return utc_time.astimezone(self.timezone)
        except (FileNotFoundError, ValueError):
            return None

    def save_last_post_time(self):
        """Save the current time as last post time"""
        current_time = datetime.now(self.timezone)
        try:
            with open(self.config.LAST_POST_FILE, "w") as f:
                f.write(str(current_time.timestamp()))
            self.last_post_time = current_time
            self.calculate_next_post_time()
        except Exception as e:
            logging.error(f"Error saving last post time: {e}")

    def calculate_next_post_time(self):
        """Calculate the next scheduled post time"""
        if self.last_post_time:
            self.next_post_time = self.last_post_time + timedelta(hours=6)
            logging.info(f"Next post scheduled for: {self.next_post_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    def log_post_status(self):
        """Log the current posting status"""
        current_time = datetime.now(self.timezone)
        logging.info("----- Current Bot Status -----")
        logging.info(f"Current time (IST): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logging.info(f"Posts made today: {self.daily_post_count}/{self.config.POSTS_PER_DAY}")
        
        if self.last_post_time:
            time_since_last = current_time - self.last_post_time
            hours_since_last = time_since_last.total_seconds() / 3600
            logging.info(f"Last post: {self.last_post_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({hours_since_last:.1f} hours ago)")
        else:
            logging.info("No posts made yet")
            
        if self.next_post_time:
            if current_time < self.next_post_time:
                time_until_next = self.next_post_time - current_time
                hours_until_next = time_until_next.total_seconds() / 3600
                logging.info(f"Next post in: {hours_until_next:.1f} hours")
            else:
                logging.info("Next post is due now")
        logging.info("-----------------------------")

    def setup_twitter_client(self):
        """Initialize Twitter API client"""
        try:
            self.client = tweepy.Client(
                bearer_token=self.config.TWITTER_BEARER_TOKEN,
                consumer_key=self.config.TWITTER_API_KEY,
                consumer_secret=self.config.TWITTER_API_SECRET,
                access_token=self.config.TWITTER_ACCESS_TOKEN,
                access_token_secret=self.config.TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
            logging.info("Twitter API client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Twitter API: {str(e)}")
            raise

    def get_news(self):
        """Get news from News API"""
        params = {
            "category": "technology",
            "language": "en",
            "apiKey": self.config.NEWS_API_KEY,
            "pageSize": 10,
            "q": "blockchain OR cryptocurrency OR bitcoin OR AI OR artificial intelligence"
        }
        
        try:
            response = requests.get(
                self.config.NEWS_API_URL, 
                params=params,
                timeout=10
            )
            response.raise_for_status()
            articles = response.json().get("articles", [])
            
            for article in articles:
                title = article.get('title', '').split(' - ')[0].strip()
                if title and title not in self.posted_tweets:
                    for topic, keywords in self.generator.TOPICS.items():
                        if any(keyword in title.lower() for keyword in keywords):
                            return title, topic
                            
            return None, None
            
        except Exception as e:
            logging.error(f"News API error: {str(e)}")
            return None, None

    def generate_tweet(self, prompt, topic):
        """Generate tweet using Hugging Face API"""
        headers = {"Authorization": f"Bearer {self.config.HUGGINGFACE_API_KEY}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 100, "temperature": 0.7}
        }
        
        try:
            response = requests.post(
                self.config.HUGGINGFACE_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()[0].get("generated_text", "")
        except Exception as e:
            logging.error(f"Hugging Face API error: {str(e)}")
            return ""

    def validate_tweet(self, text):
        """Validate tweet content"""
        if not text:
            return False
        words = text.split()
        return 10 <= len(words) <= 50

    def reset_daily_count(self):
        """Reset daily post count if it's a new day"""
        current_time = datetime.now(timezone.utc)
        if (current_time - self.last_reset).days >= 1:
            self.daily_post_count = 0
            self.last_reset = current_time
            logging.info("Daily post count reset")

    def post_tweet(self):
        """Post a tweet"""
        self.log_post_status()
        self.reset_daily_count()
        
        if self.daily_post_count >= self.config.POSTS_PER_DAY:
            logging.info("Daily post limit reached")
            return

        try:
            logging.info("Attempting to post new tweet...")
            news, topic = self.get_news()
            
            if news and topic:
                logging.info(f"Using news content - Topic: {topic}")
                prompt = random.choice(self.generator.NEWS_PROMPTS).format(
                    topic=topic,
                    news=news
                )
                tweet_text = self.generate_tweet(prompt, topic)
            else:
                logging.info("No news found, using fallback content")
                topic = random.choice(list(self.generator.TOPICS.keys()))
                insight = random.choice(self.generator.FALLBACK_INSIGHTS[topic])
                prompt = random.choice(self.generator.TREND_PROMPTS).format(topic=topic)
                tweet_text = self.generate_tweet(insight, topic)

            if not self.validate_tweet(tweet_text):
                logging.warning("Generated content failed validation")
                return

            tweet_text = f"{tweet_text} #{topic}"

            if tweet_text in self.posted_tweets:
                logging.info("Tweet content already posted")
                return

            response = self.client.create_tweet(text=tweet_text)
            if response.data:
                self.save_tweet(tweet_text)
                self.save_last_post_time()
                self.daily_post_count += 1
                logging.info(f"Tweet posted successfully: {tweet_text}")
                self.log_post_status()
            
        except Exception as e:
            logging.error(f"Error posting tweet: {str(e)}")

# def main():
#     """Main function to run the Twitter bot"""
#     setup_logging()
#     logging.info("Starting Twitter bot")
    
#     try:
#         bot = TwitterBot()
        
#         # Schedule 4 posts per day (every 6 hours)
#         schedule.every(6).hours.do(bot.post_tweet)
        
#         # Log initial schedule
#         next_run = schedule.next_run()
#         if next_run:
#             logging.info(f"First post scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
#         while True:
#             schedule.run_pending()
#             time.sleep(60)
            
#     except Exception as e:
#         logging.error(f"Fatal error: {str(e)}")
#         raise

def main():
    """Main function to run the Twitter bot"""
    setup_logging()
    logging.info("Starting Twitter bot")
    
    try:
        bot = TwitterBot()
        
        # Define posting times in 24-hour format
        posting_times = ["09:00", "15:00", "21:00", "03:00"]
        
        # Get current time in IST
        current_time = datetime.now(bot.timezone)
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Schedule posts based on current time
        for post_time in posting_times:
            hour, minute = map(int, post_time.split(':'))
            
            # If this time has already passed today, schedule for tomorrow
            if (hour < current_hour) or (hour == current_hour and minute <= current_minute):
                schedule.every().day.at(post_time).do(bot.post_tweet)
                logging.info(f"Scheduled for tomorrow at {post_time}")
            else:
                schedule.every().day.at(post_time).do(bot.post_tweet)
                logging.info(f"Scheduled for today at {post_time}")
        
        # Log next scheduled run
        next_run = schedule.next_run()
        if next_run:
            ist_time = bot.timezone.localize(next_run)
            logging.info(f"Next post scheduled for: {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()