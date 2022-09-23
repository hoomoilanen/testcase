import json
import redis
# creates a class so other apps can call the store
class store:

    # for redis connection
    redis_host = "localhost"
    redis_port = 6379
    redis_password = ""

    # key for the redis store and num_tweets will be used later on in the code to trim the database
    redis_key = 'tweets'
    num_tweets = 20
    # establishes connection to redis
    def __init__(self):
        self.db = r = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password
        )
        self.trim_count = 0
    # pushes the tweets to redis
    def push(self, data):
        self.db.lpush(self.redis_key, json.dumps(data))
        self.trim_count += 1

        # trims the list so it doesnt take too much memory
        if self.trim_count > 100:
            self.db.ltrim(self.redis_key, 0, self.num_tweets)
            self.trim_count = 0
    # selects 15 newest tweets for the app to display
    def tweets(self, limit=15):
        tweets = []

        for item in self.db.lrange(self.redis_key, 0, limit-1):
            tweet_obj = json.loads(item)
            tweets.append(tweet_obj)

        return tweets