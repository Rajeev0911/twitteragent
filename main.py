# import os
# import tweepy
# import requests
# import pytz
# from datetime import datetime, timezone, timedelta
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
#     """Configuration class to manage settings"""
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
        
#         # Settings
#         self.POSTS_PER_DAY = 4
#         self.MEMORY_FILE = "posted_tweets.txt"
#         self.LAST_POST_FILE = "last_post.txt"
#         self.TIMEZONE = pytz.timezone('Asia/Kolkata')
#         self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
#         self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

# class TweetGenerator:
#     """Class to handle tweet generation"""
    
#     # Define topics and their related keywords
#     TOPICS = {
#         'blockchain': ['blockchain', 'web3', 'defi', 'smart contract', 'distributed ledger'],
#         'cryptocurrency': ['cryptocurrency', 'crypto', 'digital currency', 'token', 'coin'],
#         'bitcoin': ['bitcoin', 'btc', 'lightning network', 'satoshi'],
#         'ai': ['artificial intelligence', 'ai', 'machine learning', 'deep learning', 'neural network', 'llm'],
#         'tech': ['technology', 'tech', 'innovation', 'digital transformation']
#     }

#     # Prompts for generating tweets from news
#     NEWS_PROMPTS = [
#         "Write a technical analysis of this {topic} development: {news}",
#         "Explain the significance of this {topic} news: {news}",
#         "Break down this important {topic} update: {news}",
#         "Analyze the implications of this {topic} news: {news}",
#         "What does this {topic} development mean for the industry: {news}"
#     ]

#     # Prompts for generating tweets from trends
#     TREND_PROMPTS = [
#         "Share insights about the latest developments in {topic}",
#         "Analyze current trends in {topic} technology",
#         "Explain how {topic} is transforming the industry",
#         "Discuss the future implications of {topic} advancement",
#         "Highlight key innovations in {topic} development"
#     ]

#     # Topic-specific insights for fallback content
#     FALLBACK_INSIGHTS = {
#         'blockchain': [
#             "Blockchain technology revolutionizes data security through decentralized ledgers, enabling trustless transactions and smart contract automation.",
#             "The evolution of blockchain networks introduces new consensus mechanisms and scaling solutions, improving efficiency and adoption.",
#             "Enterprise blockchain solutions transform supply chain management and cross-border transactions, reducing costs and increasing transparency.",
#             "Smart contracts on blockchain networks automate complex processes, reducing intermediaries and increasing efficiency.",
#             "Blockchain interoperability protocols enable seamless communication between different networks, expanding use cases."
#         ],
#         'cryptocurrency': [
#             "Cryptocurrency adoption drives financial innovation through decentralized finance protocols and digital asset management.",
#             "Digital currencies reshape traditional banking through instant, borderless transactions and programmable money features.",
#             "The cryptocurrency ecosystem expands with layer-2 scaling solutions and interoperability protocols.",
#             "Decentralized finance protocols create new possibilities for lending, borrowing, and trading digital assets.",
#             "Stablecoins bridge traditional finance with crypto markets, enabling efficient cross-border transactions."
#         ],
#         'bitcoin': [
#             "Bitcoin's Lightning Network enables instant micropayments and scales transaction capabilities while maintaining decentralization.",
#             "Institutional Bitcoin adoption increases as corporations recognize its potential as a digital store of value.",
#             "Bitcoin mining evolution focuses on renewable energy sources and efficiency improvements.",
#             "Layer-2 scaling solutions enhance Bitcoin's transaction capacity while preserving security.",
#             "Bitcoin's role as digital gold grows with increasing institutional investment and adoption."
#         ],
#         'ai': [
#             "Advanced AI models demonstrate unprecedented natural language understanding and generation capabilities.",
#             "Machine learning systems revolutionize healthcare through improved diagnosis and treatment recommendations.",
#             "AI development in autonomous systems creates new possibilities for automation and human augmentation.",
#             "Transformer models push the boundaries of language understanding and generation in AI applications.",
#             "AI-powered tools enhance productivity across industries through automation and intelligent assistance."
#         ],
#         'tech': [
#             "Quantum computing advances promise to revolutionize cryptography and complex problem-solving.",
#             "Edge computing and 5G networks enable new real-time applications and improved IoT device performance.",
#             "Open-source technology development accelerates innovation and collaboration in software.",
#             "Cloud computing evolution enables more efficient and scalable business operations.",
#             "Digital transformation accelerates with adoption of AI, blockchain, and IoT technologies."
#         ]
#     }

# class TwitterBot:
#     def __init__(self):
#         self.config = Config()
#         self.timezone = self.config.TIMEZONE
#         self.generator = TweetGenerator()
#         self.posted_tweets = self.load_posted_tweets()
#         self.daily_post_count = 0
#         self.last_reset = datetime.now(timezone.utc)
#         self.last_post_time = self.load_last_post_time()
#         self.next_post_time = None
#         self.setup_twitter_client()
#         self.log_post_status()

