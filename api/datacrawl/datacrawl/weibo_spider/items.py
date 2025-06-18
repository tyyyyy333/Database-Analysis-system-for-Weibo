import scrapy

class UserItem(scrapy.Item):
    weibo_id = scrapy.Field()
    nickname = scrapy.Field()
    verified = scrapy.Field()
    verified_type = scrapy.Field()
    followers_count = scrapy.Field()
    following_count = scrapy.Field()
    statuses_count = scrapy.Field()
    gender = scrapy.Field()
    location = scrapy.Field()
    created_at = scrapy.Field()

class TweetItem(scrapy.Item):
    post_id = scrapy.Field()
    celebrity_id = scrapy.Field()
    content = scrapy.Field()
    created_at = scrapy.Field()
    reposts_count = scrapy.Field()
    comments_count = scrapy.Field()
    likes = scrapy.Field()
    is_deleted = scrapy.Field()
    sentiment_score = scrapy.Field()

class CommentItem(scrapy.Item):
    comment_id = scrapy.Field()
    post_id = scrapy.Field()
    content = scrapy.Field()
    created_at = scrapy.Field()
    parent_id = scrapy.Field()
    user_id = scrapy.Field()
    like_count = scrapy.Field() 