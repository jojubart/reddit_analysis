import praw
import configparser
from textblob import TextBlob
from better_profanity import profanity
from datetime import datetime

#################################################
subreddits = ["aws", "askhistorians"]
num_posts = 2
###################################################

config = configparser.ConfigParser()
config.read("config.ini")

reddit = praw.Reddit(
    client_id=config["PRAW"]["client_id"],
    client_secret=config["PRAW"]["client_secret"],
    user_agent=config["PRAW"]["user_agent"],
    username=config["PRAW"]["username"],
    password=config["PRAW"]["password"],
)

# Output: redditdev
# print(subreddit.title)
# Output: reddit development
# print(subreddit.description)

for subreddit in subreddits:

    subreddit = reddit.subreddit(subreddit)
    subreddit_json = {
        "url": subreddit.url,
        "title": subreddit.title,
        "subscribers": subreddit.subscribers,
        "description_short": subreddit.public_description,
        "description_long": subreddit.description,
        "creation_date": str(datetime.utcfromtimestamp(
            subreddit.created_utc).strftime('%Y/%m/%d')),
        "over18": subreddit.over18,
    }
    print(subreddit.display_name)

    for submission in subreddit.top("day", limit=num_posts):
        timestamp_submssion = str(datetime.utcfromtimestamp(
            submission.created_utc).strftime('%Y/%m/%d %H:%M:%S'))
        submission_json = {
            "timestamp": timestamp_submssion,
            "submission_id": submission.id,
            "subreddit": submission.subreddit.url,
            "title": submission.title,
            "selftext": submission.selftext,
            "score": submission.score,
            "stickied": submission.stickied,
            "author": str(submission.author),
            "url": submission.url,
            "domain": submission.domain,
            "upvote_ratio": submission.upvote_ratio,
            "awards": submission.total_awards_received,
            "current_subreddit_subscribers": submission.subreddit_subscribers,
            "num_comments": submission.num_comments,
            "selfpost": submission.is_self,
            "distinguished": submission.distinguished,
            "num_awards": submission.total_awards_received,
            "contains_profanity": profanity.contains_profanity(submission.title + " " + submission.selftext)

        }

        all_comments = submission.comments.list()
        for comment in submission.comments.list():
            blob = TextBlob(comment.body)
            timestamp_comment = str(datetime.utcfromtimestamp(
                comment.created_utc).strftime('%Y/%m/%d %H:%M:%S'))
            comment_json = {
                "submission_id": submission.id,
                "timestamp": timestamp_comment,
                "comment_id": comment.id,
                "subreddit": str(comment.subreddit),
                "comment_body": comment.body,
                "author": str(comment.author),
                "score": comment.score,
                "controversiality": comment.controversiality,
                "num_awards": comment.total_awards_received,
                "is_submitter": comment.is_submitter,
                "is_root": comment.is_root,
                "stickied": comment.stickied,
                "contains_profanity": profanity.contains_profanity(comment.body),
                # [0.0, 1.0], 0.0: very objective
                "subjectivity": blob.subjectivity,
                "polarity": blob.polarity,  # [-1.0, 1.0]
            }


# subreddits = "nba+wallstreetbets"
# comment_stream = reddit.subreddit(subreddits)
# for comment in comment_stream.stream.comments():

#     timestamp = str(datetime.utcfromtimestamp(
#         comment.created_utc).strftime('%Y/%m/%d %H:%M:%S'))

#     comment_json = {
#         "timestamp": timestamp,
#         "comment_id": comment.id,
#         "subreddit": str(comment.subreddit),
#         "comment_body": comment.body,
#         "author": str(comment.author.name),
#         "submission_title": comment.submission.title,
#         "submission_score": comment.submission.score,

#     }