#     def load_posted_tweets(self):
#         """Load previously posted tweets from file"""
#         try:
#             with open(self.config.MEMORY_FILE, "r") as f:
#                 return set(line.strip() for line in f)
#         except FileNotFoundError:
#             open(self.config.MEMORY_FILE, "a").close()
#             return set()

#     def save_tweet(self, tweet_content):
#         """Save tweet to memory file"""
#         try:
#             with open(self.config.MEMORY_FILE, "a") as f:
#                 f.write(f"{tweet_content}\n")
#             self.posted_tweets.add(tweet_content)
#             logging.info(f"Tweet saved to memory: {tweet_content[:50]}...")
#         except Exception as e:
#             logging.error(f"Error saving tweet: {e}")

#     def load_last_post_time(self):
#         """Load the last post time from file"""
#         try:
#             with open(self.config.LAST_POST_FILE, "r") as f:
#                 timestamp = f.read().strip()
#                 utc_time = datetime.fromtimestamp(float(timestamp), timezone.utc)
#                 return utc_time.astimezone(self.timezone)
#         except (FileNotFoundError, ValueError):
#             return None

#     def save_last_post_time(self):
#         """Save the current time as last post time"""
#         current_time = datetime.now(self.timezone)
#         try:
#             with open(self.config.LAST_POST_FILE, "w") as f:
#                 f.write(str(current_time.timestamp()))
#             self.last_post_time = current_time
#             self.calculate_next_post_time()
#         except Exception as e:
#             logging.error(f"Error saving last post time: {e}")

#     def calculate_next_post_time(self):
#         """Calculate the next scheduled post time"""
#         if self.last_post_time:
#             self.next_post_time = self.last_post_time + timedelta(hours=6)
#             logging.info(f"Next post scheduled for: {self.next_post_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

#     def log_post_status(self):
#         """Log the current posting status"""
#         current_time = datetime.now(self.timezone)
#         logging.info("----- Current Bot Status -----")
#         logging.info(f"Current time (IST): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
#         logging.info(f"Posts made today: {self.daily_post_count}/{self.config.POSTS_PER_DAY}")
        
#         if self.last_post_time:
#             time_since_last = current_time - self.last_post_time
#             hours_since_last = time_since_last.total_seconds() / 3600
#             logging.info(f"Last post: {self.last_post_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({hours_since_last:.1f} hours ago)")
#         else:
#             logging.info("No posts made yet")
            
#         if self.next_post_time:
#             if current_time < self.next_post_time:
#                 time_until_next = self.next_post_time - current_time
#                 hours_until_next = time_until_next.total_seconds() / 3600
#                 logging.info(f"Next post in: {hours_until_next:.1f} hours")
#             else:
#                 logging.info("Next post is due now")
#         logging.info("-----------------------------")

#     def setup_twitter_client(self):
#         """Initialize Twitter API client"""
#         try:
#             self.client = tweepy.Client(
#                 bearer_token=self.config.TWITTER_BEARER_TOKEN,
#                 consumer_key=self.config.TWITTER_API_KEY,
#                 consumer_secret=self.config.TWITTER_API_SECRET,
#                 access_token=self.config.TWITTER_ACCESS_TOKEN,
#                 access_token_secret=self.config.TWITTER_ACCESS_TOKEN_SECRET,
#                 wait_on_rate_limit=True
#             )
#             logging.info("Twitter API client initialized successfully")
#         except Exception as e:
#             logging.error(f"Failed to initialize Twitter API: {str(e)}")
#             raise

#     def get_news(self):
#         """Get news from News API"""
#         params = {
#             "category": "technology",
#             "language": "en",
#             "apiKey": self.config.NEWS_API_KEY,
#             "pageSize": 10,
#             "q": "blockchain OR cryptocurrency OR bitcoin OR AI OR artificial intelligence"
#         }
        
#         try:
#             response = requests.get(
#                 self.config.NEWS_API_URL, 
#                 params=params,
#                 timeout=10
#             )
#             response.raise_for_status()
#             articles = response.json().get("articles", [])
            
#             for article in articles:
#                 title = article.get('title', '').split(' - ')[0].strip()
#                 if title and title not in self.posted_tweets:
#                     for topic, keywords in self.generator.TOPICS.items():
#                         if any(keyword in title.lower() for keyword in keywords):
#                             return title, topic
                            
#             return None, None
            
#         except Exception as e:
#             logging.error(f"News API error: {str(e)}")
#             return None, None

#     def generate_tweet(self, prompt, topic):
#         """Generate tweet using Hugging Face API"""
#         headers = {"Authorization": f"Bearer {self.config.HUGGINGFACE_API_KEY}"}
#         payload = {
#             "inputs": prompt,
#             "parameters": {"max_length": 100, "temperature": 0.7}
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

