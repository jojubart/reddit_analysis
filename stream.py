import praw
import configparser
from datetime import datetime


config = configparser.ConfigParser()
config.read("config.ini")

reddit = praw.Reddit(
    client_id=config["PRAW"]["client_id"],
    client_secret=config["PRAW"]["client_secret"],
    user_agent=config["PRAW"]["user_agent"],
    username=config["PRAW"]["username"],
    password=config["PRAW"]["password"],
)

print(reddit.read_only)

subreddit = reddit.subreddit("aws")

print(subreddit.display_name)
# Output: redditdev
print(subreddit.title)
# Output: reddit development
print(subreddit.description)


for submission in subreddit.top("day", limit=1):
    timestamp_submssion = str(datetime.utcfromtimestamp(
        submission.created_utc).strftime('%Y/%m/%d %H:%M:%S'))
    submission_json = {
        "timestamp": timestamp_submssion,
        "submission_id": submission.id,
        "subreddit": str(submission.subreddit),
        "title": submission.title,
        "selftext": submission.selftext,
        "score": submission.score,
        "stickied": submission.stickied,
        "author": str(submission.author),
        "url": submission.url,
        "upvote_ratio": submission.upvote_ratio,
        "awards": submission.total_awards_received,
        "subreddit_subscribers": submission.subreddit_subscribers,
        "num_comments": submission.num_comments,
        "selfpost": submission.is_self,
        "distinguished": submission.distinguished

    }

    print(submission_json)
    submission.comments.replace_more(limit=None)
    print(submission.title)
    # Output: the submission's title
    print(submission.score)
    # Output: the submission's score
    print(submission.id)
    # Output: the submission's ID
    print(submission.url)

    all_comments = submission.comments.list()
    num_comments = 0
    for comment in submission.comments.list():
        num_comments += 1
        timestamp_comment = str(datetime.utcfromtimestamp(
            comment.created_utc).strftime('%Y/%m/%d %H:%M:%S'))
        comment_json = {
            "timestamp": timestamp_comment,
            "comment_id": comment.id,
            "subreddit": str(comment.subreddit),
            "comment_body": comment.body,
            "author": str(comment.author),
            "score": comment.score,
            "controversiality": comment.controversiality,
            # "submission_title": comment.submission.title,
            # "submission_score": comment.submission.score,

        }
        print(comment_json)

print(num_comments)


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
#     print(comment_json)
