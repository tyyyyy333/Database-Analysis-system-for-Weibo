import scrapy

class UserItem(scrapy.Item):
    _id = scrapy.Field()
    nick_name = scrapy.Field()
    verified = scrapy.Field()
    verified_type = scrapy.Field()
    followers_count = scrapy.Field()
    following_count = scrapy.Field()
    statuses_count = scrapy.Field()
    gender = scrapy.Field()
    location = scrapy.Field()

class TweetItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    content = scrapy.Field()
    created_at = scrapy.Field()
    retweet_count = scrapy.Field()
    comment_count = scrapy.Field()
    like_count = scrapy.Field()
    read_count = scrapy.Field()
    is_long = scrapy.Field()
    source = scrapy.Field()
    pictures = scrapy.Field()
    video_url = scrapy.Field()

class CommentItem(scrapy.Item):
    _id = scrapy.Field()
    tweet_id = scrapy.Field()
    user_id = scrapy.Field()
    content = scrapy.Field()
    created_at = scrapy.Field()
    like_count = scrapy.Field() 