#     def validate_tweet(self, text):
#         """Validate tweet content"""
#         if not text:
#             return False
#         words = text.split()
#         return 10 <= len(words) <= 50

#     def reset_daily_count(self):
#         """Reset daily post count if it's a new day"""
#         current_time = datetime.now(timezone.utc)
#         if (current_time - self.last_reset).days >= 1:
#             self.daily_post_count = 0
#             self.last_reset = current_time
#             logging.info("Daily post count reset")

#     def post_tweet(self):
#         """Post a tweet"""
#         self.log_post_status()
#         self.reset_daily_count()
        
#         if self.daily_post_count >= self.config.POSTS_PER_DAY:
#             logging.info("Daily post limit reached")
#             return

#         try:
#             logging.info("Attempting to post new tweet...")
#             news, topic = self.get_news()
            
#             if news and topic:
#                 logging.info(f"Using news content - Topic: {topic}")
#                 prompt = random.choice(self.generator.NEWS_PROMPTS).format(
#                     topic=topic,
#                     news=news
#                 )
#                 tweet_text = self.generate_tweet(prompt, topic)
#             else:
#                 logging.info("No news found, using fallback content")
#                 topic = random.choice(list(self.generator.TOPICS.keys()))
#                 insight = random.choice(self.generator.FALLBACK_INSIGHTS[topic])
#                 prompt = random.choice(self.generator.TREND_PROMPTS).format(topic=topic)
#                 tweet_text = self.generate_tweet(insight, topic)

#             if not self.validate_tweet(tweet_text):
#                 logging.warning("Generated content failed validation")
#                 return

#             tweet_text = f"{tweet_text} #{topic}"

#             if tweet_text in self.posted_tweets:
#                 logging.info("Tweet content already posted")
#                 return

#             response = self.client.create_tweet(text=tweet_text)
#             if response.data:
#                 self.save_tweet(tweet_text)
#                 self.save_last_post_time()
#                 self.daily_post_count += 1
#                 logging.info(f"Tweet posted successfully: {tweet_text}")
#                 self.log_post_status()
            
#         except Exception as e:
#             logging.error(f"Error posting tweet: {str(e)}")

# # def main():
# #     """Main function to run the Twitter bot"""
# #     setup_logging()
# #     logging.info("Starting Twitter bot")
    
# #     try:
# #         bot = TwitterBot()
        
# #         # Schedule 4 posts per day (every 6 hours)
# #         schedule.every(6).hours.do(bot.post_tweet)
        
# #         # Log initial schedule
# #         next_run = schedule.next_run()
# #         if next_run:
# #             logging.info(f"First post scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
# #         while True:
# #             schedule.run_pending()
# #             time.sleep(60)
            
# #     except Exception as e:
# #         logging.error(f"Fatal error: {str(e)}")
# #         raise

# def main():
#     """Main function to run the Twitter bot"""
#     setup_logging()
#     logging.info("Starting Twitter bot")
    
#     try:
#         bot = TwitterBot()
        
#         # Define posting times in 24-hour format
#         posting_times = ["09:00", "15:00", "21:00", "03:00"]
        
#         # Get current time in IST
#         current_time = datetime.now(bot.timezone)
#         current_hour = current_time.hour
#         current_minute = current_time.minute
        
#         # Schedule posts based on current time
#         for post_time in posting_times:
#             hour, minute = map(int, post_time.split(':'))
            
#             # If this time has already passed today, schedule for tomorrow
#             if (hour < current_hour) or (hour == current_hour and minute <= current_minute):
#                 schedule.every().day.at(post_time).do(bot.post_tweet)
#                 logging.info(f"Scheduled for tomorrow at {post_time}")
#             else:
#                 schedule.every().day.at(post_time).do(bot.post_tweet)
#                 logging.info(f"Scheduled for today at {post_time}")
        
#         # Log next scheduled run
#         next_run = schedule.next_run()
#         if next_run:
#             ist_time = bot.timezone.localize(next_run)
#             logging.info(f"Next post scheduled for: {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
#         while True:
#             schedule.run_pending()
#             time.sleep(60)
            
#     except Exception as e:
#         logging.error(f"Fatal error: {str(e)}")
#         raise

# if __name__ == "__main__":
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
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

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
        self.GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
        
        # Validate required environment variables
        self._validate_env_vars()
        
        # Initialize Google AI with retry mechanism
        self._init_google_ai()
        
        # Settings
        self.POSTS_PER_DAY = 4
        self.MEMORY_FILE = "posted_tweets.txt"
        self.LAST_POST_FILE = "last_post.txt"
        self.TIMEZONE = pytz.timezone('Asia/Kolkata')
        self.NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
        
    def _validate_env_vars(self):
        """Validate that all required environment variables are present"""
        required_vars = [
            "TW_API_KEY", "TW_API_KEY_SECRET", "TW_ACCESS_TOKEN",
            "TW_ACCESS_TOKEN_SECRET", "TW_BEARER_TOKEN",
            "NEWS_API_KEY", "GOOGLE_AI_API_KEY"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _init_google_ai(self):
        """Initialize Google AI with retry mechanism"""
        try:
            genai.configure(api_key=self.GOOGLE_AI_API_KEY)
            self.generation_config = {
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 40,
                "max_output_tokens": 100,
            }
            self.model = genai.GenerativeModel(
                model_name="gemini-pro",
                generation_config=self.generation_config
            )
        except Exception as e:
            logging.error(f"Failed to initialize Google AI: {str(e)}")
            raise

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
        "Write a technical analysis of this {topic} development in about 200 characters: {news}",
        "Explain the significance of this {topic} news in about 200 characters: {news}",
        "Break down this important {topic} update in about 200 characters: {news}",
        "Analyze the implications of this {topic} news in about 200 characters: {news}",
        "What does this {topic} development mean for the industry (respond in about 200 characters): {news}"
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
            with open(self.config.MEMORY_FILE, "r", encoding='utf-8') as f:
                return set(line.strip() for line in f)
        except FileNotFoundError:
            open(self.config.MEMORY_FILE, "a").close()
            return set()

    def save_tweet(self, tweet_content):
        """Save tweet to memory file"""
        try:
            with open(self.config.MEMORY_FILE, "a", encoding='utf-8') as f:
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def setup_twitter_client(self):
        """Initialize Twitter API client with retry mechanism"""
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_news(self):
        """Get news from News API with retry mechanism"""
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_tweet(self, prompt, topic):
        """Generate tweet using Google AI Studio with retry mechanism"""
        try:
            response = self.config.model.generate_content(prompt)
            
            if response.text:
                tweet_text = response.text.strip().strip('"\'')
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                return tweet_text
            return ""
            
        except Exception as e:
            logging.error(f"Google AI API error: {str(e)}")
            # Fall back to pre-written content if AI generation fails
            return random.choice(self.generator.FALLBACK_INSIGHTS[topic])

    def validate_tweet(self, text):
        """Validate tweet content"""
        if not text:
            return False
        words = text.split()
        return 10 <= len(words) <= 50 and len(text) <= 280

    def reset_daily_count(self):
        """Reset daily post count if it's a new day"""
        current_time = datetime.now(timezone.utc)
        if (current_time - self.last_reset).days >= 1:
            self.daily_post_count = 0
            self.last_reset = current_time
            logging.info("Daily post count reset")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _post_tweet_with_retry(self, tweet_text):
        """Post tweet with retry mechanism"""
        response = self.client.create_tweet(text=tweet_text)
        if response.data:
            self.save_tweet(tweet_text)
            self.save_last_post_time()
            self.daily_post_count += 1
            logging.info(f"Tweet posted successfully: {tweet_text}")
            self.log_post_status()

    def post_tweet(self):
        """Post a tweet with improved error handling"""
        try:
            self.log_post_status()
            self.reset_daily_count()
            
            if self.daily_post_count >= self.config.POSTS_PER_DAY:
                logging.info("Daily post limit reached")
                return

            logging.info("Attempting to post new tweet...")
            
            # Try to get news first
            news, topic = self.get_news()
            
            # If news fetching fails or no relevant news found, use fallback content
            if news and topic:
                logging.info(f"Using news content - Topic: {topic}")
                prompt = random.choice(self.generator.NEWS_PROMPTS).format(
                    topic=topic,
                    news=news
                )
                tweet_text = self.generate_tweet(prompt, topic)
            else:
                logging.info("Using fallback content")
                topic = random.choice(list(self.generator.TOPICS.keys()))
                tweet_text = random.choice(self.generator.FALLBACK_INSIGHTS[topic])

            if not self.validate_tweet(tweet_text):
                logging.warning("Generated content failed validation, using fallback content")
                tweet_text = random.choice(self.generator.FALLBACK_INSIGHTS[topic])

            tweet_text = f"{tweet_text} #{topic}"

            if tweet_text in self.posted_tweets:
                logging.info("Tweet content already posted, trying alternative content")
                return

            # Post tweet with retry mechanism
            self._post_tweet_with_retry(tweet_text)
            
        except Exception as e:
            logging.error(f"Error in post_tweet: {str(e)}")
            # Continue execution despite errors

def main():
    """Main function to run the Twitter bot"""
    setup_logging()
    logging.info("Starting Twitter bot")
    
    try:
        bot = TwitterBot()
        
        # Define posting times in 24-hour format
        posting_times = ["09:30", "15:00", "21:00", "03:00"]
        
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